import tensorflow as tf
import numpy as np
from tensorflow.keras.layers import (Input, Conv2D, GlobalAveragePooling2D, Dense, 
                                     LSTM, Embedding, concatenate)
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import random

class MultiModalModel:
    def __init__(self, img_shape=(224, 224, 3), max_text_length=20, vocab_size=5000, action_space=3):
        self.img_shape = img_shape
        self.max_text_length = max_text_length
        self.vocab_size = vocab_size
        self.action_space = action_space  # Move to (x, y) and click
        self.tokenizer = Tokenizer(num_words=vocab_size, oov_token="<OOV>")
        self.model = self._build_model()
        self.memory = []  # Experience replay memory
        self.gamma = 0.95  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001

    def _build_model(self):
        # Image encoder
        image_input = Input(shape=self.img_shape, name="image_input")
        x = Conv2D(32, (3, 3), activation='relu')(image_input)
        x = GlobalAveragePooling2D()(x)
        x = Dense(128, activation='relu')(x)

        # Text encoder
        text_input = Input(shape=(self.max_text_length,), name="text_input")
        embedding = Embedding(input_dim=self.vocab_size, output_dim=64, mask_zero=True)(text_input)
        text_features = LSTM(64)(embedding)

        # Merge features
        merged = concatenate([x, text_features])
        merged = Dense(128, activation='relu')(merged)

        # Action output (x, y coordinates and click decision)
        action_output = Dense(self.action_space, activation='linear', name="actions")(merged)

        # Model
        model = Model(inputs=[image_input, text_input], outputs=action_output)
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate), loss='mse')

        return model

    def preprocess_text(self, texts):
        sequences = self.tokenizer.texts_to_sequences(texts)
        return pad_sequences(sequences, maxlen=self.max_text_length, padding='post')

    def train_tokenizer(self, texts):
        self.tokenizer.fit_on_texts(texts)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
        if len(self.memory) > 2000:
            self.memory.pop(0)

    def act(self, image, text):
        if np.random.rand() <= self.epsilon:
            return np.random.rand(3)  # Random (x, y, click)
        text_seq = self.preprocess_text([text])
        q_values = self.model.predict([np.expand_dims(image, axis=0), text_seq])[0]
        return q_values

    def replay(self, batch_size=32):
        if len(self.memory) < batch_size:
            return
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target += self.gamma * np.amax(self.model.predict([next_state[0], next_state[1]])[0])
            target_f = self.model.predict([state[0], state[1]])
            target_f[0][np.argmax(action)] = target
            self.model.fit([state[0], state[1]], target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

# Example usage:
# agent = RLMouseAgent()
# state = (image_data, text_data)
# action = agent.act(image_data, text_instruction)
# agent.remember(state, action, reward, next_state, done)
# agent.replay()