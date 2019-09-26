import cv2
from openalpr import Alpr
import numpy as np
from threading import Thread
import datetime
import getpass
import sqlite3
import os.path
import yaml
import time
import copy

# check if alpr configuration files and install are OK
print("loading Alpr")
alprConf = "/etc/openalpr/openalpr.conf"
print("Alpr config path: ", alprConf)
alprRunTime = "/home/" + str(getpass.getuser()) + "/openalpr/runtime_data"
print("Alpr runtime path: ", alprRunTime)
alpr = Alpr("us", alprConf, alprRunTime)
if not alpr.is_loaded():
	print("Alpr failed to load")
	exit()
else:
	print("Alpr loaded successfully")
	del alpr # just for testing!!!
# done checking

# helper modules from pyImageSearch
class FPS:
	#from pyImageSearch
	def __init__(self):
		# store the start time, end time, and total number of frames
		# that were examined between the start and end intervals
		self._start = None
		self._end = None
		self._numFrames = 0

	def start(self):
		# start the timer
		self._start = datetime.datetime.now()
		return self

	def stop(self):
		# stop the timer
		self._end = datetime.datetime.now()

	def update(self):
		# increment the total number of frames examined during the
		# start and end intervals
		self._numFrames += 1

	def elapsed(self):
		# return the total number of seconds between the start and
		# end interval
		return (self._end - self._start).total_seconds()

	def fps(self):
		# compute the (approximate) frames per second
		return self._numFrames / self.elapsed()
class WebcamVideoStream:
	# from pyImageSearch website
	def __init__(self, src=0):
		# initialize the variable used to indicate if the thread should
		# be stopped
		self.stopped = False
		# initialize the video camera stream and read the first frame
		# from the stream
		self.src = src
		self.stream = cv2.VideoCapture(src)
		#(self.grabbed, self.frame) = self.stream.read()
		self.frame = self.grabFrame()

	def start(self):
		# start the thread to read frames from the video stream
		Thread(target=self.update, args=()).start()
		return self

	def grabFrame(self):
		# handle when self.stream.read() returns None as a frame
		# network outage redundancy
		(grabbed, frame) = self.stream.read()
		while not grabbed:
			if self.stopped:	# allow clean exit with the rest of the program
				return

			self.stream = cv2.VideoCapture(self.src) # initialize a new video stream to compensate for broken network connection, slow an inefficient, can be improved but it works
			(grabbed, frame) = self.stream.read()

		return frame

	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return

			# otherwise, read the next frame from the stream
			self.frame = self.grabFrame()
			#grabbed, self.frame = self.stream.read()

	def read(self):
		# return the frame most recently read
		return self.frame

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
# end helper module definition

###### load config file data #####################
print("")
print("Loading config file")

configFilePath = "config.yml"
with open(configFilePath, 'r') as stream:
    config = yaml.load(stream)

#videoSourceList = [] # populate with members of 'cameraAddresses'
#for pair in config['cameraAddresses']:
#	for name in pair:
#		videoSourceList.append(pair[name])

gui = config['GUItoggle']
guiResolutionX = config['GUIresolutionX']
guiResolutionY = config['GUIresolutionY']
guiResolution = (guiResolutionX, guiResolutionY)

class cameraDatatype:
    def __init__(self, name, url, aoiList):
        self.name = name
        self.url = url
        self.aoiList = aoiList

cameraList = []
for camera in config['cameraAddresses']:
    for name in camera:
        cameraID = camera[name]
        cameraName = name
        cameraUrl = cameraID[0]['url']
        cameraAOI = []
        for aoi in cameraID[1]['aoi']:
            for entry in aoi:
                #print(aoi[entry])
                X = aoi[entry][0]['X']
                Y = aoi[entry][1]['Y']
                W = aoi[entry][2]['W']
                H = aoi[entry][3]['H']
                tempDict = {entry: (X, Y, W, H)}
                cameraAOI.append(tempDict)

    cameraList.append(cameraDatatype(cameraName, cameraUrl, cameraAOI))

print("Config file loaded successfully")
##### end load config file data ###################

#videoSource = "rtsp://LPRuser:ThisISfun1@10.48.140.5:554/Streaming/channels/101/" # bring from config file. Allow for multiple cameras/sources
##videoSource = videoSourceList[0]
#videoSource = "recording.avi"
##cam = WebcamVideoStream(src=videoSource).start()
##fps = FPS().start()

def startALPRonCamera(camera, dbService, alprConf, alprRunTime):
	global progTerminate, gui
	# camera, dbService, alprConf, alprRunTime

	# wants camera datatype
	cam = WebcamVideoStream(src=camera.url).start()
	guiFPS = FPS().start()

	# define search areas
	# areasOfInterest = {"IN":(232, 614, 643, 455)}#, "OUT":(997, 682, 843, 384)} #pull from config file
	# detectionBoxes = []
	# for searchbox in areasOfInterest:
	#	newBox = detectionBox("LPR CAMERA", searchbox, areasOfInterest[searchbox], cam, alprConf, alprRunTime, dbService).start()
	#	detectionBoxes.append(newBox)
	# end define

	detectionBoxes = []
	for searchbox in camera.aoiList:
		for searchBoxName in searchbox:
			# needs -->  cameraName, name, area, webcamReference, alprconfig, alprruntime, dbReference
			newBox = detectionBox(camera.name, searchBoxName, searchbox[searchBoxName], cam, alprConf, alprRunTime, dbService).start()
			detectionBoxes.append(newBox)

	# main loop
	while 1:
		if gui:
			frame = cam.read()
			guiFPS.update()

			for box in detectionBoxes:
				frame = box.draw(frame)

			frame = cv2.resize(frame, guiResolution)
			cv2.imshow(camera.name, frame)
			if cv2.waitKey(1) & 0xFF == ord('q'):
				progTerminate = True
				break
		elif progTerminate:
			break

	## When main loop exits --> program terminate and clean up

	for box in detectionBoxes:
		box.stop()

	guiFPS.stop()
	if gui:
		print(camera.name+" gui", guiFPS.fps())
	cam.stop()

	return

# customalpr modules
class databaseService():
	def __init__(self):
		# WARNING!!
		# The purpose of this thread is to control the writing to the database from multiple locations
		# This module prevents writes occuring at the same time
		# as well as handling other aspects of the database
		# technically sqlite3 can have multiple connections, but this seems like a safe idea

		# there should only be ONE databaseService initialized!!!
		self.databaseName = "database/database.db"
		# check if database already exists, if not, initialize it
		print(" ")
		print("Connecting to database...")
		if (os.path.exists(self.databaseName) == False): # true if file exists
			print("No database found, initializing...")
			connection = sqlite3.connect(self.databaseName)
			cursor = connection.cursor()

			# need to record everything in the licenseplate class
			# - plate number <string>
			# - path to plate image (one image will be saved) <string>
			# - time spotted (range?) (datetime) <?>
			# - camera name <string>
			# - detectorBoxName (IN/OUT) <string>

			tableInitializationCommand = """CREATE TABLE licenseplates (
			plate_number VARCHAR(20),
			plate_image_path VARCHAR(200),
			time_spotted VARCHAR(50),
			camera_name VARCHAR(20),
			detection_box_name VARCHAR(20));"""

			cursor.execute(tableInitializationCommand)
			connection.commit()
			connection.close()

			print("Initialized new database")
		else:
			print("Database found")

		# buffer of data entries to be entered sequentially, contains licensePlate objects
		self.entryList = []

		self.stopped = False
		self.ready = False

	def start(self):
		Thread(target=self.update, args=()).start()
		return self

	def writeToDatabase(self, licensePlate):
		# licenseplate is of the licensePlate class/ datatype
		self.entryList.append(licensePlate)

	def update(self):
		self.ready = True
		# SQLite objects can only be called in the thread that they were created in!
	 	# create SQL objects here
		connection = sqlite3.connect(self.databaseName)
		cursor = connection.cursor()
		print("Connected to database")
		print(" ")

		while True:
			if self.stopped:
				break

			# store licenseplate in database
			numCommits = 0
			for plate in self.entryList:
				# find a way to delete the licenseplate objects and release memory, later... DO in licenseplateservice
				# store image in IMAGES directory, get path
				directoryPath = "database/Images/" + str(plate.cameraName) + " " + str(plate.detectorName) + " " + str(plate.datetime).replace(".", "-") + " " + str(plate.number) + ".png"
				print("Found license plate:" + str(plate.number))
				print("Saved image to: " + directoryPath)
				cv2.imwrite(directoryPath, plate.image)

				entryCommand = 'INSERT INTO licenseplates VALUES("{}", "{}", "{}", "{}", "{}")'.format(str(plate.number), directoryPath, str(plate.datetime), plate.cameraName, plate.detectorName)
				cursor.execute(entryCommand)
				connection.commit()

				numCommits += 1

			if numCommits == len(self.entryList):
				self.entryList = []

		# clean up, the thread is dead, long live the thread!
		connection.close()		# close the connection to the database
		print(" ")
		print("Disconnected from the database")

	def stop(self):
		self.stopped = True

def getSystemUptime():
	with open('/proc/uptime', 'r') as f:
		uptime_seconds = float(f.readline().split()[0])
		#uptime_string = str(datetime.timedelta(seconds=uptime_seconds))

	return uptime_seconds

class licensePlate():
	# a simple object data type to hold the necessary data, and make things easier
	def __init__(self, number, image, time, cameraName, detectorBoxName, datetime, confidence = 0.0):
		self.number = number
		self.image = image
		self.timeSpotted = time
		self.cameraName = cameraName
		self.detectorName = detectorBoxName
		self.datetime = datetime
		self.confidence = confidence
		self.delete = False

class detectionBox():
	def __init__(self, cameraName, name, area, webcamReference, alprconfig, alprruntime, dbReference):
		self.cameraName = cameraName
		self.name = name
		self.area = area # bounding box for the search
		self.stream = webcamReference # reference to the video feed
		self.oldDetectedRect = []

		# threads cannot share alpr object, needs its own
		self.alpr = Alpr("us", alprconfig, alprruntime)
		self.alpr.set_top_n(1)

		self.fps = FPS().start()

		self.stopped = False

		# stores licensplate objects
		self.licenseplateList = []

		self.licenseplateService = licenseplateService(self, dbReference).start()

	def start(self):
		Thread(target=self.update, args=()).start()
		return self

	def update(self): # main method, do processing here
		while True:
			if self.stopped:
				return

			self.fps.update()

			# grab the most recent frame from the video thread
			frame = self.stream.read()
			croppedFrame = frame[int(self.area[1]):int(self.area[1] + self.area[3]), int(self.area[0]):int(self.area[0] + self.area[2])]

			#run the detector
			results = self.alpr.recognize_ndarray(croppedFrame)

			detectedRect = []
			# finds all rects in frame and stores in detectedRect
			if results['results']:
				for plate in results['results']:

					# offset so points are relative to the frame, not cropped frame, use to find bounding rect
					leftBottom = (plate['coordinates'][3]['x'] + self.area[0], plate['coordinates'][3]['y'] + self.area[1])
					rightBottom = (plate['coordinates'][2]['x'] + self.area[0], plate['coordinates'][2]['y'] + self.area[1])
					rightTop = (plate['coordinates'][1]['x'] + self.area[0], plate['coordinates'][1]['y'] + self.area[1])
					leftTop = (plate['coordinates'][0]['x'] + self.area[0], plate['coordinates'][0]['y'] + self.area[1])

					allPoints = np.array([leftBottom, rightBottom, leftTop, rightTop])
					boundingRect = cv2.boundingRect(allPoints)  # X, Y, W, H

					detectedRect.append(boundingRect)

					# convert lpr results into a licenseplate object and store in licenseplatelist
					plateNumber = plate['plate']
					plateImage = frame[int(boundingRect[1]):int(boundingRect[1] + boundingRect[3]), int(boundingRect[0]):int(boundingRect[0] + boundingRect[2])]
					plateDatetime = datetime.datetime.now()
					plateTime = getSystemUptime()
					plateConfidence = plate['confidence']
					newPlate = licensePlate(plateNumber, plateImage, plateTime, self.cameraName, self.name, plateDatetime, plateConfidence)
					self.licenseplateList.append(newPlate)
					self.licenseplateService.notify() # help out the poor thread

				self.oldDetectedRect = detectedRect # this way, detectedRect will be erased and operated on but oldDetectedRect will always have something in it

			else:
				# no results
				self.oldDetectedRect = []

	def draw(self, frame):
		# return frame with drawings on it
		# draw plates detected and bounding boxes
		# is this necessary? The bounding boxes of the search areas should not overlap
		# should check for overlapping bounding boxes in constructor

		# draw plates detected
		# print(len(self.oldDetectedRect))
		for rect in self.oldDetectedRect:
			#print(rect)
			cv2.rectangle(frame, rect, (0, 255, 0), 2)

		# no need to draw corner points

		# draw search box and name
		cv2.putText(frame, self.name, (self.area[0], self.area[1]-5),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (15, 15, 255), 2)
		cv2.rectangle(frame, self.area, (0, 0, 255), 2)

		# return drawn frame
		return frame

	def stop(self):
		self.fps.stop()
		print(self.name, "FPS: ", self.fps.fps())
		self.licenseplateService.stop()
		self.stopped = True

class licenseplateService():
	def __init__(self, detectionboxreference, dbReference):
		self.detectionBoxReference = detectionboxreference
		self.dbReference = dbReference

		#defintely not a speed problem!!!!
		#785484 FPS!!!

		self.stopped = False
		self.notified = False

		self.orderedLicensePlateList = []
		self.groupsList = []

	def start(self):
		Thread(target=self.update, args=()).start()
		return self

	def update(self):

		while True:
			if self.stopped:
				return

			if self.notified:
				# this means that a new license plate has been added to the list
				# time to sort and place that new plate
				self.notified = False

				# copy contents in to a buffer and flush the original buffer
				tempLicensePlateList = self.detectionBoxReference.licenseplateList
				self.detectionBoxReference.licenseplateList = []

				# use licensePlateList like a buffer of new data to be actively sorted into a new ordered list
				# order based on time stamp
				tempLicensePlateList.sort(key=lambda x: x.timeSpotted)

				# add ordered list to total list, merge
				self.orderedLicensePlateList += tempLicensePlateList

			########### PROCESS PLATES IN THIS THREAD LOOP ############

			########### BEGIN SORTING PLATES INTO GROUPS ##############

			# ordered list based on time, separate into groups based on time differentials
			# refine groups based on license plate numbers
			timeDifferentialIndexes = []				# time differential index list, difference between [i+1] - [i]
			minTimeDifferential = 3 					# seconds, should be variable, the time differential between sequential plates time spotted, 3 is good time
			maxWaitTime = 10							# seconds, should be variable, the time differential between time spotted and system time
			for i in range(len(self.orderedLicensePlateList)):
				# check if last element in list
				if i == len(self.orderedLicensePlateList)-1:
					break

				difference = self.orderedLicensePlateList[i+1].timeSpotted - self.orderedLicensePlateList[i].timeSpotted

				# system difference results in all plates being timeDifferentials if another car does not pass with in the waittime interval
				# needs to work the orderedLicensePlateList in reverse, so the LATEST plate is counted down
				# conclusion: bring system difference outside of the for loop and operate on the last element in the orderedLicenseplate List!
				#systemDifference = getSystemUptime() - self.orderedLicensePlateList[i].timeSpotted # errors out if plates are not being removed...

				#print(difference, systemDifference)

				#if (difference >= minTimeDifferential) or (systemDifference >= maxWaitTime): # include systemDifference
				if difference >= minTimeDifferential: # do not include systemDifference
					timeDifferentialIndexes.append(i)

				# works great!
				# one flaw:
				# 	needs a second plate to create a time differential thus allowing the previous plate to be processed
				#	should place and active timer in place of a differential for stability
				#	a timing thread for each group?
				#	reset a timer every time a new plate is detected, add plate to group. If timer runs out, group is sealed?
				# 	system difference has not been tested, possible flaws may exist, solves the last car problem

			# find system difference with the LAST plate in the list. operate if self.orderedLicensePlateList is NOT empty
			if len(self.orderedLicensePlateList) != 0:
				systemDifference = getSystemUptime() - self.orderedLicensePlateList[len(self.orderedLicensePlateList)-1].timeSpotted
				if systemDifference >= maxWaitTime:
					timeDifferentialIndexes.append((len(self.orderedLicensePlateList)-1))

			#print(timeDifferentialIndexes)

			groups = []										# groupings of indexes, grouped by time differentials calculated above
			lastIndex = 0
			for index in timeDifferentialIndexes:
				group = range(lastIndex, index + 1)
				lastIndex = index + 1
				groups.append(group)
			# needs testing but seems to work

			#print(groups)

			# groups is a list of ranges, use them to remove plates from orderedList and put them in a list inside of self.groups list
			indexDecrement = 0		# everytime a plate is deleted, indexDecrement goes up one. This combats the index shift that occurs in a list of changing size
			for group in groups: # AKA for range in ranges...
				tempPlateGroup = []
				for index in group:
					plate = self.orderedLicensePlateList[index -indexDecrement]
					indexDecrement += 1;
					tempPlateGroup.append(plate)
					self.orderedLicensePlateList.remove(plate) # REMOVES PLATE FROM LIST!!! Watchout for remove-erase problems
				self.groupsList.append(tempPlateGroup)


			#print(len(self.groupsList)) 		# can be used for estimating the number of cars that pass by
			#print(self.groupsList)

			#for group in self.groupsList:
			#	for plate in group:
			#		print(plate.confidence)

			################# PLATE GROUP SORTING END ################

			################# REFINE GROUPS ###################

			# take the plates in self.groupsList and check for consistency
			# refine the groups by moving plates into their correct groups if they were miss-classified
			# verify by plate number?
			# helpful in high traffic areas with lower time between plate sightings

			################## END REFINE GROUPS ##############

			################## PUBLISH DATA TO SQL DATABASE ####################

			# might be a good idea to do this in a different thread if it takes to long. Avoid missing notifications at all cost!
			# actually, buffer flushing happens in this thread, so its not too big of deal, but still avoid it if you can

			# need to record everything in the licenseplate class
			# - plate number
			# - path to plate image (one image will be saved)
			# - time spotted (range?) (first seen?)
			# - camera name
			# - detectorBoxName (IN/OUT)

			for group in self.groupsList:
				#find and publish the most confident plate in the group
				mostConfidentPlate = group[0]
				for plate in group:
					if plate.confidence > mostConfidentPlate.confidence:
						mostConfidentPlate = plate	#works!

					#plate.delete = True			#mark plate for deletion #this does not help...

				self.dbReference.writeToDatabase(copy.deepcopy(mostConfidentPlate))
			self.groupsList = []
				#print()
				#print(mostConfidentPlate.confidence)


			# choose a plate with the highest confidence to represent the group? or create a new licensePlate object to represent the group? both?
			'''tempGroupList = self.groupsList
			for group in self.groupsList:
				mostConfidentPlate = group[0] # first plate in group
				# find the plate with the highest confidence
				for plate in group:
					if plate.confidence > mostConfidentPlate.confidence:
						mostConfidentPlate = plate
				#youngest plate would be the first (or last?) in the group, FYI
				self.dbReference.writeToDatabase(mostConfidentPlate)
				tempGroupList.remove(group)

			#self.groupsList = [] # after writing the plate to database, purge the groupList. Make group list local? (remove self.X)?
			self.groupList = tempGroupList
			'''

			################## END PUBLISH DATA TO SQL DATABASE ################

	def stop(self):
		self.stopped = True

	def notify(self):
		self.notified = True

# end custom alpr module definitions



# start up the database server, REMEMBER TO ACTUALLY .start() IT!!!
dbService = databaseService().start()

# replace with better system for launching threads in order... get the OK from dbService
while not dbService.ready:
	continue

# start up ALPR loop on camera
progTerminate = False

cameraThreads = {}
for camera in cameraList:
	cameraThreads[camera.name] = Thread(target=startALPRonCamera, args=(camera, dbService, alprConf, alprRunTime)).start()
	#cameraThreads[camera.name].start()

####
# handle terminal commands in a loop here
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

while 1:
	# main thread loop, handle UI and clean exit
	if not gui:
		command = input(">> ")
		if command == "q":
			break
		elif command == "help":
			for option in usableCommands:
				print(option, " : ", usableCommands[option])
			continue

	if progTerminate:
		break

####

# send end signal to process
progTerminate = True

# threads close faster than for loop can get to them
#for camera in cameraList:
#	cameraThreads[camera.name].join()

# define search areas
#areasOfInterest = {"IN":(232, 614, 643, 455)}#, "OUT":(997, 682, 843, 384)} #pull from config file
#detectionBoxes = []
#for searchbox in areasOfInterest:
#	newBox = detectionBox("LPR CAMERA", searchbox, areasOfInterest[searchbox], cam, alprConf, alprRunTime, dbService).start()
#	detectionBoxes.append(newBox)
# end define

# setup user interface variables
#gui = True # should be a flag, or have default be set in config
#guiResolution = (800,600)
#if gui:
#	print("Starting in GUI mode")
#	print("Resolution: ", guiResolution)
#	print("press 'q' to exit")
#	print()
#else:
#	print("Starting in CONSOLE mode")
#	print("type 'help' for a list of commands")
#	print()
#usableCommands = {"help": "show all usable commands", "q": "quit the program"}
# end define

# main loop
#while 1:
#	# main thread, handle UI and clean exit
#
#	if gui:
#		frame = cam.read()
#		fps.update()
#
#		for box in detectionBoxes:
#			frame = box.draw(frame)
#
#		frame = cv2.resize(frame, guiResolution)
#		cv2.imshow('viewer', frame)
#		if cv2.waitKey(1) & 0xFF == ord('q'):
#			break
#	else:
#		command = input(">> ")
#		if command == "q":
#			break
#		elif command == "help":
#			for option in usableCommands:
#				print(option, " : ", usableCommands[option])
#			continue
#		else:
#			continue

#kill all search box threads
#for box in detectionBoxes:
#	box.stop()

#print average FPS when program terminated
#fps.stop()
#print("main", "FPS: ", fps.fps())

dbService.stop()
cv2.destroyAllWindows()

