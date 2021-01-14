import os
import sys
from pymacaron.log import pymlogger
import imp
from pymacaron import get_config
from pymacaron.crash import report_error


log = pymlogger(__name__)


# Find the nearest pym-config.yaml and load its surrounding modules
root_dir = os.path.dirname(get_config().config_path)
log.info("Appending %s to python PATH" % root_dir)
sys.path.append(root_dir)

# Get port & debug passed via environ by start_celery()
# The defaults are for when running in a container via gunicorn
port = int(os.environ.get('PYM_CELERY_PORT', 80))
debug = True if os.environ.get('PYM_CELERY_DEBUG', False) else False

# Find server.py, load it and call start()
server = imp.load_source('server', os.path.join(root_dir, 'server.py'))
try:
    server.start(port=port, debug=debug)
except Exception as e:
    report_error("Celery worker crashed: %s" % e, caught=e, is_fatal=True)
    raise e
