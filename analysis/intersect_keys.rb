#!/usr/bin/ruby

require 'set'

file1 = ARGV.shift
file2 = ARGV.shift

urls1 = Set.new
urls2 = Set.new

def get_url(line)
  line.chomp.split[0].gsub(/^http:\/\//, "").gsub(/^www./, "").gsub(/\/$/, "")
end

File.foreach(file1) do |line|
  url = get_url(line)
  urls1.add(url)
end

File.foreach(file2) do |line|
  url = get_url(line)
  urls2.add(url)
end

puts "urls1 #{urls1.size}"
puts urls1.to_a.join(" ")
puts "==="
puts "urls2 #{urls1.size}"
puts urls2.to_a.join(" ")
puts "==="
isect = urls1 & urls2
puts "isect #{isect.size}"
puts isect.to_a.join(" ")
puts "==="
diff = urls1 ^ urls2
diff.to_a.sort.each do |url|
  puts url
end
puts "==="

# TODO(cs): I suspect that the url key is the *redirect* URL, not the original
# fetch URL. Otherwise we should see an almost perfect intersection.
# (Or, another possibility: the datasets are in fact different?)

[file1, file2].each do |file|
  output = File.new(file + ".isect", "w")
  File.foreach(file) do |line|
    url = get_url(line)
    if isect.include? url
      output.puts line
    end
  end
  output.close
end
