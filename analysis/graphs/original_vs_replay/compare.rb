#!/usr/bin/env ruby

if ARGV.length != 2
  $stderr.puts "Usage #{$0} <original_plts.dat> <replay_plts.dat>"
  exit 1
end

original_plts_file = ARGV.shift
replay_plts_file = ARGV.shift

# Format of both inputs:
#   <File.basename> <url> <plt>

# We join on url

url2original = {}
url2replays = Hash.new { |h,k| h[k] = [] }
url2pcs = Hash.new { |h,k| h[k] = [] }

File.foreach(original_plts_file) do |line|
  _, url, percent_reduction = line.chomp.split
  percent_reduction = percent_reduction.to_f
  url2original[url] = percent_reduction
end

File.foreach(replay_plts_file) do |line|
  filename, url, percent_reduction = line.chomp.split
  percent_reduction = percent_reduction.to_f
  if (filename =~ /.pc.\d+.har$/)
    url2pcs[url] << percent_reduction
  else
    url2replays[url] << percent_reduction
  end
end

# Now join:
url2original.each do |url, reduction|
  replays = url2replays[url]
  pcs = url2pcs[url]
  puts "#{url} #{reduction} | #{replays.join(" ")} | #{pcs.join(" ")}"
end
