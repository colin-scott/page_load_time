#!/bin/bash

if [ "$1" == "" ]; then
  echo "Usage: $0 <unmodified PLTs> <perfect cache PLTs>"
  exit 1
fi

cut -d ' ' -f3 $1 | sort -n > buf && mv buf unmodified_plt.dat
cut -d ' ' -f3 $2 | sort -n > buf && mv buf perfect_cache_plt.dat
~/Scripts/cdf/compile_ccdf.pl unmodified_plt.dat > unmodified_plt.cdf
~/Scripts/cdf/compile_ccdf.pl perfect_cache_plt.dat > perfect_cache_plt.cdf
gnuplot plts.gpi
