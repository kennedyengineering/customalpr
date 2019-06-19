import cv2
import numpy as np

videoSource = "rtsp://LPRuser:ThisISfun1@10.48.140.5:554/Streaming/channels/101/"
cam = cv2.VideoCapture()
cam.open(videoSource)

ret, frame = cam.read()

fromCenter = False
rect = cv2.selectROI(frame, fromCenter)

print(rect)