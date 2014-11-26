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
  experiment_name = experiment_name.gsub(/.\d+.har$/, "")
  return (experiment_name =~ /.pc$/)
end

class Array
  def median
    sorted = self.sort
    len = sorted.length
    raise ValueError("Median undefined for empty array!") if len == 0
    return (sorted[(len - 1) / 2] + sorted[len / 2]) / 2.0
  end
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
    return @pc_runs.median
  end

  def get_unmodified_median
    return @unmodified_runs.median
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
      return_value = @experiment_group
      @experiment_group = nil
      return return_value
    end
  end
end

# First sort the input, so that Ruby doen't need to load the entire file into
# memory.
input = ARGV.shift
puts "Sorting #{input}..."
system("sort #{input} > buf && mv buf #{input}")

itr = DataIterator.new(input)
while experiment_group = itr.next_experiment_group
  next if experiment_group.pc_runs.length == 0
  next if experiment_group.unmodified_runs.length == 0
  pc_median = experiment_group.get_pc_median * 1.0
  unmodified_median = experiment_group.get_unmodified_median * 1.0
  percent_reduction = ((pc_median - unmodified_median) / unmodified_median) * 100.0
  puts "#{experiment_group.url} #{percent_reduction}"
end
