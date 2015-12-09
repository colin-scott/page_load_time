from base64 import urlsafe_b64encode, urlsafe_b64decode
from collections import Counter
from glob import glob
from os import path
import json
import sys

# TODO(jvesuna): Split up .pc files first

def compare(har1_path, har2_path):
    """Prints the status code counts of all hars in the two given paths

    Groups the same urls in each path together.

    :param har1_path: str of path to hars
    :param har2_path: str of path to hars
    """
    har_file_paths1 = get_paths(har1_path)
    har_file_paths2 = get_paths(har2_path)

    encoded_urls1 = set([get_encoded_url(har) for har in har_file_paths1])
    encoded_urls2 = set([get_encoded_url(har) for har in har_file_paths2])

    url_intersection = list(encoded_urls1.intersection(encoded_urls2))
    urls_not_in_har1 = encoded_urls2 - encoded_urls1
    urls_not_in_har2 = encoded_urls1 - encoded_urls2

    if urls_not_in_har1:
        print 'URLs missing from {0}:'.format(har1_path)
        print urls_not_in_har1
    if urls_not_in_har2:
        print 'URLs missing from {0}:'.format(har2_path)
        print urls_not_in_har2

    print '\n'
    print 'Comparing {0} urls (num urls in both dirs)'.format(
            str(len(url_intersection)))

    for encoded_url in url_intersection:
        decoded_url = urlsafe_b64decode(encoded_url)

        har1_count = get_status_code_count(
                path.join(har1_path, encoded_url + '.har'))
        har2_count = get_status_code_count(
                path.join(har2_path, encoded_url + '.har'))
        print 'Count for {0}:'.format(decoded_url)
        print  har1_count
        print  har2_count


def get_encoded_url(har_path):
    """Returns the encoded url portion of a filepath

    :param har_path: str path containing har file
    """
    if har_path[-3:] != 'har':
        raise NameError('Har_path must be a .har file: {0}'.format(har_path))

    encoded_file = har_path.split('/')[-1]
    encoded_url = encoded_file.split('.')[0]

    return encoded_url


def get_paths(file_path):
    """Return a list of paths for each file in the given path

    :param file_path: str path to directory
    """
    return glob(path.join(file_path, '*'))


def get_status_code_count(har_path):
    """Returns the counts of return codes for each har file

    :param har1_path: str of path to har file
    """
    har_json = {}

    try:
        with open(har_path) as f:
            har_json = json.load(f)
    except Exception as e:
        raise e

    har_status = get_status(har_json)
    return har_status


def get_status(har_json):
    """Returns a dict of status code counts

    :param har_json: dict of the complete har
    """
    entries = har_json['log']['entries']

    har_status_codes = Counter()

    for entry in entries:
        code = entry['response']['status']
        har_status_codes[code] += 1

    return har_status_codes


def __main__():
    args = sys.argv

    if len(args) != 3:
        raise Exception("Must provide 2 har directories")

    compare(args[1], args[2])


if __name__ == '__main__':
    __main__()
