from subprocess import Popen, PIPE, STDOUT
from base64 import urlsafe_b64encode, urlsafe_b64decode

def write_js(url, filename):
    """Dynamically writes a javascript file

    TODO(jvesuna): Edit CHC instead of dynamically writing out javascript
    https://github.com/cyrus-and/chrome-har-capturer

    :param url: str url
    :param filename: str filename, without the extension.
    Example: 'aHR0cDovL2phbW5vaXNlLmNvbQ=='
    """
    js_template = ("var fs = require('fs');\n"
    "var chc = require('chrome-har-capturer');\n"
    "var c = chc.load(['{0}']);\n"
    "c.on('connect', function () {{\n"
    "            console.log('Connected to Chrome');\n"
    "}});\n"
    "c.on('pageStart', function (har) {{\n"
    "    var d = new Date();\n"
    "    var n = d.getTime();\n"
    "    console.log('Start time:');\n"
    "    console.log(n);\n"
    "}});\n"
    "c.on('pageEnd', function (har) {{\n"
    "    var d = new Date();\n"
    "    var n = d.getTime();\n"
    "    console.log('End time:');\n"
    "    console.log(n);\n"
    "}});\n"
    "c.on('end', function (har) {{\n"
    "    fs.writeFileSync('{1}.har', JSON.stringify(har));\n"
    "}});\n"
    "c.on('error', function () {{\n"
    "    console.error('Cannot connect to Chrome');\n"
    "}});")
    js_with_url = js_template.format(url, filename)
    with open('{0}.js'.format(filename), 'w') as f:
        f.write(js_with_url)


def run_chc(filename):
    """Runs chrome har capturer, result is stored in harfile

    :param filename: str filename, without the extension.
    Example: 'aHR0cDovL2phbW5vaXNlLmNvbQ=='
    """
    cmd = 'nodejs {0}.js'.format(filename)
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    output, err = p.communicate()
    if err or p.returncode != 0:
        print 'Error running filename: {0}'.format(filename)


def prescreenUrl(url):
    """Returns bool if url is online and available
    :param url: str url
    """
    if url == '':
        return False

    cmd = 'wget --spider -t 1 -T 10 {0} -O /dev/null'.format(url)
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    out, err = p.communicate()

    if p.returncode != 0:
        return False

    failed = ['404 Not Found', 'Giving up', 'failed', 'FAILED',
            'Connection timed out']
    if any(x in out for x in failed):
        return False
    return True


def get_urls(path):
    """Returns a list of urls from path
    :param path: str path
    """
    urls = []
    with open(path, 'rb') as f:
        urls = [x.strip() for x in f.readlines()]

    # Prune urls that are not working
    goodUrls = []
    badUrls = []
    for url in urls:
        if prescreenUrl(url):
            print "PASS prescreen: " + str(url)
            goodUrls.append(url)
        else:
            print "FAIL prescreen: " + str(url)
            badUrls.append(url)

    with open('bad_urls', 'wb') as f:
        f.write('\n'.join(badUrls))
        f.close()

    return goodUrls


def __main__():
    # Requires google-chrome to be running via:
    # google-chrome --remote-debugging-port=9222 --enable-benchmarking \
    # --enable-net-benchmarking
    target_url_path = 'target_urls'
    # Get valid url set
    urls = get_urls(target_url_path)
    for url in urls:
        write_js(url, urlsafe_b64encode(url))
    for url in urls:
        run_chc(urlsafe_b64encode(url))


if __name__ == '__main__':
    __main__()
