import sys
import numpy as np
import pyautogui
import cv2
import time
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QObject
from PseudoScreen import PseudoScreen
from CVModel import CVModel
from MatplotlibWidget import MatplotlibWidget
from tensorflow.keras.preprocessing.image import img_to_array
import keyboard
import matplotlib.pyplot as plt

stop_flag = False

class SignalEmitter(QObject):
    update_plot_signal = pyqtSignal(list, list)

signal_emitter = SignalEmitter()

def listen_for_quit():
    global stop_flag
    print("Press 'q' at any time to stop...")
    keyboard.wait('q')
    stop_flag = True

def preprocess_image(image):
    image = cv2.resize(image, (224, 224))
    image = image.astype("float32") / 255.0
    return img_to_array(image)

def capture_screenshot():
    screenshot = pyautogui.screenshot(region=(0, 0, 1920, 1080))
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
    return preprocess_image(screenshot)

def rl_thread(screen):
    agent = CVModel()
    episodes = 100
    all_rewards = []

    for episode in range(episodes):
        print(f"Episode {episode+1}/{episodes}")
        state = capture_screenshot()
        done = False
        episode_reward = 0
        for step in range(20):
            if stop_flag:
                print("Stopping RL thread mid-episode...")
                return
            print(f"  Step {step+1}/20")
            action = agent.act(state)
            x, y, click = int(action[0]), int(action[1]), int(action[2])
            print(f"    Action taken: x={x}, y={y}, click={click}")
            if click:
                print(f"    Clicking at ({x}, {y})")
                pyautogui.click(x, y)
            time.sleep(1)
            next_state = capture_screenshot()
            reward = screen.get_reward()
            episode_reward += reward
            screen.reset_reward()
            print(f"    Reward received: {reward}, Total Rewards: {screen.get_total_rewards()}")
            agent.remember(state, action, reward, next_state, done)
            state = next_state
        print(f"  Total reward for episode {episode+1}: {episode_reward}")
        all_rewards.append(episode_reward)
        signal_emitter.update_plot_signal.emit(list(range(1, episode + 1)), all_rewards)
        print(f"  Training agent...")
        agent.replay()
    plt.ioff()
    plt.show()

def main():
    app = QApplication(sys.argv)
    matplotlib_widget = MatplotlibWidget()
    matplotlib_widget.setWindowTitle("Reinforcement Learning Reward Plot")
    matplotlib_widget.resize(800, 600)
    matplotlib_widget.show()

    def update_plot_slot(x, y):
        matplotlib_widget.showRewardPlot(x, y)

    screen = PseudoScreen()

    time.sleep(5)

    print("Starting RL thread...")
    rl_thread_instance = threading.Thread(target=rl_thread, args=(screen,))
    rl_thread_instance.start()

    print("Starting Quit Listener thread...")
    quit_listener = threading.Thread(target=listen_for_quit)
    quit_listener.start()

    plt.ion()
    signal_emitter.update_plot_signal.connect(update_plot_slot)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()