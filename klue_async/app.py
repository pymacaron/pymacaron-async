import logging
import os
from celery import Celery
from klue_microservice.config import get_config


log = logging.getLogger(__name__)


app = Celery('tasks')

# We need to name the SQS queues so they are unique for a given deployment
# of the microservice
project_name = get_config().name

# Do we have a version?
version = 'dev'
if os.path.exists('/klue/VERSION'):
    with open('/klue/VERSION', 'r') as f:
        version=f.read().replace('\n', '')

prefix = '%s_%s_' % (project_name, version)
log.info("Prefixing Celery SQS with %s" % prefix)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    broker_transport='sqs',
    broker_transport_options={
        'region': get_config().aws_default_region,
        'queue_name_prefix': prefix,
        # Make SQS task again visible to other workers after 10min
        'visibility_timeout': 600,
        'polling_interval': 1,
    },
    broker_user=get_config().aws_access_key_id,
    broker_password=get_config().aws_secret_access_key,
)
