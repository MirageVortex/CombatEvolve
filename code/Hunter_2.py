import json
import random
import math
import sys
import time
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
		self.rewards = {"Health":-20, "Death":-100, "Look":5, "Hit":10, "Kill": 50, "Win":100}

		self.q_table = {}

		self.currentHealth = 20
		self.currentTarget = ""
		self.los = ""
		self.x_pos = 0
		self.z_pos = 0

		self.enemies = {}
		self.kills = 0
		
	# get reward function
	def getReward(self, agent_host):
		reward = 0
		count = 0
		world_state = agent_host.getWorldState()
		print("world_state",world_state.number_of_observations_since_last_state)
		if world_state.number_of_observations_since_last_state > 0:
			msg = world_state.observations[-1].text
			ob = json.loads(msg)
			print(ob)
			if ('MobsKilled' not in ob) or ('LineOfSight' not in ob):
				return 0

			kills = ob['MobsKilled'] - self.kills
			damage_taken = (self.currentHealth - ob['Life'])

			if (kills > 0):
				reward += kills * self.rewards['Kill']

			if (damage_taken > 0):	
				reward += damage_taken * self.rewards["Health"]

			# update agent position
			self.x_pos = ob['XPos']
			self.z_pos = ob['ZPos']

			# update enemies info
			print("updating")
			self.getEnemiesInfo(ob['entities'])

			if (self.currentTarget == "" or kills > 0):
				if self.currentTarget in self.enemies.keys():
					self.enemies.pop(self.currentTarget)
				self.currentTarget = self.getClosestEntity()

			self.currentHealth = ob['Life']
			self.kills = ob['MobsKilled']

			# update agent sight
			self.los = ob['LineOfSight']["type"]
			if (self.lost in MOB_TYPES):
				reward += self.rewards['Look']
			self.reward += reward
		return reward

	def update_q_table(self, tau, S, A, R, T):
		curr_s, curr_a, curr_r = S.popleft(), A.popleft(), R.popleft()
		G = sum([self.gamma ** i * R[i] for i in range(len(S))])
		if tau + self.n < T:
			G += self.gamma ** self.n * self.q_table[S[-1]][A[-1]]

		old_q = self.q_table[curr_s][curr_a]
		self.q_table[curr_s][curr_a] = old_q + self.alpha * (G - old_q)

	def get_possible_actions(self):
		if self.los in MOB_TYPES:
			return self.actions
		
		possible_actions = []
		for action in self.actions:
			if action != "Attack":
				possible_actions.append(action)

		return possible_actions 


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

	def run(self, agent_host):
		win = False
		self.begin_mission()
		S, A, R = deque(), deque(), deque()
		x = 0
		world_state = agent_host.getWorldState()
		while not self.done_update:
			reward = self.getReward(agent_host)
			
			curr_state = self.get_current_state()
			possible_actions = self.get_possible_actions()
			action = self.choose_action(curr_state, possible_actions)
			S.append(curr_state)
			A.append(action)
			R.append(0)

			T = sys.maxsize
			for t in range(sys.maxsize):
				if t < T:
					reward = self.getReward(agent_host)
					R.append(reward)

					if len(self.enemies) == 0 or self.done_update:
						T = t + 1
						S.append('Term State')
						print('Points this round: ', self.reward)
					else:
						if self.kills == 1:
							win = True
							self.end_mission()
						
						curr_state = self.get_current_state()
						possible_actions = self.get_possible_actions()
						action = self.choose_action(curr_state, possible_actions)

						S.append(curr_state)
						A.append(action)

						self.process_action(agent_host, action)	

				tau = t - self.n + 1
				if tau >= 0:
					self.update_q_table(tau, S, A, R, T)

				if tau == T-1:
					while len(S) > 1:
						tau = tau + 1
						self.update_q_table(tau, S, A, R, T)
					self.end_mission()
					return win
				x += 1

	# Helper Functions
	def getDistance(self, x1, z1, x2, z2):
		return ((x1 - x2)**2 + (z1 - z2)**2)**0.5

	def getEnemiesInfo(self, entities):
		print("entities", entities)
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

	def begin_mission(self):
		self.reward = 0
		self.done_update = False

	def end_mission(self):
		self.done_update = True