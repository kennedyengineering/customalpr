from multiprocessing import Process, Value
from openalpr import Alpr
import cv2
from time import sleep
import yaml
import os
import sqlite3
import datetime
import signal
import socket

class GracefulKiller:
	kill_now = False
	def __init__(self):
		signal.signal(signal.SIGINT, self.exit_gracefully)
		signal.signal(signal.SIGTERM, self.exit_gracefully)

	def exit_gracefully(self,signum, frame):
		self.kill_now = True


databaseFilePath = "plate.db"
if os.path.isfile(databaseFilePath):
	print("database file found at, ", databaseFilePath)
else:
	print("could not find", databaseFilePath)
	print("creating new database... ")
	connection = sqlite3.connect(databaseFilePath)
	cursor = connection.cursor()
	command = """
	CREATE TABLE plates (
	plateNumber VARCHAR(10),
	plateConfidence VARCHAR(10),
	cameraLocation VARCHAR(30),
	cameraName VARCHAR(30),
	dateTime VARCHAR(30),
	imageURL VARCHAR(40));"""
	cursor.execute(command)
	connection.commit()
	connection.close()
	print("done")	

configFilePath = "config.yml"
if os.path.isfile(configFilePath):
	print("config file found at, ", configFilePath)
else:
	print("could not find ", configFilePath)
	exit()

alprConf = "/etc/openalpr/openalpr.conf"
#alprRuntime = "/usr/share/openalpr/runtime_data" #missing us config file
alprRuntime = "/home/bkennedy/openalpr/runtime_data" #not missing us config file

hostname = socket.gethostname()

progTerminate = Value('i', 0)

def processFeed(videoSourceURL, cameraName, progStatus):
	connection = sqlite3.connect(databaseFilePath)
	cursor = connection.cursor()

	alpr = Alpr("us", alprConf, alprRuntime)
	if not alpr.is_loaded():
		print("Alpr failed to load")
		return -1

	alpr.set_top_n(1) # only return the best result

	cam = cv2.VideoCapture()
	cam.open(videoSourceURL)

	if cam.isOpened():
		print("camera ", cameraName, videoSourceURL, " operational")
	else:
		print("camera ", cameraName, videoSourceURL, "  unavailable")
		return -1

	while not progStatus.value:
		ret, frame = cam.read()
		if not ret:
			print("Failed to retreive frame from ", cameraName, videoSourceURL)
			return -1
			
		results = alpr.recognize_ndarray(frame) #scan an numpy array
	
		i = 0
		if results['results']:
			print()
			print("Camera", cameraName, videoSourceURL)
		for plate in results['results']:
			i += 1
			#print()
			#print("Camera", cameraName, videoSourceURL)
			print("Plate #%d" % i)
			print("    %12s %12s" % ("Plate", "Confidence"))
			for candidate in plate['candidates']: #should be only one per plate
				prefix = "-"
				if candidate['matches_template']:
					prefix = "*"
	
				print("  %s %12s%12f" % (prefix, candidate['plate'], candidate['confidence']))
			
	
				fileName = (str(cameraName) + " " + str(datetime.datetime.now()).replace(".", " ") + ".png").replace(" ", "_")

				saveLocation = "/var/www/html/capturedImages/" + fileName
				print("saving as "+fileName)
				#cv2.imwrite(saveLocation, frame)

				imageURL = str(hostname) + "/capturedImages/" + fileName

				command = """INSERT INTO plates (plateNumber, plateConfidence, cameraLocation, cameraName, dateTime, imageURL) VALUES ("{}", "{}", "{}", "{}", "{}", "{}");""".format(candidate['plate'], candidate['confidence'], videoSourceURL, cameraName, datetime.datetime.now(), imageURL)
				cursor.execute(command)
				connection.commit()

	connection.close()
	alpr.unload()
	cam.release()
	return 0

with open(configFilePath, 'r') as stream:
	config = yaml.load(stream)

processes = {}
for pair in config['cameraAddresses']:
	for name in pair:
		processes[name] = Process(target=processFeed, args=(pair[name], name, progTerminate,))
		processes[name].start()

shutdownStatus = GracefulKiller()

while 1:
	if shutdownStatus.kill_now:
		progTerminate.value = 1

		for pair in config['cameraAddresses']:
			for name in pair:
				processes[name].join()
		print("done")
		exit(0)
