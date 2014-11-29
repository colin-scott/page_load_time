#!/usr/bin/env ruby

def split_list(l, split_ways)
  # Split our inputs into split_ways separate lists
  if split_ways < 1
    raise "Split ways must be greater than 0"
  end

  splits = []
  split_interval = l.length / split_ways # integer division = floor
  remainder = l.length % split_ways # remainder is guaranteed to be less than splitways

  start_idx = 0
  while splits.length < split_ways
    split_idx = start_idx + split_interval
    # the first 'remainder' chunks are made one element larger to chew
    # up the remaining elements (remainder < splitways)
    # note: len(l) = split_ways *  split_interval + remainder
    if remainder > 0
      split_idx += 1
      remainder -= 1
    end

    splits << l[start_idx...split_idx]
    start_idx = split_idx
  end
  splits
end

def parse_wpr_name(filename)
  filename = filename.gsub(/.wpr$/, "")
  url = filename.gsub(/.pc$/, "")
  return url
end

def correct_splits!(splits)
  # Make sure .pc experiments are co-located with the original experiments.
  i = 0
  while i + 1 < splits.length
    first_split = splits[i]
    second_split = splits[i+1]
    return if first_split.length == 0
    return if second_split.length == 0
    last_url = parse_wpr_name(first_split[-1])
    first_url = parse_wpr_name(second_split[0])
    while first_url == last_url and second_split.length > 0
      puts "Correcting #{second_split[0]}"
      first_split << second_split.shift
      first_url = parse_wpr_name(second_split[0])
    end
    i += 1
  end
end

if __FILE__ == $0
  if ARGV.length != 2
    # Second arg can be an empty file
    puts "#{__FILE__} <directory containing wpr archives> <invalid_wprs.txt, output of filter_bad_pages.rb>"
    exit 1
  end

  remote_tar_path = "/home/vagrant/page_load_time/data/wpr.tar"
  vms = ["10.9.1.2",
         "10.9.1.3",
         "10.9.1.4",
         "10.9.1.5"]

  dir = ARGV.shift
  blacklist_file = ARGV.shift
  blacklist = Set.new
  File.foreach(blacklist_file) do |line|
    blacklist.add File.basename line.chomp
  end

  # split up inputs
  Dir.chdir File.dirname(dir) do
    all_files = Dir.glob("#{File.basename(dir)}/*.wpr")
    all_valid_files = all_files.select { |f| not blacklist.include? f }.sort
    splits = split_list(all_valid_files, vms.length)
    # Make sure that .pc experiments are together with the original
    correct_splits!(splits)

    # scp each segment
    vms.zip(splits).each do |pair|
      vm, split = pair
      copy_list_file = "/tmp/copy_list.txt"
      copy_list = File.open(copy_list_file, "w")
      copy_list.write(split.join("\n"))
      copy_list.close

      # tar while scp'ing
      puts "Copying split to #{vm}."
      system(%{tar -cf - --files-from=#{copy_list_file} | ssh -i /root/.ssh/tmp_vagrant_key vagrant@#{vm} "sudo cat > #{remote_tar_path}"})
      system(%{ssh -i /root/.ssh/tmp_vagrant_key vagrant@#{vm} "cd #{File.dirname(remote_tar_path)}; tar -xvf #{File.basename(remote_tar_path)}"})
    end
  end
end
