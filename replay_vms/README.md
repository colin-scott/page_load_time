# Prereqs:
sudo apt-get install VirtualBoxHeadless
sudo apt-get install vagrant
vagrant plugin install vagrant-hostmanager

# Config:
vagrant box add ubuntu https://cloud-images.ubuntu.com/vagrant/precise/current/precise-server-cloudimg-amd64-vagrant-disk1.box
vagrant up

# Run:
analysis/wpr/modify_wpr_delays.py data/wpr

# Then:
./shard_and_copy_wprs.rb ../data/wpr
./start_parallel_replays.sh

