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

