#!/usr/bin/env ruby

# TODO(cs): make cache hit ratio tunable.
# TODO(cs): two analyses: perfect cachability at proxy, and perfect
# cachability in browser. Use CC: private vs. CC: public to make distinction.
# TODO(cs): don't assume that cache is co-located with browser, i.e. insert
# delays between browser and perfect cache.
# TODO(cs): account for performance cost of conditional GETs
# TODO(cs): show a CDF of fraction of response bytes that are cacheable per
# site.

require_relative 'har_util.rb'

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
    end
  end
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
