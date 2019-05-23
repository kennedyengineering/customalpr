from multiprocessing import Process, Value
import cv2

def renderWindow(progStatus):

    while not progStatus.value:
        pass