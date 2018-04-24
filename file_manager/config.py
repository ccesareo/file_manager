import logging
import os

import yaml

VERSION = 'v0.0.1'

logging.basicConfig(format='%%(asctime)s (%s) [%%(levelname)s] %%(message)s' % VERSION, datefmt='%Y-%m-%d %H:%M:%S')
LOG = logging.getLogger('FileManager')
LOG.setLevel(logging.INFO)


class _Settings(object):
    def __init__(self):
        self.lib_dir = os.path.dirname(__file__)

        self.main_ui = None
        self.thumb_size = 100  # percent
        self.thumbnail_folder_win = None
        self.search_timeout = None

        self.db_engine = None
        self.db_name = None
        self.db_host = None
        self.db_port = None
        self.db_user = None
        self.db_pass = None

        self._load_settings()

    def thumbs_folder(self):
        if os.name == 'nt':
            assert self.thumbnail_folder_win, 'No thumbnail_folder_win set in settings.'
            return self.thumbnail_folder_win
        raise Exception('Only windows thumbnail folder has been defined.')

    def _load_settings(self):
        settings_file = os.path.join(self.lib_dir, 'settings.yaml')
        assert os.path.isfile(settings_file), 'No settings.yaml file found, please copy the template and modify.'

        data = yaml.load(open(settings_file))
        assert 'database' in data, 'No database settings found, please reference template.'

        self.thumbnail_folder_win = data.get('thumbnail_folder_win')

        self.search_timeout = data.get('search_timeout_ms', 0)

        self.db_engine = data['database'].get('engine')

        self.db_name = data['database'].get('name')
        self.db_host = data['database'].get('host')
        self.db_port = data['database'].get('port')
        self.db_user = data['database'].get('user')
        self.db_pass = data['database'].get('pass')

        # Create directory
        if os.name == 'nt' and self.thumbnail_folder_win and not os.path.isdir(self.thumbnail_folder_win):
            os.makedirs(self.thumbnail_folder_win)


settings = _Settings()
""":type: _Settings"""
