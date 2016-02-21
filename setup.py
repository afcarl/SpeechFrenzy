#!/usr/bin/python
import sys
sys.path.append("./lib")

import httplib2
import os
from distutils.core import setup
import py2exe
import apiclient
from subprocess import call
from pydub import AudioSegment

setup(
    console=['getCaptionLang-WIN.py'],
     options = {'py2exe': {'bundle_files': 1, 'compressed': True,
     'packages':['pydub','httplib2', 'os' ]


)
