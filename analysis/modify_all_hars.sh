#!/bin/bash

# TODO(cs): handle case where there are too many files in a directory to fit in $@

for i in $@; do
  ./modify_har.py $i ${i/.har/.pc.har}
done
