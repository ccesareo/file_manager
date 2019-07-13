from Qt.QtWidgets import QApplication

from . import apply_default_color_scheme, FileManagerApp, settings

app = QApplication([])
apply_default_color_scheme()
ui = FileManagerApp()
settings.main_ui = ui
ui.resize(1600, 900)
ui.show()
app.exec_()
