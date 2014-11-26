#!/usr/bin/env ruby

require_relative 'har_util.rb'

if __FILE__ == $0
  if ARGV.length != 1
    puts "#{__FILE__} <directory containing HARs>"
    exit 1
  end

  Dir.glob(ARGV.shift + "/*.har").each do |file|
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
