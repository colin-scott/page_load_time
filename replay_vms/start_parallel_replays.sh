#!/bin/bash

pssh -h hosts -l vagrant -t 0 -A -i "cd page_load_time/data; sudo ./replay_urls_sequentially.py ./wpr"
