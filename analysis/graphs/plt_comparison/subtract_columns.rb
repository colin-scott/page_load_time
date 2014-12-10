#!/usr/bin/env ruby

File.foreach(ARGV.shift) do |line|
  c1, c2 = line.chomp.split.map { |i| i.to_i }
  puts c1 - c2
end
