#!/bin/bash

if [ "$1" == "" ]; then
  echo "Usage: $0 <output of compute_median_reduction.rb for desktop> <output of compute_median_reduction.rb for mobile>"
  exit 1
fi

for INPUT in $1 $2; do
  SUFFIX=""
  if [ "$INPUT" == "$2" ]; then
    SUFFIX=".2"
  fi

  cut -d ' ' -f2 $INPUT | sort -n > buf && mv buf percent_reduction$SUFFIX.dat
  ~/Scripts/cdf/compile_ccdf.pl percent_reduction$SUFFIX.dat > percent_reduction$SUFFIX.cdf
done

if [ "$2" == "" ]; then
  gnuplot percent_reduction.gpi
  gnuplot percent_reduction_linear.gpi
else
  gnuplot percent_reduction_2_lines.gpi
  gnuplot percent_reduction_linear_2_lines.gpi
fi
