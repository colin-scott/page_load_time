#!/usr/bin/env ruby

require_relative "urlsafe_name.rb"
require 'pty'

def kill_all_children(parent_id)
  # get a list of processes and children
  process_output = `ps -eo pid,ppid,args | grep #{parent_pid} | grep -iv grep`

  # break out column output into pid, parent_id, command
  matches = process_output.scan /^\s*(\d+)\s*(\d+)\s*(.*)$/
  return nil if matches.nil? || matches.empty?

  # check for children
  got_children = false
  matches.each do |match|
    next if match.size != 3
    next if got_children == true
    got_children = true if match[1].to_i == parent_pid
  end
  return nil unless got_children
end

File.foreach("target_urls") do |url|
  wpr_output = "wpr/#{filesafe_name(url)}.wpr"
  cmd = "sudo ../analysis/wpr/replay.py -i ../analysis/wpr/deterministic.js --record #{wpr_output}"
  pid = nil
  begin
    # Boot WPR
    puts "Starting WPR"
    (stdin, stdout, pid) = PTY.spawn( cmd )
    begin
      # Wait for it to complete its boot process:
      puts "Waiting for WPR (#{pid}) to boot..."
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
    # TODO(cs): add timeout
    system("phantomjs --disk-cache=false netsniff.js #{url} 2>&1 > #{har_output}")

    puts "Shutting down WPR"
    # XXX
    exit(0)
  rescue PTY::ChildExited
    puts "The child process exited!"
  ensure
    # TODO(cs): figure out how to kill a root process using ruby's
    # Process.kill
    system("sudo pkill -TERM -P #{pid}") unless pid.nil?
    pid = nil
  end
end
