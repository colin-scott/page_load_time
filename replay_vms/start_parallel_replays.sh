#!/usr/bin/bash

# ssh to each machine, run
# cd data
# sudo ./replay_urls_sequentially.py ./wpr/
for F in slave2 slave3 slave4 slave5; do
  vagrant ssh $F -c "cd data; sudo ./replay_urls_sequentially.py ./wpr"
done
