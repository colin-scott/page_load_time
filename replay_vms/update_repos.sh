#!/bin/bash

pssh -h hosts -l vagrant -t 0 -A -i "cd page_load_time/; git pull; cd analysis/wpr; git pull"
