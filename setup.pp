# Notes:
# Also require Phantomjs: http://phantomjs.org/

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
  # Text Editors
  'vim':;

  # Languages
  'python2.7':;
  'ruby':;
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
  'silversearcher-ag':;

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

# python_pip {
#    'cronos':;
# }

# DotFiles
file { [ "$local_home/scripts" ]:
  ensure => "directory",
  owner  => $local_user,
}
