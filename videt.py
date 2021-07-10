import os
import cv2
import argparse
from moviepy.editor import *
from cvlib.object_detection import YOLO

class Videt():
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.audio = self.video.audio
        self.video = VideoFileClip(self.input_file)
            
    def _detect_objects(self, frame):
        yolo = YOLO('./ml/yolo/yolov3.weights', './ml/yolo/yolov3.cfg', './ml/yolo/coco.names')
        bbox, label, conf = yolo.detect_objects(frame)
        return (label, bbox)
    
    def _save_content(self):
        pass

    def censor_video(obj_list=[]):
        tmp = []
        for frame in self.video.iter_frames():
            objects = filter(lambda x: x[0] in obj_list, self._detect_objects(frame))
            for img in objects:
                blur = cv2.GaussianBlur(img[1], (51,51), 0) # 51 will need to be replaced with bbox w, h
                frame[y:y+h, x:x+w] = blur
                tmp.append(frame)
        return frame

    def censor_audio(word_list=[],sound=""):
        pass

if __name__ == '__main__':
    print('Wagwan Universe')


    
