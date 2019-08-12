import cv2
import numpy

cap = cv2.VideoCapture("rtsp://LPRuser:ThisISfun1@10.48.140.5:554/Streaming/channels/101/")

if cap.isOpened() == False:
	print ("unable to open camera feed")
	cap.release()
	exit()

frame_width = int(cap.get(3))
frame_height = int(cap.get(4))

out = cv2.VideoWriter('recording.avi', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (frame_width, frame_height))

while True:
	ret, frame = cap.read()

	if ret == True:
		out.write(frame)
		cv2.imshow('frame', frame)

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

	else:
		break

cap.release()
out.release()

cv2.destroyAllWindows()
