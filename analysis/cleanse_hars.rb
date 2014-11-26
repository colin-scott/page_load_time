#!/usr/bin/env ruby

# Phantomjs output has annoying stderr lines before and after the HAR json object

require 'fileutils'

if __FILE__ == $0
  if ARGV.length != 1
    puts "#{__FILE__} <directory containing HARs>"
    exit 1
  end

  Dir.glob(ARGV.shift + "/*.har").each do |file|
    tmp_file = "/tmp/#{File.basename file}"
    File.open(tmp_file, "w") do |f|
      head_seen = false
      File.foreach(file) do |line|
        if not head_seen and line == "{\n"
          head_seen = true
        end

        if head_seen
          f.write line
        end

        if line == "}\n"
          break
        end
      end
    end
    FileUtils.mv(tmp_file, file)
  end
end
