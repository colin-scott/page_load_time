#!/bin/bash

valids=""
if [ -f ../data/filtered_stats/valids.txt ]; then
  pscp -h hosts -l vagrant -A ../data/filtered_stats/valids.txt page_load_time/data/valids.txt
  valids="./filtered_stats/valids.txt"
fi
pssh -h hosts -l vagrant -t 0 -A -i "cd page_load_time/data; sudo ./replay_urls_sequentially.py ./wpr $valids"
