import cv2
from openalpr import Alpr
import numpy as np
from threading import Thread
import datetime
import getpass

#trackerType = 'KCF'
#tracker = cv2.TrackerKCF_create()

print("loading Alpr")
alprConf = "/etc/openalpr/openalpr.conf"
print("Alpr config path: ", alprConf)
#alprRunTime = "/home/dev/openalpr/runtime_data" # MAKE SURE TO CHANGE THIS PATH!!!! should probably be automated
#could use config file, but this seems OK
alprRunTime = "/home/" + str(getpass.getuser()) + "/openalpr/runtime_data"
#alpr = Alpr("us", alprConf, alprRunTime)
print("Alpr runtime path: ", alprRunTime)
#if not alpr.is_loaded():
#	print("Alpr failed to load")
#	exit()
#alpr.set_top_n(1)

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

#videoSource = "test_clip.MOV"
videoSource = "rtsp://LPRuser:ThisISfun1@10.48.140.5:554/Streaming/channels/101/"
#cam = cv2.VideoCapture()
#cam.open(videoSource)
cam = WebcamVideoStream(src=videoSource).start()
fps = FPS().start()

#frameWidth = int(cam.get(3))
#frameHeight = int(cam.get(4))
#out = cv2.VideoWriter('out.avi', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (frameWidth, frameHeight))

class detectionBox():
	def __init__(self, name, area, webcamReference, alprconfig, alprruntime):
		self.name = name
		self.area = area # bounding box for the search
		self.stream = webcamReference
		#self.detectedRect = []
		self.oldDetectedRect = []

		# threads cannot share alpr object, needs its own
		self.alpr = Alpr("us", alprconfig, alprruntime)

		self.fps = FPS().start()

		self.stopped = False

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

					# offset so points are relative to the frame, not cropped frame
					leftBottom = (plate['coordinates'][3]['x'] + self.area[0], plate['coordinates'][3]['y'] + self.area[1])
					rightBottom = (plate['coordinates'][2]['x'] + self.area[0], plate['coordinates'][2]['y'] + self.area[1])
					rightTop = (plate['coordinates'][1]['x'] + self.area[0], plate['coordinates'][1]['y'] + self.area[1])
					leftTop = (plate['coordinates'][0]['x'] + self.area[0], plate['coordinates'][0]['y'] + self.area[1])

					allPoints = np.array([leftBottom, rightBottom, leftTop, rightTop])
					boundingRect = cv2.boundingRect(allPoints)  # X, Y, W, H

					# draw rect and corner points
					#cv2.rectangle(frame, boundingRect, (0, 255, 0), 2)
					#for coordinate in plate['coordinates']:
					#	cv2.circle(frame, (coordinate['x'], coordinate['y']), 4, (0, 255, 0), -1)
					# move to draw method

					#for rect in detectedRect:
					#	if overlap(rect, boundingRect) or overlap(boundingRect, rect):
					#		pass
					#	else:
					#		detectedRect.append(boundingRect)  # list of all detected rects
					#		break
					detectedRect.append(boundingRect)

				self.oldDetectedRect = detectedRect # this way, detectedRect will be erased and operated on but oldDetectedRect will always have something in it

				#print("results on", self.name)
			else:
				#print("no results")
				self.oldDetectedRect = []
				#pass

	def draw(self, frame):
		# return frame with drawings on it
		# draw plates detected and bounding boxes
		# is this necessary? The bounding boxes of the search areas should not overlap
		# should check for overlapping bounding boxes

		# draw plates detected
		# print(len(self.oldDetectedRect))
		for rect in self.oldDetectedRect:
			#print(rect)
			cv2.rectangle(frame, rect, (0, 255, 0), 2)

		# no need to draw corner points

		# draw search box
		cv2.rectangle(frame, self.area, (0, 0, 255), 2)

		# return drawn frame
		return frame

	def stop(self):
		self.fps.stop()
		print(self.name, "FPS: ", self.fps.fps())
		self.stopped = True

#areasOfInterest = [(71, 736, 1758, 328)]
areasOfInterest = {"IN":(232, 614, 643, 455), "OUT":(997, 682, 843, 384)}
detectionBoxes = []
for searchbox in areasOfInterest:
	newBox = detectionBox(searchbox, areasOfInterest[searchbox], cam, alprConf, alprRunTime).start()
	detectionBoxes.append(newBox)

#trackers = []

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

while 1:
	frame = cam.read()
	fps.update()

	for box in detectionBoxes:
		frame = box.draw(frame)
		# results in laggy drawings because the processing threads are using older frames, and drawing according to those frames. The actual tagging is not incorrect
		# this is fine for now, but is a little annoying

	#ret, frame = cam.read()
	#if not ret:
	#	break

	# break down frame into searchable and un searchable zones
	# possibly increase FPS
	# crop frame, should include in config file

	#area = areasOfInterest[0]
	#cv2.rectangle(frame, area, (100,100,255), 1, 1)
	#croppedFrame = frame[int(area[1]):int(area[1]+area[3]), int(area[0]):int(area[0]+area[2])]
	#cv2.imshow("ROI", croppedFrame)

	####
	#results = alpr.recognize_ndarray(croppedFrame)

	#detectedRect = []
	#finds all rects in frame and stores in detectedRect
	'''if results['results']:
		for plate in results['results']:

			# don't give buffer size here! do it after the tracker
			# tracker returns the new rect, the inflate to find numbers with lpr

			# offset so points are relative to the frame, not cropped frame
			leftBottom = (plate['coordinates'][3]['x'] + area[0], plate['coordinates'][3]['y'] + area[1])
			rightBottom = (plate['coordinates'][2]['x'] + area[0], plate['coordinates'][2]['y'] + area[1])
			rightTop = (plate['coordinates'][1]['x'] + area[0], plate['coordinates'][1]['y'] + area[1])
			leftTop = (plate['coordinates'][0]['x'] + area[0], plate['coordinates'][0]['y'] + area[1])

			allPoints = np.array([leftBottom,rightBottom,leftTop,rightTop])
			boundingRect = cv2.boundingRect(allPoints)	#X, Y, W, H
			cv2.rectangle(frame, boundingRect, (0, 255, 0), 2)

			#for coordinate in plate['coordinates']:
			#	cv2.circle(frame, (coordinate['x'], coordinate['y']), 4, (0, 255, 0), -1)
			for rect in detectedRect:
				if overlap(rect, boundingRect) or overlap(boundingRect, rect):
					pass
				else:
					detectedRect.append(boundingRect) # list of all detected rects
					break
		#print("results")
	else:
		#print("no results")
		pass'''

	# now that detectedRect is filled, remove any possible double detections
	# ensure there is one rect per plate
	'''detectedRectCopy = detectedRect
	for rect1 in detectedRect:
		for rect2 in detectedRectCopy:
			pass
			# just do this when they are detected
	'''
	# temporarily removing trackers
	####
	'''
	trackerBoxes = []

	for tracker in trackers:
		ok, bbox = tracker.update(frame)
		if not ok:
			print("removing tracker")
			trackers.remove(tracker)
			# data base entry
		else:
			bboxRect = (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))
			trackerBoxes.append(bboxRect)
			cv2.rectangle(frame, bboxRect, (255, 0, 0), 2, 1)

	if len(trackers) == 0:
		for rect in detectedRect:
			print("creating tracker")
			tracker = cv2.TrackerKCF_create()
			tracker.init(frame, rect)
			trackers.append(tracker)
	else:

		if len(trackers) >= len(detectedRect): ### SUCCESS!! One tracker per detection
			pass
		else:
			availableDetections = []

			for rect in detectedRect:
				for box in trackerBoxes:
					if overlap(box, rect) or overlap(rect, box):
						break
					else:
						availableDetections.append(rect)
						break

			for rect in availableDetections:
				print("creating other tracker")
				tracker = cv2.TrackerKCF_create()
				tracker.init(frame, rect)
				trackers.append(tracker)


			#print("availableDetections: ", len(availableDetections))
			#print("detectedrect: ", len(detectedRect))
			#print("trackerboxes:", len(trackerBoxes))
	'''
	#####
	#

	# show output
	#out.write(frame)
	cv2.imshow('viewer', frame)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

#kill all search box threads
for box in detectionBoxes:
	box.stop()

#print average FPS when program terminated
fps.stop()
print("main", "FPS: ", fps.fps())

cam.stop()
cv2.destroyAllWindows()
#cam.release()
#out.release()
