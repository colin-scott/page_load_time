#!/usr/bin/env ruby

require 'fileutils'
require_relative 'har_util.rb'

def valid_wpr(wpr_archive, url)
  httparchive_path = "#{File.dirname(File.expand_path(File.dirname(__FILE__)))}/wpr/httparchive.py"
  `#{httparchive_path} ls #{wpr_archive}`.each_line do |line|
    if line =~ /#{url}/
      return true
    end
  end
  return false
end

def get_status_for_replays(all_replays, original_404s)
  overall_replay_status = nil
  all_replays.each do |replay_har|
    replay_status = check_status(replay_har, original_404s)
    # :ok > :mismatched_404s > :no_responses > :invalid
    if replay_status == :ok
      overall_replay_status = :ok
      break
    end

    if replay_status == :mismatched_404s
      overall_replay_status = :mismatched_404s
    end

    if replay_status == :no_responses and overall_replay_status != :mismatched_404s
      overall_replay_status = :no_responses
    end

    if replay_status == :invalid and overall_replay_status != :no_responses and overall_replay_status != :mismatched_404s
      overall_replay_status = :invalid
    end
  end
end

# TODO(cs): allow espilon difference in number of 404s.

def check_status(har, original_404s)
  begin
    har = parse_har_file(har)
  rescue RuntimeError => e
    return :invalid
  end

  if not passes_sanity_check(har)
    return :no_responses
  end

  if not original_404s.nil? and get_num_404s(har) != original_404s
    return :mismatched_404s
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
  invalid_originals = File.open("#{filter_stats_directory}/invalid_originals.txt", "w")
  valid = File.open("#{filter_stats_directory}/valids.txt", "w")
  invalid_loads = File.open("#{filter_stats_directory}/invalid_loads.txt", "w")

  Dir.glob("#{har_directory}/*.har").each do |original_load|
    puts original_load
    url = decode_b64(File.basename(original_load.gsub(/.har$/, "")))

    original_har_path, wpr_archive, pc_wpr_archive, err, unmodified_replays, unmodified_errs, pc_replays, pc_errs = get_all_files_for_original_har(original_load)

    if not valid_wpr(wpr_archive, url)
      # If the WPR isn't valid, nothing else will be.
      invalid_wprs.puts wpr_archive
      # FileUtils.mv(original_har_path, filter_directory)
      # FileUtils.mv(wpr_archive, filter_directory)
      # FileUtils.mv(err, filter_directory)
      # FileUtils.rm_f([pc_wpr_archive] + all_replays + all_replay_errs)
      next
    end

    # If we don't have at least one replay for each experiment yet, too soon to diagnose
    unmodified_replays = unmodified_replays.find_all { |r| File.exist? r }
    next if unmodified_replays.empty?
    pc_replays = pc_replays.find_all { |r| File.exist? r }
    next if pc_replays.empty?

    # Check the original fetch
    original_status = check_status(original_har_path, nil)
    if original_status != :ok
      invalid_originals.puts "#{original_har_path} #{original_status}"
      next
    end

    total_404s = get_num_404s(parse_har_file(original_har_path))

    # Check the replays.
    unmodified_status = get_status_of_replays(unmodified_replays, total_404s)
    pc_status = get_status_of_replays(pc_replays, total_404s)

    # If the original, and at least one PC and one unmodified replay are OK, then we say the
    # whole set is OK.

    if original_status == :ok and unmodified_status == :ok and pc_status == :ok
      valid.puts "#{url} #{original_har_path}"
    else
      invalid_loads.puts "#{original_status} #{unmodified_status} #{pc_status} #{url} #{original_har_path}"
    end
  end

  [invalid_wprs, invalid_originals, valid, invalid_loads].each { |f| f.close }
end
