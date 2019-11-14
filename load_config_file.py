import yaml
from camera_datatype import cameraDatatype

def loadConfig(path="config.yml"):
    # load config file data
    print("")
    print("Loading config file")

    configFilePath = path
    #configFilePath = "config.yml"
    with open(configFilePath, 'r') as stream:
        config = yaml.load(stream)

    gui = config['GUItoggle']
    guiResolutionX = config['GUIresolutionX']
    guiResolutionY = config['GUIresolutionY']
    guiResolution = (guiResolutionX, guiResolutionY)

    cameraList = []
    for camera in config['cameraAddresses']:
        for name in camera:
            cameraID = camera[name]
            cameraName = name
            cameraUrl = cameraID[0]['url']
            cameraAOI = []
            for aoi in cameraID[1]['aoi']:
                for entry in aoi:
                    X = aoi[entry][0]['X']
                    Y = aoi[entry][1]['Y']
                    W = aoi[entry][2]['W']
                    H = aoi[entry][3]['H']
                    tempDict = {entry: (X, Y, W, H)}
                    cameraAOI.append(tempDict)

        cameraList.append(cameraDatatype(cameraName, cameraUrl, cameraAOI))

    print("Config file loaded successfully")
    # done loading config file data

    return (cameraList, gui, guiResolution)