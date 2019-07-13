from Qt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QHBoxLayout

from ..config import VERSION
from ..ui.menubar import FileManagerMenu
from ..ui.sidebar import SideBarBrowser
from ..ui.toolbar import FileManagerToolbar
from ..ui.viewer import FileManagerViewer


class FileManagerApp(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(FileManagerApp, self).__init__(*args, **kwargs)

        self._toolbar = FileManagerToolbar(self)
        self._browser = SideBarBrowser(self)
        self._viewer = FileManagerViewer(self)

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def resizeEvent(self, event):
        res = super(FileManagerApp, self).resizeEvent(event)
        self._viewer.update_layout()
        return res

    def _build_ui(self):
        self.setMenuBar(FileManagerMenu())

        lyt_workarea = QHBoxLayout()
        lyt_workarea.setContentsMargins(0, 0, 0, 0)
        lyt_workarea.setSpacing(4)
        lyt_workarea.addWidget(self._browser)
        lyt_workarea.addWidget(self._viewer)

        lyt_main = QVBoxLayout()
        lyt_main.setSpacing(4)
        lyt_main.addWidget(self._toolbar)
        lyt_main.addLayout(lyt_workarea)

        wdg = QWidget()
        wdg.setLayout(lyt_main)
        self.setCentralWidget(wdg)

    def _build_connections(self):
        self._toolbar.tags_changed.connect(self._browser.apply_tags)
        self._toolbar.assets_changed.connect(self._browser.apply_assets)
        self._browser.assets_selected.connect(self._viewer.view_assets)
        self._browser.tags_updated.connect(self._viewer.refresh)

        self.menuBar().database_cleared.connect(self._browser.clear)

    def _setup_ui(self):
        self.setWindowTitle('File Manager - %s' % VERSION)
