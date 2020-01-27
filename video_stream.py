# threaded cv2 video_stream class implementation
# credit to pyImageSearch website for original code

# modified by kennedyengineering for improved redundancy

import cv2
import numpy as np
from threading import Thread


class videoStream:
	def __init__(self, src=0):
		self.stopped = False							# indicates if the thread should be stopped
		self.src = src
		print("pre video capture")
		self.stream = cv2.VideoCapture(src)				# initialize the video camera stream and read the first frame
		
		print("post video capture")
		#self.frame = None #self.grab_frame()
		#print("post video capture")

		# resolution can change... dont know if thats a problem
		self.frame = np.zeros((1920, 1080, 3), np.uint8) # create a blank image


	def start(self):

		Thread(target=self.update, args=()).start()		# start the thread to read frames from the video stream
		return self

	def grab_frame(self):
		# handle when self.stream.read() returns None as a frame
		# added network outage redundancy
		(grabbed, frame) = self.stream.read()
		while not grabbed:
			if self.stopped:							# allow clean exit with the rest of the program
				return

			self.stream = cv2.VideoCapture(self.src) 	# initialize a new video stream to compensate for broken network connection
			(grabbed, frame) = self.stream.read()

		return frame

	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			if self.stopped:							# if the thread indicator variable is set, stop the thread
				return

			self.frame = self.grab_frame()				# read the next frame from the stream

	def read(self):
		# return the frame most recently read
		return self.frame

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
