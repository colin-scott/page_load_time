from base64 import urlsafe_b64encode, urlsafe_b64decode
from collections import Counter
from glob import glob
from os import path
import json
import sys

from har_profiler import *  # Better to specify methods than import *

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

        har1_dict = get_har_dict_from_file(
                path.join(har1_path, encoded_url + '.har'))
        har2_dict = get_har_dict_from_file(
                path.join(har2_path, encoded_url + '.har'))

        har1_status_code_count = get_status_code_count(har1_dict)
        har2_status_code_count = get_status_code_count(har2_dict)

        har1_response_size = get_total_body_size(har1_dict)
        har2_response_size = get_total_body_size(har2_dict)

        har1_resource_type_count = get_resource_count(har1_dict)
        har2_resource_type_count = get_resource_count(har2_dict)

        print 'Count for {0}:'.format(decoded_url)
        print  har1_status_code_count
        print  har2_status_code_count
        print 'Resource type counts for {0}:'.format(decoded_url)
        print har1_resource_type_count
        print har2_resource_type_count
        print 'Response body sizes'
        print har1_response_size
        print har2_response_size
        print '======================================================='


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


def __main__():
    args = sys.argv

    if len(args) != 3:
        raise Exception("Must provide 2 har directories")

    compare(args[1], args[2])


if __name__ == '__main__':
    __main__()
