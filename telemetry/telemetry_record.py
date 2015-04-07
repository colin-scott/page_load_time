"""Record WebPageReplay

Records running a set of target urls on the remote tablet, modifies cacheable
objects, then re-runs to see page load time differences.

Usage: sudo python record_wpr.py

Notes:
    Assumes - telemetry is in CHROMIUM_SRC/tools/telemetry/telemetry
            - page_sets is in CHROMIUM_SRC/tools/perf/page_sets
            - modify_wpr_delays.py is in CHROMIUM_SRC/third_party/webpagereplay

TODO: Measure page load time before and after modifying
TODO: Make sure to only get the most recent wpr file when moving / modifying
TODO: Clean up path dependencies, move them to the top
"""
from subprocess import Popen, PIPE, STDOUT
from sys import path
import os
import pickle

CHROMIUM_SRC='/home/jamshed/src'

def record(page_set, url, options='--browser=android-jb-system-chrome'):
    """Runs wpr with telemetry to record an initial target page set

    :param page_set: str filename of the page set
    :param url: str url used if url fails
    :param options: chromium browser options
    """
    record_path = os.path.join(CHROMIUM_SRC, 'tools/perf/record_wpr')
    cmd = ' '.join([record_path, options, page_set])
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    output = p.stdout.read()
    # Check for errors
    assert p.returncode is None, '{0} returned an error: {1}'.format(page_set,
            p.returncode)
    # Silently fail, push output to failed_urls
    if 'PASSED' not in output:
        failed_url(url, output)

def get_urls(path):
    """Returns a list of urls from path

    :param path: str relative or absolute path to target urls
    """
    urls = []
    with open(path, 'rb') as f:
        urls = [x.strip() for x in f.readlines()]
    return urls

def write_page_sets(urls):
    """Writes a page set file for each url in urls

    :param url: A list of url strings
    TODO: Change to one page set with multiple user stories if adding ID to
    each unique url. This helps group urls in the wpr file
    """
    template = ''
    page_set_path = os.path.join(CHROMIUM_SRC, 'tools/perf/page_sets/')
    with open('page_set_template.py', 'rb') as f:
        template = ''.join(f.readlines())
        assert template, 'Failed to read from page set template'
    for i in range(len(urls)):
        test_name = 'url{0}'.format(i)
        with open('{0}{1}.py'.format(page_set_path, test_name), 'wb') as f:
            f.write(template.format(test_name, urls[i]))

def store_url_mapping(url_list):
    """Stores a mapping from index to url to be used later.

    Saved to data/url_mapping.db: {index: url,...}
    """
    url_mapping = {}
    for i in range(len(url_list)):
        url_mapping[i] = url_list[i]
    try:
        pickle.dump(url_mapping, open('data/url_mapping.db', 'wb'))
    except IOError:
        raise IOError('Failed to write url mapping to data/url_mapping.db')

def move_wpr_files(name_schema):
    """Moves wpr files from within CHROMIUM_SRC to local data directory

    :param name_schema: regex for the matching filename for wpr files
    """
    remote_data_path = os.path.join(CHROMIUM_SRC, 'tools/perf/page_sets/data/',
            name_schema)
    local_path = os.path.join(os.getcwd(), 'data/wpr_source')
    p = Popen('mv {0} {1}'.format(remote_data_path, local_path), shell=True)

def modify_wpr():
    """Sets cacheable objects delay time to 0, creates pc.wpr files"""
    wpr_directory = os.path.join(os.getcwd(), 'data/wpr_source')
    wpr_path = os.path.join(CHROMIUM_SRC,
            'third_party/webpagereplay/modify_wpr_delays.py')
    p = Popen('python {0} {1}'.format(wpr_path, wpr_directory), shell=True)

def failed_url(url, output):
    """Url failed to record, place it in failed_urls

    :param url: str url
    :param output: str output of the failure
    """
    try:
        failed_set = pickle.load(open('failed_urls', 'a'))
    except IOError:
        failed_set = {}
    failed_set[url] = output
    pickle.dump(failed_set, open('failed_urls', 'a'))

def copy_wpr_to_benchmark():
    """Moves wpr and .pc.wpr (all) files from local data/wpr_source to chromium

    located: /src/tools/perf/page_sets/data/
    """
    local_path = os.path.join(os.getcwd(), 'data/wpr_source/*')
    remote_data_path = os.path.join(CHROMIUM_SRC, 'tools/perf/page_sets/data/')
    p = Popen('cp {0} {1}'.format(local_path, remote_data_path), shell=True)

def prepare_benchmark(trial_number, num_urls):
    """Simply checks to make sure the env is prepped before benchmarking

    1. Ensures that ~/page_load_time/telemetry/temp/benchmark_results.db exists
    2. Writes benchmarks to ~/src/tools/perf/benchmarks/page_cycler.py if they
       do not already exist
    """
    # Ensure benchmark_results.db exists
    telemetry_record_path = \
    '/home/jamshed/page_load_time/telemetry/temp/benchmark_results.db'
    if not os.path.isfile(telemetry_record_path):
        # Create file
        tmp = {trial_number: {}}
        pickle.dump(tmp, open(telemetry_record_path, 'wb'))
    try:
        curr_pickle = pickle.load(open(telemetry_record_path, 'rb'))
    except IOError:
        # Raise exception or rewrite benchmark_results.db?
        tmp = {trial_number: {}}
        pickle.dump(tmp, open(telemetry_record_path, 'wb'))

    # Write benchmarks to page_cycler.py
    page_cycler_path = '/home/jamshed/src/tools/perf/benchmarks/page_cycler.py'
    benchmark_template = ("@benchmark.Enabled('android')\n"
                          "class PageCyclerUrl{0}(_PageCycler):\n"
                          "    page_set = page_sets.url{0}PageSet\n\n"
        )

    with open(page_cycler_path, 'r+b') as f:
        line = f.readline()
        already_written = False
        while (line):
            if '### END OF URLS ###' in line:
                already_written = True
                break
            line = f.readline()
        if not already_written:
            # Need to write benchmarks to page_cycler.py, for now, just append
            f.write('\n\n')
            for i in range(num_urls):
                f.write(benchmark_template.format(i))
            f.write('### END OF URLS ###')

def run_benchmarks(num_urls):
    """Runs the page_cycler benchmark for each url

    Dumps data /temp/benchmark_results.db
    """
    path.append('/home/jamshed/src/tools/perf/')
    cmd = ('sudo /home/jamshed/src/tools/perf/run_benchmark '
           'page_cycler.PageCyclerUrl{0}')
    for i in range(num_urls):
        p = Popen(cmd.format(i), shell=True)
        p.wait()  # We can only load 1 url on Chrome at a time

def __main__():

    # Setup
    target_url_path = 'target_urls'
    # Clear system cache
    # Get large url set
    # Generate individual user stories
    urls = get_urls(target_url_path)
    write_page_sets(urls)
    # Record each one, measure plt
    store_url_mapping(urls)
    for i in range(len(urls)):
        test_name = 'url{0}'.format(i)
        record('{0}_page_set'.format(test_name), urls[i])
    # Move files here
    move_wpr_files('url*_page_set_*.wpr')
    # Modify wpr
    modify_wpr()
    # Move files to benchmark location
    copy_wpr_to_benchmark()
    # Prepare benchmark
    TRIAL_NUMBER = 1
    prepare_benchmark(TRIAL_NUMBER, len(urls))
    # Run benchmarks for each page set (url), N times, aggregating data
    run_benchmarks(len(urls))
    #aggregate_benchmark_data() # THEN RUN MORE TIMES
    # Convert benchmark results to har format
    # Analysis
    # Reset wpr files and benchmarks

if __name__ == '__main__':
    __main__()
