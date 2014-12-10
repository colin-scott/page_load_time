#!/usr/bin/env ruby

require_relative 'har_util.rb'

if ARGV.length != 1
  $stderr.puts "Usage #{$0} <list of HAR files to check>"
  $stderr.puts "Echoes back all HAR files that passed the sanity checks"
  exit 1
end

File.foreach(ARGV.shift) do |line|
  line = line.chomp
  begin
    har = parse_har_file(line)
    if passes_sanity_check(har)
      puts line
    end
  rescue Exception => e
    $stderr.puts "Invalid HAR #{line}. #{e.class}"
  end
end
