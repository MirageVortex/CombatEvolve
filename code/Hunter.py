import json
import random
import math
import sys
import time
from collections import deque

# rewards
DEATH_REWARD = -100

MOB_TYPES = ["Sheep", "Zombie"]

ACTION_REWARD = {"MoveUp":0, "MoveDown":0, "StopMoving":0, "TurnLeft":0, "TurnRight":0, "Attack":-5}

class Hunter(object):
	def __init__(self, alpha=0.3, gamma=1, n=1):
		self.epsilon = 0.3
		self.q_table = {}
		self.n, self.alpha, self.gamma = n, alpha, gamma
		self.distance = 0
		self.turn_rate_scale = 90
		self.done_update = False
		self.target = ""
		self.reward = 0
		self.enemies = {}

	def get_possible_actions(self, agent_host):
		action_list = ["MoveUp", "MoveDown", "StopMoving", "TurnLeft", "TurnRight", "Attack"]
		return action_list

	def choose_action(self, curr_state, possible_actions, eps):
		if curr_state not in self.q_table:
			self.q_table[curr_state] = {}
		for action in possible_actions:
			if action not in self.q_table[curr_state]:
				self.q_table[curr_state][action] = 0

		possible_action_list = {}


		for action in self.q_table[curr_state].items():
			if (len(possible_action_list) == 0):
				possible_action_list[action[0]] = action[1]
			elif (action[1] > list(possible_action_list.values())[0]):
				possible_action_list = {}
				possible_action_list[action[0]] = action[1]
			elif (action[1] == list(possible_action_list.values())[0]):

				possible_action_list[action[0]] = action[1]

		eps_decision = random.randint(0, 10)

		if (eps_decision < int(eps * 10)):
			a = random.randint(0, len(possible_action_list) - 1)
			return possible_actions[a]
		else:
			a = random.randint(0, len(possible_action_list) - 1)
			return list(possible_action_list.keys())[a]
		# return possible_actions[random.randint(0, len(possible_actions) - 1)]

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

	def get_closest_entity(self, entity_obs):
		nearest_entity = ""
		distance = 999999

		for ent in entity_obs.keys():
			if ent != "CombatEvolvedAI":
				x1 = entity_obs["CombatEvolvedAI"][1]
				z1 = entity_obs["CombatEvolvedAI"][2]
				x2 = entity_obs[ent][1]
				z2 = entity_obs[ent][2]

				comparable = self.distance_from_enemy(x1,x2,z1,z2)

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

	def look_at_target(self, agent_host, entity_obs):
		current_yaw = entity_obs["CombatEvolvedAI"][0]

		best_yaw = math.degrees(math.atan2(entity_obs[self.target][2] - entity_obs["CombatEvolvedAI"][2], 
			entity_obs[self.target][1] - entity_obs["CombatEvolvedAI"][1])) - 90
		difference = self.normalize_yaw(best_yaw - current_yaw);
		difference /= self.turn_rate_scale
		threshold = 0.0

		if difference < threshold and difference > 0:
			difference = threshold

		elif difference > -threshold and difference < 0:
			difference = -threshold

		agent_host.sendCommand("turn " + str(difference))


	def update_q_table(self, tau, S, A, R, T):
		curr_s, curr_a, curr_r = S.popleft(), A.popleft(), R.popleft()
		G = sum([self.gamma ** i * R[i] for i in range(len(S))])
		if tau + self.n < T:
			G += self.gamma ** self.n * self.q_table[S[-1]][A[-1]]

		old_q = self.q_table[curr_s][curr_a]
		self.q_table[curr_s][curr_a] = old_q + self.alpha * (G - old_q)

	def get_world_info(self, agent_host):
		entity_obs = {}
		count = 0
		sight = ""

		while True:
			world_state = agent_host.getWorldState()
			if world_state.number_of_observations_since_last_state > 0:
				msg = world_state.observations[-1].text
				ob = json.loads(msg)
				for ent in ob['entities']:		
					name = ent['name']		
					if name in MOB_TYPES:
						name=name+str(count)
						count+=1
						entity_obs[name] = (ent['yaw'], ent['x'], ent['z'], ent['life'])
					elif name == "CombatEvolvedAI":	
						entity_obs[name] = (ent['yaw'], ent['x'], ent['z'], ent['life'])
	
				if ob['LineOfSight']["type"] in MOB_TYPES:
					sight = ob['LineOfSight']["type"]

				return entity_obs, sight
			elif not world_state.is_mission_running:
				self.end_mission()
				return entity_obs, sight

	def get_current_state(self, agent_host, entity_obs, sight):
		world_state = agent_host.getWorldState()
		curr_state = []
		if (world_state.is_mission_running):
			
			x1 = entity_obs["CombatEvolvedAI"][1]
			z1 = entity_obs["CombatEvolvedAI"][2]
			for entity in entity_obs.keys():
				if entity != "CombatEvolvedAI":
					x2 = entity_obs[entity][1]
					z2 = entity_obs[entity][2]
					distance = self.distance_from_enemy(x1,x2,z1,z2)
					life = entity_obs[entity][3]
					curr_state.append((entity, distance, life))

			curr_state.append(('los',sight))

		return tuple(curr_state)

	def get_enemy_info(self, entity_obs):
		enemies = {}
		for entity in entity_obs.keys():
			if entity[:-1] in MOB_TYPES:
				enemies[entity] = entity_obs[entity][3]

		return enemies

	def distance_from_enemy(self, x1, x2, z1, z2):
		return ((x1 - x2)**2 + (z1 - z2)**2)**0.5
	
	def begin_mission(self):
		self.reward = 0
		self.done_update = False

	def end_mission(self):
		self.done_update = True

	def run(self, agent_host):
		self.begin_mission()
		S, A, R = deque(), deque(), deque()
		world_state = agent_host.getWorldState()

		while not self.done_update:
			entity_obs, sight = self.get_world_info(agent_host)

			curr_state = self.get_current_state(agent_host, entity_obs, sight)

			enemies = self.get_enemy_info(entity_obs)
			self.enemies = enemies

			possible_actions = self.get_possible_actions(agent_host)
			action = self.choose_action(curr_state, possible_actions, self.epsilon)
			self.process_action(agent_host, action)

			S.append(curr_state)
			A.append(action)
			R.append(0)

			T = sys.maxsize
			for t in range(sys.maxsize):
				if t < T:
					self.reward += ACTION_REWARD[action]
					R.append(self.reward)

					if len(self.enemies) == 0 or self.done_update:
						T = t + 1
						S.append('Term State')
						print('Points this round: ', self.reward)
					else:
						entity_obs, sight = self.get_world_info(agent_host)
						enemies = self.get_enemy_info(entity_obs)
			
						if entity_obs != {}:
							if len(self.enemies) > len(enemies):
								print("killed enemy")
								self.reward += 100
							for name1 in enemies.keys():
								for name2 in self.enemies.keys():
									if (name2 == name1 and self.enemies[name2] > enemies[name1]):
										self.reward += 50
							self.enemies = enemies
						else:
							self.reward -= 100
							self.end_mission()
						

						curr_state = self.get_current_state(agent_host, entity_obs, sight)

						possible_actions = self.get_possible_actions(agent_host)
						action = self.choose_action(curr_state, possible_actions, self.epsilon)

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
					break