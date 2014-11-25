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

    splits << l.slice[start_idx...split_idx]
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
    return if second_split.length = 0
    last_url = parse_wpr_name(first_split[-1])
    first_url = parse_wpr_name(second_split[0])
    while first_url == last_url and second_split.length > 0
      first_split << second_split.shift
      first_url = parse_wpr(second_split[0])
    end
  end
end

if __FILE__ == $0
  if ARGV.length != 1
    puts "#{__FILE__} <directory containing wpr archives>"
    exit 1
  end

  remote_tar_path = "~/page_load_time/data/archives.tar"
  vms = ["slave2",
         "slave3",
         "slave4",
         "slave5"]

  # split up inputs
  all_files = Dir.glob(ARGV.shift + "/*.wpr").sort
  splits = split_list(all_files, vms.length)
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
    system(%{tar -cf - --files-from=#{copy_list_file} | vagrant ssh #{vm} -c "cat > #{remote_tar_path}"})
    system(%{vagrant ssh #{vm} -c "cd #{File.dirname(remote_path)}; tar -xvf #{File.basename(remote_tar)}"})
  end
end
