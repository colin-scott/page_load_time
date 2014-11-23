#!/usr/bin/env ruby

if ARGV.length != 1
  puts "Usage: #{$0} <output of extract_plt.rb>"
  exit 1
end

def is_pc(experiment_name)
  # We encode the type of experiment in the filename:
  #    "(.pc)?.<replay number>.har"
  # - If .pc is present, this experiment assumes a perfect cache,
  #    else it is an unmodified execution.
  # - The replay number is 1-indexed.
  # TODO(cs): encoding the experiment in the filename is jenky.
  # Should really use a database.
  name = name.gsub(/.\d+.har$/, "")
  return (name =~ /.pc$/)
end

def median(array)
  sorted = array.sort
  len = sorted.length
  return (sorted[(len - 1) / 2] + sorted[len / 2]) / 2.0
end

class ExperimentGroup
  def initialize(url)
    @url = url
    @pc_runs = []
    @unmodified_runs = []
  end

  def append(filename, plt)
    plt = plt.to_i
    pc = is_pc(filename)
    if pc
      @pc_runs << plt
    else
      @unmodified_runs << plt
    end
  end

  def get_pc_median
    return median(@pc_runs)
  end

  def get_unmodified_median
    return median(@unmodified_runs)
  end
end

class DataIterator
  def initialize(file)
    @input = File.open(file, "r")
    @experiment_group = nil
    @current_url = ""
  end

  def next_experiment_group
    while line = @input.gets
      # Format of extract_plt.rb:
      # "#{file} #{url} #{plt}"
      filename, url, plt = line.chomp.split
      if url != @current_url
        @current_url = url
        old_experiment_group = @experiment_group
        @experiment_group = ExperimentGroup.new(url)
        @experiment_group.append(filename, plt)
        if not old_experiment_group.nil?
          return old_experiment_group
        end
      else
        @experiment_group.append(filename, plt)
      end
    end

    if not @experiment_group.nil?
      return @experiment_group
    end
  end
end

# First sort the input, so that Ruby doen't need to load the entire file into
# memory.
input = ARGV.shift
system("sort #{input} > buf && mv buf #{input}")

itr = DataIterator.new(input)
while experiment_group = itr.next_experiment_group
  pc_median = experiment_group.get_pc_median * 1.0
  unmodified_median = experiment_group.get_unmodified_median * 1.0
  percent_reduction = ((pc_median - unmodified_median) / unmodified_median) * 100.0
  puts percent_reduction
end
