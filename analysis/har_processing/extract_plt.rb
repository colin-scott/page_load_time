#!/usr/bin/env ruby

require_relative 'har_util.rb'

if __FILE__ == $0
  if ARGV.length != 1
    puts "#{__FILE__} <input list>"
    exit 1
  end

  File.foreach(ARGV.shift) do |file|
    file = file.chomp
    begin
      har = parse_har_file(file)
      if passes_sanity_check(har)
        plt = har['log']['pages'][0]['pageTimings']['onLoad']
        url = har['log']['pages'][0]['id']
        puts "#{File.basename file} #{url} #{plt}"
      end
    rescue RuntimeError => e
      $stderr.puts "Exeption processing #{file} #{e}."
    end
  end
end
