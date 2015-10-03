#!/usr/bin/env python

from telemetry_util import FileSafeName, exponential_backoff, DecodeURL
from fetch_urls_sequentially import fetch

import sys
import os
import re

def get_retries():
  retries = []
  for f in ["filtered_stats/invalid_loads.txt",
            "filtered_stats/invalid_originals.txt",
            "filtered_stats/invalid_originals.txt"]:
    with open(f) as i:
      for line in i:
        full_path = line.split()[0]
        b64_name = re.sub(".har$", "",
            re.sub(".pc$", "",
            re.sub(".wpr$", "", os.path.basename(full_path))))
        url = DecodeURL(b64_name)
        retries.append(url)
  return set(retries)

if __name__ == '__main__':
  if os.geteuid() != 0:
    print "Must run as root"
    sys.exit(1)

  retries = get_retries()
  for url in retries:
    url = url.strip()
    exponential_backoff(fetch, url)
