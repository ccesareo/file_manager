from PySide2.QtCore import Signal, Qt, QEvent
from PySide2.QtGui import QKeyEvent
from PySide2.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QLabel, QListWidget, QApplication, QComboBox

from file_manager.data.connection import get_engine
from file_manager.data.query import Query


class FileManagerToolbar(QWidget):
    tags_changed = Signal(list)
    assets_changed = Signal(list)

    def __init__(self, *args, **kwargs):
        super(FileManagerToolbar, self).__init__(*args, **kwargs)

        self._cmbo_search_type = QComboBox()

        self._str_names = set()

        self._search_filter = _SearchFilter()
        self._edit_search = _SearchField(self._search_filter)

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def _build_ui(self):
        self.setFixedHeight(35)

        self._edit_search.setFixedWidth(400)

        lyt_main = QHBoxLayout()
        lyt_main.setContentsMargins(0, 0, 10, 0)
        lyt_main.setSpacing(0)
        lyt_main.addStretch()
        lyt_main.addWidget(self._cmbo_search_type)
        lyt_main.addWidget(self._edit_search)
        self.setLayout(lyt_main)

    def _build_connections(self):
        self._edit_search.textChanged.connect(self._update_tags)
        self._edit_search.textChanged.connect(self._update_search_filter)
        self._search_filter.item_selected.connect(self._tag_selected)
        self._cmbo_search_type.currentIndexChanged.connect(self._edit_search.clear)

    def _setup_ui(self):
        self._cmbo_search_type.addItems(['asset', 'tag'])

    def _update_search_filter(self):
        self._search_filter.clear()

        last_item = self._split_labels()[-1]
        if not last_item:
            self._search_filter.hide()
            return

        q = Query(self._search_type())
        q.add_filter('name', last_item, operator=q.OP.MATCH, match_case=False)
        engine = get_engine()
        result = engine.select(q)
        if result:
            names = [x.name for x in result]
            names.sort()
            self._search_filter.addItems(names)
            self._search_filter.show()
            pt = self._edit_search.mapToParent(self._edit_search.rect().bottomLeft())
            pt = self.mapToGlobal(pt)
            self._search_filter.move(pt)
        else:
            self._search_filter.hide()

    def _update_tags(self):
        items = self._split_labels()
        if items:
            q = Query(self._search_type())
            q.start_filter_group(q.OP.OR)
            for item in items:
                q.add_filter('name', '^%s$' % item, operator=q.OP.MATCH)
            q.end_filter_group()
            rec_by_name = {r.name: r for r in (get_engine().select(q))}
        else:
            rec_by_name = dict()

        _found_names = set(rec_by_name.keys())
        if self._str_names - _found_names:
            pass
        elif _found_names - self._str_names:
            pass
        else:
            return

        if self._search_type() == 'tag':
            self.tags_changed.emit(sorted(items))
        else:
            self.assets_changed.emit(sorted(items))

    def _search_type(self):
        return self._cmbo_search_type.currentText()

    def _split_labels(self):
        s = self._edit_search.text().strip()
        items = s.split(',')
        items = [x.strip() for x in items if x.strip()]
        return items

    def _tag_selected(self, tag_name):
        items = self._split_labels()
        items[-1] = tag_name
        self._edit_search.setText(','.join(items) + ',')


class _SearchField(QLineEdit):
    def __init__(self, search_filter, *args, **kwargs):
        """
        :type search_filter: _SearchFilter
        """
        super(_SearchField, self).__init__(*args, **kwargs)

        self._search_filter = search_filter

        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Return, Qt.Key_PageUp, Qt.Key_PageDown):
                event.ignore()
                evt = QKeyEvent(QEvent.KeyPress, event.key(), 0)
                app = QApplication.instance()
                app.postEvent(self._search_filter, evt)
        return super(_SearchField, self).eventFilter(obj, event)

    def focusOutEvent(self, *args, **kwargs):
        super(_SearchField, self).focusOutEvent(*args, **kwargs)

        app = QApplication.instance()
        if app.focusWidget() not in (self._search_filter, self):
            self._search_filter.hide()


class _SearchFilter(QListWidget):
    item_selected = Signal(str)

    def __init__(self, *args, **kwargs):
        super(_SearchFilter, self).__init__(*args, **kwargs)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)
        self.itemActivated.connect(self._emit_current)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

    def eventFilter(self, *args, **kwargs):
        return super(_SearchFilter, self).eventFilter(*args, **kwargs)

    def _emit_current(self):
        selection = self.selectedItems()
        if selection:
            self.item_selected.emit(selection[0].text())
            self.hide()
