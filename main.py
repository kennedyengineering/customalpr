# imports
#import yaml
#import cv2
from threading import Thread
import getpass

# customalpr modules
from database_service import databaseService
from start_alpr_camera import startALPRonCamera
from check_alpr import checkALPR
from load_config_file import loadConfig

# verify ALPR install is working
alprConf = "/etc/openalpr/openalpr.conf"
alprRunTime = "/home/" + str(getpass.getuser()) + "/openalpr/runtime_data"
if checkALPR(alprConf, alprRunTime) == False:
	exit()

# parse settings from config file
(cameraList, gui, guiResolution) = loadConfig()

# start up the database server, REMEMBER TO ACTUALLY .start() IT!!!
dbService = databaseService().start()

# replace with better system for launching threads in order... get the OK from dbService
while not dbService.ready:
	continue

# start up ALPR loop on camera
#progTerminate = False
'''
cameraThreads = {}
for camera in cameraList:
	cameraThreads[camera.name] = Thread(target=startALPRonCamera, args=(camera, dbService, alprConf, alprRunTime, gui, guiResolution))#.start()
	cameraThreads[camera.name].start()
'''
cameraThreads = []
for camera in cameraList:
	cameraThreads.append(Thread(target=startALPRonCamera, args=(camera, dbService, alprConf, alprRunTime, gui, guiResolution)))
for thread in cameraThreads:
	thread.start()

# handle console commands in a loop
if gui:
	print("Starting in GUI mode")
	print("Resolution: ", guiResolution)
	print("press 'q' to exit")
	print()
else:
	print("Starting in CONSOLE mode")
	print("type 'help' for a list of commands")
	print()
usableCommands = {"help": "show all usable commands", "q": "quit the program"}

# main thread loop, handle UI and clean exit
while 1:
	if not gui:
		command = input(">> ")
		if command == "q":
			break
		elif command == "help":
			for option in usableCommands:
				print(option, " : ", usableCommands[option])
			continue

	else:
		# check for closed threads, exit when no more cameras are working
		cameraThreads = [thread for thread in cameraThreads if thread.isAlive()]
		if len(cameraThreads) == 0:
			break

dbService.stop()