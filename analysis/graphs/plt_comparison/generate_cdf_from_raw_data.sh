#!/bin/bash

if [ "$1" == "" ]; then
  echo "Usage: $0 <path to plt_comparison.desktop.dat> [path to plt_comparison.mobile.dat]"
  exit 1
fi

for INPUT in $1 $2; do
  SUFFIX=""
  if [ "$INPUT" == "$2" ]; then
    SUFFIX=".2"
  fi

  cut -d ' ' -f 2,4 $INPUT > original_unmodified$SUFFIX.dat
  cut -d ' ' -f 2,6 $INPUT > original_perfect_cache$SUFFIX.dat
  ./subtract_columns.rb original_unmodified$SUFFIX.dat | sort -n > buf && mv buf original_unmodified$SUFFIX.dat
  ./subtract_columns.rb original_perfect_cache$SUFFIX.dat | sort -n > buf && mv buf original_perfect_cache$SUFFIX.dat
  ~/Scripts/cdf/compile_ccdf.pl original_unmodified$SUFFIX.dat > original_unmodified$SUFFIX.cdf
  ~/Scripts/cdf/compile_ccdf.pl original_perfect_cache$SUFFIX.dat > original_perfect_cache$SUFFIX.cdf
done

# TODO(cs): modify gpi file to allow for 4 lines instead of 2
gnuplot plt_comparison.gpi
