# Voice recognition settings
VOICE_TIMEOUT = 1  # seconds to wait for phrase start
VOICE_PHRASE_TIME_LIMIT = 5  # max seconds for a phrase

# Window settings
MINIMIZED_X = 20
MINIMIZED_Y = 20
MINIMIZED_WIDTH = 200
MINIMIZED_HEIGHT = 150
MINIMIZED_FACE_WIDTH = 180  # Slightly smaller than window
MINIMIZED_FACE_HEIGHT = 130 # Slightly smaller than window
BORDER_WIDTH = 5
MAXIMIZED_FACE_SCALE_W = 0.8 # Face width as % of screen width when maximized
MAXIMIZED_FACE_SCALE_H = 0.8 # Face height as % of screen height when maximized


# Animation settings
ANIMATION_FPS = 15 # Frames per second for face animation
GRADIENT_UPDATE_INTERVAL = 50  # milliseconds for border animation speed

# Commands - SINGLE SOURCE OF TRUTH
# Use _get_open_command for cross-platform app opening
# Use direct shell commands for specific actions
COMMANDS = {
    # Web Browse
    "open youtube": {"type": "url", "action": "https://youtube.com"},
    "open google": {"type": "url", "action": "https://google.com"},
    "open fireship": {"type": "url", "action": "https://www.youtube.com/@Fireship"}, # Example specific channel

    # Applications (Use placeholder names, _get_open_command will resolve)
    "open chrome": {"type": "app", "action": "Google Chrome"}, # Use exact app name for macOS/Windows if known
    "open browser": {"type": "app", "action": "Google Chrome"}, # Generic alias
    "open safari": {"type": "app", "action": "Safari"},
    "open terminal": {"type": "app", "action": "Terminal"}, # macOS/Linux default
    "open command prompt": {"type": "app", "action": "cmd"}, # Windows
    "open finder": {"type": "app", "action": "Finder"}, # macOS
    "open explorer": {"type": "app", "action": "explorer"}, # Windows
    "open mail": {"type": "app", "action": "Mail"}, # macOS Default
    "open outlook": {"type": "app", "action": "Outlook"}, # Windows often
    "open calendar": {"type": "app", "action": "Calendar"},
    "open messages": {"type": "app", "action": "Messages"}, # macOS
    "open photos": {"type": "app", "action": "Photos"}, # macOS
    "open settings": {"type": "app", "action": "System Settings"}, # Newer macOS name
    "open system preferences": {"type": "app", "action": "System Preferences"}, # Older macOS name
    "open control panel": {"type": "app", "action": "control"}, # Windows

    # System Actions (OS specific commands)
    "go to sleep": {"type": "shell", "action": {"darwin": "pmset sleepnow", "windows": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0", "linux": "systemctl suspend"}},
    "lock screen": {"type": "shell", "action": {"darwin": "pmset displaysleepnow", "windows": "rundll32.exe user32.dll,LockWorkStation", "linux": "xdg-screensaver lock"}}, # Linux might vary
    "what time is it": {"type": "shell_speak", "action": {"darwin": "date '+%I:%M %p'", "windows": "time /T", "linux": "date '+%I:%M %p'"}},
    "what's the date": {"type": "shell_speak", "action": {"darwin": "date '+%A, %B %d, %Y'", "windows": "date /T", "linux": "date '+%A, %B %d, %Y'"}},

    # Add more commands here...
    "tell me a joke": {"type": "speak", "action": "Why don't scientists trust atoms? Because they make up everything!"},
}

# Voice responses
RESPONSES = {
    "greeting": "Yes? How can I help you?",
    "listening": "I'm listening.",
    "executing": "Right away.",
    "opening_url": "Opening that website for you.",
    "opening_app": "Opening that application.",
    "running_command": "Running that command.",
    "speaking_response": "Okay, here is the result.",
    "unknown_command": "Sorry, I didn't understand that command.",
    "goodbye": "Goodbye!",
    "anything_else": "Is there anything else I can help you with?",
    "error_execute": "Sorry, I encountered an error trying to do that.",
    "error_speak": "Sorry, I had trouble getting that information.",
}

# Exit phrases
EXIT_PHRASES = ["no thank you", "no thanks", "that's all", "goodbye", "exit", "quit", "nothing else", "nope"]

# --- Platform Specific Mappings ---
# These help _get_open_command find the right executable/command name
APP_MAP = {
    "darwin": {
        "google chrome": "Google Chrome",
        "chrome": "Google Chrome",
        "safari": "Safari",
        "terminal": "Terminal",
        "finder": "Finder",
        "mail": "Mail",
        "calendar": "Calendar",
        "messages": "Messages",
        "photos": "Photos",
        "system settings": "System Settings", # Newer macOS
        "system preferences": "System Preferences", # Older macOS
        "textedit": "TextEdit",
        "notes": "Notes",
        "vscode": "Visual Studio Code",
    },
    "windows": {
        "google chrome": "chrome",
        "chrome": "chrome",
        "edge": "msedge",
        "firefox": "firefox",
        "command prompt": "cmd",
        "cmd": "cmd",
        "explorer": "explorer",
        "mail": "outlook", # Often default
        "outlook": "outlook",
        "calendar": "outlookcal:", # URI scheme
        "settings": "start ms-settings:", # URI scheme
        "control panel": "control",
        "notepad": "notepad",
        "vscode": "code",
        "task manager": "taskmgr",
    },
    "linux": {
        "google chrome": "google-chrome",
        "chrome": "google-chrome", # Or just 'chrome' sometimes
        "firefox": "firefox",
        "terminal": "gnome-terminal", # Common examples, might vary
        "konsole": "konsole",
        "files": "nautilus", # Gnome default file manager
        "dolphin": "dolphin", # KDE default file manager
        "mail": "thunderbird", # Common mail client
        "calendar": "gnome-calendar", # Example
        "settings": "gnome-control-center", # Example
        "text editor": "gedit", # Example
        "vscode": "code",
    }
}