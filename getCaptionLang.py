#!/usr/bin/python

import sys
sys.path.append("./lib")

import httplib2
import os

from subprocess import call
from pydub import AudioSegment
from apiclient.discovery import build_from_document
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

INPUT_DIR = "./input/"
OUTPUT_DIR = "./output/"
START_TAG = "start"
DUR_TAG = "dur"
STARTFIX = 150

CLIENT_SECRETS_FILE = "client_secrets.json"

YOUTUBE_READ_WRITE_SSL_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:
   %s
with information from the APIs Console
https://console.developers.google.com

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

# Authorize the request and store authorization credentials.
def get_authenticated_service(args):
  flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_READ_WRITE_SSL_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, args)

  # Trusted testers can download this discovery document from the developers page
  # and it should be in the same directory with the code.
  with open("youtube-v3-api-captions.json", "r") as f:
    doc = f.read()
    return build_from_document(doc, http=credentials.authorize(httplib2.Http()))


def downloadVideo(channelID, videoID):
  print "getting vid", "https://www.youtube.com/watch?v="+videoID
  call(["./lib/youtube-dl", "-f", "bestaudio", "-o", INPUT_DIR+"123.webm", "https://www.youtube.com/watch?v="+videoID])

def deleteVideo(channelID, videoID):
  call(["rm", INPUT_DIR+"123.webm"])

def cutTheAudio(filename, timeOne, timeTwo, captionNum):
  success = 0;
  webm_version = AudioSegment.from_file(INPUT_DIR+filename)
  split = webm_version[timeOne:timeTwo]
  split.export(OUTPUT_DIR+filename+"-"+str(captionNum)+".wav", format="wav")
  return success;

def convTimeToMilli(time):
  milliTime = 0
  times = time.split(":")
  milliTime += int(times[0])*60*60*1000
  milliTime += int(times[1])*60*1000
  milliTime += float(times[2])*1000
  return milliTime

def trim(subtitle):
  splitSubs = subtitle.split("\n")
  capCount = 1
  captionFinishedState = 1
  startSplit = 0
  endSplit = 0
  currLine =""
  for s in splitSubs:
    if len(s) == 0:
      print currLine
      cutTheAudio("123.webm", startSplit, endSplit, capCount)
      capCount+=1
      captionFinishedState=1
    else:
      if captionFinishedState==1:
        print capCount
        currLine =""
        times = s.split(",")
        millistart = convTimeToMilli(times[0])
        startSplit=millistart - STARTFIX > 0 if millistart-STARTFIX else 0
        endSplit=convTimeToMilli(times[1]) + STARTFIX
        print "start at ",times[0], "or", startSplit
        print "end at ",times[1], "or", endSplit
        captionFinishedState=0
      else:
        currLine +=s.strip()+" "

# Call the API's captions.list method to list the existing caption tracks.
def list_captions(youtube, video_id):
  results = youtube.captions().list(
    part="snippet",
    videoId=video_id
  ).execute()

  downloadVideo("",video_id)
  for item in results["items"]:
    capid = item["id"]
    language = item["snippet"]["language"]
    trackKind = item["snippet"]["trackKind"]

    print "Caption track in '%s' language, of type '%s'." % (language,trackKind)
    if trackKind == "ASR" or language != "en":
      print "Type ASR, skipping"
      continue
    subtitle = youtube.captions().download(
      id=capid,
      tfmt='sbv').execute()

    #TODO CHANNEL ID ON LEFT
    trim(subtitle)

    # print "First line of caption track: %s" % (subtitle)
  deleteVideo("",video_id)
    

if __name__ == "__main__":
  argparser.add_argument("--videoid", help="Required; ID for video for which the caption track will be uploaded.")

  args = argparser.parse_args()

  youtube = get_authenticated_service(args)
  try:
    list_captions(youtube, args.videoid)
  except HttpError, e:
    print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
  else:
    print "Created and managed caption tracks."
