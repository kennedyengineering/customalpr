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