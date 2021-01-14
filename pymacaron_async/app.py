from pymacaron.log import pymlogger
from celery import Celery
from celery.signals import after_setup_logger
from pymacaron.monitor import monitor_init
from pymacaron.log import setup_logger


log = pymlogger(__name__)


app = Celery('tasks')


# Redirect celery logs to stdout
# See https://stackoverflow.com/questions/22146815/how-to-programmatically-tell-celery-to-send-all-log-messages-to-stdout-or-stderr
@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    setup_logger(celery=True)

# Initialize monitoring, if any
monitor_init(celery=True)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    broker_url='redis://localhost:6379/0',
    broker_transport_options={
        'visibility_timeout': 3600,
    }
)
