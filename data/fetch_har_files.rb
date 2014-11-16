#!/usr/bin/env ruby

# Does not download a HAR file if it already exists. To refetch corrupt files,
# first invoke ./remove_all_invalid_har_files.rb

require 'csv.rb'

limit = 20

if ARGV.length == 0
  puts "Usage: #{$0} /path/to/httparchive_pages.csv"
  exit 1
end

def fetch_har(wptid, run)
  output_file = wptid + "_" + run + ".har"
  if not File.exist?("har/#{output_file}")
    cmd = <<-eos
      wget "http://httparchive.webpagetest.org/export.php?test=#{wptid}&run=#{run}&bodies=1&pretty=0" -O har/#{output_file}
    eos
    system(cmd)
  end
end

current_row = 0
CSV.foreach ARGV.shift do |row|
  wptid = row[5]
  run = row[6]
  fetch_har(wptid, run)
  current_row += 1
  break if current_row >= limit
end
