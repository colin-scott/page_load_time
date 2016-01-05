#!/bin/bash

if [ "$1" == "" ]; then
  echo "Usage: $0 <output of compute_median_reduction.rb for desktop> <output of compute_median_reduction.rb for mobile>"
  exit 1
fi

for INPUT in $1 $2 $3 $4 $5; do
  SUFFIX=""
  # TODO(cs): does bash have an `enumerate` equivalent? this is super clunky
  if [ "$INPUT" == "$2" ]; then
    SUFFIX=".2"
  fi
  if [ "$INPUT" == "$3" ]; then
    SUFFIX=".3"
  fi
  if [ "$INPUT" == "$4" ]; then
    SUFFIX=".4"
  fi
  if [ "$INPUT" == "$5" ]; then
    SUFFIX=".5"
  fi

  cut -d ' ' -f2 $INPUT | sort -n > buf && mv buf percent_reduction$SUFFIX.dat
  ~/Scripts/cdf/compile_ccdf.pl percent_reduction$SUFFIX.dat > percent_reduction$SUFFIX.cdf
done

if [ "$2" == "" ]; then
  gnuplot percent_reduction.gpi
  gnuplot percent_reduction_linear.gpi
elif [ "$3" == "" ]; then
  gnuplot percent_reduction_2_lines.gpi
  gnuplot percent_reduction_linear_2_lines.gpi
elif [ "$4" == "" ]; then
  gnuplot percent_reduction_3_lines.gpi
  gnuplot percent_reduction_linear_3_lines.gpi
elif [ "$5" == "" ]; then
  gnuplot percent_reduction_4_lines.gpi
  gnuplot percent_reduction_linear_4_lines.gpi
else
  gnuplot percent_reduction_linear_5_lines.gpi
fi
