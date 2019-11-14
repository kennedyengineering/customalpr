import sqlite3
import cv2
import os
from threading import Thread

class databaseService():
	def __init__(self):
		# WARNING!!
		# The purpose of this thread is to control the writing to the database from multiple locations
		# This module prevents writes occuring at the same time
		# as well as handling other aspects of the database
		# technically sqlite3 can have multiple connections, but this seems like a safe idea

		# there should only be ONE databaseService initialized!!!
		self.databaseName = "database/database.db"
		# check if database already exists, if not, initialize it
		print(" ")
		print("Connecting to database...")
		if (os.path.exists(self.databaseName) == False): # true if file exists
			print("No database found, initializing...")
			connection = sqlite3.connect(self.databaseName)
			cursor = connection.cursor()

			# need to record everything in the licenseplate class
			# - plate number <string>
			# - path to plate image (one image will be saved) <string>
			# - time spotted (range?) (datetime) <?>
			# - camera name <string>
			# - detectorBoxName (IN/OUT) <string>

			tableInitializationCommand = """CREATE TABLE licenseplates (
			plate_number VARCHAR(20),
			plate_image_path VARCHAR(200),
			time_spotted VARCHAR(50),
			camera_name VARCHAR(20),
			detection_box_name VARCHAR(20));"""

			cursor.execute(tableInitializationCommand)
			connection.commit()
			connection.close()

			print("Initialized new database")
		else:
			print("Database found")

		# buffer of data entries to be entered sequentially, contains licensePlate objects
		self.entryList = []

		self.stopped = False
		self.ready = False

	def start(self):
		Thread(target=self.update, args=()).start()
		return self

	def writeToDatabase(self, licensePlate):
		# licenseplate is of the licensePlate class/ datatype
		self.entryList.append(licensePlate)

	def update(self):
		self.ready = True
		# SQLite objects can only be called in the thread that they were created in!
	 	# create SQL objects here
		connection = sqlite3.connect(self.databaseName)
		cursor = connection.cursor()
		print("Connected to database")
		print(" ")

		while True:
			if self.stopped:
				break

			# store licenseplate in database
			numCommits = 0
			for plate in self.entryList:
				# find a way to delete the licenseplate objects and release memory, later... DO in licenseplateservice
				# store image in IMAGES directory, get path
				directoryPath = "database/Images/" + str(plate.cameraName) + " " + str(plate.detectorName) + " " + str(plate.datetime).replace(".", "-") + " " + str(plate.number) + ".png"
				print("Found license plate:" + str(plate.number))
				print("Saved image to: " + directoryPath)
				cv2.imwrite(directoryPath, plate.image)

				entryCommand = 'INSERT INTO licenseplates VALUES("{}", "{}", "{}", "{}", "{}")'.format(str(plate.number), directoryPath, str(plate.datetime), plate.cameraName, plate.detectorName)
				cursor.execute(entryCommand)
				connection.commit()

				numCommits += 1

			if numCommits == len(self.entryList):
				self.entryList = []

		# clean up, the thread is dead, long live the thread!
		connection.close()		# close the connection to the database
		print(" ")
		print("Disconnected from the database")

	def stop(self):
		self.stopped = True