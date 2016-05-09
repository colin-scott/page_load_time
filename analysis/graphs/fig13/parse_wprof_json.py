#!/usr/bin/python

import json
import sys

# We should write a script to create Figure 13, given the raw data. The raw data is of the following format:
#
# a JSON array, with 33 entries in it.
#
# The first 5 entries correspond raw page load times for C=0, N=[0,1/4,1/2,3/4,1].
# The next 5 entries correspond to C=1/4, ...
# C=1/2
# C=3/4
# C=1
# The 26th through 30th entries correpond to C=2.
#
# The last 3 entries can be ignored.
#
# The actual PLT should be the 25th entry, C=1,N=1. We should then normalize the raw PLTs to that number.
#
# From that, we can generate the gnuplot figure.

# Note that we ignore C=1/4 and C=3/4.

to_ignore = set(["1/4","3/4"])

c_to_dat_filename = {
  "0": "c0.dat",
  "1/2": "c.5.dat",
  "1": "c1.dat",
  "2": "c2.dat"
}

class Series(object):
  def initialize(self, c, datapoints):
    self.c = c
    self.datapoints = datapoints

def parse_json(json_str):
  a = json.loads(json_str)
  plt = a[24]
  series = []
  step = 5
  for start_index, c in [(0,"0"),(5,"1/4"),(10,"1/2"),(15,"3/4"),(20,"1"),(25,"2")]:
    datapoints = a[start_index:start_index+step]
    normalized = map(lambda x: x / plt, datapoints)
    if c not in to_ignore:
      series.append(Series(c, normalized))
  return series

if sys.argc < 1:
  print >> sys.stderr, "Usage: <JSON array for whatif_matrix>"
  sys.exit(1)

series = parse_json(sys.argv[1])
for s in series:
  output = c_to_dat_filename[s.c]
  with open(output, "w") as f:
    for x,y in zip([0,0.25,0.5,0.75,1], s.datapoints):
      print >> f, "%f $f" % ((x,y))
