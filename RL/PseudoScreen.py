import random
from PyQt5.QtWidgets import QWidget, QPushButton
from PyQt5.QtCore import QRect, pyqtSignal

class PseudoScreen(QWidget):
    reward_updated = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Button Reward Game")

        self.buttons = {
            "Red": QPushButton("Red Button", self),
            "Green": QPushButton("Green Button", self),
            "Blue": QPushButton("Blue Button", self)
        }

        self.rewards = {"Red": 0, "Green": 1, "Blue": 0}
        self.last_reward = -1
        self.total_rewards = 0
        self.showFullScreen()

        for color, button in self.buttons.items():
            button.setStyleSheet(f"background-color: {color.lower()}; color: white; font-size: 14px;")
            button.clicked.connect(lambda _, c=color: self.button_clicked(c))

        self.randomize_positions()

    def button_clicked(self, color):
        self.last_reward = self.rewards[color]
        print(f"You clicked {color}! Reward: {self.last_reward}")
        self.reward_updated.emit(self.last_reward)
        self.randomize_positions()

    def randomize_positions(self):
        screen_width = self.width()
        screen_height = self.height()

        for button in self.buttons.values():
            x = random.randint(0, screen_width - 100)
            y = random.randint(0, screen_height - 40)
            button.setGeometry(QRect(x, y, 100, 40))

    def get_reward(self):
        return self.last_reward if self.last_reward != -1 else -1

    def get_total_rewards(self):
        return self.last_reward

    def add_rewards(self, reward):
        self.total_rewards += reward

    def reset_reward(self):
        self.last_reward = -1