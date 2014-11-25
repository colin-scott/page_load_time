#!/usr/bin/env ruby

if ARGV.length != 2
  puts "Usage: #{$0} <output of compute_median_reduction.rb> <output of extract_cacheable_bytes.rb>"
  exit 1
end

# I need data with the following format:
#  <URL> <Percent reduction in PLT> <Percent cacheable bytes>
#
# I get it by joining on URL.

# Format of compute_median_reduction.rb:
#  <URL> <Percent reduction>

# Format of extract_cacheable_bytes.rb:
#  <URL> #{cacheable_bytes_fraction} #{total_cacheable_bytes} #{total_bytes_in}"

reduction_input = ARGV.shift
cacheable_input = ARGV.shift

url2reduction = {}
url2cacheable = {}

File.foreach(reduction_input) do |line|
  url, percent_reduction = line.chomp.split
  percent_reduction = percent_reduction.to_f
  url2reduction[url] = percent_reduction
end

File.foreach(cacheable_input) do |line|
  url, cacheable_bytes_fraction, _, _ = line.chomp.split
  cacheable_bytes_fraction = cacheable_bytes_fraction.to_f
  url2reduction[url] = cacheable_bytes_fraction
end

# Now join:
url2reduction.each do |url, reduction|
  cacheable_fraction = url2cacheable[url]
  ratio = cacheable_fraction / reduction
  puts "#{url} #{ratio}"
end
