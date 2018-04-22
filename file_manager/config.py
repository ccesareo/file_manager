import logging
import os

import yaml

VERSION = 'v0.0.1'

logging.basicConfig(format='%%(asctime)s (%s) [%%(levelname)s] %%(message)s' % VERSION, datefmt='%Y-%m-%d %H:%M:%S')
LOG = logging.getLogger('FileManager')
LOG.setLevel(logging.DEBUG)


class _Settings(object):
    def __init__(self):
        self.lib_dir = os.path.dirname(__file__)

        self.db_engine = None

        self.db_name = None
        self.db_host = None
        self.db_port = None
        self.db_user = None
        self.db_pass = None

        self._load_settings()

    def _load_settings(self):
        settings_file = os.path.join(self.lib_dir, 'settings.yaml')
        assert os.path.isfile(settings_file), 'No settings.yaml file found, please copy the template and modify.'

        data = yaml.load(open(settings_file))
        assert 'database' in data, 'No database settings found, please reference template.'

        self.db_engine = data['database'].get('engine')

        self.db_name = data['database'].get('name')
        self.db_host = data['database'].get('host')
        self.db_port = data['database'].get('port')
        self.db_user = data['database'].get('user')
        self.db_pass = data['database'].get('pass')


settings = _Settings()
""":type: _Settings"""
