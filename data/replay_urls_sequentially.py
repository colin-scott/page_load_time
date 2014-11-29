#!/usr/bin/env python

import re
import os
import sys
import optparse
import glob
import subprocess

import telemetry_web_page_replay as wpr
from telemetry_util import exponential_backoff, DecodeURL

if os.geteuid() != 0:
  print "Must run as root"
  sys.exit(1)

phantomjs_path = "phantomjs"
if os.path.exists("/home/vagrant/local/bin/phantomjs"):
  phantomjs_path = "/home/vagrant/local/bin/phantomjs"

def replay(wpr_archive, url, filename, num_replays=1):
  for replay in xrange(1, num_replays+1):
    print "Replay #%d %s" % (replay, url)
    phantomjs_err = "replay/%s.%d.err" % (filename, replay)
    replay_output = "replay/%s.%d.har" % (filename, replay)
    if os.path.exists(replay_output):
      print "Replay file %s already exists" % replay_output
      return
    def execute_replay():
      replay_options = ["--use_server_delay", "--use_closest_match"]
      with wpr.ReplayServer(wpr_archive, replay_options=replay_options):
        cmd = ("%s --disk-cache=false netsniff.js '%s'>'%s' 2>'%s'" %
               (phantomjs_path, url, replay_output, phantomjs_err))
        print "Executing", cmd
        subprocess.Popen(cmd, shell=True)
    exponential_backoff(execute_replay)

if __name__ == '__main__':
  # Second arg can be an empty file.
  option_parser = optparse.OptionParser(
      usage='%prog <directory containing wpr files> <valids.txt, output of filter_bad_pages.rb>')

  options, args = option_parser.parse_args()

  if len(args) < 2:
    print 'args: %s' % args
    option_parser.error('Must specify a directory containing wpr files, and valids.txt')

  whitelist_file = args[1]
  url_whitelist = set()
  with open(whitelist_file) as f:
    for line in iter(f):
      url_whitelist.add(line.split()[0])

  for wpr_archive in sorted(glob.glob(args[0] + "/*.wpr")):
    filename = re.sub(".wpr$", "", os.path.basename(wpr_archive))
    b64_name = re.sub(".pc$", "", filename)
    url = DecodeURL(b64_name)
    if url not in url_whitelist:
      replay(wpr_archive, url, filename)
