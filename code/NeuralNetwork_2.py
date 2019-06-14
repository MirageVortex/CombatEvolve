from collections import deque
import tensorflow as tf
import numpy as np
import random
import Hunter_3
import cv2

image_dim = 84
sess = tf.InteractiveSession()
pixels = image_dim**2
neurons = 512

filter1_dim = 8
filter1_depth = 32
filter1_stride = 4
filter2_dim = 4
filter2_depth = 64
filter2_stride = 2
filter3_dim = 3
filter3_depth = 64
filter3_stride = 1

actions = 6
gamma = .99
observe = 1000

initial_epsilon = 1.0
final_epsilon = 0.05
decay_rate = 0.995
replay_memory = 20000
batch = 32

frames = 3

class NeuralNetwork:
	def __init__(self):
		self.save = True;
		self.sess = tf.InteractiveSession()
		self.agent = Hunter_3.Hunter()
		self.epsilon = initial_epsilon
		self.D = deque()
		self.Holdout = deque()

		self.s, self.readout, h_fc1 = self.create_network()
		self.state = self.action = None

		self.a = tf.placeholder("float", [None, actions])
		self.y = tf.placeholder("float", [None])

		readout_action = tf.reduce_sum(tf.multiply(self.readout, self.a), reduction_indices=1)
		cost = tf.reduce_mean(tf.square(self.y - readout_action))
		self.train_step = tf.train.AdamOptimizer(1e-6).minimize(cost)
		
		
		self.t = 0
		self.sess.run(tf.initialize_all_variables())

	def weight_variable(self, shape):
		initial = tf.truncated_normal(shape, stddev=0.01)
		return tf.Variable(initial)

	def bias_variable(self, shape):
		initial = tf.constant(0.1, shape=shape)
		return tf.Variable(initial)

	def conv2d(self, x, W, stride):
		return tf.nn.conv2d(x, W, strides = [1, stride, stride, 1], padding = "VALID")

	def create_network(self):
		W_conv1 = self.weight_variable([filter1_dim, filter1_dim, frames, filter1_depth]) #8,8,4,32
		b_conv1 = self.bias_variable([filter1_depth]) #32

		W_conv2 = self.weight_variable([filter2_dim, filter2_dim, filter1_depth, filter2_depth]) #4,4,32,64
		b_conv2 = self.bias_variable([filter2_depth]) #64

		W_conv3 = self.weight_variable([filter3_dim, filter3_dim, filter2_depth, filter3_depth]) #3,3,64,64
		b_conv3 = self.bias_variable([filter3_depth]) #64

		W_fc1 = self.weight_variable([7*7*filter3_depth, neurons]) #7*7*64, 512
		b_fc1 = self.bias_variable([neurons]) #512

		W_fc2 = self.weight_variable([neurons, actions]) #512
		b_fc2 = self.bias_variable([actions])

		s = tf.placeholder(tf.float32, [None, image_dim, image_dim, frames])

		h_conv1 = tf.nn.relu(self.conv2d(s, W_conv1, filter1_stride) + b_conv1) #stride 4
		h_conv2 = tf.nn.relu(self.conv2d(h_conv1, W_conv2, filter2_stride) + b_conv2) #stride 2
		h_conv3 = tf.nn.relu(self.conv2d(h_conv2, W_conv3, filter3_stride) + b_conv3) #stride 1
		h_conv3_flat = tf.reshape(h_conv3, [-1, 7*7*filter3_depth])
		h_fc1 = tf.nn.relu(tf.matmul(h_conv3_flat, W_fc1) + b_fc1)

		# readout layer

		readout = tf.matmul(h_fc1, W_fc2) + b_fc2
		return s, readout, h_fc1


	def init_network(self, frame, ob, eval):
		x_t = self.agent.resize(self.agent.getPixels(frame))
		x_t = x_t.reshape(image_dim, image_dim)

		reward = self.agent.getReward(ob)
		terminal = False

		self.state = np.stack((x_t, x_t, x_t), axis = 2)

		readout_t = self.readout.eval(feed_dict={self.s : [self.state]})[0]
		self.action = np.zeros([actions])

		if not eval and random.random() <= self.epsilon:
			print("Random Action")
			action_index = random.randrange(actions)
			self.action[action_index] = 1
		else:
			action_index = np.argmax(readout_t)
			self.action[action_index] = 1

		return action_index

	def train_network(self, frame, ob, done):
		if self.epsilon > final_epsilon:
			self.epsilon *= decay_rate

		x_t = self.agent.resize(self.agent.getPixels(frame))
		x_t = x_t.reshape(image_dim, image_dim, 1)

		reward = self.agent.getReward(ob)

		state = np.append(x_t, self.state[:,:,:frames-1], axis = 2)

		if self.t < 2000:
			self.Holdout.append((state))

		if self.t % 1000 == 0 and self.t >= 2000:
			readout_batch = self.readout.eval(feed_dict = {self.s : list(self.Holdout)})
			readout_batch = np.array(readout_batch)

		self.D.append((self.state, self.action, reward, state, done))

		if len(self.D) > replay_memory:
			self.D.popleft()

		if self.t > observe:
			minibatch = random.sample(self.D, batch)

			state_batch = [d[0] for d in minibatch]
			action_batch = [d[1] for d in minibatch]
			reward_batch = [d[2] for d in minibatch]
			next_state_batch = [d[3] for d in minibatch]

			y_batch = []
			readout_t = self.readout.eval(feed_dict={self.s : next_state_batch})
			for i in range(0, len(minibatch)):
				done = minibatch[i][4]
				if done:
					y_batch.append(reward_batch[i])
				else:
					y_batch.append(reward_batch[i] + gamma * np.max(readout_t[i]))

			self.train_step.run(feed_dict = {
				self.y : y_batch,
				self.a : action_batch,
				self.s : state_batch}
			)

		self.state = state
		self.t += 1

		readout_t = self.readout.eval(feed_dict={self.s : [self.state]})[0]

		self.action = np.zeros([actions])
		if random.random() <= self.epsilon:
			action_index = random.randrange(actions)
			self.action[action_index] = 1
		else:
			action_index = np.argmax(readout_t)
			self.action[action_index] = 1

		return action_index

	def evalNetwork(self, frame, ob):
		
		x_t = self.agent.resize( self.agent.getPixels(frame))
		x_t = x_t.reshape(84,84,2)
		reward = self.agent.getReward(ob)

		terminal = False 
		state = np.append(x_t, self.state[:, :, :frames-1], axis = 2)
		
		self.state = state
		self.t += 1

		readout_t = self.readout.eval(feed_dict={self.s : [self.s_t]})[0]
		self.action = np.zeros([actions])
		action_index = np.argmax(readout_t)
		self.action[action_index] = 1

		if max(readout_t)> self.max:
			cv2.imwrite('hiq.png', self.agent.getPixels(frame))
			self.max = max(readout_t)
		elif max(readout_t) < self.min:
			cv2.imwrite('lowq.png', self.agent.getPixels(frame))
			self.min = max(readout_t)
				
		return action_index

