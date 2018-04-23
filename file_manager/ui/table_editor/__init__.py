from PySide2.QtWidgets import QWidget, QTreeWidget, QVBoxLayout, QTreeWidgetItem

from file_manager.data.connection import get_engine
from file_manager.data.query import Query


class FileManagerTableEditor(QWidget):
    def __init__(self, model_class, *args, **kwargs):
        """
        :type model_class: file_manager.data.base_model.BaseModel
        """
        super(FileManagerTableEditor, self).__init__(*args, **kwargs)

        self._model = model_class
        self._tree = QTreeWidget()
        self._columns = [field.name for field in self._model.fields()]

        self._build_ui()
        self._build_connections()
        self._setup_ui()

        self._populate()

    def _build_ui(self):
        self._tree.setRootIsDecorated(False)
        self._tree.setSelectionMode(QTreeWidget.ExtendedSelection)

        lyt_main = QVBoxLayout()
        lyt_main.setContentsMargins(0, 0, 0, 0)
        lyt_main.setSpacing(0)
        lyt_main.addWidget(self._tree)
        self.setLayout(lyt_main)

    def _build_connections(self):
        pass

    def _setup_ui(self):
        fields = self._model.fields()

        self._tree.setColumnCount(len(fields))
        self._tree.setHeaderLabels([x.name for x in fields])

    def _populate(self):
        query = Query(self._model.NAME)

        engine = get_engine()
        result = engine.select(query)
        for item in result:
            values = [getattr(item, c) for c in self._columns]
            values = [str(v) if v not in (None, 0) else '' for v in values]
            item = QTreeWidgetItem(values)
            self._tree.addTopLevelItem(item)
        for i in range(self._tree.columnCount()):
            self._tree.resizeColumnToContents(i)
