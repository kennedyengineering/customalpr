import cv2
from openalpr import Alpr
import numpy as np

#trackerType = 'KCF'
#tracker = cv2.TrackerKCF_create()

alprConf = "/etc/openalpr/openalpr.conf"
alprRunTime = "/home/bkennedy/openalpr/runtime_data"
alpr = Alpr("us", alprConf, alprRunTime)
if not alpr.is_loaded():
	print("Alpr failed to load")
	exit()
alpr.set_top_n(1)

videoSource = "test_clip.MOV"
cam = cv2.VideoCapture()
cam.open(videoSource)

frameWidth = int(cam.get(3))
frameHeight = int(cam.get(4))
out = cv2.VideoWriter('out.avi', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (frameWidth, frameHeight))

trackers = []

def overlap(a, b):
	# x,y,w,h
	# a is first
	# b is second
	# test if any point from first rect is inside second rect

	x = a[0]
	y = a[1]
	w = a[2]
	h = a[3]
	upperleft1 = (x, y)
	upperright1 = (x + w, y)
	lowerleft1 = (x, y + h)
	lowerright1 = (x + w, y + h)

	x = b[0]
	y = b[1]
	w = b[2]
	h = b[3]
	upperleft2 = (x, y)
	upperright2 = (x + w, y)
	lowerleft2 = (x, y + h)
	lowerright2 = (x + w, y + h)

	# check top left
	topLeftX = False
	if (upperleft1[0] < upperright2[0]):
		if (upperleft1[0] > upperleft2[0]):
			topLeftX = True
	topLeftY = False
	if (upperleft1[1] > upperleft2[1]):
		if (upperleft1[1] < lowerleft2[1]):
			topLeftY = True
	topLeft = False
	if topLeftY and topLeftX:
		topLeft = True

	# check top right
	topRightX = False
	if (upperright1[0] < upperright2[0]):
		if (upperright1[0] > upperleft2[0]):
			topRightX = True
	topRightY = False
	if (upperright1[1] > upperleft2[1]):
		if (upperright1[1] < lowerleft2[1]):
			topRightY = True
	topRight = False
	if topRightY and topRightX:
		topRight = True

	# check bottom left
	bottomLeftX = False
	if (lowerleft1[0] < upperright2[0]):
		if (lowerleft1[0] > upperleft2[0]):
			bottomLeftX = True
	bottomLeftY = False
	if (lowerleft1[1] > upperleft2[1]):
		if (lowerleft1[1] < lowerleft2[1]):
			bottomLeftY = True
	bottomLeft = False
	if bottomLeftY and bottomLeftX:
		bottomLeft = True

	# check bottom right
	bottomRightX = False
	if (lowerright1[0] < upperright2[0]):
		if (lowerright1[0] > upperleft2[0]):
			bottomRightX = True
	bottomRightY = False
	if (lowerright1[1] > upperleft2[1]):
		if (lowerright1[1] < lowerleft2[1]):
			bottomRightY = True
	bottomRight = False
	if bottomRightX and bottomRightY:
		bottomRight = True

	#return bool
	if bottomRight or bottomLeft or topLeft or topRight:
		return True
	else:
		return False

while 1:
	ret, frame = cam.read()
	if not ret:
		break

	results = alpr.recognize_ndarray(frame)

	detectedRect = []

	if results['results']:
		for plate in results['results']:

			# don't give buffer size here! do it after the tracker
			# tracker returns the new rect, the inflate to find numbers with lpr
			
			leftBottom = (plate['coordinates'][3]['x'], plate['coordinates'][3]['y'])
			rightBottom = (plate['coordinates'][2]['x'], plate['coordinates'][2]['y'])
			rightTop = (plate['coordinates'][1]['x'], plate['coordinates'][1]['y'])
			leftTop = (plate['coordinates'][0]['x'], plate['coordinates'][0]['y'])

			allPoints = np.array([leftBottom,rightBottom,leftTop,rightTop])
			boundingRect = cv2.boundingRect(allPoints)	#X, Y, W, H
			cv2.rectangle(frame, boundingRect, (0, 255, 0), 3)
			
			for coordinate in plate['coordinates']:
				cv2.circle(frame, (coordinate['x'], coordinate['y']), 4, (0, 255, 0), -1)
			
			detectedRect.append(boundingRect) # list of all detected rects			

		print("results")
	else:
		print("no results")

	trackerBoxes = []

	for tracker in trackers:
		ok, bbox = tracker.update(frame)
		if not ok:
			print("removing tracker")
			trackers.remove(tracker)
			# data base entry
		else:
			bboxRect = (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))
			trackerBoxes.append(bboxRect)
			cv2.rectangle(frame, bboxRect, (255, 0, 0), 2, 1)

	if len(trackers) == 0:
		for rect in detectedRect:
			print("creating tracker")
			tracker = cv2.TrackerKCF_create()
			tracker.init(frame, rect)
			trackers.append(tracker)
	else:

		if len(trackers) >= len(detectedRect): ### SUCCESS!! One tracker per detection
			pass
		else:
			availableDetections = []

			for rect in detectedRect:
				for box in trackerBoxes:
					if overlap(box, rect) or overlap(rect, box):
						break
					else:
						availableDetections.append(rect)
						break

			for rect in availableDetections:
				print("creating other tracker")
				tracker = cv2.TrackerKCF_create()
				tracker.init(frame, rect)
				trackers.append(tracker)


			print("availableDetections: ", len(availableDetections))
			print("detectedrect: ", len(detectedRect))
			print("trackerboxes:", len(trackerBoxes))

	out.write(frame)

cam.release()
out.release()
