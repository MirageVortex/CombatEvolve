from __future__ import print_function
from builtins import range
import Hunter_3
import NeuralNetwork_2 as nn
import MalmoPython
import RoomGeneration as roomgen
import random
import json
import math
import errno
import os
import sys
import time
import cv2
import time

if sys.version_info[0] == 2:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately
else:
    import functools
    print = functools.partial(print, flush=True)

if __name__=='__main__':
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

	agent_host.setObservationsPolicy(MalmoPython.ObservationsPolicy.LATEST_OBSERVATION_ONLY)
	agent_host.setVideoPolicy(MalmoPython.VideoPolicy.LATEST_FRAME_ONLY)

	network = nn.NeuralNetwork()
	num_reps = 5000
	win = 0
	kills = 0
	prev_kills = 0
	win_generation = []
	random.seed(0)
	start_time = time.time()
	print('Starting...', flush=True)

	for iRepeat in range(num_reps):
		room = roomgen.generate_room(20,20,True)

		missionXML='''
		<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
		<Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
			<About>
		        <Summary>Combat Evolved Project 1 - Prototype. AI vs Zombie</Summary>
		    </About>

		    <ModSettings>
				<MsPerTick>10</MsPerTick>
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
				</AgentHandlers>
			</AgentSection>
		</Mission>'''

		network.agent = Hunter_3.Hunter()
		t = network.t
		first = True
		prev_kills += kills

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
		agent_host.sendCommand("chat /gamerule naturalRegeneration false")

		while world_state.is_mission_running:
			time.sleep(0.02)
			if len(world_state.observations) > 0 and len(world_state.video_frames) > 0:
				if (first == True):
					msg = world_state.observations[-1].text
					ob = json.loads(msg)
					frame = world_state.video_frames[0]
					action = network.init_network(frame, ob, False)
					network.agent.process_action(agent_host, network.agent.actions[action])
					first = False
				else:
					msg = world_state.observations[-1].text
					ob = json.loads(msg)
					frame = world_state.video_frames[0]
					prev_action = action
					action = network.train_network(frame, ob, False)
					network.agent.process_action(agent_host, network.agent.actions[action])

				if len(ob['entities']) == 1:
					kills = 1
					agent_host.sendCommand("quit")

			world_state = agent_host.getWorldState()
			for error in world_state.errors:
				print("Error:",error.text)


		network.train_network(frame, ob, True)
		print("Mission ended")
		print("score:", network.agent.reward)
		print("wins:", win)
		print("kills: " ,kills )
		# time = start_time - time.time()
		# print("time:", time)
		print(win_generation)