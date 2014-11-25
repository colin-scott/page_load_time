sudo apt-get install vagrant
vagrant plugin install vagrant-hostmanager
vagrant box add ubuntu https://cloud-images.ubuntu.com/vagrant/precise/current/precise-server-cloudimg-amd64-vagrant-disk1.box
vagrant up

# Run modify_wpr.py

# split up inputs, scp each segment to
# 10.9.1.1:~/page_load_time/data/wpr
# 10.9.1.2:~/page_load_time/data/wpr
# 10.9.1.3:~/page_load_time/data/wpr
# 10.9.1.4:~/page_load_time/data/wpr

# ssh to each machine, run
# cd data
# sudo ./replay_urls_sequentially.py ./wpr/
