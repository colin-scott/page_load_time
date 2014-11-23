#!/usr/bin/env ruby

require_relative 'har_util.rb'


if __FILE__ == $0
  if ARGV.length != 1
    puts "#{__FILE__} <directory containing HARs>"
    exit 1
  end

  Dir.glob(ARGV.shift + "/*.har").each do |file|
    har = parse_har_file(file)
    plt = har['log']['pages'][0]['pageTimings']['onLoad']
    url = har['log']['pages'][0]['id']
    puts "#{File.basename file} #{url} #{plt}"
  end
end
