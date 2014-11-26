#!/bin/bash

if [ "$1" == "" ]; then
  echo "Usage: $0 <output of extract_cacheable_bytes.rb>"
  exit 1
fi

# Format:
#"#{url} #{cacheable_bytes_fraction} #{total_cacheable_bytes} #{total_bytes_in}"

cut -d ' ' -f 3 $1 | sort -n > total_bytes.cdf
~/Scripts/cdf/compile_ccdf.pl total_bytes.cdf > buf && mv buf total_bytes.cdf
gnuplot total_bytes.gpi
