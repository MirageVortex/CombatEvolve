import json
import random
import math

# rewards
DEATH_REWARD = -100

MOB_TYPES = ["Sheep"]

class Hunter(object):
	def __init__(self, alpha=0.3, gamma=1, n=1):
		self.epsilon = 0.3
		self.q_table = {}
		self.n, self.alpha, self.gamma = n, alpha, gamma
		self.distance = 0
		self.turn_rate_scale = 90
		self.target = ""

	def get_possible_actions(self, agent_host):
		action_list = ["MoveUp", "MoveDown", "StopMoving"]
		# if ()

		return action_list

	def choose_action(self, current_state, possible_actions, eps):

		return possible_actions[radnom.randint(0, len(possible_actions) - 1)]

	def process_action(self, action):
		if action == "StopMoving":
			self._host.sendCommand("setYaw 90")
			self._host.sendCommand("strafe 0")
			self._host.sendCommand("move 0")

		elif action == "MoveUp":
			self._host.sendCommand("setYaw 90")
			self._host.sendCommand("strafe 0")
			self._host.sendCommand("move 1")

		elif action == "MoveDown":
			self._host.sendCommand("setYaw 90")
			self._host.sendCommand("strafe 0")
			self._host.sendCommand("move -1")

		# elif action == "TurnLeft":
		# 	self._host.sendCommand("setYaw 90")
		# 	self._host.sendCommand("move 0")
		# 	self._host.sendCommand("strafe -1")

		# elif action == "TurnRight":
		# 	self._host.sendCommand("setYaw 90")
		# 	self._host.sendCommand("move 0")
		# 	self._host.sendCommand("strafe 1")

		# elif action == "Attack":
		# 	self.stop_moving
		# 	self._host.sendCommand("attack 1")
		# 	self._host.sendCommand("attack 0")

	def get_closest_entity(self, nearby_obs):
		nearest_entity = ""
		distance = 999999

		for ent in nearby_obs.keys():
			if ent != "CombatEvolvedAI":
				x1 = nearby_obs["CombatEvolvedAI"][1]
				z1 = nearby_obs["CombatEvolvedAI"][2]
				x2 = nearby_obs[ent][1]
				z2 = nearby_obs[ent][2]

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

	def look_at_target(self, agent_host, nearby_obs):
		current_yaw = nearby_obs["CombatEvolvedAI"][0]

		best_yaw = math.degrees(math.atan2(nearby_obs[self.target][2] - nearby_obs["CombatEvolvedAI"][2], 
			nearby_obs[self.target][1] - nearby_obs["CombatEvolvedAI"][1])) - 90
		difference = self.normalize_yaw(best_yaw - current_yaw);
		difference /= self.turn_rate_scale
		threshold = 0.0

		if difference < threshold and difference > 0:
			difference = threshold

		elif difference > -threshold and difference < 0:
			difference = -threshold

		agent_host.sendCommand("turn " + str(difference))


	def update_q_table(self):
		return


	def get_current_state(self, agent_host):
		nearby_obs = {}
		count = 0
		life = 0
		while True:
			world_state = agent_host.getWorldState()
			if world_state.number_of_observations_since_last_state > 0:
				msg = world_state.observations[-1].text
				ob = json.loads(msg)
				#life = ob[u'Life']
				for ent in  ob['entities']:		
					name = ent['name']		
					if name in MOB_TYPES:
						name=name+str(count)
						count+=1						
					nearby_obs[name] = (ent['yaw'], ent['x'], ent['z'])

				return nearby_obs, count
			elif not world_state.is_mission_running:
				return nearby_obs, count

	def distance_from_enemy(self, x1, x2, z1, z2):
		return ((x1 - x2)**2 + (z1 - z2)**2)**0.5
		

	def run(self, agent_host):
		#Action_List = deque()
		done_update = False
		world_state = agent_host.getWorldState()

		# for now AI will always be swinging the sword
		

		while not done_update :
			nearby_obs, count = self.get_current_state(agent_host)
			agent_host.sendCommand("attack 1")

			if self.target == "":
				self.target = self.get_closest_entity(nearby_obs)
			# AI will also look at enemy at all times (track and turn at enemy)

			self.look_at_target(agent_host, nearby_obs)

			possible_actions = self.get_possible_actions(agent_host)
			# action = self.choose_action()			

			# if (self.distance_from_enemy(nearby_obs) == 0):
			# 	reward += 100
			# 	done_update = True
			world_state = agent_host.getWorldState()

		# reward = world_state.rewards[-1],getValue()
		# print('Points this round: ', reward)


