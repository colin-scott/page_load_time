#!/usr/bin/env ruby

require 'pty'

raise 'Must run as root' unless Process.uid == 0

def kill_wpr(out, stdin, pid)
  puts "Shutting down #{pid}"
end

wpr_file = "/tmp/t.wpr"
cmd = "../analysis/wpr/replay.py -i ../analysis/wpr/deterministic.js --record #{wpr_file}"
(wpr_out, wpr_in, wpr_pid) = PTY.spawn cmd
wpr_out.close
wpr_in.close
Process.kill("TERM", wpr_pid)
Process.wait wpr_pid

