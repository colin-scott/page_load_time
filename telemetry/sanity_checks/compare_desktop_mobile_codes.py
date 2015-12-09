from collections import Counter
from glob import glob
import json
import sys


def compare(har1_path, har2_path):
    """Print the counts of return codes for each har file

    :param har1_path: str of path to har file
    :param har2_path: str of path to har file
    """
    har1_json = {}
    har2_json = {}

    try:
        with open(har1_path) as f:
            har1_json = json.load(f)
        with open(har2_path) as f:
            har2_json = json.load(f)

    except Exception as e:
        raise e

    har1_status = get_status(har1_json)
    har2_status = get_status(har2_json)

    print har1_status
    print har2_status


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
        raise Exception("Must provide 2 har files")

    compare(args[1], args[2])


if __name__ == '__main__':
    __main__()
