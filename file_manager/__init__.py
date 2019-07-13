from .config import settings
from .ui import FileManagerApp
from .ui.style import apply_default_color_scheme

# TODO - sha1 files so they can be remapped to new locations if moved


def set_file_action(action_name, action_callback, filetypes):
    """
    :param action_name: Name of the menu option
    :param action_callback: Method that takes in a file path
    :param filetypes: List of filetypes to apply action to
    """
    settings.set_file_action(action_name, action_callback, filetypes)
