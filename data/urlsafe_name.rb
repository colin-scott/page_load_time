#!/usr/bin/env ruby

require "base64"

def filesafe_name(name)
  Base64.urlsafe_encode64(name)
end

if __FILE__ == $0
  puts filesafe_name(ARGV.shift)
end
