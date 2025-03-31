import sys
from PyQt5.QtWidgets import QApplication
from UI.display import MainWindow
from Voice.voice_control import VoiceController

def main():
    app = QApplication(sys.argv)

    window = MainWindow()

    voice_controller = VoiceController(window)

    window.setup_voice_controller(voice_controller)

    voice_controller.start_listening()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()