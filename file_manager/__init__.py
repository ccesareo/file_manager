import os

from PySide2.QtWidgets import QApplication

from file_manager.config import settings
from file_manager.ui import FileManagerApp


def set_file_action(action_name, action_callback, filetypes):
    """
    :param action_name: Name of the menu option
    :param action_callback: Method that takes in a file path
    :param filetypes: List of filetypes to apply action to
    """
    settings.set_file_action(action_name, action_callback, filetypes)


if __name__ == '__main__':
    app = QApplication([])
    ui = FileManagerApp()
    settings.main_ui = ui
    qss_path = os.path.join(os.path.dirname(__file__), 'ui', 'style', 'style.qss')
    ui.setStyleSheet(open(qss_path).read())
    ui.resize(1600, 900)
    ui.show()
    app.exec_()
