import os
basedir = os.path.dirname(__file__)
activate_this = os.path.join(basedir, '.venv', 'bin', 'activate_this.py')
execfile(activate_this, dict(__file__=activate_this))
from marv import create_app, load_formats, load_jobs
load_formats()
load_jobs()
instancepath = os.getenv('MARV_INSTANCE_PATH')
application = create_app(config_obj='marv.settings.Production', INSTANCE_PATH=instancepath)
import logging
application.logger.addHandler(logging.StreamHandler())
# for debugging
#application.logger.setLevel(logging.DEBUG)
#application.config['LOG_REQUESTS'] = True