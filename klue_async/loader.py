import os
import sys
import logging
import inspect
import importlib
from klue_microservice import get_config
from klue_async.app import app


log = logging.getLogger(__name__)


# Find the nearest klue-config.yaml and load its surrounding modules
root_dir = os.path.dirname(get_config().config_path)
log.info("Appending %s to python PATH" % root_dir)
sys.path.append(root_dir)

# Find apis, and load all modules used in the api specs
for m in get_config().load_async_modules:
    log.info("Loading module %s" % m)
    importlib.import_module(m)
