from videt import Videt
from default import *
from moviepy.editor import *
form google

x = Videt(input_file=input_path, output_file=output_path)
clip = VideoFileClip(input_path)
# clip = VideoFileClip('./fake.mp4')

# load audio
def load_audio():
    assert x.audio == clip.audio, "Error loading audio"

def convert_text_to_speech():
    sample1 = x.transcribe_audio()
    sample2 = 


if __name__ == '__main__':
