#!/usr/bin/env ruby

# TODO(cs): make cache hit ratio tunable.
# TODO(cs): two analyses: perfect cachability at proxy, and perfect
# cachability in browser. Use CC: private vs. CC: public to make distinction.

require 'json'

def parse_har_file(path)
  begin
    return JSON.parse File.read(path)
  rescue => err
    raise "Could not parse archive file #{path}: #{err.to_s}"
  end
end

def write_har_file(har, path)
  File.open(path, "w") do |f|
    f.write(har.to_json)
  end
end

# har is a Hash. Assumes that the har is for only a single page load.
def assume_perfect_cache!(har)
  har['log']['entries'].each do |entry|
    if is_cacheable(entry['response'])
      entry['time'] = 0
      timings = entry['timings']
      timings['blocked'] = 0
      timings['dns'] = 0
      timings['connect'] = 0
      timings['send'] = 0
      timings['wait'] = 0
      timings['receive'] = 0
      timings['ssl'] = -1
    else
      puts "Not cacheable! Note rewriting #{entry.inspect}"
    end
  end
end

def is_cacheable(response)
  cc_header = ""
  expires_header = ""
  response['headers'].each do |header|
    if header['name'] =~ /cache-control/i
      puts "Warning: two CC headers. Previous: #{cc_header} Current: #{header['name']}" unless cc_header.empty?
      puts "cc_header! #{header.inspect}"
      cc_header = header['value']
    end
    if header['name'] =~ /expires/i
      puts "Warning: two CC headers. Previous: #{expires_header} Current: #{header['name']}" unless expires_header.empty?
      puts "expires_header! #{header.inspect}"
      expires_header = header['value']
    end
  end

  # N.B. we consider undefined as cacheable.
  # WHEN LENGTH(resp_cache_control) = 0
  #   AND LENGTH(resp_expires) = 0
  #   THEN "undefined"
  if cc_header.empty? and expires_header.empty?
    puts "undefined"
    return true
  end

  # WHEN resp_cache_control CONTAINS "no-store"
  #   OR resp_cache_control CONTAINS "no-cache"
  #   OR resp_cache_control CONTAINS "max-age=0"
  #   OR resp_expires = "-1"
  #   THEN "non-cacheable"
  if (cc_header =~ /no-store/i or
      cc_header =~ /no-cache/i or
      cc_header =~ /max-age=0/i or
      expires_header =~ /-1/)
    puts "Not Cacheable"
    return false
  end

  # ELSE "cacheable"
  puts "Cacheable"
  return true
end

if __FILE__ == $0
  if ARGV.length != 2
    puts "#{__FILE__} /path/to/archive.har /path/to/modified_archive.har"
    exit 1
  end

  har = parse_har_file(ARGV.shift)
  assume_perfect_cache!(har)
  write_har_file(har, ARGV.shift)
end
