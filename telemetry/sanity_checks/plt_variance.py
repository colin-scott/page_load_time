from base64 import urlsafe_b64encode, urlsafe_b64decode
from glob import glob
from optparse import OptionParser
import json
import numpy

def plt_variance(goodStdev, use_stdev=False):
    """Checks each plt and pc plt and returns if any plts are > 1 std

    :param stdev: float number of standard deviations away from the mean for a
    plt to be considered good
    """
    aggregated_data = {}
    data_path = '../temp/*'
    data_files = [f for f in glob(data_path) if '.json' not in f]
    sorted_files = sorted(data_files)
    num_plts = len(data_files)

    num_bad_plts = 0
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

        values.sort()
        if len(values) <= 3:
            import ipdb; ipdb.set_trace()
            raise Exception("Length of values != 3")

        d1 = abs(values[1] - values[0])
        d2 = abs(values[2] - values[1])

        norm1 = float(d1) / values[1]
        norm2 = float(d2) / values[1]

        if norm1 > 0.05 or norm2 > 0.05:
            print norm1, norm2, "******"
        else:
            print norm1, norm2

        if use_stdev:
            npValues = numpy.array(values)
            stdev = numpy.std(npValues)
            mean = numpy.mean(npValues)

            is_good_plt = True
            for val in values:
                pltStd = (abs(val - mean ) / float(stdev))
                if pltStd >  goodStdev:
                    if is_good_plt:
                        is_good_plt = False
                        num_bad_plts += 1
                    encodedURL = tmp_file.split("/")[-1].split(".")[0]
                    url = urlsafe_b64decode(encodedURL)
                    print "Found plt > 1 stdev: {0}".format(url)
                    print "stdev: {0}".format(stdev)
                    print "mean: {0}".format(mean)
                    print "plt: {0}".format(val)
                    print "plt stdev: {0}".format(pltStd)
    print "Total plts; {0}, Num bad plts: {1}, bad plt percent: {2}".format(
            num_plts, num_bad_plts, 0 if num_bad_plts == 0 else
            float(num_bad_plts) / float(num_plts))

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
