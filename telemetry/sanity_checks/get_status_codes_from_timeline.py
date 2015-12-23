"""Prints a status code dict from a given timeline events.json file

Requires proper json formatting
"""
from collections import Counter
from re import search
from subprocess import call
import sys

def __main__():

    args = sys.argv

    if len(args) != 2:
        raise Exception("Must provide json file")

    return_code = \
    call('cat {0} | python -m json.tool > /tmp/tmp.json'.format(args[1]), shell=True)

    if return_code != 0:
        raise Exception('Unable to pretty print ~/events.json')

    content = []
    with open('/tmp/tmp.json', 'rb') as f:
        content = f.readlines()

    if content == [] or len(content) < 10:
        raise Exception('events.json is empty or not formatted properly')


    status_code_dict = Counter()
    type_dict = Counter()
    for i in range(len(content) - 2):
        label = content[i]
        misc = content[i+1]
        status_code = content[i+2]
        if 'statusCode' in status_code:
            try:
                code =  search('([0-9]+)', status_code)
                if code is not None:
                    code = code.group(0)
                object_type =  search('([a-zA-Z]+\/[a-zA-Z]+)', label)
                if object_type is not None:
                    object_type = object_type.group(0)
                status_code_dict[code] += 1
                type_dict[object_type] += 1
            except:
                import ipdb; ipdb.set_trace()

    print status_code_dict
    print type_dict

if __name__ == '__main__':
    __main__()
