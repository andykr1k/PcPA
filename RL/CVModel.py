import tensorflow as tf
import numpy as np
import random
from tensorflow.keras.layers import Input, Conv2D, GlobalAveragePooling2D, Dense
from tensorflow.keras.models import Model

class CVModel:
    def __init__(self, img_shape=(224, 224, 3), action_space=3):
        self.img_shape = img_shape
        self.action_space = action_space  # (x, y, click)
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
            return np.array([random.randint(50, 500), random.randint(50, 300), random.choice([0, 1])])
        q_values = self.model.predict(np.expand_dims(image, axis=0))[0]
        return q_values

    def replay(self, batch_size=32):
        if len(self.memory) < batch_size:
            return
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target += self.gamma * np.amax(self.model.predict(np.expand_dims(next_state, axis=0))[0])
            target_f = self.model.predict(np.expand_dims(state, axis=0))
            target_f[0][np.argmax(action)] = target
            self.model.fit(np.expand_dims(state, axis=0), target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
