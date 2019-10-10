import cv2
import numpy as np

videoSource = input("Video Source: ")
cam = cv2.VideoCapture()
cam.open(videoSource)

ret, frame = cam.read()

fromCenter = False
rect = cv2.selectROI(frame, fromCenter)

print(rect)
