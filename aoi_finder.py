# utility script
# takes a frame from a valid video source (local camera/IP/video file)
# allows the user to select the area of interest for use in the config file

import cv2
import numpy as np


video_source = input("Video Source: ")
cam = cv2.VideoCapture()
cam.open(video_source)

ret, frame = cam.read()

from_center = False
rect = cv2.selectROI(frame, from_center)

print(rect)
