#!/usr/bin/env ruby

require 'json'
require 'base64'

def parse_har_file(path)
  begin
    return JSON.parse File.read(path)
  rescue => err
    raise "Could not parse archive file #{path}: #{err.inspect}"
  end
end

def write_har_file(har, path)
  File.open(path, "w") do |f|
    f.write(har.to_json)
  end
end

def decode_b64(b64)
  Base64.urlsafe_decode64(b64)
end

def get_all_files_for_original_har(original_har_path)
  basename = File.basename original_har_path
  b64 = basename.gsub(/.har$/, "")
  data_dir = File.dirname(File.dirname(original_har_path))

  # WPR files:
  wpr_dir = "#{data_dir}/wpr"
  wpr = "#{b64}.wpr"
  wpr_archive = "#{wpr_dir}/#{wpr}"
  pc_wpr = "#{b64}.pc.wpr"
  pc_wpr_archive = "#{wpr_dir}/#{pc_wpr}"
  err = "#{b64}.err"
  err_file = "#{wpr_dir}/#{err}"

  # Replay files:
  replay_dir = "#{data_dir}/replay"
  unmodified_replays = []
  unmodified_errs = []
  pc_replays = []
  pc_errs = []
  # XXX
  num_replays = 1
  (1..num_replays).each do |i|
    unmodified_replays << "#{replay_dir}/#{b64}.#{i}.har"
    pc_replays << "#{replay_dir}/#{b64}.pc.#{i}.har"
    unmodified_errs << "#{replay_dir}/#{b64}.#{i}.err"
    pc_errs << "#{replay_dir}/#{b64}.pc.#{i}.err"
  end

  # N.B. last two elements are lists
  return [original_har_path,
          wpr_archive,
          pc_wpr_archive,
          err,
          unmodified_replays,
          unmodified_errs,
          pc_replays,
          pc_errs]
end

def get_num_404s(har)
  total = 0
  har['log']['entries'].each do |entry|
    if entry['response']['status'].to_i == 404
      total += 1
    end
  end
  total
end

def passes_sanity_check(har)
  # TODO(cs): completely redundant with extract_cacheable_bytes.rb
  total_bytes_in = 0
  total_responses = 0
  total_non_200s = 0
  har['log']['entries'].each do |entry|
    ['headersSize', 'bodySize'].each do |part|
      if entry['response'][part].nil?
        puts "Warning: #{part} nil?. Entry: #{entry['response'].inspect}"
      elsif entry['response'][part] != -1
        total_bytes_in += entry['response'][part]
      end
      total_responses += 1
      if entry['response']['status'].to_i != 200
        total_non_200s += 1
      end
    end
  end

  if total_bytes_in == 0
    return false
  end

  if total_responses == total_non_200s
    return false
  end

  return true
end

def is_cacheable(response)
  # We use an array to handle the case where there are redundant headers. The
  # most restrictive caching header wins.
  cc_headers = []
  expires_headers = []
  response['headers'].each do |header|
    if header['name'] =~ /cache-control/i
      cc_headers << header['value']
    end
    if header['name'] =~ /expires/i
      expires_headers << header['value']
    end
  end

  # N.B. we consider undefined as cacheable.
  # WHEN LENGTH(resp_cache_control) = 0
  #   AND LENGTH(resp_expires) = 0
  #   THEN "undefined"
  if cc_headers.empty? and expires_headers.empty?
    return true
  end

  # WHEN resp_cache_control CONTAINS "no-store"
  #   OR resp_cache_control CONTAINS "no-cache"
  #   OR resp_cache_control CONTAINS "max-age=0"
  #   OR resp_expires = "-1"
  #   THEN "non-cacheable"
  cc_headers.each do |cc_header|
    if (cc_header =~ /no-store/i or
        cc_header =~ /no-cache/i or
        cc_header =~ /max-age=0/i)
      return false
    end
  end

  expires_headers.each do |expires_header|
    return false if expires_header =~ /-1/
  end

  # ELSE "cacheable"
  return true
end

