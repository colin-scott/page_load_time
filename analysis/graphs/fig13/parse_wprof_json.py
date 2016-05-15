#!/usr/bin/python

import json
import sys

# We should write a script to create Figure 13, given the raw data. The raw data is of the following format:
#
# a JSON array, with 33 entries in it.
#
# The first 6 entries correspond raw page load times for # N=0,C=[0,1/4,1/2,3/4,1,2]
# Next 6 entries: N=1/4...
# Next 6 entries: N=1/2..
# Next 6 entries: N=3/4..
# Next 6 entries: N=1..
#
# The last 3 entries can be ignored.
#
# The actual PLT should be the 29th entry, C=1,N=1. We should then normalize the raw PLTs to that number.
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
  def __init__(self, c, datapoints):
    self.c = c
    self.datapoints = datapoints

def parse_json(json_str):
  a = json.loads(json_str)[0:30]
  assert(len(a) == 30)
  plt = a[28]
  series = []
  step = 6
  for start_index, c in [(0,"0"),(1,"1/4"),(2,"1/2"),(3,"3/4"),(4,"1"),(5,"2")]:
    datapoints = a[start_index::step]
    assert(len(datapoints) == 5) # 5 values for N
    normalized = map(lambda x: x / plt, datapoints)
    if c not in to_ignore:
      series.append(Series(c, normalized))
  return series

if len(sys.argv) < 1:
  print >> sys.stderr, "Usage: <JSON array for whatif_matrix>"
  sys.exit(1)

series = parse_json(sys.argv[1])
for s in series:
  output = c_to_dat_filename[s.c]
  with open(output, "w") as f:
    for x,y in zip([0,0.25,0.5,0.75,1], s.datapoints):
      print >> f, "%f %f" % ((x,y))
