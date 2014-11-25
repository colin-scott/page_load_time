#!/usr/bin/bash

if [ "$1" == "" ]; then
  echo "Usage: $0 <output of compute_ratio.rb>"
  exit 1
fi

cut -d ' ' -f2 $1 | sort -n > buf && mv buf ratio.dat
~/Scripts/cdf/compile_ccdf.pl ratio.dat > ratio.cdf
gnuplot ratio.gpi
open *pdf
