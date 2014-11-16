#!/usr/bin/env ruby

require_relative '../analysis/har_util.rb'

ARGV.each do |file|
 begin
   parse_har_file file
   puts "#{file} is valid"
 rescue
   puts "Deleting #{file}"
   File.delete(file)
 end
end
