import cv2
from openalpr import Alpr
import numpy as np
from threading import Thread
import datetime
import getpass
import matplotlib

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
# end helper module definition

videoSource = "rtsp://LPRuser:ThisISfun1@10.48.140.5:554/Streaming/channels/101/" # bring from config file. Allow for multiple cameras
cam = WebcamVideoStream(src=videoSource).start()
fps = FPS().start()

# customalpr modules
def getSystemUptime():
	with open('/proc/uptime', 'r') as f:
		uptime_seconds = float(f.readline().split()[0])
		#uptime_string = str(datetime.timedelta(seconds=uptime_seconds))

	return uptime_seconds

class licensePlate():
	# a simple object data type to hold the necessary data, and make things easier
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
					#plateTime = datetime.datetime.now()
					plateTime = getSystemUptime()
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

		#defintely not a speed problem!!!!
		#785484 FPS!!!

		self.stopped = False
		self.notified = False

		self.orderedLicensePlateList = []

		#self.outputfile = open("timedensity.txt", "w+")

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

				#licensePlateListLength = len(self.detectionBoxReference.licenseplateList)
				#print("Added plate to list. Current length: ", licensePlateListLength)

				# use licensePlateList like a buffer of new data to be actively sorted into a new ordered list
				# order based on time stamp
				tempLicensePlateList.sort(key=lambda x: x.timeSpotted)

				# diagnostic for loop
				for plate in tempLicensePlateList:
					print(plate.timeSpotted)
					#print(plate.timeSpotted)

				# add ordered list to total list
				self.orderedLicensePlateList += tempLicensePlateList

				# ordered list based on time, separate into groups based on time differentials
				# refine groups based on license plate numbers
				timeDifferentialIndexes = []				# time differential index list, difference between [i+1] - [i]
				minTimeDifferential = 3 # seconds
				for i in range(len(self.orderedLicensePlateList)):
					# check if last element in list
					if i == len(self.orderedLicensePlateList)-1:
						break

					difference = self.orderedLicensePlateList[i+1].timeSpotted - self.orderedLicensePlateList[i].timeSpotted
					print(difference)

					if difference >= minTimeDifferential:
						timeDifferentialIndexes.append(i)

				groups = []
				for i in range(len(timeDifferentialIndexes)):
					# check if last element in list
					if i == len(timeDifferentialIndexes)-1:
						break

					indexRange = range(timeDifferentialIndexes[i], timeDifferentialIndexes[i+1]) # goes from numbers i --> one less than i+1
					groups.append(indexRange)

				print(timeDifferentialIndexes)
				print(groups)

				#self.outputfile.write(str(datetime.datetime.now().time())+"\n")
				#print(uptimeToSeconds(self.detectionBoxReference.licenseplateList[licensePlateListLength-1].timeSpotted))

	def stop(self):
		#self.outputfile.close()
		self.stopped = True

	def notify(self):
		self.notified = True
# end custom alpr module definitions

# define search areas
areasOfInterest = {"IN":(232, 614, 643, 455)}#, "OUT":(997, 682, 843, 384)}
detectionBoxes = []
for searchbox in areasOfInterest:
	newBox = detectionBox("LPR CAMERA", searchbox, areasOfInterest[searchbox], cam, alprConf, alprRunTime).start()
	detectionBoxes.append(newBox)
# end define

# setup user interface variables
gui = True # should be a flag, or have default be set in config
guiResolution = (800,600)
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
# end define

# main loop
while 1:
	# main thread, handle UI and clean exit

	if gui:
		frame = cam.read()
		fps.update()

		for box in detectionBoxes:
			frame = box.draw(frame)

		frame = cv2.resize(frame, guiResolution)
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