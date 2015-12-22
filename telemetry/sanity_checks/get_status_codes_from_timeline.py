"""Prints a status code dict from a given timeline events.json file

Requires proper json formatting
"""
from collections import Counter
from re import search

def __main__():
    content = []
    with open('/home/jamshed/events.json', 'rb') as f:
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
            code =  search('([0-9]+)', status_code).group(0)
            object_type =  search('([a-zA-Z]+\/[a-zA-Z]+)', label).group(0)
            status_code_dict[code] += 1
            type_dict[object_type] += 1

    print status_code_dict
    print type_dict

if __name__ == '__main__':
    __main__()
