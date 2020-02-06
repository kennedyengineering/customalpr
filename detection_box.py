# detectionBox class implementation
# searches for license plates within a given frame buffer

from openalpr import Alpr
from fps import FPS
from license_plate_service import licensePlateService
from threading import Thread
import cv2
import numpy as np
import datetime
from get_system_uptime import get_system_uptime
from license_plate_datatype import licensePlate
import copy


class detectionBox:
	def __init__(self, camera_name, name, area, video_stream_reference, config, runtime, db_reference):
		self.camera_name = camera_name
		self.name = name
		self.area = area 							# bounding box for the search
		self.stream = video_stream_reference 		# reference to the video feed
		self.old_detected_rect = []

		# threads cannot share alpr object, needs its own
		self.alpr = Alpr("us", config, runtime)
		self.alpr.set_top_n(1)

		self.fps = FPS().start_timer()

		self.stopped = False

		# stores license plate objects
		self.license_plate_list = []

		self.licensePlateService = licensePlateService(self, db_reference).start()

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
			frame_copy = copy.copy(frame)
			cropped_frame = frame[int(self.area[1]):int(self.area[1] + self.area[3]), int(self.area[0]):int(self.area[0] + self.area[2])]

			# run the detector
			results = self.alpr.recognize_ndarray(cropped_frame)

			detected_rect = []
			# finds all rects in frame and stores in detectedRect
			if results['results']:
				for plate in results['results']:

					# offset so points are relative to the frame, not cropped frame, use to find bounding rect
					left_bottom = (plate['coordinates'][3]['x'] + self.area[0], plate['coordinates'][3]['y'] + self.area[1])
					right_bottom = (plate['coordinates'][2]['x'] + self.area[0], plate['coordinates'][2]['y'] + self.area[1])
					right_top = (plate['coordinates'][1]['x'] + self.area[0], plate['coordinates'][1]['y'] + self.area[1])
					left_top = (plate['coordinates'][0]['x'] + self.area[0], plate['coordinates'][0]['y'] + self.area[1])

					all_points = np.array([left_bottom, right_bottom, left_top, right_top])
					bounding_rect = cv2.boundingRect(all_points)  # X, Y, W, H

					detected_rect.append(bounding_rect)

					# convert lpr results into a license plate object and store in license_plate_list
					plate_number = plate['plate']
					#plate_image = frame[int(bounding_rect[1]):int(bounding_rect[1] + bounding_rect[3]), int(bounding_rect[0]):int(bounding_rect[0] + bounding_rect[2])]
					plate_image = cv2.resize(frame_copy, (720, 480), interpolation=cv2.INTER_AREA)
					plate_datetime = datetime.datetime.now()
					plate_time = get_system_uptime()
					plate_confidence = plate['confidence']
					new_plate = licensePlate(plate_number, plate_image, plate_time, self.camera_name, self.name, plate_datetime, plate_confidence)
					self.license_plate_list.append(new_plate)
					self.licensePlateService.notify()   # help out the poor thread

				self.old_detected_rect = detected_rect  # this way, detectedRect will be erased and operated on but oldDetectedRect will always have something in it

			else:
				# no results
				self.old_detected_rect = []

	def draw(self, frame):
		# return frame with drawings on it
		# draw plates detected and bounding boxes
		# is this necessary? The bounding boxes of the search areas should not overlap
		# should check for overlapping bounding boxes in constructor

		# draw plates detected
		# print(len(self.oldDetectedRect))
		for rect in self.old_detected_rect:
			cv2.rectangle(frame, rect, (0, 255, 0), 2)

		# draw search box and name
		cv2.putText(frame, self.name, (self.area[0], self.area[1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (15, 15, 255), 2)
		cv2.rectangle(frame, self.area, (0, 0, 255), 2)

		# return drawn frame
		return frame

	def stop(self):
		self.fps.stop()
		print(self.name, "FPS: ", self.fps.fps())
		self.licensePlateService.stop()
		self.stopped = True
