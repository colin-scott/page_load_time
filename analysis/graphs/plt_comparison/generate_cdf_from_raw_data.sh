#!/bin/bash

if [ "$1" == "" ]; then
  echo "Usage: $0 <path to plt_comparison.dat>"
  exit 1
fi

cut -d ' ' -f 2,4 $1 > original_unmodified.dat
cut -d ' ' -f 2,6 $1 > original_perfect_cache.dat
./subtract_columns.rb original_unmodified.dat | sort -n > buf && mv buf original_unmodified.dat
./subtract_columns.rb original_perfect_cache.dat | sort -n > buf && mv buf original_perfect_cache.dat
~/Scripts/cdf/compile_ccdf.pl original_unmodified.dat > original_unmodified.cdf
~/Scripts/cdf/compile_ccdf.pl original_perfect_cache.dat > original_perfect_cache.cdf

gnuplot plt_comparison.gpi
