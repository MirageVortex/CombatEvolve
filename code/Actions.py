
class Actions(object):
	"""docstring for ClassName"""
	def __init__(self, agent_host):
		self._host = agent_host

	# Move Commands
	def stop_moving(self):
        self._host.sendCommand("setYaw 90")
        self._host.sendCommand("strafe 0")
        self._host.sendCommand("move 0")

	def move_up(self):
		self._host.sendCommand("setYaw 90")
		self._host.sendCommand("strafe 0")
		self._host.sendCommand("move 1")

    def move_down(self):
        self._host.sendCommand("setYaw 90")
        self._host.sendCommand("strafe 0")
        self._host.sendCommand("move -1")

    def move_left(self):
        self._host.sendCommand("setYaw 90")
        self._host.sendCommand("move 0")
        self._host.sendCommand("strafe -1")

    def move_right(self):
        self._host.sendCommand("setYaw 90")
        self._host.sendCommand("move 0")
        self._host.sendCommand("strafe 1")

    def attack(self):
    	self.stop_moving
    	self._host.sendCommand("attack 1")
    	self._host.sendCommand("attack 0")
		