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

		self.actions = ["MoveUp", "MoveDown", "StopMoving", "TurnLeft", "TurnRight", "Attack"]
		self.rewards = {"Health":-5, "Death":-20, "Swing":-1, "Hit":30, "Kill": 80, "Distance":-0.1, "NotLook":-0.1, "Look":1}

		self.q_table = {}

		self.currentHealth = 20
		self.currentTarget = ""
		self.current_yaw = 0
		self.look_difference = 0
		self.turn_rate_scale = 90
		self.los = ""
		self.yaw = 0
		self.x_pos = 0
		self.z_pos = 0
		self.prev_action = ""

		self.enemies = {}
		self.alive = 0
		
	# get reward function
	def getReward(self, ob):
		reward = 0
		if ('MobsKilled' not in ob) or ('LineOfSight' not in ob):
			return 0

		#if self.prev_action == "Attack":
			#reward += self.rewards["Swing"]

		self.alive = len(ob['entities'])
		kills = (len(ob['entities']) - 1) - self.alive
		damage_taken = (self.currentHealth - ob['Life'])

		self.yaw = ob['Yaw']

		if (kills > 0):
			reward += kills * self.rewards['Kill']

		if (damage_taken > 0):
			reward += damage_taken * self.rewards["Health"]

		# update agent position
		self.x_pos = ob['XPos']
		self.z_pos = ob['ZPos']

		# update enemies info
		self.getEnemiesInfo(ob['entities'])
		current_enemies = [entity['id'] for entity in ob['entities'] if entity['name'] != "CombatEvolvedAI"]

		if self.currentTarget == "" or self.currentTarget not in current_enemies:
			if self.currentTarget != "":
				self.enemies.pop(self.currentTarget)
			self.currentTarget = self.getClosestEntity()
		
		if self.currentTarget != "":
			# self.look_at_target()

			distance_from_target = self.getDistance(self.x_pos, self.z_pos, self.enemies[self.currentTarget][0][0], self.enemies[self.currentTarget][0][0])
			reward += distance_from_target * self.rewards['Distance']

		self.currentHealth = ob['Life']
		self.kills = ob['MobsKilled']

		# update agent sight
		if ob['LineOfSight']["type"] in MOB_TYPES:
			reward += self.rewards['Look']
		else:
			reward += self.rewards['NotLook']


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

	def process_action(self, agent_host, action, degree = 0):
		self.prev_action = action 
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
			agent_host.sendCommand("turn -0.7")

		elif action == "TurnRight":
			agent_host.sendCommand("move 0")
			agent_host.sendCommand("turn 0.7")

		elif action == "Turn":
			agent_host.sendCommand("turn" + str(degree))

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

	def getClosestEntity(self):
		nearest_entity = ""
		distance = 999999

		for ent in self.enemies.keys():				
			x2 = self.enemies[ent][0][0]
			z2 = self.enemies[ent][0][1]

			comparable = self.getDistance(self.x_pos,x2,self.z_pos,z2)

			if comparable < distance:
				distance = comparable
				nearest_entity = ent

		return nearest_entity

	def normalize_yaw(self, yaw):
		original_yaw = yaw
		if yaw > 180.:
			factor = math.floor((yaw + 180.) / 360.)
		elif yaw < -180:
			factor = math.ceil((yaw-180.) / 360.)
		else:
			return yaw
		yaw -= 360. * factor
		return yaw

	def look_at_target(self):
		current_yaw = self.yaw
		current_target = self.enemies[self.currentTarget]
		best_yaw = math.degrees(math.atan2(current_target[0][1] - self.z_pos, 
			current_target[0][0] - self.x_pos)) - 90
		difference = self.normalize_yaw(best_yaw - current_yaw);
		difference /= self.turn_rate_scale
		threshold = 0.0

		if difference < threshold and difference > 0:
			difference = threshold

		elif difference > -threshold and difference < 0:
			difference = -threshold

		self.look_difference = difference

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