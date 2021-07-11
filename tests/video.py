from videt import Videt
from default import *

from moviepy.editor import *
from cvlib.object_detection import YOLO

x = Videt(input_file=input_path, output_file=output_path)

clip = VideoFileClip(input_path)
# clip = VideoFileClip("./fake.mp4") 
yolo = YOLO('../ml/yolo/yolov3.weights', '../ml/yolo/yolov3.cfg', '../ml/yolo/coco.names')

# load correct video
def load_correct_video():
    assert x.video == clip, "Error with loading Video"

# get correct frame count
def get_correct_frame_count():
    assert x.video.reader.nframes == clip.reader.nframes, "Incorrect frame count"

# get correct w x h
def correct_w_x_h():
    assert (x.video.w, x.video.h) == (clip.w, clip.h), "Incorrect Width & Height"

# detect default objects
def detect_default_objects():
    assert yolo.detect_objects(x.get_frame(3)) == yolo.detect_objects(clip.get_frame(3)), "Error with finding objects"
    

if __name__ == '__main__':
    print('Load Correct Video: ',load_correct_video())
    print('Get Correct Frame Count: ', get_correct_frame_count())
    print('Get Correct Width & Height: ', correct_w_x_h())
    print('Get Default Objects: ', detect_default_objects())