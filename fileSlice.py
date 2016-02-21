
import sys
sys.path.append("./lib")

from pydub import AudioSegment

INPUT_DIR = "./input/"
OUTPUT_DIR = "./output/"
START_TAG = "start"
DUR_TAG = "dur"

def trim(filename, timeOne, timeTwo, captionNo):
   success = 0;
   #TODO deal with >>, different people speaking etc
   # ogg_version = AudioSegment.from_ogg(INPUT_DIR+filename+".ogg")
   webm_version = AudioSegment.from_ogg(INPUT_DIR+filename+".webm")
   split = song[timeOne:timeTwo]

   split.export(OUTPUT_DIR+filename+"-"+captionNo+".wav", format="wav")
   return success;


# trim('Eo-Drako')

#http://stackoverflow.com/questions/193077/standalone-python-applications-in-linux
#http://undefined.org/python/py2app.html