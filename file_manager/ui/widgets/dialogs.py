from PySide2.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton


def ask(title, question):
    dlg = QDialog()
    dlg.setWindowTitle(title)

    yes = QPushButton('Yes')
    yes.clicked.connect(dlg.accept)
    no = QPushButton('No')
    no.clicked.connect(dlg.reject)

    lyt = QGridLayout()
    lyt.addWidget(QLabel(question), 0, 0, 1, 2)
    lyt.addWidget(yes, 1, 0)
    lyt.addWidget(no, 1, 1)
    dlg.setLayout(lyt)
    return dlg.exec_()
