from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTreeWidget, QVBoxLayout, QTreeWidgetItem, QApplication, QDialog, QPushButton, \
    QHBoxLayout, QGridLayout, QLabel, QLineEdit, QSpinBox

from file_manager.data.connection import get_engine
from file_manager.data.query import Query


class TableEditor(QDialog):
    def __init__(self, model_class, allow_create=False, *args, **kwargs):
        """
        :type model_class: file_manager.data.base_model.BaseModel
        """
        super(TableEditor, self).__init__(*args, **kwargs)

        self._model = model_class
        self._allow_create = allow_create
        self._tree = QTreeWidget()
        self._columns = [field.name for field in self._model.fields()
                         if field.name not in ('id', 'timestamp', 'username')]

        self._btn_add = QPushButton('Create %s' % model_class.NAME.title())

        self._build_ui()
        self._build_connections()
        self._setup_ui()

        self._populate()

    def _build_ui(self):
        self._tree.setRootIsDecorated(False)
        self._tree.setSelectionMode(QTreeWidget.ExtendedSelection)

        lyt_main = QVBoxLayout()
        if self._allow_create:
            lyt_top = QHBoxLayout()
            lyt_top.setContentsMargins(0, 0, 0, 0)
            lyt_top.setSpacing(0)
            lyt_top.addWidget(self._btn_add)
            lyt_top.addStretch()
            lyt_main.addLayout(lyt_top)
        lyt_main.addWidget(self._tree)
        self.setLayout(lyt_main)

    def _build_connections(self):
        self._tree.itemChanged.connect(self._column_data_changed)
        self._btn_add.clicked.connect(self._create_record)

    def _setup_ui(self):
        self._tree.setColumnCount(len(self._columns))
        self._tree.setHeaderLabels(self._columns)
        self._tree.setSortingEnabled(True)
        self._tree.setEditTriggers(QTreeWidget.DoubleClicked)

    def _create_record(self):
        editor = RecordCreation(self._model, parent=self)
        editor.exec_()
        # TODO

    def _column_data_changed(self, item, column_number):
        column = self._columns[column_number]

        record = item.data(0, Qt.UserRole)
        setattr(record, column, item.data(column_number, Qt.DisplayRole))
        get_engine().update(record)

    def _populate(self):
        query = Query(self._model.NAME)

        engine = get_engine()
        result = engine.select(query)
        for item in result:
            values = [getattr(item, c) for c in self._columns]
            values = [str(v) if v not in (None, 0) else '' for v in values]
            titem = QTreeWidgetItem(values)
            titem.setFlags(titem.flags() | Qt.ItemIsEditable)
            titem.setData(0, Qt.UserRole, item)
            self._tree.addTopLevelItem(titem)
        for i in range(self._tree.columnCount()):
            self._tree.resizeColumnToContents(i)


class RecordCreation(QDialog):
    def __init__(self, model, *args, **kwargs):
        super(RecordCreation, self).__init__(*args, **kwargs)

        self._model = model

        self._wdg_map = dict()

        self._btn_cancel = QPushButton('CANCEL')
        self._btn_create = QPushButton('CREATE')

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def _build_ui(self):
        fields = self._model.fields()
        fields = [x for x in fields if x.name not in ('id', 'timestamp', 'username')]

        lyt_buttons = QHBoxLayout()
        lyt_buttons.addWidget(self._btn_create)
        lyt_buttons.addWidget(self._btn_cancel)

        r = 0
        lyt_grid = QGridLayout()
        for field in fields:
            editor = QLineEdit()
            if field.type == int:
                editor = QSpinBox()
                editor.setRange(-1000000, 1000000)
            self._wdg_map[field] = editor
            lyt_grid.addWidget(QLabel(field.name), r, 0)
            lyt_grid.addWidget(editor, r, 1)
            r += 1

        lyt_main = QVBoxLayout()
        lyt_main.addLayout(lyt_grid)
        lyt_main.addLayout(lyt_buttons)

        self.setLayout(lyt_main)

    def _build_connections(self):
        self._btn_cancel.clicked.connect(self.reject)
        self._btn_create.clicked.connect(self._create_record)

    def _setup_ui(self):
        self.setWindowTitle('%s Creation' % self._model.NAME.title())
        self.setMinimumWidth(300)

    def _create_record(self):
        data = dict()
        for field, wdg in self._wdg_map.items():
            column = field.name
            if field.type == int:
                value = wdg.value()
            else:
                value = wdg.text()
            data[column] = value

        record = self._model(**data)
        get_engine().create(record)

        self.accept()


if __name__ == '__main__':
    from file_manager.data.models.tag import TagModel

    app = QApplication([])
    ui = TableEditor(TagModel)
    ui.resize(1200, 900)
    ui.show()
    app.exec_()
