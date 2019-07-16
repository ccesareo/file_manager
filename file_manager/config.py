import ConfigParser
import glob
import logging
import os
from collections import defaultdict

VERSION = 'v0.0.2'

logging.basicConfig(format='%%(asctime)s (%s) [%%(levelname)s] %%(message)s' % VERSION, datefmt='%Y-%m-%d %H:%M:%S')
LOG = logging.getLogger('FileManager')
LOG.setLevel(logging.DEBUG)


class _Settings(object):
    def __init__(self):
        self.lib_dir = os.path.dirname(__file__)

        self.file_actions = defaultdict(dict)

        self.main_ui = None
        self.thumb_size = 100  # percent
        self._thumbnail_folder = None
        self._app_icons_win = None

        self.db_engine = None
        self.db_name = None
        self.db_host = None
        self.db_port = None
        self.db_user = None
        self.db_pass = None

        self._load_settings()

    @property
    def thumbs_folder(self):
        if os.name == 'nt':
            assert self._thumbnail_folder, 'No thumbnail_folder set in settings.'
            return self._thumbnail_folder
        raise Exception('Only windows thumbnail folder has been defined.')

    @property
    def templates_folder(self):
        return (os.path.dirname(self.lib_dir) or '.') + '\\templates'

    @property
    def templates(self):
        templates = glob.glob(settings.templates_folder + '\\*.py')
        templates.sort()
        templates = [os.path.basename(p) for p in templates]
        if 'default.py' in templates:
            templates.remove('default.py')
            templates.insert(0, 'default.py')
        return templates

    @property
    def icons_folder(self):
        if os.name == 'nt':
            return self._app_icons_win
        raise Exception('Only windows thumbnail folder has been defined.')

    def _load_settings(self):
        settings_file = os.path.join(self.lib_dir, 'settings.ini')
        assert os.path.isfile(settings_file), 'No settings.ini file found, please copy the template and modify.'

        config = ConfigParser.ConfigParser()
        config.readfp(open(settings_file))

        self._thumbnail_folder = config.get('settings', 'thumbnail_folder')
        self._app_icons_win = config.get('settings', 'app_icons_win')

        self.db_engine = config.get('database', 'engine')
        self.db_name = config.get('database', 'name')
        self.db_host = config.get('database', 'host')
        self.db_port = int(config.get('database', 'port') or 0)
        self.db_user = config.get('database', 'user')
        self.db_pass = config.get('database', 'pass')

        # Create directory
        if os.name == 'nt' and self._thumbnail_folder and not os.path.isdir(self._thumbnail_folder):
            os.makedirs(self._thumbnail_folder)


settings = _Settings()
""":type: _Settings"""
