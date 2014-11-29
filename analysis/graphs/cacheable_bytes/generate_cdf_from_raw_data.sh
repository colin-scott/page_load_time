#!/bin/bash

if [ "$1" == "" ]; then
  echo "Usage: $0 <output of extract_cacheable_bytes.rb>"
  exit 1
fi

# Format:
#"#{url} #{cacheable_bytes_fraction} #{total_cacheable_bytes} #{total_bytes_in}"

cut -d ' ' -f 2 $1 | sort -n > cacheable_bytes.cdf
~/Scripts/cdf/compile_ccdf.pl cacheable_bytes.cdf > buf && mv buf cacheable_bytes.cdf
gnuplot cacheable_bytes.gpi
gnuplot cacheable_bytes_linear.gpi
