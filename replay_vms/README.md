# Prereqs:
sudo apt-get install VirtualBoxHeadless
sudo apt-get install vagrant
vagrant plugin install vagrant-hostmanager

# Install ruby: http://tecadmin.net/install-ruby-2-1-on-centos-rhel/

# Config:
vagrant box add ubuntu https://cloud-images.ubuntu.com/vagrant/precise/current/precise-server-cloudimg-amd64-vagrant-disk1.box
vagrant up

# Run:
analysis/wpr/modify_wpr_delays.py data/wpr

# Then:
./shard_and_copy_wprs.rb ../data/wpr ../data/filtered_stats/invalid_wprs.txt
./start_parallel_replays.sh


