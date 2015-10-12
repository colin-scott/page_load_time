from glob import glob
from subprocess import Popen, PIPE, STDOUT

def check_har_objects():
    """Check if all objects in the original wpr file are in the pc wpr file"""
    data_path = '../data/wpr_source/*'
    data_files = [f for f in glob(data_path) if '.json' not in f]
    sorted_files = sorted(data_files)
    print len(sorted_files)

    i = 0
    while i < len(sorted_files):
        original = sorted_files[i]
        pc = sorted_files[i+1]

        cmd = "sudo ~/src/third_party/webpagereplay/httparchive.py ls {0}"

        p = Popen(cmd.format(original), shell=True, stdin=PIPE, stdout=PIPE,
                stderr=STDOUT)
        output, err = p.communicate()
        original_objects = output

        p = Popen(cmd.format(pc), shell=True, stdin=PIPE, stdout=PIPE,
                stderr=STDOUT)
        output, err = p.communicate()
        pc_objects = output

        if original_objects != pc_objects:
            print "Found difference in har objects:"
            print "Original:"
            print original_objects
            print "--------"
            print "Pc:"
            print pc_objects

        i += 2

def __main__():
    check_har_objects()

if __name__ == '__main__':
    __main__()
