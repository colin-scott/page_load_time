#!/usr/bin/env python

import os
import subprocess
import signal
import sys

import telemetry_web_page_replay as wpr
from telemetry_util import FileSafeName, exponential_backoff

phantomjs_path = "phantomjs"
if os.path.exists("/home/cs/local/bin/phantomjs"):
  phantomjs_path = "/home/cs/local/bin/phantomjs"


def fetch(url):
  print "Fetching ", url
  filename = FileSafeName(url)
  wpr_output = "wpr/" + filename + ".wpr"
  phantomjs_err = "wpr/" + filename + ".err"
  har_output = "har/" + filename + ".har"
  with wpr.ReplayServer(wpr_output, replay_options=["--record"]):
    subprocess.Popen(
      "%s --disk-cache=false --ignore-ssl-errors=true "
      "netsniff.js '%s'>'%s' 2>'%s'" %
      (phantomjs_path, url, har_output, phantomjs_err),
      shell=True)


if __name__ == '__main__':
  if os.geteuid() != 0:
    print "Must run as root"
    sys.exit(1)

  with open("target_urls") as f:
    for url in f:
      url = url.strip()
      exponential_backoff(fetch, url)
