import sqlite3
import socket
from openalpr import Alpr
import cv2
import datetime

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

    while not progStatus.value:
        ret, frame = cam.read()
        if not ret:
            print("Failed to retrieve frame from ", cameraName, videoSourceURL)
            return -1

        results = alpr.recognize_ndarray(frame)  # scan an numpy array

        i = 0
        if results['results']:
            print()
            print("Camera", cameraName, videoSourceURL)
        for plate in results['results']:
            i += 1
            # print()
            # print("Camera", cameraName, videoSourceURL)
            print("Plate #%d" % i)
            print("    %12s %12s" % ("Plate", "Confidence"))
            for candidate in plate['candidates']:  # should be only one per plate
                prefix = "-"
                if candidate['matches_template']:
                    prefix = "*"

                print("  %s %12s%12f" % (prefix, candidate['plate'], candidate['confidence']))

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

    connection.close()
    alpr.unload()
    cam.release()
    return 0
