#!/bin/bash

pslurp -h hosts -l vagrant -t 0 -A -L ../data/replay --recursive page_load_time/data/replay/ replay
cd ../data/replay
for F in 10.9.1.*; do
  mv $F/replay/* .
  rm -rf $F
done
