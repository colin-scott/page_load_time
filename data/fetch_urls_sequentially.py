#!/usr/bin/env python

import os
import subprocess
import signal
import sys
import time

import telemetry_web_page_replay as wpr
from telemetry_util import FileSafeName

if os.geteuid() != 0:
  print "Must run as root"
  sys.exit(1)

def exponential_backoff(function, arg):
  success = False
  current_try = 0
  max_tries = 5
  while not success and current_try <= max_tries:
    try:
      current_try += 1
      function(arg)
      success = True
    except Exception as e:
      print "Failed. Retrying.", str(e)
      time.sleep(1 << current_try)

def fetch(url):
  print "Fetching ", url
  filename = FileSafeName(url)
  wpr_output = "wpr/" + filename + ".wpr"
  phantomjs_err = "wpr/" + filename + ".err"
  har_output = "har/" + filename + ".har"
  with wpr.ReplayServer(wpr_output, replay_options=["--record"]):
    subprocess.Popen("phantomjs --disk-cache=false netsniff.js '%s'>'%s' 2>'%s'" %
                     (url, har_output, phantomjs_err), shell=True)

with open("target_urls") as f:
  for url in f:
    url = url.strip()
    exponential_backoff(fetch, url)
