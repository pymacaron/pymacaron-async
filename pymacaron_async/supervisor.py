import sys

# Copied from https://github.com/coderanger/supervisor-stdout/blob/master/setup.py

def write_stdout(s):
    sys.stdout.write(s)
    sys.stdout.flush()

def write_stderr(s):
    sys.stderr.write(s)
    sys.stderr.flush()

def event_handler(event, response):
    line, data = response.split('\n', 1)
    headers = dict([x.split(':') for x in line.split()])
    lines = data.split('\n')
    prefix = '%s %s | '%(headers['processname'], headers['channel'])
    print('\n'.join([prefix + l for l in lines]))
