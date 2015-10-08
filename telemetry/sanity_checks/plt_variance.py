from base64 import urlsafe_b64encode, urlsafe_b64decode
from glob import glob
from optparse import OptionParser
import json
import numpy

def plt_variance(goodStdev):
    """Checks each plt and pc plt and returns if any plts are > 1 std

    :param stdev: float number of standard deviations away from the mean for a
    plt to be considered good
    """
    aggregated_data = {}
    data_path = '../temp/*'
    data_files = [f for f in glob(data_path) if '.json' not in f]
    sorted_files = sorted(data_files)

    curr_url = None
    for tmp_file in sorted_files:
        data = {}
        with open(tmp_file) as f:
            data = json.load(f)
        if data == {}:
            raise IOError('Problem reading {0}'.format(tmp_file))
        trial = int(tmp_file.split("/")[-1].split('.')[1])
        url = data.keys()[0]
        values = data[url]['cold_times']['trial{0}'.format(trial)]
        npValues = numpy.array(values)
        stdev = numpy.std(npValues)
        mean = numpy.mean(npValues)

        for val in values:
            pltStd = (abs(val - mean ) / float(stdev))
            if pltStd >  goodStdev:
                encodedURL = tmp_file.split("/")[-1].split(".")[0]
                url = urlsafe_b64decode(encodedURL)
                print "Found plt > 1 stdev: {0}".format(url)
                print "stdev: {0}".format(stdev)
                print "mean: {0}".format(mean)
                print "plt: {0}".format(val)
                print "plt stdev: {0}".format(pltStd)

def __main__():
    parser = OptionParser()
    parser.add_option('-s', '--stdev', action='store', dest='stdev',
        help='threashold standard deviation for each plt to be considered good')
    options, args = parser.parse_args()
    if options.stdev is None:
        stdev = 1
    else:
        stdev = float(options.stdev)

    plt_variance(stdev)

if __name__ == '__main__':
    __main__()
