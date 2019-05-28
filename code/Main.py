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
enemy_type = "Sheep"

room = roomgen.generate_room(20,20,1)

missionXML='''
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
	<About>
        <Summary>Combat Evolved Project 1 - Prototype. Getting the AI to walk towards an enemy</Summary>
    </About>
    <ServerSection>
        <ServerInitialConditions>
            <Time>
                <StartTime>12000</StartTime>
                <AllowPassageOfTime>false</AllowPassageOfTime>
            </Time>
            <Weather>clear</Weather>
        </ServerInitialConditions>
        <ServerHandlers>
            <FlatWorldGenerator generatorString="3;7,57*1,5*3,2;3;,biome_1"/>
            <DrawingDecorator>
                '''+room+'''
            </DrawingDecorator>
            <ServerQuitFromTimeUp timeLimitMs="25000"/>
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
			<RewardForDamagingEntity>
				<Mob type="Zombie" reward="50"/>
			</RewardForDamagingEntity>
			<ContinuousMovementCommands turnSpeedDegs="180"/>
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

	num_reps = 100
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
		print("Generation:", iRepeat)
		print("You have entered a dungeon")

		sung_woo.run(agent_host)

		print("Mission ended")
		if world_state.is_mission_running:
			time.sleep(15)
