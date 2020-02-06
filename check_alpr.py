# utility function
# check if openALPR installation is valid for this machine

from openalpr import Alpr


def check_alpr(alpr_conf, alpr_run_time):
    # check if openALPR configuration files and install are OK
    print("loading Alpr")
    print("openALPR config path: ", alpr_conf)
    print("openALPR runtime path: ", alpr_run_time)
    alpr = Alpr("us", alpr_conf, alpr_run_time)

    if not alpr.is_loaded():
        print("openALPR failed to load")
        del alpr
        return False
    else:
        print("openALPR loaded successfully")
        del alpr
        return True
