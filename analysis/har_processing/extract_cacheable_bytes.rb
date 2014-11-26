#!/usr/bin/env ruby

require_relative 'har_util.rb'

def extract_cacheable_bytes(har)
  total_cacheable_bytes = 0
  # WPT only tracks bytes in before Document Complete time. This tracks all
  # bytes in.
  total_bytes_in = 0
  har['log']['entries'].each do |entry|
    ['headersSize', 'bodySize'].each do |part|
      if entry['response'][part].nil?
        puts "Warning: #{part} nil?. Entry: #{entry['response'].inspect}"
      elsif entry['response'][part] != -1
        total_bytes_in += entry['response'][part]
        total_cacheable_bytes += entry['response'][part] if is_cacheable(entry['response'])
      end
    end
  end

  return if total_bytes_in == 0
  # 404 not found
  return if total_bytes_in == 13

  page = har['log']['pages'][0]
  url = page['id']
  cacheable_bytes_fraction = total_cacheable_bytes * 1.0 / total_bytes_in
  puts "#{url} #{cacheable_bytes_fraction} #{total_cacheable_bytes} #{total_bytes_in}"
end

if __FILE__ == $0
  if ARGV.length != 1
    puts "#{__FILE__} <directory containing HARs>"
    exit 1
  end

  Dir.glob(ARGV.shift + "/*.har").each do |file|
    begin
      har = parse_har_file(file)
      extract_cacheable_bytes(har)
    rescue RuntimeError => e
      $stderr.puts "Exception processing #{file} #{e.class}."
    end
  end
end
