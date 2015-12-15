from __builtin__ import any
from glob import glob
from os import path
import pickle
import sys

sys.path.append('/Users/jamshed/tmp/web-page-replay')

def compare(mobile_path, desktop_path):
    """Returns the set intersection and outliers for all wpr resources

    :param mobile_path: str path to wpr-mobile directory
    :param desktop_path: str path to wpr-desktop directory
    """
    mobile_files = glob(path.join(mobile_path,'*.inter'))
    desktop_files = glob(path.join(desktop_path, '*.inter'))
    mobile_files.sort()
    desktop_files.sort()

    assert len(mobile_files) == len(desktop_files), 'Directories must have the '
    'same number of files'

    for mobile_file in mobile_files:
        file_name = mobile_file.split('/')[-1]
        if any(file_name in x for x in desktop_files):
            desktop_file = path.join(desktop_path, file_name)

            mobile_dict = pickle.load(open(mobile_file, 'rb'))['data']
            mobile_requests = set(mobile_dict[0])
            mobile_responses = set(mobile_dict[1])

            desktop_dict = pickle.load(open(desktop_file, 'rb'))['data']
            desktop_requests = set(desktop_dict[0])
            desktop_responses = set(desktop_dict[1])

            mobile_intersection, mobile_difference = \
                compare_wpr_resources(mobile_requests, desktop_requests)
            desktop_intersection, desktop_difference = \
                    compare_wpr_resources(mobile_responses, desktop_responses)

            if mobile_difference:
                print '\n'
                print 'Found difference in mobile: {0}'.format(mobile_file)
                print mobile_difference
            if desktop_difference:
                print '\n'
                print 'Found difference in desktop: {0}'.format(desktop_file)
                print desktop_difference
        else:
            print 'File not found in desktop: {0}'.format(file_name)


def compare_wpr_resources(mobile_set, desktop_set):
    """Returns the set intersection and set difference of the given sets"""
    return mobile_set.intersection(desktop_set), mobile_set.symmetric_difference(desktop_set)


def __main__():
    args = sys.argv

    if len(args) != 3:
        raise Exception("Must provide 2 har directories")

    compare(args[1], args[2])

if __name__ == '__main__':
    __main__()
