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

sys.getdefaultencoding()

CLIENT_SECRETS_FILE = "client_secrets.json"

YOUTUBE_READ_WRITE_SSL_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
folderName =""
videoIDName =""
videoCount = 0
captionFileName ="captionLabels.csv"

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
  call(["./lib/youtube-dl", "-f", "bestaudio", "-o", INPUT_DIR+videoIDName, "https://www.youtube.com/watch?v="+videoID])

def deleteVideo():
  call(["rm", INPUT_DIR+videoIDName])

def mkdir():
  call(["mkdir", OUTPUT_DIR+folderName+"/"])
  file(OUTPUT_DIR+folderName+captionFileName,'wt')

def cutTheAudio(timeOne, timeTwo, captionNum):
  success = 0;
  webm_version = AudioSegment.from_file(INPUT_DIR+videoIDName)
  split = webm_version[timeOne:timeTwo]
  split.export(OUTPUT_DIR+folderName+videoIDName+"-"+str(captionNum)+".wav", format="wav")
  return success;

def convTimeToMilli(time):
  milliTime = 0
  times = time.split(":")
  
  milliTime += int(times[0])*60*60*1000
  milliTime += int(times[1])*60*1000
  milliTime += float(times[2])*1000
  return milliTime

def captionParser(allCaptions):
  with open(OUTPUT_DIR+folderName+captionFileName, "a") as captionFile:
    captionBlocks = allCaptions.split("\n\n")
    capCount = 1
    for block in captionBlocks:      
      if len(block) >= 3:
        print "["+ str(videoCount) + "] " + videoIDName + " " + str(capCount) + "/" + str(len(captionBlocks)) + "\n"
        # timestamps
        lines = block.split("\n")
        times = lines[0].split(",")
        millistart = convTimeToMilli(times[0])
        startSplit= millistart-STARTFIX if millistart - STARTFIX > 0  else int(0)
        endSplit=convTimeToMilli(times[1]) + STARTFIX
        #print "start at ",times[0], "or", startSplit
        #print "end at ",times[1], "or", endSplit
        
        #caption text
        currLine =""
        for i in range(1, len(lines)):
          currLine += lines[i].strip()+" "
         
        #print currLine
        # save the data
        cutTheAudio(startSplit, endSplit, capCount)
        text = videoIDName+"| "+str(capCount)+"| "+ str(startSplit)+"| "+ str(endSplit)+"| "+ str(endSplit-startSplit) + "| "
        text = text.encode("UTF-8") + currLine + "\n"
        captionFile.write(text)
        capCount+=1;

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
    if trackKind == "ASR" or "en" not in language:
      print "Type ASR or no en -> skipping"
      continue
    allCaptions = youtube.captions().download(
      id=capid,
      tfmt='sbv').execute()

    #TODO CHANNEL ID ON LEFT
    captionParser(allCaptions)
    

    # print "First line of caption track: %s" % (subtitle)
  deleteVideo()
    
def callVid(video_id):
  try:
    list_captions(youtube, video_id)
    videoCount += 1
  except HttpError, e:
    print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
  else:
    print "Created and managed caption tracks."

if __name__ == "__main__":
  argparser.add_argument("--channelid", help="Required; ID for channel from which the videos will be sourced from")
  args = argparser.parse_args()
  youtube = get_authenticated_service(args)

  channels_response = youtube.channels().list(
    id=args.channelid,
    part="contentDetails"
  ).execute()

  for channel in channels_response["items"]:
    uploads_list_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

    print "Videos in list %s" % uploads_list_id

    playlistitems_list_request = youtube.playlistItems().list(
      playlistId=uploads_list_id,
      part="snippet",
      maxResults=50
    )

    folderName=args.channelid+"/"
    mkdir()
    while playlistitems_list_request:
      playlistitems_list_response = playlistitems_list_request.execute()


      for playlist_item in playlistitems_list_response["items"]:
        title = playlist_item["snippet"]["title"]
        video_id = playlist_item["snippet"]["resourceId"]["videoId"]
        videoIDName=video_id
        callVid(video_id)

      playlistitems_list_request = youtube.playlistItems().list_next(
        playlistitems_list_request, playlistitems_list_response)