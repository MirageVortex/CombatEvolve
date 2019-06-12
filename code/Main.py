from __future__ import print_function
from builtins import range
import MalmoPython
import RoomGeneration as roomgen
import random
import json
import math
import errno
import Hunter
import os
import sys
import time

if sys.version_info[0] == 2:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately
else:
    import functools
    print = functools.partial(print, flush=True)


# enemy_type = "Zombie"
# Uncomment below to make enemy a non-hostile enemy (training purposes)
MOB_TYPES = ["Zombie", "Spider", "Skeleton"]

room = roomgen.generate_room(20,20,3)

missionXML='''
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
	<About>
        <Summary>Combat Evolved Project 1 - Prototype. AI vs Zombie</Summary>
    </About>

	<ModSettings>
		<MsPerTick>5</MsPerTick>
	</ModSettings>

    <ServerSection>
        <ServerInitialConditions>
            <Time>
                <StartTime>6000</StartTime>
                <AllowPassageOfTime>false</AllowPassageOfTime>
            </Time>
            <Weather>clear</Weather>
            <AllowSpawning>false</AllowSpawning>
        </ServerInitialConditions>
        <ServerHandlers>
            <FlatWorldGenerator generatorString="3;7,57*1,5*3,2;3;,biome_1"/>
            <DrawingDecorator>
                '''+room+'''
            </DrawingDecorator>
            
            <ServerQuitWhenAnyAgentFinishes/>
        </ServerHandlers>
    </ServerSection>
	<AgentSection mode="Survival">
        <Name>CombatEvolvedAI</Name>
        <AgentStart>
            <Placement x="0" y="64" z="-7" yaw="0"/>
            <Inventory>
            	<InventoryItem slot="0" type="diamond_sword"/>
            </Inventory>
        </AgentStart>
		<AgentHandlers>
			<ObservationFromRay/>
			<ObservationFromNearbyEntities>
				<Range name="entities" xrange="40" yrange="40" zrange="40"/>
			</ObservationFromNearbyEntities>
			<ObservationFromFullStats/>
			<MissionQuitCommands quitDescription="killed_all"/>
			<ContinuousMovementCommands turnSpeedDegs="180"/>
			<ChatCommands/>
			<ObservationFromGrid>
				<Grid name="env">
					<min x="-10" y="0" z="-10"/>
					<max x="10" y="0" z="10"/>
				</Grid>
			</ObservationFromGrid>
		</AgentHandlers>
	</AgentSection>
</Mission>'''

if __name__=='__main__':
	win = 0
	win_generation = []
	monster_count = 1
	random.seed(0)
	print('Starting...', flush=True)

	my_client_pool = MalmoPython.ClientPool()
	my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10000))

	agent_host = MalmoPython.AgentHost()
	try:
	    agent_host.parse( sys.argv )
	except RuntimeError as e:
	    print('ERROR:',e)
	    print(agent_host.getUsage())
	    exit(1)
	if agent_host.receivedArgument("help"):
	    print(agent_host.getUsage())
	    exit(0)

	num_reps = 500
	# alpha
	sung_woo = Hunter.Hunter()

	for iRepeat in range(num_reps):
		my_mission = MalmoPython.MissionSpec(missionXML, True)
		my_mission_record = MalmoPython.MissionRecordSpec()
		my_mission.requestVideo(800, 500)
		my_mission.setViewpoint(0)
		# Attempt to start a mission:
		max_retries = 3
		for retry in range(max_retries):
		    try:
		        agent_host.startMission( my_mission, my_client_pool, my_mission_record, 0, "Sung Woo")
		        break
		    except RuntimeError as e:
		        if retry == max_retries - 1:
		            print("Error starting mission:",e)
		            exit(1)
		        else:
		            time.sleep(2)

		# Loop until mission starts:
		print("Waiting for the mission to start ", end=' ')
		world_state = agent_host.getWorldState()
		while not world_state.has_mission_begun:
			print(".", end ="")
			time.sleep(0.1)
			world_state = agent_host.getWorldState()
		for error in world_state.errors:
			print("Error:",error.text)


		print()
		print("Generation:", iRepeat+1)
		print("You have entered a dungeon")

		if (iRepeat) > 150:
			monster_count += 2

		for i in range(monster_count):
			monster = random.choice(MOB_TYPES)
			x_pos = random.randint(-9, 9)
			z_pos = random.randint(0, 9)
			summon_command = "chat /summon " + monster + " " + str(x_pos) + " 64 " + str(z_pos)
			agent_host.sendCommand(summon_command)

		if sung_woo.run(agent_host):
			win += 1
			win_generation.append(iRepeat+1)

		print("Mission ended")
		print("Wins:", win)
		print(win_generation)
		if (sung_woo.epsilon > sung_woo.final_ep):
			sung_woo.epsilon *= sung_woo.decay_rate
		agent_host.sendCommand("quit")