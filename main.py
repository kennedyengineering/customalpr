# customALPR main script
# kennedyengineering 1/8/20

import getpass
# customARLP modules
from database_service import databaseService
from alpr_camera import ALPRCamera
from check_alpr import check_alpr
from load_config_file import load_config
from gui import GUI


# verify openALPR install is working
conf = "/etc/openalpr/openalpr.conf"
runtime = "/home/" + str(getpass.getuser()) + "/openalpr/runtime_data"
if not check_alpr(conf, runtime):
	exit()

# parse settings from config file
(camera_list, gui, gui_resolution) = load_config()

# start the database service
dbService = databaseService().start()
while not dbService.ready:
	continue

# launch camera threads for ALPR
render_window = None
if gui:
	render_window = GUI(gui_resolution)
camera_threads = []
for camera in camera_list:
	camera_threads.append(ALPRCamera(camera, dbService, conf, runtime, gui))
for thread in camera_threads:
	thread.start()
	if gui:
		render_window.cap_list.append(thread)

# handle console commands
if gui:
	print("starting in GUI mode")
	print("resolution: ", gui_resolution)
	print("press 'q' to exit")
	print()
else:
	print("starting in CONSOLE mode")
	print("type 'help' for a list of commands")
	print()

usable_commands = {"help": "show all usable commands", "q": "quit the program"}

# main thread loop, handle UI and clean exit
initial_num_cameras = len(camera_threads)

# main loop
while 1:
	if not gui:
		command = input(">> ")
		if command == "q":
			for thread in camera_threads:
				thread.stop()

			break
		elif command == "help":
			for option in usable_commands:
				print(option, " : ", usable_commands[option])

			continue

	else:
		if not render_window.update():
			break

dbService.stop()
