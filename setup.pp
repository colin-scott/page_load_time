# Notes:
# Assumes page_load_time/ is in your home directory
# Also require Phantomjs > 1.9 : http://phantomjs.org/

$local_user = "vagrant"
$local_home = "/home/$local_user"
$paths = [ "/usr/local/bin/", "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ]

user {$local_user:
     ensure => present,
     shell  => "/bin/bash",
}

define local_package () {
  package { "$name":
    ensure  => latest,
  }
}

define local_absent () {
  package { "$name":
    ensure => absent,
  }
}

local_package {
  # PhantomJS Requirements
  'phantomjs':;

  # Uncomment if building phantomjs from source
  #'build-essential':;
  #'g++':;
  #'flex':;
  #'bison':;
  #'gperf':;
  #'ruby':;
  #'perl':;
  #'libsqlite3-dev':;
  #'libfontconfig1-dev':;
  #'libicu-dev':;
  #'libfreetype6':;
  #'libssl-dev':;
  #'libpng-dev':;
  #'libjpeg-dev':;
  #'python':;
  #'libx11-dev':;
  #'libxext-dev':;


  # Text Editors
  'vim':;
  # Languages
  'python2.7':;
  'ruby1.9.1':;
  'ruby1.9.1-dev':;

  # Providers
  'python-pip':;

  # Networking
  'curl':;
  'ftp':;
  'openssh-client':;
  'openssh-server':;
  'ssh':;
  'wget':;
  'whois':;

  # Version Control
  'git':;
  'rdiff-backup':;
  'rsync':;

  # Searching
  'grep':;
  'ack-grep':;

  # Processes
  'htop':;

  # Misc tools
  'bash':;
  'cron':;
  'screen':;
  'tar':;
  'tmux':;
  'xclip':;
}

# Remove apt-get packages
#local_absent {
#}

## Python Pip

define python_pip () {
  package { "$name":
    ensure   => ['installed', 'latest'],
    provider => 'pip',
  }
}

# Remove python-pip packages
define remove_python_pip () {
  package { "$name":
    ensure   => absent,
    provider => 'pip',
  }
}

python_pip {
   'ipdb':;
}

# DotFiles
file { [ "$local_home/scripts" ]:
  ensure => "directory",
  owner  => $local_user,
}

# Download web-page-replay
exec { "download_wpr":
  require => Package['git'],
  command => "git clone https://github.com/colin-scott/web-page-replay.git $local_home/page_load_time/wpr",
  creates => "$local_home/page_load_time/wpr",
  path    => $paths,
  user    => $local_user,
}

# Uncomment to build PhantomJS from source
# After downloading, cd into ~/phantomjs and run `./build.py`
# Ensure that phantomjs is > 1.9
# exec { "download_phantomjs":
#   require => Package['git'],
#   command => "git clone --recurse-submodules git://github.com/ariya/phantomjs.git $local_home/phantomjs",
#   cwd     => "$local_home/",
#   creates => "$local_home/phantomjs",
#   path    => $paths,
#   user    => $local_user,
# }
