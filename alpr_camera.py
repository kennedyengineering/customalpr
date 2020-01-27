# main class for customALPR
# each instance handles a camera

from video_stream import videoStream
from fps import FPS
from detection_box import detectionBox
import cv2
from threading import Thread


class ALPRCamera:
    def __init__(self, camera, db_service, alpr_config, alpr_run_time, gui):
        self.stopped = False

        print("pre cam")
        self.camera_name = camera.name
        self.cam = videoStream(src=camera.url)
        print("post cam")


        self.guiFPS = FPS()
        self.gui = gui
        print("starting detection box")
        self.detection_boxes = []
        for search_box in camera.aoi_list:
            for search_box_name in search_box:
                new_box = detectionBox(camera.name, search_box_name, search_box[search_box_name],
                                       self.cam, alpr_config, alpr_run_time, db_service)
                self.detection_boxes.append(new_box)

    def get_frame(self):
        frame = self.cam.read()
        self.guiFPS.update()

        for box in self.detection_boxes:
            frame = box.draw(frame)

        return frame

    def is_alive(self):
        return not self.stopped

    def start(self):
        Thread(target=self.run, args=()).start()
        return self

    def stop(self):
        self.stopped = True

    def run(self):
        self.cam.start()
        self.guiFPS.start_timer()
        for box in self.detection_boxes:
            box.start()

        # main loop
        while not self.stopped:
            continue

        for box in self.detection_boxes:
            box.stop()

        self.guiFPS.stop()
        if self.gui:
            print(self.camera_name + " gui", self.guiFPS.fps())

        self.cam.stop()

        cv2.destroyAllWindows()

        return
