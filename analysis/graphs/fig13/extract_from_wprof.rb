#!/usr/bin/ruby

# Invoke from parallel_wprof directory, where each subdir is named according
# to the url, and contains analysis_t/data/ with a single datapoint for that
# url.

output = File.open("whatif.dat", "w")

Dir.glob("*-1").each do |url|
  Dir.chdir "#{url}/analysis_t/temp_files/wprof_300_5_pro_1" do
    File.foreach(url) do |line|
      if line.start_with? "whatif_matrix"
        split = line.chomp.split
        output.puts "#{url} #{split[1]}"
      end
    end
  end
end

output.close
