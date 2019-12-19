from video_stream import WebcamVideoStream
from fps import FPS
from detection_box import detectionBox
import cv2
from threading import Thread

class startALPRonCamera():

	def __init__(self, camera, dbService, alprConf, alprRunTime, gui):

		self.killed = False

		self.camera_name = camera.name
		self.cam = WebcamVideoStream(src=camera.url)#.start()
		self.guiFPS = FPS()#.start()

		self.gui = gui # boolean

		self.detectionBoxes = []
		for searchbox in camera.aoiList:
			for searchBoxName in searchbox:
				# needs -->  cameraName, name, area, webcamReference, alprconfig, alprruntime, dbReference
				newBox = detectionBox(camera.name, searchBoxName, searchbox[searchBoxName], self.cam, alprConf, alprRunTime, dbService)#.start()
				self.detectionBoxes.append(newBox)

	def getFrame(self):
		frame = self.cam.read()
		self.guiFPS.update()

		for box in self.detectionBoxes:
			frame = box.draw(frame)

		return frame

	def isAlive(self):
		return not self.killed

	def start(self):
		Thread(target=self.run, args=()).start()
		return self

	def stop(self):
		self.killed = True

	def run(self):
		# main loop

		self.cam.start()
		self.guiFPS.start()
		for box in self.detectionBoxes:
			box.start()

		# main loop
		while not self.killed:
			continue
			#if self.gui:
			#	frame = self.cam.read()
			#	self.guiFPS.update()
			#	#print("got frame", self.camera_name)

			#	for box in self.detectionBoxes:
			#		frame = box.draw(frame)

			#	frame = cv2.resize(frame, self.guiResolution)
			#	#cv2.imshow(self.camera_name, frame)
			#	#if cv2.waitKey(1) & 0xFF == ord('q'):
			#	#	self.killed = True
			#	self.rendered_frame = frame

		## When main loop exits --> program terminate and clean up

		for box in self.detectionBoxes:
			box.stop()

		self.guiFPS.stop()
		if self.gui:
			print(self.camera_name+" gui", self.guiFPS.fps())
		self.cam.stop()

		cv2.destroyAllWindows()

		return
