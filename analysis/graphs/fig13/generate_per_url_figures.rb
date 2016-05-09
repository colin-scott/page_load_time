#!/usr/bin/ruby

# Takes: whatif.dat [output of extract_from_wprof.rb]
# Generates a figure for each URL, and places them into per_url/

File.foreach(ARGV.shift) do |line|
  url, whatif = line.chomp.split
  system "./parse_wprof_json.py #{whatif}"
  system "./generate_cdf_from_raw_data.sh"
  system "mv whatif.pdf per_url/#{url}.pdf"
end
