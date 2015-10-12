from glob import glob
from optparse import OptionParser
import re

def parse_logs(numUrls):

    logFiles = [f for f in glob("/home/jamshed/src/webpagereplay_logs/*")]
    logFiles.sort()

    match200 = re.compile(".*200, 'OK'")
    match400 = re.compile(".*404, 'Not Found'")
    match304 = re.compile(".*304, 'Not Modified'")

    parsedLogs = []

    for logFile in logFiles:
        with open(logFile) as f:
            content = f.readlines()

        counts = {404: 0, 200: 0, 304: 0, 'content200': set(),
                'content404': set()}

        for line in content:
            if match200.match(line):
                counts[200] += 1
                counts['content200'].add(line)
            elif match400.match(line):
                counts[404] += 1
                counts['content404'].add(line)
            elif match304.match(line):
                counts[304] += 1

        # print counts
        counts['total'] = counts[404] + counts[200] + counts[304]
        counts['file'] = logFile.split('/')[-1]
        parsedLogs.append(counts)

    recordWpr = parsedLogs[:numUrls]
    restWpr = parsedLogs[numUrls:]

    # Uncomment to include content
    # print "record"
    # for i in recordWpr:
        # print i
    # print "rest"
    # for i in restWpr:
        # print i

    i = 0
    while i < len(restWpr):
        print "For url #{0}".format(i)
        original = restWpr[i]
        pc = restWpr[i+1]

        diff200 = original['content200'].difference(pc['content200'])
        len_diff200 = len(original['content200']) - len(pc['content200'])
        print "difference in size of diff200: {0}".format(len_diff200)
        print "size of diff200 is {0}".format(len(diff200))

        diff404 = original['content404'].difference(pc['content404'])
        len_diff404 = len(original['content404']) - len(pc['content404'])
        print "difference in size of diff200: {0}".format(len_diff404)
        print "size of diff404 is {0}".format(len(diff404))

        i += 2

def __main__():
    parser = OptionParser()
    parser.add_option('-n', '--number', action='store', dest='number',
        help='number of valid urls in the set of logs')
    options, args = parser.parse_args()

    if options.number is None:
        number = -1
        raise Exception("Must define number of urls")
    else:
        number = int(options.number)

    parse_logs(number)

if __name__ == '__main__':
    __main__()
