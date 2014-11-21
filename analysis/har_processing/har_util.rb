#!/usr/bin/env ruby

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

