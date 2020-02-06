# license plate datatype

class licensePlate():
	# a simple object data type to hold the necessary data, and make things easier
	def __init__(self, number, image, time, camera_name, detector_box_name, datetime, confidence=0.0):
		self.number = number
		self.image = image
		self.time_spotted = time
		self.camera_name = camera_name
		self.detector_name = detector_box_name
		self.datetime = datetime
		self.confidence = confidence
		self.delete = False