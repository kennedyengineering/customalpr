import yaml
with open("config.yml", 'r') as stream:
    config = yaml.load(stream)

#print(config)

class cameraDatatype:
    def __init__(self, name, url, aoiList):
        self.name = name
        self.url = url
        self.aoiList = aoiList

cameraList = []

for camera in config['cameraAddresses']:
    for name in camera:
        cameraID = camera[name]
        cameraName = name
        cameraUrl = cameraID[0]['url']
        cameraAOI = []
        for aoi in cameraID[1]['aoi']:
            for entry in aoi:
                #print(aoi[entry])
                X = aoi[entry][0]['X']
                Y = aoi[entry][1]['Y']
                W = aoi[entry][2]['W']
                H = aoi[entry][3]['H']
                tempDict = {entry: (X, Y, W, H)}
                cameraAOI.append(tempDict)

    cameraList.append(cameraDatatype(cameraName, cameraUrl, cameraAOI))

for camera in cameraList:
    print(camera.name, camera.url, camera.aoiList)

