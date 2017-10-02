import logging
import inspect
from functools import wraps
from subprocess import Popen, PIPE, STDOUT
from klue_microservice import get_config
from celery import Celery


log = logging.getLogger(__name__)


app = Celery('tasks', broker='pyamqp://guest@localhost//')

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)


def start_celery(debug):
    """Make sure both celeryd and rabbitmq are running"""

    # TODO: first, killall celery and wait for them to have terminated

    level = 'debug' if debug else 'info'
    maxmem = 200*1024
    concurrency = 1
    cmd = 'celery worker -E -A klue_async --concurrency=%s --loglevel=%s --include klue_async,server --max-memory-per-child=%s' % (concurrency, level, maxmem)

    log.info("Spawning celery worker")
    proc = Popen(
        [cmd],
        bufsize=0,
        shell=True,
        close_fds=True
    )


def asynctask(f):

    log.info("\n\n\n\n\nRegistering celery task for %s()\n\n\n\n\n" % (f.__name__))

    # Import the module where f is located
    m = inspect.getmodule(f)
    if not m:
        raise Exception("Failed to find the module containing %s()" % (f.__name__))
    log.debug("%s() is from module %s" % (f.__name__, m))



    # Make f into a celery task
    f = app.task(f)
    log.debug("got back: %s" % f)

    def wrap_task(*args, **kwargs):
        log.info('Queuing celery task for %s()' % (f.__name__, ))
        f.delay(*args, **kwargs)
        return

    return wrap_task
