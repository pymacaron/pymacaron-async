import logging
from celery import Celery
from pymacaron import get_config
from pymacaron.utils import get_app_name
from pymacaron.monitor import monitor_init


log = logging.getLogger(__name__)


app = Celery('tasks')


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
