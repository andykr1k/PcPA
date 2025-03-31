import speech_recognition as sr
import pyttsx3
import webbrowser
import platform
import subprocess
import shlex
import traceback
import logging
from enum import Enum, auto
from threading import Thread, Event
from PyQt5.QtCore import QObject, pyqtSignal

try:
    from Utils import config
except ImportError:
    logging.error("Failed to import config module. Check the folder name case.")
    class DummyConfig:
        COMMANDS = {}
        RESPONSES = {"greeting": "Yes?", "goodbye": "Goodbye!"}
        EXIT_PHRASES = ["exit", "quit", "goodbye"]
        APP_MAP = {}
        VOICE_TIMEOUT = 5
        VOICE_PHRASE_TIME_LIMIT = 10
    config = DummyConfig()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ListeningState(Enum):
    """States for the voice controller state machine"""
    INACTIVE = auto()        # Not listening at all
    WAIT_WAKE_WORD = auto()  # Listening for wake word
    WAIT_COMMAND = auto()    # Listening for command after wake word
    SPEAKING = auto()        # Currently speaking, will return to previous state after

class VoiceController(QObject):
    # Signals for UI updates
    command_received = pyqtSignal(str)
    minimize_window = pyqtSignal()
    close_window = pyqtSignal()
    show_window = pyqtSignal()

    # Signals for face animation based on speech
    started_speaking = pyqtSignal()
    finished_speaking = pyqtSignal()
    
    # New signal for error reporting
    error_occurred = pyqtSignal(str)

    def __init__(self, window=None):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.engine = None
        self.current_os = platform.system().lower()
        self.state = ListeningState.INACTIVE
        
        # Events for thread synchronization
        self.stop_event = Event()
        self.speech_finished_event = Event()
        self.speech_finished_event.set()  # Initially not speaking
        
        # Initialize configuration
        self._init_config()
        
        # Initialize TTS engine
        if not self._init_tts_engine():
            self.error_occurred.emit("Failed to initialize TTS engine")
        
        # Initialize recognition components in the listener thread
        self.listener_thread = None
        
    def _init_config(self):
        """Load configuration from config module"""
        try:
            self.commands = config.COMMANDS
            self.responses = config.RESPONSES
            self.exit_phrases = config.EXIT_PHRASES
            self.app_map = config.APP_MAP.get(self.current_os, {})
            self.voice_timeout = getattr(config, 'VOICE_TIMEOUT', 5)
            self.voice_phrase_limit = getattr(config, 'VOICE_PHRASE_TIME_LIMIT', 10)
            logging.info("Configuration loaded successfully")
        except AttributeError as e:
            logging.error(f"Failed to load configuration: {e}")
            # Set defaults to prevent crashes
            self.commands = {}
            self.responses = {"greeting": "Yes?", "goodbye": "Goodbye!"}
            self.exit_phrases = ["exit", "quit", "goodbye"]
            self.app_map = {}
            self.voice_timeout = 5
            self.voice_phrase_limit = 10
            
    def _init_tts_engine(self):
        """Initialize TTS engine with proper error handling"""
        try:
            logging.info("Initializing TTS engine")
            self.engine = pyttsx3.init()
            
            # Configure the engine
            self.engine.setProperty('rate', 180)
            self.engine.setProperty('volume', 0.9)
            
            # Connect speech callbacks
            self.engine.connect('started-utterance', self._on_speak_start)
            self.engine.connect('finished-utterance', self._on_speak_finish)
            
            # Get some property to verify engine is working
            voices = self.engine.getProperty('voices')
            voice_info = f"(Found {len(voices)} voices)" if voices else ""
            logging.info(f"TTS engine initialized successfully {voice_info}")
            
            return True
        except Exception as e:
            logging.error(f"Failed to initialize TTS engine: {e}")
            logging.error(traceback.format_exc())
            self.engine = None
            return False
    
    def _on_speak_start(self, name):
        """Callback when TTS starts speaking"""
        logging.debug(f"TTS started speaking (name={name})")
        self.speech_finished_event.clear()  # Mark that speaking has started
        self.started_speaking.emit()
        
    def _on_speak_finish(self, name, completed):
        """Callback when TTS finishes speaking"""
        logging.debug(f"TTS finished speaking (name={name}, completed={completed})")
        self.speech_finished_event.set()  # Mark that speaking has finished
        self.finished_speaking.emit()
    
    def start_listening(self):
        """Start the listening process"""
        if self.state != ListeningState.INACTIVE:
            logging.info("Already listening, ignoring start request")
            return
            
        if not self.engine:
            self.error_occurred.emit("Cannot start listening - TTS Engine not initialized")
            return
            
        logging.info("Starting listener thread")
        self.stop_event.clear()  # Clear the stop event flag
        
        # Create a new thread if needed (can't restart a stopped thread)
        if not self.listener_thread or not self.listener_thread.is_alive():
            self.listener_thread = Thread(target=self._listen_loop, daemon=True)
            self.listener_thread.start()
            
        self.state = ListeningState.WAIT_WAKE_WORD
    
    def stop_listening(self):
        """Signal the listening thread to stop"""
        if self.state == ListeningState.INACTIVE:
            return
            
        logging.info("Stopping listener thread")
        self.stop_event.set()  # Signal the thread to stop
        self.state = ListeningState.INACTIVE
    
    def speak(self, text):
        if not self.engine:
            logging.error("TTS Engine not available. Cannot speak.")
            self.speech_finished_event.set()
            return
            
        previous_state = self.state
        self.state = ListeningState.SPEAKING
        
        try:
            logging.debug(f"Speaking: '{text}'")
            self.speech_finished_event.clear()
            self.engine.say(text)
            
            # Use a timeout to prevent blocking forever
            self.engine.runAndWait()
            
            # Ensure we don't get stuck if the callback fails
            if not self.speech_finished_event.is_set():
                logging.warning("Speech finished event not set by callback, setting manually")
                self.speech_finished_event.set()
                self.finished_speaking.emit()  # Make sure to emit the signal too
        except Exception as e:
            logging.error(f"Error during speak: {e}")
            logging.error(traceback.format_exc())
            self.speech_finished_event.set()
            self.finished_speaking.emit()  # Ensure signal is emitted
            
            try:
                self.engine.stop()
            except Exception as stop_e:
                logging.error(f"Error stopping engine: {stop_e}")
        
        # Ensure state is restored even if exceptions occurred
        self.state = previous_state
    
    def _listen_loop(self):
        """Main listening loop that runs in a separate thread"""
        mic_retry_delay = 3
        noise_adjust_duration = 1.0
        
        try:
            # Initialize microphone once outside the loop
            with sr.Microphone() as source:
                logging.info(f"Microphone '{source.device_index}' opened")
                
                # Main listening loop
                while not self.stop_event.is_set():
                    try:
                        # Adjust for ambient noise periodically
                        self.recognizer.adjust_for_ambient_noise(source, duration=noise_adjust_duration)
                        
                        # Handle different states
                        if self.state == ListeningState.WAIT_WAKE_WORD:
                            self._listen_for_wake_word(source)
                        elif self.state == ListeningState.WAIT_COMMAND:
                            self._listen_for_command(source)
                        elif self.state == ListeningState.SPEAKING:
                            # If we're speaking, wait a bit before checking again
                            # This avoids consuming CPU while waiting for speech to finish
                            self.speech_finished_event.wait(timeout=0.1)
                            
                    except sr.WaitTimeoutError:
                        # Timeouts are normal during listening, no need to log
                        continue
                    except sr.UnknownValueError:
                        # Unrecognized speech is normal, no need to log
                        continue
                    except sr.RequestError as e:
                        logging.error(f"Speech recognition service error: {e}")
                        if self.state == ListeningState.WAIT_COMMAND:
                            self.speak(self.responses.get("speech_service_error", "Sorry, speech service failed."))
                            self.state = ListeningState.WAIT_WAKE_WORD
                    except Exception as e:
                        logging.error(f"Error in listening loop: {e}")
                        logging.error(traceback.format_exc())
                        # Wait a bit before retrying to avoid rapid error loops
                        if self.stop_event.wait(timeout=1):
                            break  # Stop was requested during wait
                    
        except (OSError, AttributeError) as e:
            logging.error(f"Microphone error: {e}")
            self.error_occurred.emit(f"Microphone error: {e}")
        except Exception as e:
            logging.error(f"Fatal error in listener thread: {e}")
            logging.error(traceback.format_exc())
            self.error_occurred.emit(f"Fatal error: {e}")
        
        logging.info("Listener thread terminated")
    
    def _listen_for_wake_word(self, source):
        """Listen specifically for the wake word"""
        logging.debug("Listening for wake word...")
        
        # Listen for audio
        audio = self.recognizer.listen(
            source, 
            timeout=self.voice_timeout,
            phrase_time_limit=self.voice_phrase_limit
        )
        
        # Recognize the speech
        text = self.recognizer.recognize_google(audio).lower()
        logging.debug(f"Heard: '{text}'")
        
        # Check for wake word
        if "hey jarvis" in text:  # Could be made configurable
            logging.info("Wake word detected!")
            self.show_window.emit()
            
            # # Speak greeting
            # self.speak(self.responses.get("greeting", "Yes?"))
            
            # # Wait for speech to finish 
            # self.speech_finished_event.wait()
            
            # Transition to command listening state
            self.state = ListeningState.WAIT_COMMAND
    
    def _listen_for_command(self, source):
        """Listen for and process commands after wake word is detected"""
        logging.debug("Listening for command...")
        
        # Listen with slightly longer timeouts for commands
        audio = self.recognizer.listen(
            source, 
            timeout=self.voice_timeout + 3,
            phrase_time_limit=self.voice_phrase_limit + 4
        )
        
        # Recognize the speech
        text = self.recognizer.recognize_google(audio).lower()
        logging.info(f"Command recognized: '{text}'")
        
        # Process the command
        self._process_command(text)
    
    def _process_command(self, text):
        """Process the recognized command text"""
        logging.info(f"Processing command: '{text}'")
        self.command_received.emit(text)
        
        # Check for exit phrases
        if any(phrase in text for phrase in self.exit_phrases):
            logging.info("Exit phrase detected")
            # self.speak(self.responses.get("goodbye", "Goodbye!"))
            # self.speech_finished_event.wait()  # Wait for goodbye to finish
            self.close_window.emit()
            self.stop_listening()
            return
        
        # Process other commands
        command_executed = False
        matched_command = None
        
        # Sort commands by length for better matching
        sorted_command_phrases = sorted(self.commands.keys(), key=len, reverse=True)
        
        for command_phrase in sorted_command_phrases:
            if command_phrase in text:
                details = self.commands[command_phrase]
                matched_command = command_phrase
                logging.info(f"Matched command phrase: '{command_phrase}'")
                
                command_type = details.get("type")
                action = details.get("action")
                
                try:
                    # Execute command based on type
                    if command_type == "url":
                        command_executed = self._execute_url_command(action)
                    elif command_type == "app":
                        command_executed = self._execute_app_command(action)
                    elif command_type in ["shell", "shell_speak"]:
                        command_executed = self._execute_shell_command(command_type, action)
                    elif command_type == "speak":
                        command_executed = self._execute_speak_command(action)
                    else:
                        logging.warning(f"Unknown command type '{command_type}' for phrase '{command_phrase}'")
                except Exception as e:
                    logging.error(f"Error executing command '{command_phrase}': {e}")
                    logging.error(traceback.format_exc())
                    # self.speak(self.responses.get("error_execute", "Sorry, an error occurred while doing that."))
                
                # Stop looking for more commands once we find a match
                break
        
        # Handle post-execution actions
        if command_executed:
            logging.info("Command executed successfully")
            self.minimize_window.emit()
            # self.speak(self.responses.get("anything_else", "Is there anything else?"))
            # Stay in command listening state
        elif matched_command:
            logging.info("Command matched but failed execution")
            # self.speak(self.responses.get("anything_else", "Is there anything else I can try?"))
            # Stay in command listening state
        else:
            logging.info(f"No matching command found for: '{text}'")
            # self.speak(self.responses.get("unknown_command", "Sorry, I don't know how to do that."))
            # self.speak(self.responses.get("anything_else", "Is there anything else?"))
            # Stay in command listening state
    
    def _execute_url_command(self, url):
        """Execute a URL command"""
        logging.info(f"Opening URL: {url}")
        # self.speak(self.responses.get("opening_url", "Opening website."))
        webbrowser.open(url)
        return True
    
    def _execute_app_command(self, app_name):
        """Execute an application command"""
        app_command_str = self._get_open_command(app_name)
        if not app_command_str:
            logging.error(f"Could not generate command for app '{app_name}'")
            # self.speak(self.responses.get("error_execute", "Error preparing app command."))
            return False
            
        logging.info(f"Running app command: `{app_command_str}`")
        # self.speak(self.responses.get("opening_app", "Opening application."))
        
        try:
            result = subprocess.run(
                app_command_str, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=False,  # Don't raise exception on non-zero exit
                timeout=10
            )
            
            if result.returncode != 0:
                logging.warning(f"App command returned non-zero exit code {result.returncode}: {result.stderr}")
            
            return True  # Consider it executed even if there was an error
        except subprocess.TimeoutExpired:
            logging.error(f"App command timed out: {app_command_str}")
            return False
        except Exception as e:
            logging.error(f"Error running app command: {e}")
            return False
    
    def _execute_shell_command(self, command_type, action):
        """Execute a shell command"""
        # Get OS-specific command
        shell_action_str = action.get(self.current_os) if isinstance(action, dict) else action
        
        if not shell_action_str:
            logging.warning(f"Shell command not supported on OS '{self.current_os}'")
            # self.speak(self.responses.get("os_not_supported", "Sorry, that command isn't available on your system."))
            return False
            
        logging.info(f"Running shell command: `{shell_action_str}`")
        # self.speak(self.responses.get("running_command", "Running command."))
        
        try:
            result = subprocess.run(
                shell_action_str, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=True,  # Raise exception on non-zero exit
                timeout=15
            )
            
            # Handle shell_speak type to speak the output
            if command_type == "shell_speak" and result.stdout:
                response_text = result.stdout.strip()
                logging.info(f"Shell speak response: '{response_text}'")
                # self.speak(f"{self.responses.get('speaking_response', 'Okay:')} {response_text}")
                
            return True
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.strip() if e.stderr else e.stdout.strip()
            error_msg = error_output if error_output else f"Command failed with exit code {e.returncode}."
            logging.error(f"Shell command failed: {error_msg}")
            # self.speak(f"{self.responses.get('error_execute', 'Command failed:')} {error_msg[:100]}")
            return False
        except subprocess.TimeoutExpired:
            logging.error(f"Shell command timed out: {shell_action_str}")
            # self.speak(self.responses.get("error_timeout", "The command took too long to respond."))
            return False
        except Exception as e:
            logging.error(f"Error running shell command: {e}")
            # self.speak(self.responses.get("error_execute", "Error running command."))
            return False
    
    def _execute_speak_command(self, text):
        """Execute a speak command"""
        logging.info(f"Speaking: '{text}'")
        # self.speak(text)
        return True
    
    def _get_open_command(self, app_name_key):
        """Get the appropriate open command based on OS and config mapping"""
        # Use lowercase for matching keys in the map
        app_name = self.app_map.get(app_name_key.lower(), app_name_key)
        logging.info(f"Opening app. Key='{app_name_key}', Mapped Name='{app_name}', OS='{self.current_os}'")
        
        try:
            if self.current_os == "darwin":  # macOS
                return f"open -a '{app_name}'"
            elif self.current_os == "windows":
                # Handle URI schemes
                if ":" in app_name and not app_name.startswith("http"):
                    return f'start "" "{app_name}"'
                else:
                    return f'start "" "{app_name}"'
            elif self.current_os == "linux":
                return shlex.quote(app_name)
            else:
                logging.warning(f"Unknown OS '{self.current_os}', using basic quote for app '{app_name}'")
                return shlex.quote(app_name)
        except Exception as e:
            logging.error(f"Failed to generate open command for '{app_name_key}': {e}")
            return None