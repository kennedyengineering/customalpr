from threading import Thread
from get_system_uptime import getSystemUptime
import copy

class licenseplateService():
	def __init__(self, detectionboxreference, dbReference):
		self.detectionBoxReference = detectionboxreference
		self.dbReference = dbReference

		#defintely not a speed problem!!!!
		#785484 FPS!!!

		self.stopped = False
		self.notified = False

		self.orderedLicensePlateList = []
		self.groupsList = []

	def start(self):
		Thread(target=self.update, args=()).start()
		return self

	def update(self):

		while True:
			if self.stopped:
				return

			if self.notified:
				# this means that a new license plate has been added to the list
				# time to sort and place that new plate
				self.notified = False

				# copy contents in to a buffer and flush the original buffer
				tempLicensePlateList = self.detectionBoxReference.licenseplateList
				self.detectionBoxReference.licenseplateList = []

				# use licensePlateList like a buffer of new data to be actively sorted into a new ordered list
				# order based on time stamp
				tempLicensePlateList.sort(key=lambda x: x.timeSpotted)

				# add ordered list to total list, merge
				self.orderedLicensePlateList += tempLicensePlateList

			########### PROCESS PLATES IN THIS THREAD LOOP ############

			########### BEGIN SORTING PLATES INTO GROUPS ##############

			# ordered list based on time, separate into groups based on time differentials
			# refine groups based on license plate numbers
			timeDifferentialIndexes = []				# time differential index list, difference between [i+1] - [i]
			minTimeDifferential = 3 					# seconds, should be variable, the time differential between sequential plates time spotted, 3 is good time
			maxWaitTime = 10							# seconds, should be variable, the time differential between time spotted and system time
			for i in range(len(self.orderedLicensePlateList)):
				# check if last element in list
				if i == len(self.orderedLicensePlateList)-1:
					break

				difference = self.orderedLicensePlateList[i+1].timeSpotted - self.orderedLicensePlateList[i].timeSpotted

				# system difference results in all plates being timeDifferentials if another car does not pass with in the waittime interval
				# needs to work the orderedLicensePlateList in reverse, so the LATEST plate is counted down
				# conclusion: bring system difference outside of the for loop and operate on the last element in the orderedLicenseplate List!
				#systemDifference = getSystemUptime() - self.orderedLicensePlateList[i].timeSpotted # errors out if plates are not being removed...

				#print(difference, systemDifference)

				#if (difference >= minTimeDifferential) or (systemDifference >= maxWaitTime): # include systemDifference
				if difference >= minTimeDifferential: # do not include systemDifference
					timeDifferentialIndexes.append(i)

				# works great!
				# one flaw:
				# 	needs a second plate to create a time differential thus allowing the previous plate to be processed
				#	should place and active timer in place of a differential for stability
				#	a timing thread for each group?
				#	reset a timer every time a new plate is detected, add plate to group. If timer runs out, group is sealed?
				# 	system difference has not been tested, possible flaws may exist, solves the last car problem

			# find system difference with the LAST plate in the list. operate if self.orderedLicensePlateList is NOT empty
			if len(self.orderedLicensePlateList) != 0:
				systemDifference = getSystemUptime() - self.orderedLicensePlateList[len(self.orderedLicensePlateList)-1].timeSpotted
				if systemDifference >= maxWaitTime:
					timeDifferentialIndexes.append((len(self.orderedLicensePlateList)-1))

			#print(timeDifferentialIndexes)

			groups = []										# groupings of indexes, grouped by time differentials calculated above
			lastIndex = 0
			for index in timeDifferentialIndexes:
				group = range(lastIndex, index + 1)
				lastIndex = index + 1
				groups.append(group)
			# needs testing but seems to work

			#print(groups)

			# groups is a list of ranges, use them to remove plates from orderedList and put them in a list inside of self.groups list
			indexDecrement = 0		# everytime a plate is deleted, indexDecrement goes up one. This combats the index shift that occurs in a list of changing size
			for group in groups: # AKA for range in ranges...
				tempPlateGroup = []
				for index in group:
					plate = self.orderedLicensePlateList[index -indexDecrement]
					indexDecrement += 1;
					tempPlateGroup.append(plate)
					self.orderedLicensePlateList.remove(plate) # REMOVES PLATE FROM LIST!!! Watchout for remove-erase problems
				self.groupsList.append(tempPlateGroup)


			#print(len(self.groupsList)) 		# can be used for estimating the number of cars that pass by
			#print(self.groupsList)

			#for group in self.groupsList:
			#	for plate in group:
			#		print(plate.confidence)

			################# PLATE GROUP SORTING END ################

			################# REFINE GROUPS ###################

			# take the plates in self.groupsList and check for consistency
			# refine the groups by moving plates into their correct groups if they were miss-classified
			# verify by plate number?
			# helpful in high traffic areas with lower time between plate sightings

			################## END REFINE GROUPS ##############

			################## PUBLISH DATA TO SQL DATABASE ####################

			# might be a good idea to do this in a different thread if it takes to long. Avoid missing notifications at all cost!
			# actually, buffer flushing happens in this thread, so its not too big of deal, but still avoid it if you can

			# need to record everything in the licenseplate class
			# - plate number
			# - path to plate image (one image will be saved)
			# - time spotted (range?) (first seen?)
			# - camera name
			# - detectorBoxName (IN/OUT)

			for group in self.groupsList:
				#find and publish the most confident plate in the group
				mostConfidentPlate = group[0]
				for plate in group:
					if plate.confidence > mostConfidentPlate.confidence:
						mostConfidentPlate = plate	#works!

					#plate.delete = True			#mark plate for deletion #this does not help...

				self.dbReference.writeToDatabase(copy.deepcopy(mostConfidentPlate))
			self.groupsList = []
				#print()
				#print(mostConfidentPlate.confidence)


			# choose a plate with the highest confidence to represent the group? or create a new licensePlate object to represent the group? both?
			'''tempGroupList = self.groupsList
			for group in self.groupsList:
				mostConfidentPlate = group[0] # first plate in group
				# find the plate with the highest confidence
				for plate in group:
					if plate.confidence > mostConfidentPlate.confidence:
						mostConfidentPlate = plate
				#youngest plate would be the first (or last?) in the group, FYI
				self.dbReference.writeToDatabase(mostConfidentPlate)
				tempGroupList.remove(group)

			#self.groupsList = [] # after writing the plate to database, purge the groupList. Make group list local? (remove self.X)?
			self.groupList = tempGroupList
			'''

			################## END PUBLISH DATA TO SQL DATABASE ################

	def stop(self):
		self.stopped = True

	def notify(self):
		self.notified = True
