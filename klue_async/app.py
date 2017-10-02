import logging
from celery import Celery


log = logging.getLogger(__name__)


app = Celery('tasks', broker='pyamqp://guest@localhost//')

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)
