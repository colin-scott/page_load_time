#!/usr/bin/env ruby

# TODO(cs): make cache hit ratio tunable.
# TODO(cs): two analyses: perfect cachability at proxy, and perfect
# cachability in browser. Use CC: private vs. CC: public to make distinction.
# TODO(cs): don't assume that cache is co-located with browser, i.e. insert
# delays between browser and perfect cache.

require_relative 'har_util.rb'

# har is a Hash. Assumes that the har is for only a single page load.
def assume_perfect_cache!(har)
  total_cacheable_bytes = 0
  # WPT only tracks bytes in before Document Complete time. This tracks all
  # bytes in.
  total_bytes_in = 0
  har['log']['entries'].each do |entry|
    is_cacheable = is_cacheable(entry['response'])
    ['headersSize', 'bodySize'].each do |part|
      if entry['response'][part].nil?
        puts "Warning: #{part} nil?. Entry: #{entry['response'].inspect}"
      elsif entry['response'][part] != -1
        total_bytes_in += entry['response'][part]
        total_cacheable_bytes += entry['response'][part] if is_cacheable
      end
    end
    if is_cacheable
      entry['time'] = 0
      timings = entry['timings']
      timings['blocked'] = 0
      timings['dns'] = 0
      timings['connect'] = 0
      timings['send'] = 0
      timings['wait'] = 0
      timings['receive'] = 0
      timings['ssl'] = -1
    end
  end
  page = har['log']['pages'][0]
  page['_cacheable_response_bytes'] = total_cacheable_bytes
  page['_cacheable_bytes_fraction'] = total_cacheable_bytes * 1.0 / total_bytes_in
  page['_total_bytes_in'] = total_bytes_in
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

if __FILE__ == $0
  if ARGV.length != 2
    puts "#{__FILE__} /path/to/archive.har /path/to/modified_archive.har"
    exit 1
  end

  har = parse_har_file(ARGV.shift)
  assume_perfect_cache!(har)
  write_har_file(har, ARGV.shift)
end
