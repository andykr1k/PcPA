import sys
import numpy as np
import pyautogui
import cv2
import time
import threading
from PyQt5.QtWidgets import QApplication
from PseudoScreen import PseudoScreen
from CVModel import CVModel
from tensorflow.keras.preprocessing.image import img_to_array

def preprocess_image(image):
    image = cv2.resize(image, (224, 224))
    image = image.astype("float32") / 255.0
    return img_to_array(image)

def capture_screenshot():
    screenshot = pyautogui.screenshot(region=(100, 100, 600, 400))
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
    return preprocess_image(screenshot)

def rl_thread(screen):
    agent = CVModel()
    episodes = 100

    for episode in range(episodes):
        print(f"Episode {episode+1}/{episodes}")

        state = capture_screenshot()
        done = False

        episode_reward = 0  # Track total reward for the episode
        for step in range(20):
            print(f"  Step {step+1}/20")

            # Select action based on the current state
            action = agent.act(state)
            x, y, click = int(action[0]), int(action[1]), int(action[2])

            # Log action
            print(f"    Action taken: x={x}, y={y}, click={click}")

            # Perform the action if 'click' is 1
            if click:
                print(f"    Clicking at ({x+100}, {y+100})")  # Adjust for screen offset
                pyautogui.click(x+100, y+100)

            time.sleep(1)  # Let the UI update

            # Capture the next state (screenshot)
            next_state = capture_screenshot()

            # Get the reward from the screen (based on button clicked)
            reward = screen.get_reward()
            episode_reward += reward  # Add reward for this step

            # Log reward
            print(f"    Reward received: {reward}")

            # Store the experience in memory
            agent.remember(state, action, reward, next_state, done)

            # Transition to the next state
            state = next_state

        # Log the total reward for this episode
        print(f"  Total reward for episode {episode+1}: {episode_reward}")

        # Train the model using the experience replay
        print(f"  Training agent...")
        agent.replay()

def main():
    app = QApplication(sys.argv)
    screen = PseudoScreen()
    screen.show()

    time.sleep(5) # give time to the UI to load.
    rl_thread_instance = threading.Thread(target=rl_thread, args=(screen,))
    rl_thread_instance.start()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()