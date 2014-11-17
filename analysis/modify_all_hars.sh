#!/bin/bash

# TODO(cs): handle case where there are too many files in a directory to fit in $@

for i in $@; do
  if [[ ${i/.har/.pc.har} != *pc.pc.* ]]; then
    ./modify_har.rb $i ${i/.har/.pc.har}
  else
    echo "Skipping $i. Already modified."
  fi
done
