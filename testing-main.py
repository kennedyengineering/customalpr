import cv2
from openalpr import Alpr
import numpy as np
from threading import Thread
import datetime
import getpass
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

# helper modules from
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
		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(src)
		(self.grabbed, self.frame) = self.stream.read()

		# initialize the variable used to indicate if the thread should
		# be stopped
		self.stopped = False

	def start(self):
		# start the thread to read frames from the video stream
		Thread(target=self.update, args=()).start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return

			# otherwise, read the next frame from the stream
			(self.grabbed, self.frame) = self.stream.read()

	def read(self):
		# return the frame most recently read
		return self.frame

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True

videoSource = "rtsp://LPRuser:ThisISfun1@10.48.140.5:554/Streaming/channels/101/" # bring from config file. Allow for multiple cameras
cam = WebcamVideoStream(src=videoSource).start()
fps = FPS().start()

class licensePlate():
	# a simple object to hold the necessary data, and make things easier
	def __init__(self, number, image, time, cameraName, detectorBoxName):
		self.number = number
		self.image = image
		self.timeSpotted = time
		self.cameraName = cameraName
		self.detectorName = detectorBoxName

class detectionBox():
	def __init__(self, cameraName, name, area, webcamReference, alprconfig, alprruntime):
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

		self.licenseplateService = licenseplateService(self).start()

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
					plateTime = datetime.datetime.now()
					newPlate = licensePlate(plateNumber, plateImage, plateTime, self.cameraName, self.name)
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
	def __init__(self, detectionboxreference):
		self.detectionBoxReference = detectionboxreference

		#copy.copy --> shallow copy
		#copy.deepcopy --> deep copy

		#start both as the same thing
		self.lastLicenseplateList = self.detectionBoxReference.licenseplateList
		self.currentLicenseplateList = self.lastLicenseplateList

		#defintely not a speed problem!!!!
		#785484 FPS!!!

		self.stopped = False
		self.notified = True

	def start(self):
		Thread(target=self.update, args=()).start()
		return self

	def update(self):
		while True:
			if self.stopped:
				return

			if self.notified:

				# this means that a new license plate has been added to the list
				self.notified = False
				print("ON IT!", len(self.detectionBoxReference.licenseplateList))


			'''
			self.currentLicenseplateList = self.detectionBoxReference.licenseplateList

			lastQuantity = len(self.lastLicenseplateList)
			currentQuantity = len(self.currentLicenseplateList)

			if currentQuantity != lastQuantity:
				print(currentQuantity, lastQuantity, len(self.detectionBoxReference.licenseplateList))

			self.lastLicenseplateList = self.currentLicenseplateList
			'''

			'''
			if self.lastLicenseplateList == None:
				self.lastLicenseplateList = self.currentLicenseplateList
				continue
			else:
				lastQuantity = len(self.lastLicenseplateList)
				currentQuantity = len(self.currentLicenseplateList)

				if currentQuantity != lastQuantity:
					print(currentQuantity, lastQuantity)

				#if self.lastLicenseplateList != self.currentLicenseplateList:
				#	print(len(self.currentLicenseplateList))

			self.lastLicenseplateList = self.currentLicenseplateList
			'''

	def stop(self):
		self.stopped = True

	def notify(self):
		self.notified = True

areasOfInterest = {"IN":(232, 614, 643, 455)}#, "OUT":(997, 682, 843, 384)}
detectionBoxes = []
for searchbox in areasOfInterest:
	newBox = detectionBox("LPR CAMERA", searchbox, areasOfInterest[searchbox], cam, alprConf, alprRunTime).start()
	detectionBoxes.append(newBox)

def overlap(a, b):
	# x,y,w,h
	# a is first
	# b is second
	# test if any point from first rect is inside second rect

	x = a[0]
	y = a[1]
	w = a[2]
	h = a[3]
	upperleft1 = (x, y)
	upperright1 = (x + w, y)
	lowerleft1 = (x, y + h)
	lowerright1 = (x + w, y + h)

	x = b[0]
	y = b[1]
	w = b[2]
	h = b[3]
	upperleft2 = (x, y)
	upperright2 = (x + w, y)
	lowerleft2 = (x, y + h)
	lowerright2 = (x + w, y + h)

	# check top left
	topLeftX = False
	if (upperleft1[0] < upperright2[0]):
		if (upperleft1[0] > upperleft2[0]):
			topLeftX = True
	topLeftY = False
	if (upperleft1[1] > upperleft2[1]):
		if (upperleft1[1] < lowerleft2[1]):
			topLeftY = True
	topLeft = False
	if topLeftY and topLeftX:
		topLeft = True

	# check top right
	topRightX = False
	if (upperright1[0] < upperright2[0]):
		if (upperright1[0] > upperleft2[0]):
			topRightX = True
	topRightY = False
	if (upperright1[1] > upperleft2[1]):
		if (upperright1[1] < lowerleft2[1]):
			topRightY = True
	topRight = False
	if topRightY and topRightX:
		topRight = True

	# check bottom left
	bottomLeftX = False
	if (lowerleft1[0] < upperright2[0]):
		if (lowerleft1[0] > upperleft2[0]):
			bottomLeftX = True
	bottomLeftY = False
	if (lowerleft1[1] > upperleft2[1]):
		if (lowerleft1[1] < lowerleft2[1]):
			bottomLeftY = True
	bottomLeft = False
	if bottomLeftY and bottomLeftX:
		bottomLeft = True

	# check bottom right
	bottomRightX = False
	if (lowerright1[0] < upperright2[0]):
		if (lowerright1[0] > upperleft2[0]):
			bottomRightX = True
	bottomRightY = False
	if (lowerright1[1] > upperleft2[1]):
		if (lowerright1[1] < lowerleft2[1]):
			bottomRightY = True
	bottomRight = False
	if bottomRightX and bottomRightY:
		bottomRight = True

	#return bool
	if bottomRight or bottomLeft or topLeft or topRight:
		return True
	else:
		return False

gui = True # should be a flag, or have default be set in config
if gui:
	print("Starting in GUI mode")
	print("press 'q' to exit")
	print()
else:
	print("Starting in CONSOLE mode")
	print("type 'help' for a list of commands")
	print()

usableCommands = {"help": "show all usable commands", "q": "quit the program"}

# main loop
while 1:
	# main thread, handle GUI and clean exit

	if gui:
		frame = cam.read()
		fps.update()

		for box in detectionBoxes:
			frame = box.draw(frame)

		cv2.imshow('viewer', frame)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
	else:
		command = input(">> ")
		if command == "q":
			break
		elif command == "help":
			for option in usableCommands:
				print(option, " : ", usableCommands[option])
			continue
		else:
			continue

#kill all search box threads
for box in detectionBoxes:
	box.stop()

#print average FPS when program terminated
fps.stop()
print("main", "FPS: ", fps.fps())

#stop camera, destroy gui
cam.stop()
cv2.destroyAllWindows()