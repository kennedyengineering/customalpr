from multiprocessing import Process, Value
from time import sleep
import yaml
import os
import sqlite3
import signal
from cameraThread import processFeed

class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True

databaseFilePath = "plate.db"
if os.path.isfile(databaseFilePath):
    print("database file found at, ", databaseFilePath)
else:
    print("could not find", databaseFilePath)
    print("creating new database... ")
    connection = sqlite3.connect(databaseFilePath)
    cursor = connection.cursor()
    command = """
	CREATE TABLE plates (
	plateNumber VARCHAR(10),
	plateConfidence VARCHAR(10),
	cameraLocation VARCHAR(30),
	cameraName VARCHAR(30),
	dateTime VARCHAR(30),
	imageURL VARCHAR(40));"""
    cursor.execute(command)
    connection.commit()
    connection.close()
    print("done")

configFilePath = "config.yml"
if os.path.isfile(configFilePath):
    print("config file found at, ", configFilePath)
else:
    print("could not find ", configFilePath)
    exit()

alprConf = "/etc/openalpr/openalpr.conf"
# alprRuntime = "/usr/share/openalpr/runtime_data" #missing us config file
alprRuntime = "/home/bkennedy/openalpr/runtime_data"  # not missing us config file

progTerminate = Value('i', 0)

with open(configFilePath, 'r') as stream:
    config = yaml.load(stream)

processes = {}
for pair in config['cameraAddresses']:
    for name in pair:
        processes[name] = Process(target=processFeed,
                                  args=(pair[name], name, progTerminate, alprRuntime, alprConf, databaseFilePath))
        processes[name].start()

shutdownStatus = GracefulKiller()

while 1:
    if shutdownStatus.kill_now:
        progTerminate.value = 1

        for pair in config['cameraAddresses']:
            for name in pair:
                processes[name].join()

        print("done")
        exit(0)
