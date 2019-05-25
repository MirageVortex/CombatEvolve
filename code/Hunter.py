import json

# rewards
DEATH_REWARD = -100

MOB_TYPES = ["Sheep"]

class Hunter(object):
	def __init__(self, alpha=0.3, gamma=1, n=1):
		self.epsilon = 0.3
		self.q_table = {}
		self.n, self.alpha, self.gamma = n, alpha, gamma
		self.distance_from_enemy = 0

	def get_possible_actions(self, agent_host):
		action_list = ["MoveUp", "MoveDown", "TurnLeft", "TurnRight", "StopMoving"]
		if ()

		return action_list

	def choose_action(self, current_state, possible_actions, eps):
		if current_state not

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

		elif action == "TurnLeft":
			self._host.sendCommand("setYaw 90")
			self._host.sendCommand("move 0")
			self._host.sendCommand("strafe -1")

		elif action == "TurnRight":
			self._host.sendCommand("setYaw 90")
			self._host.sendCommand("move 0")
			self._host.sendCommand("strafe 1")

		elif action == "Attack":
			self.stop_moving
			self._host.sendCommand("attack 1")
			self._host.sendCommand("attack 0")


	def get_current_state(self, agent_host):
		nearby_obs = {}
		count = 0
		life = 0
		while True:
			world_state = agent_host.getWorldState()
			if world_state.number_of_observations_since_last_state > 0:
				msg = world_state.observations[-1].text
				ob = json.loads(msg)
				life = ob[u'Life']
				for ent in  ob['entities']:
					name = ent['name']
					if name in MOB_TYPES:
						count++;
					nearby_obs[name] = (ent['yaw'], ent['x'], ent['z'])

				return nearby_obs, count, life

	def distance_from_enemy(nearby_obs):
		return ((nearby_obs['Sheep'][1] - nearby_obs['CombatEvolvedAI'][1])**2 + (nearby_obs['Sheep'][2] - nearby_obs['CombatEvolvedAI'][2])**2)**0.5
		

	def run(self, agent_host):
		Action_List = deque()
		done_update = False
		world_state = agent_host.getWorldState()

		while world_state.is_mission_running and not done_update :

			nearby_obs, count, life = self.get_current_state(agent_host)
			possible_actions = self.get_possible_actions(agent_host)
			action = self.choose_action()
			if (distance_from_enemy(nearby_obs) == 0):
				reward += 100
				done_update = True
			else:


			world_state = agent_host.getWorldState()

		reward = world_state.rewards[-1],getValue()
		print('Points this round: ', reward)


