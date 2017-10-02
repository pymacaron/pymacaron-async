import os
import sys
import logging
import inspect
import imp
from klue_microservice import get_config
from klue_async.app import app


log = logging.getLogger(__name__)


# Find the nearest klue-config.yaml and load its surrounding modules
root_dir = os.path.dirname(get_config().config_path)
log.info("Appending %s to python PATH" % root_dir)
sys.path.append(root_dir)

# Get port & debug passed via environ by start_celery()
# The defaults are for when running in a container via gunicorn
port = int(os.environ.get('KLUE_CELERY_PORT', 80))
debug = True if os.environ.get('KLUE_CELERY_DEBUG', False) else False

# Find server.py, load it and call start()
server = imp.load_source('server', os.path.join(root_dir, 'server.py'))
server.start(port=port, debug=debug)
