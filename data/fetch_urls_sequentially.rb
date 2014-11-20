#!/usr/bin/env ruby

require_relative "urlsafe_name.rb"
require 'pty'

File.foreach("target_urls") do |url|
  wpr_output = "wpr/#{filesafe_name(url)}.wpr"
  cmd = "sudo ../analysis/web-page-replay/replay.py -i ../analysis/web-page-replay/deterministic.js --record #{wpr_output}"
  begin
    # Boot WPR
    puts "Starting WPR"
    (stdin, stdout, pid) = PTY.spawn( cmd )
    begin
      # Wait for it to complete its boot process:
      puts "Waiting for WPR to boot..."
      stdin.each do |line|
        puts line
        break if line =~ /HTTPS server started on/
      end
    rescue Errno::EIO
      puts "Errno:EIO error, but this probably just means " +
            "that the process has finished giving output"
    end

    puts "Fetching page #{url}"
    har_output = "har/#{filesafe_name(url)}.har"
    system("phantomjs --disk-cache=false netsniff.js #{url} > #{har_output}")

    puts "Shutting down WPR"
    # TODO(cs): figure out how to kill a root process using ruby's
    # Process.kill
    system("sudo kill -15 #{pid}")
  rescue PTY::ChildExited
    puts "The child process exited!"
  end
end
