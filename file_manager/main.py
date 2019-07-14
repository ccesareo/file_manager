import os

from Qt import QtCore, QtWidgets
from . import apply_default_color_scheme, FileManagerApp, settings

app = QtWidgets.QApplication([])
apply_default_color_scheme()
ui = FileManagerApp()
settings.main_ui = ui
ui.resize(1600, 900)
ui.show()
app.exec_()
