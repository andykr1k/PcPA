import tensorflow as tf
import numpy as np
import random
from tensorflow.keras.layers import Input, Conv2D, GlobalAveragePooling2D, Dense
from tensorflow.keras.models import Model

physical_devices = tf.config.list_physical_devices('GPU')
if physical_devices:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)
    print("Using GPU for training!")
else:
    print("GPU is not available. Using CPU.")

class CVModel:
    def __init__(self, img_shape=(224, 224, 3), action_space=3, screen_width=1920, screen_height=1080):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.img_shape = img_shape

        # Define the discrete action space (grid of x, y, and click)
        self.actions = []
        step_size = 10
        for x in range(0, self.screen_width, step_size):
            for y in range(0, self.screen_height, step_size):
                for click in [0, 1]:  # 0: No click, 1: Click
                    self.actions.append((x, y, click))

        self.action_space = len(self.actions)  # Number of possible actions
        self.learning_rate = 0.001
        self.model = self._build_model()
        self.memory = []  # Experience replay memory
        self.gamma = 0.95  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995

    def _build_model(self):
        image_input = Input(shape=self.img_shape, name="image_input")
        x = Conv2D(32, (3, 3), activation='relu')(image_input)
        x = GlobalAveragePooling2D()(x)
        x = Dense(128, activation='relu')(x)

        # Output layer: One output per action in the discrete action space
        action_output = Dense(self.action_space, activation='linear', name="actions")(x)

        model = Model(inputs=image_input, outputs=action_output)
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate), loss='mse')

        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
        if len(self.memory) > 2000:
            self.memory.pop(0)

    def act(self, image):
        if np.random.rand() <= self.epsilon:
            # Random action: choose a random action from the discrete action space
            return random.choice(self.actions)

        # Predict Q-values for all actions and return the action with the highest Q-value
        q_values = self.model.predict(np.expand_dims(image, axis=0))[0]
        best_action_index = np.argmax(q_values)
        return self.actions[best_action_index]

    def replay(self, batch_size=32):
        if len(self.memory) < batch_size:
            return

        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            # Get the index of the action
            action_index = self.actions.index(action)

            # Predict the current Q-values for the state
            target = self.model.predict(np.expand_dims(state, axis=0))[0]

            # Predict the next Q-values for the next state
            future_q = self.model.predict(np.expand_dims(next_state, axis=0))[0]
            target_q_value = reward
            if not done:
                target_q_value += self.gamma * np.max(future_q)

            # Update the Q-value for the taken action
            target[action_index] = target_q_value

            # Train the model with the new target
            self.model.fit(np.expand_dims(state, axis=0), np.expand_dims(target, axis=0), epochs=1, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

