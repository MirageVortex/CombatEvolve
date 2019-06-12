import json
import random
import math
import sys
import time
import numpy as np
import cv2
from collections import deque

MOB_TYPES = ["Zombie", "Creeper", "Spider", "Skeleton"]

class Hunter:
	""" Tabular Q-learning agent """

	def __init__(self):
		self.reward = 0
		self.n = 1
		self.gamma = 1
		self.epsilon = 0.3
		self.alpha = 0.3

		self.actions = ["MoveUp", "MoveDown", "StopMoving", "TurnLeft", "TurnRight", "Attack"]
		self.rewards = {"Health":-5, "Death":-100, "Look":1, "Hit":100, "Kill": 200, "Win":300}

		self.q_table = {}

		self.currentHealth = 20
		self.currentTarget = ""
		self.los = ""
		self.x_pos = 0
		self.z_pos = 0

		self.enemies = {}
		self.alive = 0
		
	# get reward function
	def getReward(self, ob):
		reward = 0

		if ('MobsKilled' not in ob) or ('LineOfSight' not in ob):
			return 0

		self.alive = len(ob['entities'])
		kills = (len(ob['entities']) - 1) - self.alive
		damage_taken = (self.currentHealth - ob['Life'])

		if (kills > 0):
			reward += kills * self.rewards['Kill']

		if (damage_taken > 0):
			reward += damage_taken * self.rewards["Health"]

		# update agent position
		self.x_pos = ob['XPos']
		self.z_pos = ob['ZPos']

		# update enemies info
		self.getEnemiesInfo(ob['entities'])

		self.currentHealth = ob['Life']
		self.kills = ob['MobsKilled']

		# update agent sight
		self.los = ob['LineOfSight']["type"]
		if (self.los in MOB_TYPES):
			reward += self.rewards['Look']

		self.reward += reward

		return reward

	def choose_action(self, curr_state, possible_actions):
		if curr_state not in self.q_table:
			self.q_table[curr_state] = {}
		for action in possible_actions:
			if action not in self.q_table[curr_state]:
				self.q_table[curr_state][action] = 0

		possible_action_list = {}

		for action in self.q_table[curr_state].items():
			if (len(possible_action_list) == 0 or action[1] == list(possible_action_list.values())[0]):
				possible_action_list[action[0]] = action[1]
			elif (action[1] > list(possible_action_list.values())[0]):
				possible_action_list = {}
				possible_action_list[action[0]] = action[1]

		rnd = random.random()

		if rnd <= self.epsilon:
			return random.choice(possible_actions)
		else:
			return random.choice(list(possible_action_list.keys()))

	def process_action(self, agent_host, action):
		if action == "StopMoving":
			agent_host.sendCommand("setYaw 90")
			agent_host.sendCommand("move 0")
			agent_host.sendCommand("turn 0")

		elif action == "MoveUp":
			agent_host.sendCommand("setYaw 90")
			agent_host.sendCommand("move 1")
			agent_host.sendCommand("turn 0")

		elif action == "MoveDown":
			agent_host.sendCommand("setYaw 90")
			agent_host.sendCommand("move -1")
			agent_host.sendCommand("turn 0")

		elif action == "TurnLeft":
			agent_host.sendCommand("move 0")
			agent_host.sendCommand("turn -0.5")

		elif action == "TurnRight":
			agent_host.sendCommand("move 0")
			agent_host.sendCommand("turn 0.5")

		elif action == "Attack":
			agent_host.sendCommand("attack 1")
			agent_host.sendCommand("attack 0")

	def get_current_state(self):
		curr_state = []

		curr_state.append(("CombatEvolvedAI", (self.x_pos,self.z_pos), self.currentHealth))
		curr_state.append(("Target", self.currentTarget))
		for enemy in self.enemies.keys():
			distance = self.getDistance(self.x_pos, self.z_pos, self.self.enemies[enemy][0][0], self.enemies[enemy][0][1])
			curr_state.append((enemy, distance, self.enemies[enemy][1]))

		curr_state.append(("los", self.los))

		return tuple(curr_state)


	# Helper Functions
	def getDistance(self, x1, z1, x2, z2):
		return ((x1 - x2)**2 + (z1 - z2)**2)**0.5

	def getEnemiesInfo(self, entities):
		for ent in entities:	
			name = ent['name']
			if name in MOB_TYPES:
				key = ent['id']
				enemy_health = ent['life']
				if key in self.enemies.keys():
					self.reward += (self.enemies[key][1] - enemy_health) * self.rewards["Hit"]
				self.enemies[key] = ((ent['x'], ent['z']), enemy_health)

	def getPixels(self, frame):                                    
		width = frame.width                                
		height = frame.height                              
		channels = frame.channels                          
		pixels = np.array(frame.pixels, dtype = np.uint8)       
		img = np.reshape(pixels, (height, width, channels))                        
		return img      
														   
	def resize(self, image):
		return cv2.cvtColor(cv2.resize(image, (84, 84)), cv2.COLOR_RGB2GRAY)
	
	def threshold(self, image):
		retval, th_image = cv2.threshold(image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
		return th_image