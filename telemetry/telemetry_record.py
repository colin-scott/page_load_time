"""Record WebPageReplay, modify, and record page load times

Records running a set of target urls on the remote tablet, modifies cacheable
objects, then re-runs to see page load time differences. Writes 1 har file for
each url and modified url in page_load_time/data/hars/

Usage: sudo python telemetry_record.py -t 2

Notes:
    Assumes - telemetry is in CHROMIUM_SRC/tools/telemetry/telemetry
            - page_sets is in CHROMIUM_SRC/tools/perf/page_sets
            - modify_wpr_delays.py is in CHROMIUM_SRC/third_party/webpagereplay
            - url data set is in PLT_SRC/telemetry/targer_urls, line delimited

Workflow:
    1. Clean up old session data
    2. Read target_urls
    3. Write a page_set for each target url and its modified version to
       CHROMIUM_SRC/tools/perf/page_sets
    4. Creates *.json files to point to archive files for modified urls
       stored in CHROMIUM_SRC/tools/perf/page_sets/data as we only record
       unmodified urls
    5. Record wpr for each url and its modified version, save to
       CHROMIUM_SRC/tools/perf/page_sets/data/
    6. Move wpr files to PLT_SRC/telemetry/data/wpr_source/ for processing
    7. Modify wpr and assume a perfect cache, save to
       PLT_SRC/telemetry/data/wpr_source/
    8. Copy local wpr files to benchmark, located at
       CHROMIUM_SRC/tools/perf/page_set/data
    For each trial:
    9. Write CHROMIUM_SRC/tools/perf/benchmarks/telemetryBenchmarks.py, the
       benchmark file for each url and modified url. We have 1 class for each
       benchmark to run
    10. Run telemetryBenchmarks.PageCyclerUrl{url index}{_pc}, save data for
        each trial in PLT_SRC/telemetry/temp/. The filename is
        base64(url).trial_number{.pc}
    11. Go back to #9 for each trial
    Done trial loop
    12. Aggregte the minimum of all trials for each url and its modified url,
        write to PLT_SRC/telemetry/data/results.db
    13. Convert PLT_SRC/data/results.db to har files and move hars to
        PLT_SRC/data/har
"""
from base64 import urlsafe_b64encode, urlsafe_b64decode
from glob import glob
from optparse import OptionParser
from os import listdir, path, geteuid
from shutil import move, copy
from subprocess import Popen, PIPE, STDOUT
from sys import path, exit
import cPickle
import json
import os
import pickle
import socket

from functools import wraps
import errno
import os
import signal
from time import sleep

class TimeoutError(Exception):
    pass

def timeout(seconds=40, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(
                    '{0} ran for more than {1} seconds'.format(
                        func.__name__, seconds))
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator

CHROMIUM_SRC='/home/jamshed/src'
PLT_SRC='/home/jamshed/page_load_time'

path.append(os.path.join(CHROMIUM_SRC, 'third_party/webpagereplay'))

def prescreenUrl(url):
    """Returns bool if url is online

    :param url: str url
    """
    if url == '':
        return False

    cmd = 'wget -t 1 -T 10 {0} -O /dev/null'.format(url)
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    out, err = p.communicate()

    failed = ['Giving up', 'failed', 'FAILED', 'Connection timed out']
    if any(x in out for x in failed):
        return False
    return True

def record(page_set, url, options='--browser=android-jb-system-chrome'):
    """Runs wpr with telemetry to record an initial target page set

    :param page_set: str filename of the page set
    :param url: str url used if url fails
    :param options: chromium browser options
    """
    record_path = os.path.join(CHROMIUM_SRC, 'tools/perf/record_wpr')
    cmd = ' '.join(['sudo', record_path, options, page_set])
    print cmd
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    output, err = p.communicate()
    print output
    # Silently fail, push output to failed_urls
    if p.returncode == 1 or 'FAILED' in output or 'PASSED' not in output:
        failed_url(url, output)
        print 'Url failed: ' + url
        return 1
    return 0

def get_urls(path):
    """Returns a list of urls from path

    :param path: str relative (to PLT_SRC/telemetry) or absolute path to target
    urls
    """
    urls = []
    with open(path, 'rb') as f:
        urls = [x.strip() for x in f.readlines()]

    # Prune urls that are not working
    goodUrls = []
    badUrls = []
    for url in urls:
        if prescreenUrl(url):
            goodUrls.append(url)
        else:
            badUrls.append(url)

    with open('bad_urls', 'wb') as f:
        f.write('\n'.join(badUrls))
        f.close()

    with open(path, 'wb') as f:
        f.write('\n'.join(goodUrls))
        f.close()

    return goodUrls

def write_page_sets(urls):
    """Writes a page set file for each url (and its modified version) in urls

    Writes to CHROMIUM_SRC/tools/perf/page_sets/
    :param urls: A list of url strings
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
        test_name = 'url{0}'.format(str(i) + '_pc')
        with open('{0}{1}.py'.format(page_set_path, test_name), 'wb') as f:
            f.write(template.format(test_name, urls[i]))

def move_wpr_files(name_schema):
    """Moves wpr files from within CHROMIUM_SRC to local data directory

    :param name_schema: regex for the matching filename for wpr files
    """
    remote_data_path = os.path.join(CHROMIUM_SRC, 'tools/perf/page_sets/data/',
            name_schema)
    local_path = 'data/wpr_source/'
    # Uses shutil.move
    [move(f, local_path) for f in glob(remote_data_path)]

def make_modified_json(num_urls):
    """Creates *.json files to point to the modified archive files

    Located in CHROMIUM_SRC/tools/perf/page_sets/data/
    :param num_urls: int for the number of target urls
    TODO: add sha1 to remove runtime WARNING
    """
    json_path = os.path.join(CHROMIUM_SRC, 'tools/perf/page_sets/data/')
    json_template = ('{{'
            '"description": "Describes the Web Page Replay archives for a user '
            'story set. Dont edit by hand! Use record_wpr for updating.", '
            '"archives": {{ "url{0}_page_set_000.wpr": ["url{0}"]}}}}\n')
    for i in range(num_urls):
        modified_name = str(i) + '_pc'
        file_name = 'url{0}_page_set.json'
        with open('{0}{1}'.format(json_path,
            file_name.format(modified_name)), 'wb') as f:
            f.write(json_template.format(modified_name))

def modify_wpr():
    """Sets cacheable objects delay time to 0, creates pc.wpr files

    Note: *.pc.wpr files are converted to url{index}_pc.wpr, which lets
    them be treated like regular urls.
    """
    wpr_directory = 'data/wpr_source'
    wpr_path = os.path.join(CHROMIUM_SRC,
            'third_party/webpagereplay/modify_wpr_delays.py')
    p = Popen('python {0} {1}'.format(wpr_path, wpr_directory), shell=True)
    p.wait()
    pc_files = filter(lambda x: 'pc' in x, os.listdir(wpr_directory))
    for pc_file in pc_files:
        insert_index = pc_file.find('_page_set')
        new_file = pc_file[:insert_index] + '_pc' + pc_file[insert_index:]
        new_file = new_file.replace('.pc', '')
        # Uses shutil.move
        move(os.path.join(wpr_directory, pc_file), os.path.join(wpr_directory,
            new_file))

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
    """Copies wpr and _pc.wpr (all) files from local data/wpr_source to chromium

    located: CHROMIUM_SRC/tools/perf/page_sets/data/
    """
    local_path = 'data/wpr_source/*'
    remote_data_path = os.path.join(CHROMIUM_SRC, 'tools/perf/page_sets/data/')
    # Uses shutil.copy
    [copy(f, remote_data_path) for f in glob(local_path)]

def prepare_benchmark(trial_number, num_urls):
    """Writes telemetryBenchmarks.py, the benchmark for Chromium to run

    1. Writes benchmarks to
       CHROMIUM_SRC/tools/perf/benchmarks/telemetryBenchmarks.py if they do not
       already exist
    :param trial_number: int for the number of this trial run
    :param num_urls: int of the number of urls to run through
    """
    telemetry_page_cycler_path = os.path.join(CHROMIUM_SRC,
            'tools/perf/benchmarks/telemetryBenchmarks.py')

    class_template = ("from measurements import page_cycler\n"
            "import page_sets\n"
            "from telemetry import benchmark\n\n"
            "class _PageCycler(benchmark.Benchmark):\n"
            "    options = {'pageset_repeat': 6}\n"
            "    @classmethod\n"
            "    def AddBenchmarkCommandLineArgs(cls, parser):\n"
            "        parser.add_option('--v8-object-stats',\n"
            "            action='store_true',\n"
            "            help='Enable detailed V8 object statistics.')\n"
            "        parser.add_option('--user-server-delay')\n"
            "        print 'IN BENCHMARK'\n"
            "        parser.add_option('--report-speed-index',\n"
            "            action='store_true',\n"
            "            help='Enable the speed index metric.')\n"
            "        parser.add_option('--cold-load-percent', type='int', "
                         "default=50,\n"
            "            help='%d of page visits for which a cold load is "
                         "forced')\n\n"
            "    def CreatePageTest(self, options):\n"
            "        return page_cycler.PageCycler(\n"
            "            page_repeat = options.page_repeat,\n"
            "            pageset_repeat = options.pageset_repeat,\n"
            "            cold_load_percent = options.cold_load_percent,\n"
            "            record_v8_object_stats = options.v8_object_stats,\n"
            "            report_speed_index = options.report_speed_index)\n\n")

    benchmark_template = ("@benchmark.Enabled('android')\n"
                          "class PageCyclerUrl{0}(_PageCycler):\n"
                          "    print 'Using page cycler'\n"
                          "    page_set = page_sets.url{0}PageSet\n\n")

    with open(telemetry_page_cycler_path, 'w') as f:
        f.write(class_template)
        for i in range(num_urls):
            f.write(benchmark_template.format(i))
            f.write(benchmark_template.format(str(i) + '_pc'))

@timeout(1000)  # About 15 minutes
def bindSocket():
    """Binds to a socket and returns information from a benchmark"""
    # Create the socket
    # This allows the benchmark to pass data back here
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.remove("/tmp/telemetrySocket")
    except OSError:
        pass
    s.bind("/tmp/telemetrySocket")
    s.listen(1)


    def signal_handler(signum, frame):
            raise Exception("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(900)
    try:
        conn, addr = s.accept()  # Still gets stuck here
    except Exception as e:
        raise TimeoutError('Timed out!!')

    tmp_results = ''
    while 1:
        data = conn.recv(1024)
        tmp_results += data
        if not data:
            break
    conn.close()
    return tmp_results

@timeout(1000)  # About 15 minutes
def get_benchmark_result(cmd):
    """Runs the benchmark cmd and returns the result, or throws an error if the

    benchmark timesout
    :param cmd: str benchmark command to run
    """
    print "running benchmark with command:"
    print cmd
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    out, err = p.communicate() # We can only load 1 url on Chrome at a time
    print out
    return out, err, p.returncode

def run_benchmarks(urls, urlIndices, trial_number):
    """Runs the telemetryBenchmarks benchmark for each url and modified url

    Dumps data temp/
    Sample filename: base64('http://jamnoise.com').1.pc
    Sample output:
    {'http://jamnoise.com':
        {'cold_times':
            {'trial0': [1,2,3,4,5]}
        }
    }
    :param urls: a list of str urls to run through
    :param urlIndices: a list of int indices from the original list
    :param trial_number: the current trial number
    """
    path.append(os.path.join(CHROMIUM_SRC, 'tools/perf/'))
    benchmark_path = os.path.join(CHROMIUM_SRC, 'tools/perf/run_benchmark')
    output_path = 'temp'
    trial_key = 'trial{0}'.format(trial_number)

    cmd = ('sudo ' + benchmark_path + ' telemetryBenchmarks.url{0}')
    for i in urlIndices:
        #p = Popen(
            #cmd.format(i), shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)

        try:
            out, err, returncode = get_benchmark_result(cmd.format(i))
            timeout = False
            print 'successfully ran benchmark for url' + str(i)
        except TimeoutError:
            # Benchmark failed
            print 'Benchmark Timeout!'
            out = ''
            returncode = 1
            timeout = True

        #out, err = p.communicate() # We can only load 1 url on Chrome at a time

        failed = ['FAILED']
        #success = ['RESULT cold_times']
        if returncode != 0 or any(x in out for x in failed) or timeout:
                #not any(x in out for x in success) or timeout: # Add returncode != 0
            # If a benchmark fails, remove its corresponding wpr file, and act
            # as if it didn't exist
            # Remove from data/wpr_source

            print 'Benchmark {0} failed'.format(i)
            print 'return code is ' + str(returncode)
            print out
            print '======='
            print err
            #import ipdb; ipdb.set_trace()
            urlName = 'url{0}_page_set_000.wpr'.format(i)
            urlpcName = 'url{0}_pc_page_set_000.wpr'.format(i)
            urlFilePath = os.path.join('data/wpr_source',urlName)
            urlpcFilePath = os.path.join('data/wpr_source',urlpcName)
            urlCmd = 'rm -f {0}'.format(urlFilePath)
            urlpcCmd = 'rm -f {0}'.format(urlpcFilePath)
            print 'Removing: {0}, {1}'.format(urlFilePath, urlpcFilePath)
            commands = [
                    'rm -f {0}'.format(urlFilePath),
                    'rm -f {0}'.format(urlpcFilePath)
                    ]
            for cmdss in commands:
                p = Popen(cmdss, shell=True)
                p.wait()
            # Skip the rest of this url
            print "Moving on!"
            continue

        # Parse data
        tmp_path = 'temp/tmp_benchmark_result_json'
        with open(tmp_path, 'rb') as f:
            tmp_json = json.load(f)
        benchmark_results = tmp_json['values']
        commands = [
            'rm -f ~/page_load_time/telemetry/temp/tmp_benchmark_result_json',
                ]
        for cmds in commands:
            p = Popen(cmds, shell=True)
            p.wait()

        output = {urls[i]: {'cold_times': {trial_key: benchmark_results}}}
        output_file = os.path.join(output_path, urlsafe_b64encode(urls[i]))
        output_file += '.' + str(trial_number)
        try:
            with open(output_file, 'w') as f:
                json.dump(output, f)
        except IOError:
            raise IOError('Unable to write to {0}'.format(output_file))


        ############### Now run for Perfect Cache file ################

        #p = Popen(
            #cmd.format(str(i) + '_pc'),
            #shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)

        try:
            out, err, returncode = get_benchmark_result(cmd.format(str(i) + '_pc'))
            timeout = False
            print 'successfully ran benchmark for url' + str(i) + '_pc'
        except TimeoutError:
            # Benchmark failed
            print 'Benchmark Timeout!'
            out = ''
            returncode = 1
            timeout = True

        #out, err = p.communicate() # We can only load 1 url on Chrome at a time

        failed = ['FAILED']
        #success = ['RESULT cold_times']
        if returncode != 0 or any(x in out for x in failed) or timeout:
        #if returncode != 0 or any(x in out for x in failed) or \
                #not any(x in out for x in success) or timeout:
            # If a benchmark fails, remove its corresponding wpr file, and act
            # as if it didn't exist
            # Remove from data/wpr_source

            print 'Benchmark {0}_pc failed'.format(i)
            print out
            print '======='
            print err
            #import ipdb; ipdb.set_trace()
            urlName = 'url{0}_page_set_000.wpr'.format(i)
            urlpcName = 'url{0}_pc_page_set_000.wpr'.format(i)
            urlFilePath = os.path.join('data/wpr_source',urlName)
            urlpcFilePath = os.path.join('data/wpr_source',urlpcName)
            urlCmd = 'rm -f {0}'.format(urlFilePath)
            urlpcCmd = 'rm -f {0}'.format(urlpcFilePath)
            print 'Removing: {0}, {1}'.format(urlFilePath, urlpcFilePath)
            commands = [
                    'rm -f {0}'.format(urlFilePath),
                    'rm -f {0}'.format(urlpcFilePath)
                    ]
            for cmdss in commands:
               p = Popen(cmdss, shell=True)
               p.wait()
            # Skip the rest of this url
            print "Moving on!"
            continue


        # Parse data
        tmp_path = 'temp/tmp_benchmark_result_json'
        # import ipdb; ipdb.set_trace()
        with open(tmp_path, 'rb') as f:
            tmp_json = json.load(f)
        #tmp_json = json.loads(tmp_results)
        benchmark_results = tmp_json['values']

        commands = [
            'rm -f ~/page_load_time/telemetry/temp/tmp_benchmark_result_json',
                ]
        for cmds in commands:
            p = Popen(cmds, shell=True)
            p.wait()

        output = {urls[i]: {'cold_times': {trial_key: benchmark_results}}}
        output_file = os.path.join(output_path, urlsafe_b64encode(urls[i]))
        output_file +=  '.' + str(trial_number) + '.pc'
        try:
            with open(output_file, 'w') as f:
                json.dump(output, f)
        except IOError:
            raise IOError('Unable to write to {0}'.format(output_file))

def reset_old_files():
    """Deletes old files to make way for a new run

    Removes:
    CHROMIUM_SRC/tools/perf/page_sets/url*
    CHROMIUM_SRC/tools/perf/page_sets/data/url*
    CHROMIUM_SRC/tools/perf/benchmarks/telemetryBenchmarks.py
    PLT_SRC/telemetry/data/wpr_source/*
    PLT_SRC/telemetry/data/results.db
    PLT_SRC/data/har/*
    PLT_SRC/data/replay/*
    PLT_SRC/telemetry/temp/*
    """
    commands = [
        'rm -f {0}/tools/perf/page_sets/url*'.format(CHROMIUM_SRC),
        'rm -f {0}/tools/perf/page_sets/data/url*'.format(CHROMIUM_SRC),
        'rm -f ' \
        '{0}/tools/perf/benchmarks/telemetryBenchmarks.py'.format(CHROMIUM_SRC),
        'rm -f data/wpr_source/*',
        'rm -f temp/*',
        'rm -f data/results.db',
        'rm -f {0}/data/har/*'.format(PLT_SRC),
        'rm -f {0}/data/replay/*'.format(PLT_SRC),
            ]

    for cmd in commands:
        p = Popen(cmd, shell=True)
        p.wait()

def trial_reset():
    """Deletes files between trials

    Removes:
    temp/*
    """
    commands = [
        'rm -f temp/*',
        ]

    for cmd in commands:
        p = Popen(cmd, shell=True)
        p.wait()

def aggregate_min_results():
    """Writes data/results.db with the min of each url and pc url

    Format of output:
    {'http://jamnoise.com':
        {'cold_time': 314.159,
         'modified_cold_time': '300.201'},
         ...
    }
    """
    aggregated_data = {}
    data_path = 'temp/*'
    data_files = [f for f in glob(data_path) if '.json' not in f]
    sorted_files = sorted(data_files)

    curr_url = None
    for tmp_file in sorted_files:
        data = {}
        with open(tmp_file) as f:
            data = json.load(f)
        if data == {}:
            raise IOError('Problem reading {0}'.format(tmp_file))
        trial = int(tmp_file.split('.')[1])
        url = data.keys()[0]
        values = data[url]['cold_times']['trial{0}'.format(trial)]
        min_value = min(values)

        is_pc = False
        if '.pc' in tmp_file:
            is_pc = True

        if url not in aggregated_data:
            aggregated_data[url] = {'cold_time': float('inf'),
                                   'modified_cold_time': float('inf')}
        # Modified cold time
        if is_pc:
            aggregated_data[url]['modified_cold_time'] = \
                    min(aggregated_data[url]['modified_cold_time'],
                            min_value)
        # Regular cold time
        else:
            aggregated_data[url]['cold_time'] = \
                    min(aggregated_data[url]['cold_time'],
                            min_value)

    result_path = 'data/results.db'
    pickle.dump(aggregated_data, open(result_path, 'w'))


def generate_hars():
    """Merge plts and wprs into a har file

    Stores 2 .har files per url (regular and modified) in data/replay/
    """
    results_path = 'data/results.db'
    results_data = {}
    try:
        results_data = pickle.load(open(results_path, 'rb'))
    except IOError:
        raise IOError('Could not read from {0}'.format(results_path))

    wpr_path = 'data/wpr_source'
    wpr_files = filter(lambda x: '.wpr' in x, os.listdir(wpr_path))
    print wpr_files
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
        wpr_host = None
        # print "Looping here"
        print wpr_file
        for key, value_lst in zip(curr_wpr.keys(), curr_wpr.values()):
            matches = [full_url for full_url in results_data.keys() if \
                    key.host in full_url]
            if matches:
                if len(matches) != 1:
                    print "Found 2 urls with the same name!"
                    print matches
                    continue
                assert len(matches) == 1, ('Found more than 1 match for'
                        ' {0}'.format(matches))
                agg_key = matches[0]
                # Found a match!
                curr_har_dict['log']['pages'][0]['id'] = key.host
                curr_har_dict['log']['pages'][0]['title'] = key.host  # Set both
                if '_pc' in wpr_file:
                    wpr_host = urlsafe_b64encode(agg_key) + '.pc'
                    # It's a modified wpr file
                    curr_har_dict['log']['pages'][0]['pageTimings']['onLoad'] \
                            = results_data[agg_key]['modified_cold_time']
                else:
                    wpr_host = urlsafe_b64encode(agg_key)
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
            # TODO: Correct way to calculate headersSize and bodySize?
            headerSize = 0  # Need to find this in value_lst
            bodySize = 0  # Need to find this in value_lst
            # Create each element's header list
            tmp_header_lst = []
            for name, value in value_lst.headers:
                if 'content-length' in name:
                    bodySize = int(value)
                headerSize += len(name) + len(value)  # This should be verified
                tmp_header_lst.append({'name': name, 'value': value})

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
            curr_entry = tmp_entry.copy()
            curr_entry['request']['method'] = method
            curr_entry['request']['url'] = element_url
            curr_entry['response']['status'] = status
            curr_entry['response']['headers'] = tmp_header_lst
            curr_entry['response']['headersSize'] = headerSize
            curr_entry['response']['bodySize'] = bodySize

            curr_har_dict['log']['entries'].append(curr_entry)

        # Write to har file
        if wpr_host is None:
            print 'Could not create host from url: {0}'.format(wpr_file)
            continue
            #raise KeyError(
                    #'Could not create host from url: {0}'.format(wpr_file))

        har_path = '../data/replay/'
        #file_name = har_path + wpr_host + '.1.har'  # Used for replays
        file_name = har_path + wpr_host + '.har'  # Modified for har processing
        with open(file_name, 'wb') as f:
            try:
                json.dump(curr_har_dict, f)
            except:
                # Silently fail
                print "Unable to write har file: " + str(file_name)

def write_valids():
    """Creates PLT_SRC/data/filtered_stats/valids.txt

    valids.txt contains the valid urls to be included in data analysis
    Each line is:
    url path/to/har/file
    Note: does not include pc files
    """
    har_path = os.path.join(PLT_SRC, 'data/replay/*')
    valid_path = '../data/filtered_stats/valids.txt'

    #har_files = [f for f in glob(har_path) if '.pc' not in f]
    har_files = [f for f in glob(har_path)]  # Include pc files?
    urls = \
        [urlsafe_b64decode(f.split('/')[-1].split('.')[0]) for f in har_files]
    with open(valid_path, 'w') as f:
        for url, url_har_path in zip(urls, har_files):
            f.write('{0} {1}\n'.format(url, url_har_path))

def __main__():

    # Must run as root
    if geteuid() != 0:
        print "Must run as root"
        exit(1)
    # Get the number of trials to run for each url and modified url
    parser = OptionParser()
    parser.add_option('-t', '--trials', action='store', dest='trials',
        help='number of trials to run each url and modified url')
    options, args = parser.parse_args()
    if options.trials is None:
        parser.error('Must specify number of trials with -t')
    NUMBER_OF_TRIALS = int(options.trials)
    # Clean up old sessions
    reset_old_files()
    # Setup
    target_url_path = 'target_urls'
    # Get url set
    urls = get_urls(target_url_path)
    # Generate individual user stories
    write_page_sets(urls)
    make_modified_json(len(urls))
    # Record each one, measure plt
    working_urls = []
    working_url_indices = []
    bad_urls = []
    for i in range(len(urls)):
        print 'Recording url {0}'.format(i)
        test_name = 'url{0}'.format(i)
        success = record('{0}_page_set'.format(test_name), urls[i])
        if success == 0:
            # Good url
            working_urls.append(urls[i])
            working_url_indices.append(i)
        elif success == 1:
            # Bad url
            bad_urls.append(urls[i])
    # Write out bad urls
    for url in bad_urls:
        failed_url(url, 'Recording error')
    # Move files here
    move_wpr_files('url*_page_set_*.wpr')
    # Modify wpr
    modify_wpr()
    # Move files to benchmark location
    copy_wpr_to_benchmark()
    # Run trials
    for trial_number in range(NUMBER_OF_TRIALS):
        print 'preparing benchmark trial#{0}'.format(trial_number)
        # Prepare benchmark
        prepare_benchmark(trial_number, len(urls))
        # Run benchmarks for each page set (url), N times, aggregating data
        print 'running benchmark'
        run_benchmarks(urls, working_url_indices, trial_number)
    # Aggregate benchmark data
    print 'Aggregating min results'
    aggregate_min_results()
    # Convert benchmark results to har format
    print 'Generating hars'
    generate_hars()
    # Analysis
    print 'Writing valids'
    write_valids()

if __name__ == '__main__':
    __main__()
