#!/usr/bin/env ruby

require 'fileutils'
require_relative 'har_util.rb'

def valid_wpr(wpr_archive, url)
  httparchive_path = "#{File.dirname(File.expand_path(File.dirname(__FILE__)))}/wpr/httparchive.py"
  puts httparchive_path
  `#{httparchive_path} ls #{wpr_archive}`.each_line do |line|
    if line =~ /#{url}/
      return true
    end
  end
  return false
end

def check_status(har)
  begin
    har = parse_har_file(file)
  rescue RuntimeError => e
    return :invalid
  end

  if not passes_sanity_check(har)
    return :no_responses
  end

  return :ok
end

if __FILE__ == $0
  if ARGV.length != 1
    puts "#{__FILE__} <path to har data directory (original page loads)>"
    exit 1
  end

  har_directory = ARGV.shift
  data_dir = File.dirname((File.expand_path(har_directory)))

  # Where we place bad files
  filter_directory = "#{data_dir}/filtered"
  # Where we place stats on the number of bad files
  filter_stats_directory = "#{data_dir}/filtered_stats"

  invalid_wprs = File.open("#{filter_stats_directory}/invalid_wprs.txt", "w")
  valid = File.open("#{filter_stats_directory}/valids.txt", "w")
  invalid_loads = File.open("#{filter_stats_directory}/invalid_loads.txt", "w")

  Dir.glob("#{har_directory}/*.har").each do |original_load|
    puts original_load
    url = decode_b64(File.basename(original_load.gsub(/.har$/, "")))

    original_har_path, wpr_archive, pc_wpr_archive, err, all_replays, all_replay_errs = get_all_files_for_original_har(original_load)

    if not valid_wpr(wpr_archive, url)
      # If the WPR isn't valid, nothing else will be.
      invalid_wprs.puts wpr_archive
      # FileUtils.mv(original_har_path, filter_directory)
      # FileUtils.mv(wpr_archive, filter_directory)
      # FileUtils.mv(err, filter_directory)
      # FileUtils.rm_f([pc_wpr_archive] + all_replays + all_replay_errs)
      next
    end

    all_replays = all_replays.find_all { |r| File.exist? r }
    # If we don't have the replays yet, too soon to diagnose
    next if all_replays.empty?

    original_status = check_status(original_har_path)

    overall_replay_status = nil
    all_replays.each do |replay_har|
      replay_status = check_status(replay_har)
      if replay_status == :ok
        overall_replay_status = :ok
        break
      end
      if replay_status == :invalid and overall_replay_status != :no_responses
        overall_replay_status = :invalid
      end
      if replay_status == :no_responses
        overall_replay_status = :no_responses
      end
    end

    if original_status == :ok and overall_replay_status == :ok
      valid.puts "#{url} #{original_har_path}"
    else
      # A few cases:
      #   - original valid, replays valid
      #   - original valid, replays invalid
      #   - original valid, replays no_responses
      #   - original invalid, replays valid
      #   - original invalid, replays invalid
      #   - original invalid, replays no_responses
      #   - original no_responses, replays valid
      #   - original no_responses, replays invalid
      #   - original no_responses, replays no_responses
      invalid_loads.puts "#{original_status} #{overall_replay_status} #{url} #{original_har_path}"
    end
  end

  [invalid_wprs, valid, invalid_loads].each { |f| f.close }
end
