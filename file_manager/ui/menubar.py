from PySide2.QtWidgets import QMenuBar


class FileManagerMenu(QMenuBar):
    def __init__(self, *args, **kwargs):
        super(FileManagerMenu, self).__init__(*args, **kwargs)

        self.addMenu('File')
        self.addMenu('Edit')
