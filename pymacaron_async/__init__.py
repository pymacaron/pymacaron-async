import sys
import os
import signal
import logging
import inspect
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
    concurrency = 1

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


def asynctask(f):

    fname = f.__name__
    m = inspect.getmodule(f)
    if m:
        fname = '%s.%s()' % (m.__name__, f.__name__)

    #
    # Is this code loading inside a Flask app or a Celery worker?
    #

    if 'celery' in sys.argv[0].lower():

        # We are in celery - Let's put f in a wrapper that emulates a Flask
        # context + handles crashes the same way pymacaron microservice does
        # for API endpoints
        log.info("Wrapping %s in a Flask/PyMacaron context emulator" % fname)

        # Wrap f in the same crash handler as used in the API server
        f = generate_crash_handler_decorator()(f)

        @wraps(f)
        def mock_flask_context(url, token, *args, **kwargs):
            log.info("pymacaron-async wrapper: using url [%s] and token [%s]" % (url, token))
            with flaskapp.test_request_context(url):
                if token:
                    load_auth_token(token)
                log.info("pymacaron-async wrapper: calling %s" % fname)
                f(*args, **kwargs)

        # Then register task
        newf = app.task(mock_flask_context, typing=False)
        return newf

    # We are in the Flask app
    log.info("Registering celery task for %s" % fname)
    f = app.task(f, typing=False)

    # Call the asynchronous method via celery
    def queue_task(*args, **kwargs):
        url = request.url
        token = get_user_token()
        log.info('Queuing celery task for %s' % fname)
        f.delay(url, token, *args, **kwargs)
        return

    # And return the stub launching the Celery task
    return queue_task
