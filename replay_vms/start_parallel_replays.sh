#!/bin/bash

pscp -h hosts -l vagrant -A ../data/filtered_stats/valids.txt page_load_time/data/valids.txt
pssh -h hosts -l vagrant -t 0 -A -i "cd page_load_time/data; sudo ./replay_urls_sequentially.py ./wpr ./filtered_stats/valids.txt"
