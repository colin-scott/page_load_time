#!/bin/bash

if [ "$1" == "" ]; then
  echo "Usage: $0 <output of compute_median_reduction.rb>"
  exit 1
fi

cut -d ' ' -f2 $1 | sort -n > buf && mv buf percent_reduction.dat
~/Scripts/cdf/compile_ccdf.pl percent_reduction.dat > percent_reduction.cdf
gnuplot percent_reduction.gpi
