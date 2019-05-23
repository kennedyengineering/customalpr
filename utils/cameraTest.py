import cv2

cam = cv2.VideoCapture()
#cam.open("http://admin:password1@10.10.1.123:80/Streaming/Channels/2/httppreview")
#cam.open("http://root:pass@10.10.1.175/mjpg/1/video.mjpg")
cam.open("http://admin:activeALPR@10.10.1.58/Streaming/channels/101/preview")
if cam.isOpened():
	print("camera operational")
else:
	print("camera failed")
	exit(-1)
while True:
	ret, frame = cam.read()
	if not ret:
		print("reconnecting...")
		while not ret:
			ret, frame = cam.read()
		print("reconnected")

	cv2.imshow("net cam", frame)
	
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break
cam.release()
cv2.destroyAllWindows()
