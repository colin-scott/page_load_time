#!/usr/bin/env ruby

require_relative 'har_util.rb'

if __FILE__ == $0
  if ARGV.length != 1
    puts "#{__FILE__} <path to har data directory (original page loads)>"
    exit 1
  end

  File.foreach(ARGV.shift) do |har_path|
    har_path = har_path.chomp
    _, _, _, _, unmodified_replays, _, pc_replays, _ = get_all_files_for_original_har(har_path)
    [unmodified_replays, pc_replays].each do |replays|
      replays.each do |replay|
        if File.exist? replay
          puts File.expand_path replay
        end
      end
    end
  end
end
