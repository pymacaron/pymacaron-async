import logging
from celery import Celery
from klue_microservice.config import get_config


log = logging.getLogger(__name__)


app = Celery('tasks')

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    broker_transport='sqs',
    broker_transport_options={
        'region': get_config().aws_default_region,
        'queue_name_prefix': 'celery-',
    },
    broker_user=get_config().aws_access_key_id,
    broker_password=get_config().aws_secret_access_key,
)
