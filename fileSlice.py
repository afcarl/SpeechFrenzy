
import sys
sys.path.append("./lib")


import xml.etree.ElementTree as ET
from pydub import AudioSegment

INPUT_DIR = "./input/"
OUTPUT_DIR = "./output/"
START_TAG = "start"
DUR_TAG = "dur"



def trim( filename ):
   success = 0;
   root = ET.parse(INPUT_DIR+filename+'.xml').getroot()
   #TODO deal with >>, different people speaking etc
   ogg_version = AudioSegment.from_ogg(INPUT_DIR+filename+".ogg")

   halfway_point = len(ogg_version) / 2
   second_half = ogg_version[halfway_point:]

   second_half_3_times.export(OUTPUT_DIR+"file.ogg", format="ogg")
   curTime = 0

   for child in root:
   	if curTime != child.get(START_TAG):
		curTime = child.get(START_TAG)
   	
   	endTime = curTime + child.get(DUR_TAG)



	print child.tag, child.attrib
	print child.text
	return success;


trim('Eo-Drako')

#http://stackoverflow.com/questions/193077/standalone-python-applications-in-linux
#http://undefined.org/python/py2app.html