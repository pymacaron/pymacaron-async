import sys
import os
import logging
import inspect
from flask import Flask, request
from functools import wraps
from subprocess import Popen
from celery import Celery
from klue_async.app import app
from klue_microservice.config import get_config
from klue_microservice.auth import get_user_token, load_auth_token


log = logging.getLogger(__name__)


flaskapp = Flask('klue-async')


def start_celery(port, debug):
    """Make sure both celeryd and rabbitmq are running"""

    # TODO: first, killall celery and wait for them to have terminated

    level = 'debug' if debug else 'info'
    maxmem = 200*1024
    concurrency = 1
    os.environ['KLUE_CELERY_PORT'] = str(port)
    os.environ['KLUE_CELERY_DEBUG'] = '1' if debug else ''
    cmd = 'celery worker -E -A klue_async --concurrency=%s --loglevel=%s --include klue_async.loader --max-memory-per-child=%s' % (concurrency, level, maxmem)

    log.info("Spawning celery worker")
    proc = Popen(
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

        # We are in celery - Let's put f in a wrapper around f that emulates a
        # Flask context + handles crashes the same way klue-microservice does
        # for API endpoints
        log.info("Wrapping %s in a Flask/Klue context emulator" % fname)

        @wraps(f)
        def mock_flask_context(url, token, *args, **kwargs):
            log.info("klue-async wrapper: using url [%s] and token [%s]" % (url, token))
            with flaskapp.test_request_context(url):
                if token:
                    load_auth_token(token)
                log.info("klue-async wrapper: calling %s" % fname)
                f(*args, **kwargs)

        # TODO: decorate with klue crash-handler

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
