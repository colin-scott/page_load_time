"""Record WebPageReplay, modify, and record page load times

Records running a set of target urls on the remote tablet, modifies cacheable
objects, then re-runs to see page load time differences.

Usage: sudo python telemetry_record.py

Notes:
    Assumes - telemetry is in CHROMIUM_SRC/tools/telemetry/telemetry
            - page_sets is in CHROMIUM_SRC/tools/perf/page_sets
            - modify_wpr_delays.py is in CHROMIUM_SRC/third_party/webpagereplay

TODO: Make sure to only get the most recent wpr file when moving / modifying
TODO: Clean up path dependencies, move them to the top
"""
from os import listdir, path
from re import findall
from subprocess import Popen, PIPE, STDOUT
from sys import path
import cPickle
import json
import os
import pickle
import re

path.append('/home/jamshed/src/third_party/webpagereplay')

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
        # Write modified version
        test_name = 'url{0}'.format('999999' + str(i))
        with open('{0}{1}.py'.format(page_set_path, test_name), 'wb') as f:
            f.write(template.format(test_name, urls[i]))

def store_url_mapping(url_list):
    """Stores a mapping from index to url to be used later.

    Saved to data/url_mapping.db: {index: url,...}
    :param url_list: a list of each url to store
    """
    url_mapping = {}
    for i in range(len(url_list)):
        url_mapping[i] = url_list[i]
        # Write modified version
        url_mapping[int('999999' + str(i))] = url_list[i]
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

def make_modified_json(num_urls):
    """Creates *.json files to point to the right archive files

    Located in ~/src/tools/perf/page_sets/data
    :param num_urls: int for the number of target urls
    TODO: add sha1?
    """
    json_path = '/home/jamshed/src/tools/perf/page_sets/data/'
    json_template = ('{{'
            '"description": "Describes the Web Page Replay archives for a user '
            'story set. Dont edit by hand! Use record_wpr for updating.", '
            '"archives": {{ "url{0}_page_set_000.wpr": ["url{0}"]}}}}\n')
    for i in range(num_urls):
        modified_name = '999999' + str(i)
        file_name = 'url{0}_page_set.json'
        with open('{0}{1}'.format(json_path,
            file_name.format(modified_name)), 'wb') as f:
            f.write(json_template.format(modified_name))

def modify_wpr():
    """Sets cacheable objects delay time to 0, creates pc.wpr files

    Note: *.pc.wpr files are converted to 999999 + str(url name), which lets
    them be treated like regular urls. Just know that six 9's indicate a
    modified wpr file
    TODO: Fix the 999999 notation
    """
    wpr_directory = os.path.join(os.getcwd(), 'data/wpr_source')
    wpr_path = os.path.join(CHROMIUM_SRC,
            'third_party/webpagereplay/modify_wpr_delays.py')
    p = Popen('python {0} {1}'.format(wpr_path, wpr_directory), shell=True)
    p.wait()
    pc_files = filter(lambda x: 'pc' in x, os.listdir(wpr_directory))
    for pc_file in pc_files:
        new_file = re.sub(r'url(\d+)*', r'url999999\1', pc_file).replace('.pc',
                '')
        p = Popen('mv {0}/{1} {0}/{2}'.format(wpr_directory, pc_file, new_file),
                shell=True)
        p.wait()

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
    NOTE: You may need to clear out the end of
    ~/src/tools/perf/benchmarks/page_cycler.py for a clean start!
    :param trial_number: int for the number of this trial run
    :param num_urls: int of the number of urls to run through
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
                          "    page_set = page_sets.url{0}PageSet\n\n")

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
                f.write(benchmark_template.format('999999' + str(i)))
            f.write('### END OF URLS ###')

def run_benchmarks(num_urls):
    """Runs the page_cycler benchmark for each url

    Dumps data /temp/benchmark_results.db
    :param num_urls: int of the number of urls to run through
    """
    path.append('/home/jamshed/src/tools/perf/')
    cmd = ('sudo /home/jamshed/src/tools/perf/run_benchmark '
           'page_cycler.PageCyclerUrl{0}')
    for i in range(num_urls):
        p = Popen(cmd.format(i), shell=True)
        p.wait()  # We can only load 1 url on Chrome at a time
        # Also run the modified version
        p = Popen(cmd.format('999999' + str(i)), shell=True)
        p.wait()  # We can only load 1 url on Chrome at a time

def aggregate_benchmark_data():
    """Merges data from /temp/benchmark_results.db with /temp/aggregate.db

    Note: temp/aggregate.db looks like {'http://jamnoise.com':
                                           {'cold_times':
                                               {'trial1': [data],...}}}
    """
    benchmark_results = '/data/benchmark_results.db'
    benchmark_result_path = \
            '/home/jamshed/page_load_time/telemetry/temp/benchmark_results.db'
    aggregate_path = \
            '/home/jamshed/page_load_time/telemetry/temp/aggregate.db'

    # Get current benchmark data and aggregate data
    if not os.path.isfile(benchmark_result_path):
        # Ensure path exists
        tmp = {}
        pickle.dump(tmp, open(benchmark_result_path, 'wb'))
    if not os.path.isfile(aggregate_path):
        # Ensure path exists
        tmp = {}
        pickle.dump(tmp, open(aggregate_path, 'wb'))
    try:
        curr_benchmark_data = pickle.load(open(benchmark_result_path, 'rb'))
        curr_aggregate_data = pickle.load(open(aggregate_path, 'rb'))
    except IOError:
        # Raise exception or rewrite benchmark_results.db?
        raise IOError('Failed to read benchmark or aggregate data path')

    # Get url mappings
    url_mappings = {}
    try:
        url_mappings = pickle.load(open('data/url_mapping.db', 'rb'))
    except IOError:
        raise IOError('Failed to read url mapping from data/url_mapping.db')
    if url_mappings == {}:
        raise KeyError('url_mappings is empty')

    # Enforce benchmark data only has one trial
    if len(curr_benchmark_data.keys()) != 1:
        raise KeyError('Current benchmark data contains > 1 trial')

    # Merge data, use url mapping
    trial_number = curr_benchmark_data.keys()[0]
    trial_name = 'trial{0}'.format(trial_number)
    print "Trial: " + str(trial_number)

    url_regex = 'url(\d+)'
    for urlId in curr_benchmark_data[trial_number]:
        measurement = 'cold_times'
        if '999999' in str(urlId):
            measurement = 'modified_cold_times'

        curr_id = int(findall(url_regex, urlId)[0])
        url_name = url_mappings[curr_id]
        cold_time_data = \
        eval(str(curr_benchmark_data[trial_number][urlId]['cold_times']))
        if url_name in curr_aggregate_data.keys():
            if measurement in curr_aggregate_data[url_name].keys():
                if trial_name in \
                        curr_aggregate_data[url_name][measurement].keys():
                    raise KeyError('Trial {0} already exists! Please remove it'
                                   .format(trial_name))
                else:
                    curr_aggregate_data[url_name][measurement][trial_name] = \
                            cold_time_data
            else:
                curr_aggregate_data[url_name][measurement] = {
                        trial_name: cold_time_data
                        }
        else:
            curr_aggregate_data[url_name] = {measurement: {
                                                trial_name: cold_time_data
                                            }
                                        }
    # Write back to aggregate
    pickle.dump(curr_aggregate_data, open(aggregate_path, 'wb'))

def reset_old_files():
    """Deletes old files to make way for a new run

    Removes:
    /home/jamshed/src/tools/perf/page_sets/url*
    /home/jamshed/src/tools/perf/page_sets/data/url*
    /home/jamshed/page_load_time/telemetry/data/wpr_source/*
    """
    commands = [
        'rm -f /home/jamshed/src/tools/perf/page_sets/url*',
        'rm -f /home/jamshed/src/tools/perf/page_sets/data/url*',
        'rm -f /home/jamshed/page_load_time/telemetry/data/wpr_source/*',
        'rm -f /home/jamshed/page_load_time/telemetry/temp/aggregate.db',
        'rm -f '
        '/home/jamshed/page_load_time/telemetry/temp/benchmark_results.db',
        'rm -f /home/jamshed/page_load_time/telemetry/data/results.db',
        'rm -f /home/jamshed/page_load_time/data/har/*',
            ]

    for cmd in commands:
        p = Popen(cmd, shell=True)
        p.wait()

def trial_reset():
    """Deletes files between trials

    Removes:
    /home/jamshed/page_load_time/telemetry/benchmark_results.db
    """
    commands = [
        'rm -f '
        '/home/jamshed/page_load_time/telemetry/temp/benchmark_results.db'
        ]

    for cmd in commands:
        p = Popen(cmd, shell=True)
        p.wait()

def get_min_results():
    """Converts temp/aggregate.db into results.db, only taking min times

    Format of output:
    {'http://jamnoise.com':
        {'cold_time': 314.159,
         'modified_cold_time': '300.201'},
         ...
    }
    """
    aggregate_path = \
            '/home/jamshed/page_load_time/telemetry/temp/aggregate.db'
    aggregate_data = {}
    try:
        aggregate_data = pickle.load(open(aggregate_path, 'rb'))
    except IOError:
        raise IOError('Could not read from {0}'.format(aggregate_path))

    min_data = {}

    for url in aggregate_data:
        url_min_results = {}
        url_results = aggregate_data[url]
        cold_time_min = None
        modified_time_min = None
        if 'cold_times' in url_results:
            for trial in url_results['cold_times']:
                if type(url_results['cold_times'][trial]) == float or \
                        type(url_results['cold_times'][trial]) == int:
                            url_results['cold_times'][trial] = \
                            [url_results['cold_times'][trial]]
                if cold_time_min is None:
                    cold_time_min = min(url_results['cold_times'][trial])
                else:
                    cold_time_min = min(cold_time_min,
                            min(url_results['cold_times'][trial]))
        if 'modified_cold_times' in url_results:
            for trial in url_results['modified_cold_times']:
                if type(url_results['modified_cold_times'][trial]) == float or \
                        type(url_results['modified_cold_times'][trial]) == int:
                            url_results['modified_cold_times'][trial] = \
                            [url_results['modified_cold_times'][trial]]
                if modified_time_min is None:
                    modified_time_min = \
                        min(url_results['modified_cold_times'][trial])
                else:
                    modified_time_min = min(cold_time_min,
                            min(url_results['modified_cold_times'][trial]))
        url_min_results['cold_time'] = cold_time_min
        url_min_results['modified_cold_time'] = modified_time_min
        min_data[url] = url_min_results

    pickle.dump(min_data, open('data/results.db', 'wb'))

def generate_hars():
    """Merge plts and wprs into a har file

    Stores 2 .har files per url in /home/jamshed/page_load_time/data/har/
    One named with the original url, and one appended with '_modified'
    """
    results_path = \
            '/home/jamshed/page_load_time/telemetry/data/results.db'
    results_data = {}
    try:
        results_data = pickle.load(open(results_path, 'rb'))
    except IOError:
        raise IOError('Could not read from {0}'.format(results_path))

    wpr_path = os.path.join(os.getcwd(), 'data/wpr_source')
    wpr_files = filter(lambda x: '.wpr' in x, os.listdir(wpr_path))
    for wpr_file in wpr_files:
        curr_wpr = cPickle.load(open(os.path.join(wpr_path, wpr_file), 'rb'))
        curr_har_dict = {'log':
                            {'pages':
                                [{'id': '',
                                 'title': '',
                                 'pageTimings': {
                                        'onContentLoad': None,
                                        'onLoad': None
                                        }
                                 }],
                             'entries': []
                            }
                        }
        tmp_entry = {
                    'request': {
                        'method': None,
                        'url': None
                        },
                    'response': {
                            'status': None,
                            'headers': [],
                            'headersSize': None,
                            'bodySize': None
                        }
                }
        wpr_host = None
        for key, value_lst in zip(curr_wpr.keys(), curr_wpr.values()):
            matches = [full_url for full_url in results_data.keys() if \
                    key.host in full_url]
            if matches:
                assert len(matches) == 1, ('Found more than 1 match for'
                        ' {0}'.format(matches))
                agg_key = matches[0]
                # Found a match!
                curr_har_dict['log']['pages'][0]['id'] = key.host
                curr_har_dict['log']['pages'][0]['title'] = key.host  # Set both
                if '999999' in wpr_file:
                    wpr_host = key.host + '_modified'
                    # It's a modified wpr file
                    curr_har_dict['log']['pages'][0]['pageTimings']['onLoad'] \
                            = results_data[agg_key]['modified_cold_time']
                else:
                    wpr_host = key.host
                    # It's an original wpr file
                    curr_har_dict['log']['pages'][0]['pageTimings']['onLoad'] \
                            = results_data[agg_key]['cold_time']
            else:
                # This website is loading a third party object
                # Still include this in the har file
                pass
            # Add to each element to entries
            # Request data
            method = key.command
            element_url = key.host + key.full_path
            # Response data
            status = value_lst.status
            headerSize = 0  # Need to find this in value_lst
            bodySize = 0  # Need to find this in value_lst
            # Create each element's header list
            tmp_header_lst = []
            for name, value in value_lst.headers:
                tmp_header_lst.append({'name': name, 'value': value})

            curr_entry = tmp_entry.copy()
            curr_entry['request']['method'] = method
            curr_entry['request']['url'] = element_url
            curr_entry['response']['status'] = status
            curr_entry['response']['headers'] = tmp_header_lst
            curr_entry['response']['headerSize'] = headerSize
            curr_entry['response']['bodySize'] = bodySize

            curr_har_dict['log']['entries'].append(curr_entry)

        # Write to har file
        if wpr_host is None:
            raise KeyError('Could not find host in aggregate.db')

        har_path = '../data/har/'
        file_name = har_path + wpr_host
        with open(file_name, 'wb') as f:
            json.dump(curr_har_dict, f)


def __main__():

    # Clean up old sessions
    # Also be sure to clean benchmarks/page_cycler.py
    reset_old_files()
    # Setup
    target_url_path = 'target_urls'
    # Clear system cache
    # Get large url set
    # Generate individual user stories
    urls = get_urls(target_url_path)
    write_page_sets(urls)
    make_modified_json(len(urls))
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
    # Clean out aggregate benchmark data?
    NUMBER_OF_TRIALS = 2
    for trial_number in range(NUMBER_OF_TRIALS):
        # Prepare benchmark
        prepare_benchmark(trial_number, len(urls))
        # Run benchmarks for each page set (url), N times, aggregating data
        run_benchmarks(len(urls))
        # Aggregate benchmark data
        aggregate_benchmark_data()
        # Clean up this session
        trial_reset()
    get_min_results()
    # Convert benchmark results to har format
    generate_hars()
    # Analysis

if __name__ == '__main__':
    __main__()
