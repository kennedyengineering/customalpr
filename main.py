# imports
import getpass

# customalpr modules
from database_service import databaseService
from start_alpr_camera import startALPRonCamera
from check_alpr import checkALPR
from load_config_file import loadConfig
from gui import GUI

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

if gui:
	render_window = GUI(guiResolution)
# launch camera threads for alpr
cameraThreads = []
for camera in cameraList:
	cameraThreads.append(startALPRonCamera(camera, dbService, alprConf, alprRunTime, gui))
for thread in cameraThreads:
	thread.start()
	if gui:
		render_window.cap_list.append(thread)

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
initial_num_cameras = len(cameraThreads)

while 1:
	if not gui:
		command = input(">> ")
		if command == "q":
			# need to notify thread somehow and quit it
			for thread in cameraThreads:
				thread.stop()
			break
		elif command == "help":
			for option in usableCommands:
				print(option, " : ", usableCommands[option])
			continue

	else:
		# check for closed threads, exit when no more cameras are working
		#cameraThreads = [thread for thread in cameraThreads if thread.isAlive()]
		#if len(cameraThreads) < initial_num_cameras:
		#	for thread in cameraThreads:
		#		thread.stop()

		#	break
		if not render_window.update():
			break

# figure out how to tell all threads to terminate
dbService.stop()