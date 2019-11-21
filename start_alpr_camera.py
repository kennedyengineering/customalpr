from video_stream import WebcamVideoStream
from fps import FPS
from detection_box import detectionBox
import cv2

def startALPRonCamera(camera, dbService, alprConf, alprRunTime, gui, guiResolution):
	# camera, dbService, alprConf, alprRunTime
	#global progTerminate
	#progTerminate = False

	# wants camera datatype
	cam = WebcamVideoStream(src=camera.url).start()
	guiFPS = FPS().start()

	detectionBoxes = []
	for searchbox in camera.aoiList:
		for searchBoxName in searchbox:
			# needs -->  cameraName, name, area, webcamReference, alprconfig, alprruntime, dbReference
			newBox = detectionBox(camera.name, searchBoxName, searchbox[searchBoxName], cam, alprConf, alprRunTime, dbService).start()
			detectionBoxes.append(newBox)

	# main loop
	while 1:
		if gui:
			frame = cam.read()
			guiFPS.update()

			for box in detectionBoxes:
				frame = box.draw(frame)

			frame = cv2.resize(frame, guiResolution)
			cv2.imshow(camera.name, frame)
			if cv2.waitKey(1) & 0xFF == ord('q'):
				#progTerminate = True
				break
		#elif progTerminate:
		#	break

	## When main loop exits --> program terminate and clean up

	for box in detectionBoxes:
		box.stop()

	guiFPS.stop()
	if gui:
		print(camera.name+" gui", guiFPS.fps())
	cam.stop()

	cv2.destroyAllWindows()

	return