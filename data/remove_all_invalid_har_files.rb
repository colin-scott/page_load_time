#!/usr/bin/env ruby

# For your own safety, file *must* end in .har.

require_relative '../analysis/har_util.rb'

ARGV.each do |file|
 begin
   if file.end_with? ".har"
     parse_har_file file
     puts "#{file} is valid"
   else
     puts "#{file} does not have .har extension"
   end
 rescue
   puts "Deleting #{file}"
   File.delete(file)
 end
end
