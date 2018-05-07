import ConfigParser
import logging
import os
from collections import defaultdict


VERSION = 'v0.0.1'

logging.basicConfig(format='%%(asctime)s (%s) [%%(levelname)s] %%(message)s' % VERSION, datefmt='%Y-%m-%d %H:%M:%S')
LOG = logging.getLogger('FileManager')
LOG.setLevel(logging.INFO)


class _Settings(object):
    def __init__(self):
        self.lib_dir = os.path.dirname(__file__)

        self.file_actions = defaultdict(dict)

        self.main_ui = None
        self.thumb_size = 100  # percent
        self.thumbnail_folder_win = None
        self.app_icons_win = None
        self.search_timeout = None

        self.db_engine = None
        self.db_name = None
        self.db_host = None
        self.db_port = None
        self.db_user = None
        self.db_pass = None

        self._load_settings()

    def set_file_action(self, action_name, action_callback, filetypes):
        for filetype in filetypes:
            self.file_actions[filetype][action_name] = action_callback

    def thumbs_folder(self):
        if os.name == 'nt':
            assert self.thumbnail_folder_win, 'No thumbnail_folder_win set in settings.'
            return self.thumbnail_folder_win
        raise Exception('Only windows thumbnail folder has been defined.')

    def icons_folder(self):
        if os.name == 'nt':
            return self.app_icons_win
        raise Exception('Only windows thumbnail folder has been defined.')

    def _load_settings(self):
        settings_file = os.path.join(self.lib_dir, 'settings.ini')
        assert os.path.isfile(settings_file), 'No settings.ini file found, please copy the template and modify.'

        config = ConfigParser.ConfigParser()
        config.readfp(open(settings_file))

        self.thumbnail_folder_win = config.get('settings', 'thumbnail_folder_win')
        self.app_icons_win = config.get('settings', 'app_icons_win')

        self.search_timeout = config.getint('settings', 'search_timeout_ms')

        self.db_engine = config.get('database', 'engine')
        self.db_name = config.get('database', 'name')
        self.db_host = config.get('database', 'host')
        self.db_port = config.getint('database', 'port')
        self.db_user = config.get('database', 'user')
        self.db_pass = config.get('database', 'pass')

        # Create directory
        if os.name == 'nt' and self.thumbnail_folder_win and not os.path.isdir(self.thumbnail_folder_win):
            os.makedirs(self.thumbnail_folder_win)


settings = _Settings()
""":type: _Settings"""
