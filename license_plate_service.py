# license plate service class

from threading import Thread
from get_system_uptime import get_system_uptime
import copy


class licensePlateService:
	def __init__(self, detection_box_reference, db_reference):
		self.detection_box_reference = detection_box_reference
		self.db_reference = db_reference

		self.stopped = False
		self.notified = False

		self.ordered_license_plate_list = []
		self.groups_list = []

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
				temp_license_plate_list = self.detection_box_reference.license_plate_list
				self.detection_box_reference.license_plate_list = []

				# use licensePlateList like a buffer of new data to be actively sorted into a new ordered list
				# order based on time stamp
				temp_license_plate_list.sort(key=lambda x: x.time_spotted)

				# add ordered list to total list, merge
				self.ordered_license_plate_list += temp_license_plate_list

			# ordered list based on time, separate into groups based on time difference
			time_differential_indexes = []			# time differential index list, difference between [i+1] - [i]
			min_time_differential = 3 				# seconds, should be variable, the time differential between sequential plates time spotted, 3 is good time
			max_wait_time = 10						# seconds, should be variable, the time differential between time spotted and system time
			for i in range(len(self.ordered_license_plate_list)):
				# check if last element in list
				if i == len(self.ordered_license_plate_list)-1:
					break

				difference = self.ordered_license_plate_list[i+1].time_spotted - self.ordered_license_plate_list[i].time_spotted
				if difference >= min_time_differential:
					time_differential_indexes.append(i)

			# find system difference with the LAST plate in the list. operate if self.orderedLicensePlateList is not empty
			if len(self.ordered_license_plate_list) != 0:
				system_difference = get_system_uptime() - self.ordered_license_plate_list[len(self.ordered_license_plate_list)-1].time_spotted
				if system_difference >= max_wait_time:
					time_differential_indexes.append((len(self.ordered_license_plate_list)-1))

			groups = []								# groupings of indexes, grouped by time differentials calculated above
			last_index = 0
			for index in time_differential_indexes:
				group = range(last_index, index + 1)
				last_index = index + 1
				groups.append(group)

			# groups is a list of ranges, use them to remove plates from orderedList and put them in a list inside of self.groups list
			index_decrement = 0						# everytime a plate is deleted, indexDecrement goes up one. This combats the index shift that occurs in a list of changing size
			for group in groups:
				temp_plate_group = []
				for index in group:
					plate = self.ordered_license_plate_list[index - index_decrement]
					index_decrement += 1
					temp_plate_group.append(plate)
					self.ordered_license_plate_list.remove(plate)

				self.groups_list.append(temp_plate_group)

			for group in self.groups_list:
				# find and publish the most confident plate in the group
				most_confident_plate = group[0]
				for plate in group:
					if plate.confidence > most_confident_plate.confidence:
						most_confident_plate = plate

				self.db_reference.write_to_database(copy.deepcopy(most_confident_plate))

			self.groups_list = []

	def stop(self):
		self.stopped = True

	def notify(self):
		self.notified = True
