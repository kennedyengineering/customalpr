# simple rendering window for multiple video sources

import cv2
import pygame as gui
import numpy
import math


class GUI:
    def __init__(self, resolution):
        gui.init()
        self.display = gui.display.set_mode(resolution, gui.RESIZABLE)
        gui.display.set_caption("CustomALPR Viewer")
        self.clock = gui.time.Clock()
        self.cap_list = []

    def array_to_surface(self, array):
        array = array.swapaxes(0, 1)
        array = gui.surfarray.make_surface(array)
        return array

    def update(self):
        print("updating gui")
        # handle events
        for event in gui.event.get():
            if event.type == gui.QUIT:
                for cap in self.cap_list:
                    cap.stop()
                gui.quit()
                return False
            if event.type == gui.VIDEORESIZE:
                self.display = gui.display.set_mode((event.w, event.h), gui.RESIZABLE)

        self.display.fill((255, 255, 255))

        num_cams = len(self.cap_list)
        num_cols = 4  # how to make this dynamic? # calculate based on num_cams
        num_rows = math.ceil(num_cams / num_cols)  # is this even right?
        if num_rows == 1: num_rows += 1
        screen_width, screen_height = gui.display.get_surface().get_size()
        frame_width = int(screen_width / num_cols)
        frame_height = int(screen_height / num_rows)

        iter_col = 0
        iter_row = 0
        for cap in self.cap_list:
            frame = cap.get_frame()

            frame = self.array_to_surface(frame)
            frame = gui.transform.scale(frame, (frame_width, frame_height))
            self.display.blit(frame, (frame_width * iter_col, frame_height * iter_row))

            iter_col += 1
            if iter_col == num_cols:
                iter_col = 0
                iter_row += 1

        gui.display.update()
        self.clock.tick(60)

        return True
