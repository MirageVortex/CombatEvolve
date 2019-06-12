from collections import deque
from tqdm import tqdm, tqdm_notebook
from iPython.display import clear_output
import numpy as np
import random
import time
import tensorflow as tf
import tensorflow.contrib.slim as slim


ACTIONS = 6
neurons = 512

GAMMA = 0.99
OBSERVE = 1000
EXPLORE = 80000
INITAL_EPSILON = 1
FINAL_EPSILON = 0.05
REPLAY_MEMORY = 20000

class DeepLearner:
	def __init__(self, env):
		self.env = env
		self.model = self.buildNetwork()

	def buildNetwork(self):
		model = tf.keras.Sequential()
		model.add(tf.keras.layers.Dense(self.env.action_space.n, activation=None, use_bias=False))
		model.compile('SGD', loss=tf.keras.losses.MeanSquaredError())
		return model

	def encode_state(self, curr_state):
		encoded_state = np.identity(self.env.observation_space.n)[curr_state:curr_state+1]
		return encoded_state

	def predict(self, curr_state):
		return self.model.predict(curr_state, batch_size=1, steps=1)

	def update(self, curr_state, action, target, lr = 0.2):
		target_f = self.predict(curr_state)
		target = target_f[0][action]
		self.model.fit(curr_state, epochs=1, verbose=1, steps_per_epoch=1)

	def render(self):
		for state in range(self.env.observation_space.n):
			print(self.predict(self.encode_state(state)))

class Q_Table():
	def __init__(self, env):
		self.reset(env)

	def reset(self, env):
		self.Q = np.zeros(shape=(env.observation_space.n, env.action_space.n))

	def predict(self, state):
		return self.Q[state,:]

	def update(self, state, action, target, lr = 0.2):
		self.Q[state, action] = (1.0-lr) * self.Q[state,action] + lr * target

	def render(self):
		print(self.Q)

	def encode_state(self, state):
		return state

class Memory():
	def __init__(self, max_len=200):
		self.history = deque(maxlen = maxlen)

	def clear(self):
		self.history.clear()

	def remember(self, state, action, reward, next_state, done):
		self.history.append((state, action, reward, next_state, done))

	def get_batch(self, batch_size):
		return random.sample(self.history, min(batch_size, len(self.history)))

	def discount_rewards(self, gamma=1):
		ep_history = np.array(self.history)
		running_add = 0
		for t in reversed(range(ep_history[:,2].size)):
			running_add = running_add * gamma + ep_history[t,2]
			ep_history[t,2] = running_add
		return ep_history

def QLearning():
	def __init__(self, env, q_function):
		self.env = env
		self.lr = 0.2
		self.y = .99
		# initial start at 1
		self.epsilon = 1.0
		self.final_epsilon = 0.05
		self.epsilon_decay = .95
		self.q_function = q_function
		self.memory = Memory()

	def reset(self):
		self.Q = np.zeros(shape=(env.observation_space.n, env.action_space.n))

	def choose_action(self, state, training = True):
		if training and np.random.rand() < self.epsilon:
			return self.env.action_space.sample()

		else:
			return np.argmax(self.q_function.predict(self.q_function.encode_state))

	def replay(self, batch_size):
		batch = self.memory.get_batch(batch_size)
		for state, action, reward, next_state, done in batch:
			if not done:
				target = reward + self.y * np.amax(self.q_function.predict(next_state))
			else:
				target = reward

			self.q_function.update(state, action, target, self.lr)

		if self.epsilon > self.final_epsilon:
			self.epsilon *= self.epsilon_decay

	def train(self, num_ep = 2000, max_steps = 100):
		jList = []
		reward_list = []
		for ep in tqdm_notebook(range(num_ep)):
			state = self.env.reset()
			total_reward = 0
			done = False
			for j in range(1, max_steps):
				action = self.choose_action(state, training=True)
				next_state, reward, done = self.env.step(action)

				self.memory.remember(state, action, reward, next_state, done)
				total_reward += reward
				state = next_state
				if done:
					break
			jList.append(j)
			reward_list.append(reward)
			self.replay(32)

	def test(self, num_ep = 1, render = False):
		reward_list = []
		for ep in tqdm_notebook(range(num_ep)):
			done = False
			state = self.env.reset()
			while not done:
				if render:
					clear_output(wait=True)
					self.env.render()
					time.sleep(0.005)
				action = self.choose_action(state, training=False)
				next_state, reward, done = self.env.step(action)

			if render:
				clear_output(wait=True)
				self.env.render()
				time.sleep(.25)
			reward_list.append(reward)
		return reward_list

	def render(self):
		self.q_function.render()

