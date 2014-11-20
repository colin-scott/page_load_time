#!/usr/bin/env ruby

require_relative 'har_util.rb'

def extract_response_bodies(har)
  har['log']['entries'].each do |entry|
    if entry['response']['content'].include? 'text'
      puts entry['_full_url']
      puts entry['response']['content']['text']
      puts "===================="
    end
  end
end

if __FILE__ == $0
  if ARGV.length != 1
    puts "#{__FILE__} /path/to/archive.har"
    exit 1
  end

  har = parse_har_file(ARGV.shift)
  extract_response_bodies(har)
end
