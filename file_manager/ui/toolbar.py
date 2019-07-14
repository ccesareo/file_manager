from Qt import QtCore, QtGui, QtWidgets


class FileManagerToolbar(QtWidgets.QWidget):
    tags_changed = QtCore.Signal(str)
    assets_changed = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super(FileManagerToolbar, self).__init__(*args, **kwargs)

        self._cmbo_search_type = FlatCombo(['asset', 'tag'])
        self._edit_search = QtWidgets.QLineEdit()

        self._timer_search = QtCore.QTimer()
        self._timer_search.setSingleShot(True)
        self._timer_search.setInterval(300)

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def _build_ui(self):
        self.setFixedHeight(40)
        self._edit_search.setFixedHeight(34)
        self._edit_search.setFixedWidth(400)

        lyt_main = QtWidgets.QHBoxLayout()
        lyt_main.setContentsMargins(0, 0, 0, 0)
        lyt_main.setSpacing(5)
        lyt_main.addStretch()
        lyt_main.addWidget(self._cmbo_search_type)
        lyt_main.addWidget(self._edit_search)
        lyt_main.addStretch()
        self.setLayout(lyt_main)

    def _build_connections(self):
        self._edit_search.textChanged.connect(self._timer_search.start)

        self._cmbo_search_type.option_changed.connect(self._edit_search.clear)
        self._cmbo_search_type.option_changed.connect(self._timer_search.start)

        # TODO - emit regex
        self._timer_search.timeout.connect(self._search_changed)

    def _setup_ui(self):
        self._edit_search.setStyleSheet("""
        QLineEdit {
            border-radius: 17px;
            font-size: 18px;
        }
        """)
        self._edit_search.setAlignment(QtCore.Qt.AlignCenter)

    def _search_type(self):
        return self._cmbo_search_type.current_text()

    def _search_changed(self):
        search_text = self._edit_search.text()
        if self._search_type() == 'asset':
            self.assets_changed.emit(search_text)
        elif self._search_type() == 'tag':
            self.tags_changed.emit(search_text)


class FlatCombo(QtWidgets.QWidget):
    option_changed = QtCore.Signal(str)

    def __init__(self, options, *args, **kwargs):
        super(FlatCombo, self).__init__(*args, **kwargs)

        assert options, 'No options given.'

        self._lbl = QtWidgets.QLabel(options[0])
        self._btn = QtWidgets.QPushButton(u'\u25BC')

        self._items = options[:]

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    # noinspection PyPep8Naming
    def mouseReleaseEvent(self, evt):
        if evt.button() == QtCore.Qt.LeftButton:
            self._show_menu()
            return True
        else:
            return super(FlatCombo, self).mouseReleaseEvent(evt)

    def current_text(self):
        return self._lbl.text()

    def _build_ui(self):
        lyt = QtWidgets.QHBoxLayout()
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setSpacing(2)
        lyt.addWidget(self._lbl)
        lyt.addWidget(self._btn)
        self.setLayout(lyt)

    def _build_connections(self):
        self._btn.clicked.connect(self._show_menu)

    def _setup_ui(self):
        self._btn.setFixedSize(20, 20)
        self._btn.setFlat(True)

        _font = self.font()
        _font.setBold(True)
        self._btn.setFont(_font)
        self._lbl.setFont(_font)

        self._lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self._lbl.setStyleSheet('font-size: 16px;')
        self._btn.setStyleSheet('border: none;')

    def _show_menu(self):
        menu = QtWidgets.QMenu()
        for item in self._items:
            menu.addAction(item)
        a = menu.exec_(QtGui.QCursor().pos())
        if a is not None:
            value = a.text()
            self._lbl.setText(value)
            self.option_changed.emit(value)
