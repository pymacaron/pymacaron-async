import logging
from celery import Celery
from pymacaron import get_config
from pymacaron.utils import get_app_name


log = logging.getLogger(__name__)


app = Celery('tasks')


# Enable Scoutapp monitoring, if available
conf = get_config()
if hasattr(conf, 'scout_key'):
    import scout_apm.celery
    from scout_apm.api import Config

    Config.set(
        key=conf.scout_key,
        name=get_app_name(),
        monitor=True
    )

    scout_apm.celery.install()
# END OF scoutapp support

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    broker_url='redis://localhost:6379/0',
    broker_transport_options={
        'visibility_timeout': 3600,
    }
)
