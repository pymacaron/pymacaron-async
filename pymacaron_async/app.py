import logging
from celery import Celery


log = logging.getLogger(__name__)


app = Celery('tasks')


app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    broker_url='redis://localhost:6379/0',
    broker_transport_options={
        'visibility_timeout': 3600,
    }
)
