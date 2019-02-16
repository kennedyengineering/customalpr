from multiprocessing import Process, Value
from openalpr import Alpr
import cv2
from time import sleep
import yaml
import os

configFilePath = "config.yml"
if os.path.isfile(configFilePath):
	print("config file found at, ", configFilePath)
else:
	print("could not find ", configFilePath)
	exit()

alprConf = "/etc/openalpr/openalpr.conf"
#alprRuntime = "/usr/share/openalpr/runtime_data" #missing us config file
alprRuntime = "/home/bkennedy/openalpr/runtime_data" #not missing us config file

progTerminate = Value('i', 0)

def processFeed(videoSourceURL, progStatus):
	alpr = Alpr("us", alprConf, alprRuntime)
	if not alpr.is_loaded():
		print("Alpr failed to load")
		return -1

	alpr.set_top_n(5) #only return top five results

	cam = cv2.VideoCapture()
	cam.open(videoSourceURL)

	if cam.isOpened():
		print("camera ", videoSourceURL, " operational")
	else:
		print("camera ", videoSourceURL, "  unavailable")
		return -1

	while not progStatus.value:
		ret, frame = cam.read()
		if not ret:
			print("Failed to retreive frame from ", videoSourceURL)
			return -1
			
		results = alpr.recognize_ndarray(frame) #scan an numpy array
	
		i = 0
		for plate in results['results']:
			i += 1
			print("Plate #%d" % i)
			print("    %12s %12s" % ("Plate", "Confidence"))
			for candidate in plate['candidates']:
				prefix = "-"
				if candidate['matches_template']:
					prefix = "*"
	
				print("  %s %12s%12f" % (prefix, candidate['plate'], candidate['confidence']))

	alpr.unload()
	cam.release()
	return 0

with open(configFilePath, 'r') as stream:
	config = yaml.load(stream)

processes = {}
for address in config['cameraAddresses']:
	processes[address] = Process(target=processFeed, args=(address, progTerminate,))
	processes[address].start()

sleep(5)
progTerminate.value = 1

for address in config['cameraAddresses']:
	processes[address].join()

print("done")
