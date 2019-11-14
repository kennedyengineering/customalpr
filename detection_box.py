from openalpr import Alpr
from fps import FPS
from licenseplate_service import licenseplateService
from threading import Thread
import cv2
import numpy as np

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