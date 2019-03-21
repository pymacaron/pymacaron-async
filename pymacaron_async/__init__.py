import sys
import os
import signal
import logging
import inspect
import json
from flask import Flask, request
from functools import wraps
from subprocess import Popen
from pymacaron_async.app import app
from pymacaron.auth import get_user_token, load_auth_token
from pymacaron.crash import generate_crash_handler_decorator


log = logging.getLogger(__name__)


flaskapp = Flask('pym-async')


def get_celery_cmd(debug, keep_alive=False):
    level = 'debug' if debug else 'info'
    maxmem = 200 * 1024
    concurrency = 2

    cmd = 'celery worker -E -A pymacaron_async --concurrency=%s --loglevel=%s --include pymacaron_async.loader --max-memory-per-child=%s' % (concurrency, level, maxmem)
    if keep_alive:
        cmd = 'while true; do %s; sleep 5; done' % cmd

    return cmd


def kill_celery():
    """Kill celery workers"""
    for line in os.popen("ps ax | grep 'celery worker -E -A pymacaron_async' | grep -v grep"):
        fields = line.split()
        pid = fields[0]
        log.warn("Killing celery worker with pid %s" % pid)
        os.kill(int(pid), signal.SIGTERM)


def start_celery(port, debug):
    """Start celery workers"""

    # First, stop currently running celery workers (only those running pymacaron microservices)
    kill_celery()

    # Then start celery anew
    os.environ['PYM_CELERY_PORT'] = str(port)
    os.environ['PYM_CELERY_DEBUG'] = '1' if debug else ''
    cmd = get_celery_cmd(debug, keep_alive=False)

    log.info("Spawning celery worker")
    Popen(
        [cmd],
        bufsize=0,
        shell=True,
        close_fds=True
    )


class asynctask(object):

    def __init__(self, delay=0):
        self.delay = delay
        self.magic = 'PYMACARON_ALSO_WHIPS_THE_LLAMA_S'

    def get_task_scheduler(self, fname, f):
        """Return a function that will schedule a task to execute f"""
        log.info("Registering celery task for %s (delay: %s)" % (fname, self.delay))
        f = app.task(f, typing=False)

        # Call the asynchronous method via celery
        def queue_task(*args, **kwargs):
            url = request.url
            token = get_user_token()
            log.info('Queuing celery task for %s with delay=%s' % (fname, self.delay))
            args = (self.magic, url, token) + args
            f.apply_async(args=args, kwargs=kwargs, countdown=self.delay)
            # f.delay(url, token, *args, **kwargs)
            return

        return queue_task


    def __call__(self, f):
        fname = f.__name__
        m = inspect.getmodule(f)
        if m:
            fname = '%s.%s()' % (m.__name__, f.__name__)

        #
        # Is this code loading inside a Flask app or a Celery worker?
        #

        if 'celery' not in sys.argv[0].lower():
            # We are in the Flask app. Let's just schedule the task
            return self.get_task_scheduler(fname, f)


        # We are in celery - Let's put f in a wrapper that emulates a Flask
        # context + handles crashes the same way pymacaron microservice does
        # for API endpoints
        log.info("Wrapping %s in a Flask/PyMacaron context emulator" % fname)

        # Wrap f in the same crash handler as used in the API server
        f = generate_crash_handler_decorator()(f)

        @wraps(f)
        def mock_flask_context(*args, **kwargs):

            # We are executing in a worker, but this worker could be scheduling a new task...
            # Let's check if the token is indeed a token. If not, we assume the worker
            # is scheduling a new task.
            if args and len(args) >= 3 and type(args[0]) is str and args[0] == self.magic:
                # Wheeee!!! We got a task to execute!
                url = args[1]
                token = args[2]
                args = args[3:]

                log.info('')
                log.info('')
                log.info(' => ASYNC TASK %s (delayed: %s sec)' % (fname, self.delay))
                log.info('')
                log.info('')
                log.info('    url: %s' % url)
                log.info('    token: %s' % token)
                log.debug('    args: %s' % json.dumps(args, indent=4))
                log.debug('    kwargs: %s' % json.dumps(kwargs, indent=4))
                log.info('')
                log.info('')
                with flaskapp.test_request_context(url):
                    if token:
                        load_auth_token(token)
                    f(*args, **kwargs)
            else:
                # This is a task in a task, no need to reschedule it
                log.info(" => TASK IN TASK: executing %s immediately" % fname)
                f(*args, **kwargs)

        # Return the wrapped task
        newf = app.task(mock_flask_context, typing=False)
        return newf
