import sqlite3
import time
import datetime

class plateLifespan:
    def __init__(self, number, frame, cameraname, cameraurl, databasefilepath):
        self.cameraName = cameraname
        self.cameraUrl = cameraurl

        self.number = number

        self.numberList = []
        self.numberList.append(number) # use to estimate actual number, average digits?

        self.frameList = []
        self.frameList.append(frame)

        self.databasePath = databasefilepath

        self.startTime = datetime.datetime.now()

        self.numSightings = 0

    def newSighting(self, number, frame):
        self.numberList.append(number)
        self.frameList.append(frame)

        self.number = number

        self.numberList += 1 #use to check for limit # before object gets to large

    def logData(self): #acts as soft __del__ function # log all data to database
        connection = sqlite3.connect(self.databasePath)
        cursor = connection.cursor()

        endTime = datetime.datetime.now()

    '''def __del__(self):
        connection = sqlite3.connect(self.databasePath)
        cursor = connection.cursor() #add data to database? here or in cameraThread? Main?

        endTime = datetime.datetime.now()

        #find most likely plate number AKA the real one
        plateNumber = None
    '''

