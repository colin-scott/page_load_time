#!/bin/bash

# TODO(cs): handle case where there are too many files in a directory to fit in $@

for i in $@; do
  if [ ! -f ${i/.har/.pc.har} ]; then
    ./modify_har.rb $i ${i/.har/.pc.har}
  fi
done
