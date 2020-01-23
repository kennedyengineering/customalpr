# fps counter class
# credit to pyImageSearch website for original code

import datetime


class FPS:
	def __init__(self):
		# store the start time, end time, and total number of frames
		# that were examined between the start and end intervals
		self.start = None
		self.end = None
		self.num_frames = 0

	def start_timer(self):
		# start the timer
		self.start = datetime.datetime.now()
		return self

	def stop(self):
		# stop the timer
		self.end = datetime.datetime.now()

	def update(self):
		# increment the total number of frames examined during the
		# start and end intervals
		self.num_frames += 1

	def elapsed(self):
		# return the total number of seconds between the start and
		# end interval
		return (self.end - self.start).total_seconds()

	def fps(self):
		# compute the (approximate) frames per second
		return self.num_frames / self.elapsed()
