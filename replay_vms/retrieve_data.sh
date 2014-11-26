#!/bin/bash

pslurp -h hosts -l vagrant -t 0 -A -L ../data/replay --recursive /home/vagrant/page_load_time/data/replay/ replay
cd ../data/replay
for F in 10.9.1.*; do
  find $F/replay -name "*har" | xargs -I '{}' mv '{}' .
  find $F/replay -name "*err" | xargs -I '{}' mv '{}' .
  rm -rf $F
done
