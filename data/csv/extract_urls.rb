#!/usr/bin/env ruby

require "csv"

filter_adult_sites = true

text = File.read(ARGV.shift).gsub(/(?<!\\)\\"/,'""')
CSV.parse text do |row|
  puts row[7] unless filter_adult_sites and row[63].to_i == 1
end
