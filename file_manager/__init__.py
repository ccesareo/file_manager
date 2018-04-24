import os

from PySide2.QtWidgets import QApplication

from file_manager.ui import FileManagerApp

if __name__ == '__main__':
    app = QApplication([])
    ui = FileManagerApp()
    qss_path = os.path.join(os.path.dirname(__file__), 'ui', 'style', 'style.qss')
    ui.setStyleSheet(open(qss_path).read())
    ui.resize(1600, 900)
    ui.show()
    app.exec_()
