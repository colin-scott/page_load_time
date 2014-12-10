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

# def get_status_of_replays(all_replays_infos, original_info)
#   overall_replay_status = nil
#   all_replays_infos.each do |replay_status|
#     replay_status = replay_status.get_status
#     # :ok > :mismatched_404s > :no_responses > :invalid
#     if replay_status == :ok
#       overall_replay_status = :ok
#       break
#     end
#
#     if replay_status == :mismatched_404s
#       overall_replay_status = :mismatched_404s
#     end
#
#     if replay_status == :no_responses and overall_replay_status != :mismatched_404s
#       overall_replay_status = :no_responses
#     end
#
#     if replay_status == :invalid and overall_replay_status != :no_responses and overall_replay_status != :mismatched_404s
#       overall_replay_status = :invalid
#     end
#   end
#   overall_replay_status
# end

# TODO(cs): allow espilon difference in number of 404s.

class LoadInfo
  def initialize(har_path)
    @status = nil
    @num_404s = nil

    begin
      @har = parse_har_file(har_path)
    rescue RuntimeError => e
      @status = :invalid
    end
  end

  def get_total_404s
    if @status == :invalid
      return nil
    end

    if @num_404s.nil?
      @num_404s = get_num_404s(@har)
    end
    @num_404s
  end

  def get_status(original_404s)
    if not @status.nil?
      return @status
    end

    if not passes_sanity_check(@har)
      @status = :no_responses
      return @status
    end

    if not original_404s.nil? and get_num_404s(@har) != original_404s
      @status = :mismatched_404s
      return @status
    end

    @status = :ok
    return @status
  end
end

if __FILE__ == $0
  if ARGV.length != 1
    puts "#{__FILE__} <path to har data directory (original page loads)>"
    exit 1
  end

  har_directory = File.expand_path(ARGV.shift)
  data_dir = File.dirname((File.expand_path(har_directory)))

  # Where we place bad files
  filter_directory = "#{data_dir}/filtered"
  # Where we place stats on the number of bad files
  filter_stats_directory = "#{data_dir}/filtered_stats"

  # target URL doesn't show up in WPR archive:
  invalid_wprs = File.open("#{filter_stats_directory}/invalid_wprs.txt", "w")
  # Empty response body, or nothing but non-200s:
  invalid_originals = File.open("#{filter_stats_directory}/invalid_originals.txt", "w")
  # At least one replay was screwed up:
  invalid_loads = File.open("#{filter_stats_directory}/invalid_loads.txt", "w")
  # Valid for both original fetch and all replays:
  valid = File.open("#{filter_stats_directory}/valids.txt", "w")

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

    # Check the original fetch
    original_info = LoadInfo.new(original_har_path)
    original_status = original_info.get_status(nil)
    if original_status != :ok
      invalid_originals.puts "#{original_har_path} #{original_status}"
      next
    end

    # If we don't have at least one replay for each experiment yet, too soon to diagnose
    unmodified_replays = unmodified_replays.find_all { |r| File.exist? r }
    next if unmodified_replays.empty?
    pc_replays = pc_replays.find_all { |r| File.exist? r }
    next if pc_replays.empty?

    # Check the replays.
    # XXX Assumes one replay per experiment
    unmodified_info = LoadInfo.new(unmodified_replays[0])
    unmodified_status = unmodified_info.get_status(original_info.get_total_404s)
    pc_info = LoadInfo.new(pc_replays[0])
    pc_status = pc_info.get_status(original_info.get_total_404s)

    # If the original, and at least one PC and one unmodified replay are OK, then we say the
    # whole set is OK.
    if original_status == :ok and unmodified_status == :ok and pc_status == :ok
      valid.puts "#{url} #{original_har_path}"
    else
      invalid_loads.puts "#{url} #{original_status} #{original_info.get_total_404s} #{unmodified_status} #{unmodified_info.get_total_404s} #{pc_status} #{pc_info.get_total_404s} #{original_har_path}"
    end
  end

  [invalid_wprs, invalid_originals, valid, invalid_loads].each { |f| f.close }
end
