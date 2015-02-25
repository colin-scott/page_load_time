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
        test_name = 'test{0}'.format(i)
        with open('{0}{1}.py'.format(page_set_path, test_name), 'wb') as f:
            f.write(template.format(test_name, urls[i]))

def move_wpr_files(name_schema):
    """Moves wpr files from within CHROMIUM_SRC to local data directory

    :param name_schema: regex for the matching filename for wpr files
    """
    remote_data_path = os.path.join(CHROMIUM_SRC, 'tools/perf/page_sets/data/',
            name_schema)
    local_path = os.path.join(os.getcwd(), 'data/')
    p = Popen('mv {0} {1}'.format(remote_data_path, local_path), shell=True)

def modify_wpr():
    """Sets cacheable objects delay time to 0, creates  pc.wpr files"""
    wpr_directory = os.path.join(os.getcwd(), 'data/')
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


def __main__():

    # Setup
    target_url_path = 'target_urls'
    # Clear system cache
    # Get large url set
    # Generate individual user stories
    urls = get_urls(target_url_path)
    write_page_sets(urls)
    # Record each one, measure plt
    for i in range(len(urls)):
        test_name = 'test{0}'.format(i)
        record('{0}_page_set'.format(test_name), urls[i])
    # Move files here
    move_wpr_files('test*_page_set_*.wpr')
    # Modify wpr
    modify_wpr()
    # Re-record, measure plt
    # Analysis

if __name__ == '__main__':
    __main__()
