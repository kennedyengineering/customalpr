from openalpr import Alpr

def checkALPR(alprConf, alprRunTime):
    # check if alpr configuration files and install are OK
    print("loading Alpr")
    #alprConf = "/etc/openalpr/openalpr.conf"
    print("Alpr config path: ", alprConf)
    #alprRunTime = "/home/" + str(getpass.getuser()) + "/openalpr/runtime_data"
    print("Alpr runtime path: ", alprRunTime)
    alpr = Alpr("us", alprConf, alprRunTime)
    if not alpr.is_loaded():
        print("Alpr failed to load")
        return False
    else:
        print("Alpr loaded successfully")
        del alpr
        return True
    # done checking