# one thread instance to represent the sqlite database
# slight speed advantage
# is redundant. Should replace with SQLalchemy or the like

import sqlite3
import cv2
import os
from threading import Thread


class databaseService():
	def __init__(self):
		# The purpose of this thread is to control the writing to the database from multiple locations
		# This module prevents writes occurring at the same time
		# as well as handling other aspects of the database
		# technically sqlite3 can have multiple connections, but this seems like a safe idea

		# there should only be ONE databaseService initialized
		self.database_name = "database/database.db"

		# check if database already exists, if not, initialize it
		print(" ")
		print("Connecting to database...")
		if (os.path.exists(self.database_name) == False): # true if file exists
			print("No database found, initializing...")
			connection = sqlite3.connect(self.database_name)
			cursor = connection.cursor()

			# need to record everything in the license plate class

			table_initialization_command = """CREATE TABLE licenseplates (
			plate_number VARCHAR(20),
			plate_image_path VARCHAR(200),
			time_spotted VARCHAR(50),
			camera_name VARCHAR(20),
			detection_box_name VARCHAR(20));"""

			cursor.execute(table_initialization_command)
			connection.commit()
			connection.close()

			print("Initialized new database")
		else:
			print("Database found")

		# buffer of data entries to be entered sequentially, contains licensePlate objects
		self.entry_list = []

		self.stopped = False
		self.ready = False

	def start(self):
		Thread(target=self.update, args=()).start()
		return self

	def writeToDatabase(self, license_plate):
		# license plate is of the licensePlate class/ datatype
		self.entry_list.append(license_plate)

	def update(self):
		self.ready = True
		# SQLite objects can only be called in the thread that they were created in

		connection = sqlite3.connect(self.database_name)
		cursor = connection.cursor()
		print("Connected to database")
		print(" ")

		while True:
			if self.stopped:
				break

			# store license plate in database
			num_commits = 0
			for plate in self.entry_list:
				# store image in IMAGES directory, get path
				directory_path = "database/Images/" + str(plate.camera_name) + " " + str(plate.detector_name) + " " + str(plate.datetime).replace(".", "-") + " " + str(plate.number) + ".png"
				print("Found license plate:" + str(plate.number))
				print("Saved image to: " + directory_path)
				cv2.imwrite(directory_path, plate.image)

				entry_command = 'INSERT INTO licenseplates VALUES("{}", "{}", "{}", "{}", "{}")'.format(str(plate.number), directory_path, str(plate.datetime), plate.camera_name, plate.detector_name)
				cursor.execute(entry_command)
				connection.commit()

				num_commits += 1

			if num_commits == len(self.entry_list):
				self.entry_list = []

		# clean up, the thread is dead, long live the thread!
		connection.close()		# close the connection to the database
		print(" ")
		print("Disconnected from the database")

	def stop(self):
		self.stopped = True