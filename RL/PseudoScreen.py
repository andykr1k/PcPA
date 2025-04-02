import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import QRect

class PseudoScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Button Reward Game")
        self.setGeometry(100, 100, 600, 400)

        self.buttons = {
            "Red": QPushButton("Red Button", self),
            "Green": QPushButton("Green Button", self),
            "Blue": QPushButton("Blue Button", self)
        }

        self.rewards = {"Red": 0, "Green": 1, "Blue": 0}
        self.last_reward = 0  # Store the last reward received
        self.total_rewards = 0

        for color, button in self.buttons.items():
            button.setStyleSheet(f"background-color: {color.lower()}; color: white; font-size: 14px;")
            button.clicked.connect(lambda _, c=color: self.button_clicked(c))

        self.randomize_positions()

    def button_clicked(self, color):
        self.last_reward = self.rewards[color]
        print(f"You clicked {color}! Reward: {self.last_reward}")
        self.randomize_positions()

    def randomize_positions(self):
        for button in self.buttons.values():
            x, y = random.randint(50, 500), random.randint(50, 300)
            button.setGeometry(QRect(x, y, 100, 40))

    def get_reward(self):
        return self.last_reward

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PseudoScreen()
    window.show()
    sys.exit(app.exec_())