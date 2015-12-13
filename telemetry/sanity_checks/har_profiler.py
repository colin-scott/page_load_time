from collections import Counter
import json

def get_resource_count(har_json):
    """Returns a dict of resource counts

    :param har_json: dict of the complete har
    """
    entries = har_json['log']['entries']

    resource_type_counts = Counter()

    for entry in entries:
        resource = entry['request']['url']
        dirty_resource_type = resource.split('.')[-1]
        resource_type = dirty_resource_type.split('?')[0]  # Remove url params
        if len(resource_type) > 4:
            resource_type_counts['other'] += 1
            # print 'Found other resource type: {0}'.format(resource_type)
        else:
            resource_type_counts[resource_type] += 1

    return resource_type_counts


def get_har_dict_from_file(har_path):
    """Returns the dict from the har path

    :param har1_path: str of path to har file
    """
    har_json = {}

    try:
        with open(har_path) as f:
            har_json = json.load(f)
    except Exception as e:
        raise e

    return har_json


def get_status_code_count(har_json):
    """Returns a dict of status code counts

    :param har_json: dict of the complete har
    """
    entries = har_json['log']['entries']

    har_status_codes = Counter()

    for entry in entries:
        code = entry['response']['status']
        har_status_codes[code] += 1

    return har_status_codes


def get_total_body_size(har_json):
    """Returns total size of all response bodies, in bytes

    :param har_json: dict of the complete har
    """
    total_size = 0

    for entry in har_json['log']['entries']:
        total_size += entry['response']['bodySize']

    return total_size
