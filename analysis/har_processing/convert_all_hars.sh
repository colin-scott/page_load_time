#!/bin/bash

for i in $@; do
  dir=`dirname $i`
  root=`dirname $dir`
  ./wpr/convert_har_to_wpr.py $i $root/wpr/`basename ${i/.har/.wpr}`
done
