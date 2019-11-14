import cv2
from threading import Thread

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