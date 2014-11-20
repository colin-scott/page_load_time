#!/usr/bin/env ruby

require "csv"

text = File.read(ARGV.shift).gsub(/(?<!\\)\\"/,'""')
CSV.parse text do |row|
  puts row[7]
end
