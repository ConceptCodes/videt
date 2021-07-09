import os
import cv2
import argparse
from moviepy.editor import *

class Videt():
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.video_frames = self._load_frames()

    # ------------ Helper Functions ---------------------
    def _load_frames(self):
        tmp =[]
        cap = cv.VideoCapture(self.input_file)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Error with loading video")
                break
            tmp.append(frame)
            if cv.waitKey(1) == ord('q'):
                break
        cap.release()
        return tmp

    def _load_audio(self):
        pass

    def _detect_objects(self):
        pass
    
    def _save_content(self):
        cap = cv.VideoCapture(0)
        fourcc = cv.VideoWriter_fourcc(*'XVID')
        out = cv.VideoWriter(self.output_file, fourcc, 20.0, (640,  480)) #need to grab framse size, will throw in init to prevent writing twice
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break
            frame = cv.flip(frame, 0)
            # write the flipped frame
            out.write(frame)
            cv.imshow('frame', frame)
            if cv.waitKey(1) == ord('q'):
                break
        # Release everything if job is finished
        cap.release()
        out.release()
    # ------------- Core Algorithm ----------------------
    def censor_video(obj_list=[]):
        pass

    def censor_audio(word_list=[],sound=""):
        pass

# --------------- Main Function ------------------------
if __name__ == '__main__':
    print('Wagwan Universe')


    
