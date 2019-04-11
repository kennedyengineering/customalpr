import sqlite3
import socket
import math
from openalpr import Alpr
import cv2
import datetime
from plateThread import plateLifespan
import Levenshtein as lev

def matchStringToArray(string, stringArray):
    bestMatch = math.inf
    bestString = ""
    for i in stringArray:
            distance = lev.distance(string, i)
            if distance < bestMatch:    #does not compensate for two equal best distances!!!
                    bestMatch = distance
                    bestString = i
    return bestString


def processFeed(videoSourceURL, cameraName, progStatus, alprRuntime, alprConf, databaseFilePath):
    hostname = socket.gethostname()

    connection = sqlite3.connect(databaseFilePath)
    cursor = connection.cursor()

    alpr = Alpr("us", alprConf, alprRuntime)
    if not alpr.is_loaded():
        print("Alpr failed to load")
        return -1

    alpr.set_top_n(1)  # only return the best result

    cam = cv2.VideoCapture()
    cam.open(videoSourceURL)

    if cam.isOpened():
        print("camera ", cameraName, videoSourceURL, " operational")
    else:
        print("camera ", cameraName, videoSourceURL, "  unavailable")
        return -1

    previousPlateQuantity = None
    currentPlateQuantity = None

    lifeSpanList = []
    currentPlateNumberList = []

    ### main loop ###
    while not progStatus.value:
        # handle image feed
        ret, frame = cam.read()
        if not ret:
            print("Failed to retrieve frame from ", cameraName, videoSourceURL)
            return -1

        # openalpr scan numpy array
        results = alpr.recognize_ndarray(frame)  # scan an numpy array for license plates

        ### printing outputs ###
        i = 0
        if results['results']:
            print()
            print("Camera", cameraName, videoSourceURL)
        for plate in results['results']:
            i += 1
            print("Plate #%d" % i)
            print("    %12s %12s" % ("Plate", "Confidence"))
            for candidate in plate['candidates']:  # should be only one per plate
                prefix = "-"
                if candidate['matches_template']:
                    prefix = "*"

                print("  %s %12s%12f" % (prefix, candidate['plate'], candidate['confidence']))
                currentPlateNumberList.append(candidate['plate'])
        ### done printing outputs ###

        #print(i)
        #for i in currentPlateNumberList:
        #    print(i)

        ### handle lifespans ###
        currentPlateQuantity = i
        if (previousPlateQuantity == None) and (currentPlateQuantity != None): #previousPlateQuantity should never equal None after the first plate is detected
            #create first lifespan!
            print("Found first plate")
            for plateNumber in currentPlateNumberList: #create new plateLifespan objects for each plate number
                lifeSpanList.append(plateLifespan(plateNumber, frame, cameraName, videoSourceURL, databaseFilePath))

        elif previousPlateQuantity != None:
            #create filter? boolean estimation based on current and previous... no, just use certainty to filter if anything
            if currentPlateQuantity == previousPlateQuantity:
                #string matching probability function, with cut off
                #match plates to their pre-existing plate objects. continue life span
                #use Levenshtein distance
                print("No new plates in this frame")
                #access list of plates, match with lifespans
                #continue living...
                #for plateNumber in currentPlateNumberList:
                #    #match string returns bestString

                #   bestString = matchStringToArray(plateNumber, )
                for span in lifeSpanList:
                    bestNumber = matchStringToArray(span.number, currentPlateNumberList)
                    span.newSighting(bestNumber, frame)
                    currentPlateNumberList.remove(bestNumber) #if there are two identical numbers, will remove the first one in the list  # shouldnt be any members in the list after this loop
            else:
                if currentPlateQuantity > previousPlateQuantity:
                    #create new plate object
                    #find out which number is the new one
                    print("Found new plate")
                    for span in lifeSpanList:   #match plates to spans
                        bestNumber = matchStringToArray(span.number, currentPlateNumberList)
                        span.newSighting(bestNumber, frame)
                        currentPlateNumberList.remove(bestNumber)

                    for plateNumber in currentPlateNumberList: #remaining numbers are new ones
                        lifeSpanList.append(plateLifespan(plateNumber, frame, cameraName, videoSourceURL, databaseFilePath))

                if currentPlateQuantity < previousPlateQuantity:
                    #find which plates lifespan to end
                    # get date from lifespan and put into database
                    # find out which one is missing
                    missingList = lifeSpanList
                    print("Lost a plate")
                    for span in lifeSpanList:
                        bestNumber = matchStringToArray(span.number, currentPlateNumberList)
                        span.newSighting(bestNumber, frame)
                        currentPlateNumberList.remove(bestNumber)
                        missingList.remove(span)

                    for span in missingList:
                        # DIE!!!
                        # implement kill function! data handler
                        span.logData()
                        lifeSpanList.remove(span)

        previousPlateQuantity = currentPlateQuantity
        currentPlateNumberList = [] #make sure it is empty!

        xxxx =  '''
                fileName = (str(cameraName) + " " + str(datetime.datetime.now()).replace(".", " ") + ".png").replace(
                    " ", "_")
                saveLocation = "/var/www/html/capturedImages/" + fileName
                print("saving as " + fileName)
                # cv2.imwrite(saveLocation, frame)

                imageURL = str(hostname) + "/capturedImages/" + fileName

                command = """INSERT INTO plates (plateNumber, plateConfidence, cameraLocation, cameraName, dateTime, imageURL) VALUES ("{}", "{}", "{}", "{}", "{}", "{}");""".format(
                    candidate['plate'], candidate['confidence'], videoSourceURL, cameraName, datetime.datetime.now(),
                    imageURL)
                cursor.execute(command)
                connection.commit()
                '''

    connection.close()
    alpr.unload()
    cam.release()
    return 0
