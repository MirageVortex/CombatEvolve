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
	monster_count = 1
	win = 0
	kills = 0
	prev_kills = 0
	scores = []
	win_generation = []
	times = []
	mode = "Survival"
	random.seed(0)
	
	print('Starting...', flush=True)

	for iRepeat in range(1, num_reps+1):
		if iRepeat % 350 == 0:
			monster_count +=1

		if iRepeat == 100:
			mode = "Survival"
		room = roomgen.generate_room(20,20,monster_count)
		start_time = time.time()
		missionXML='''
		<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
		<Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
			<About>
		        <Summary>Combat Evolved Project</Summary>
		    </About>

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
		            <ServerQuitFromTimeUp timeLimitMs="30000"/>
		            <ServerQuitWhenAnyAgentFinishes/>
		        </ServerHandlers>
		    </ServerSection>
			<AgentSection mode="'''+mode+'''">
		        <Name>CombatEvolvedAI</Name>
		        <AgentStart>
		            <Placement x="0" y="64" z="-7" yaw="0"/>

		        </AgentStart>
				<AgentHandlers>
					<ObservationFromRay/>
					<ObservationFromNearbyEntities>
						<Range name="entities" xrange="60" yrange="1" zrange="60"/>
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
		print("Generation:", iRepeat)
		print("You have entered a dungeon")
		agent_host.sendCommand("chat /gamerule naturalRegeneration false")
		agent_host.sendCommand("chat /gamerule doMobLoot false")
		if (win_generation == [] or win_generation[-1] != iRepeat-1):
			agent_host.sendCommand("chat /give @p diamond_sword 1 0 {display:{Name:'Death',Lore:['one hit kill']},ench:[{id:16,lvl:1000},{id:20,lvl:1000},{id:21,lvl:30},{id:32,lvl:100},{id:34,lvl:1000},{id:51,lvl:1000}],HideFlags:5,Unbreakable:1}")

		while world_state.is_mission_running:
			time.sleep(0.01)
			# agent_host.sendCommand("turn 0")
			# agent_host.sendCommand("turn " + str(network.agent.look_difference))
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
					img = network.agent.getPixels(frame)
					cv2.imshow('image', img)
					cv2.waitKey(0)
					prev_action = action
					action = network.train_network(frame, ob, False)
					network.agent.process_action(agent_host, network.agent.actions[action])

				if len(ob['entities']) == 1:
					win += 1
					win_generation.append(iRepeat)
					timer = time.time() - start_time
					times.append(round(timer, 2))
					agent_host.sendCommand("quit")

			world_state = agent_host.getWorldState()
			for error in world_state.errors:
				print("Error:",error.text)


		network.train_network(frame, ob, True)
		print("Mission ended")
		scores.append(round(network.agent.reward,2))
		print("score:", round(network.agent.reward,2))
		print("wins:", win)
		print(times)
		print(scores)
		print(win_generation)
		agent_host.sendCommand("quit")