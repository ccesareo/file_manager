from Qt import QtWidgets


def ask(title, question):
    dlg = QtWidgets.QDialog()
    dlg.setWindowTitle(title)

    yes = QtWidgets.QPushButton('Yes')
    yes.clicked.connect(dlg.accept)
    no = QtWidgets.QPushButton('No')
    no.clicked.connect(dlg.reject)

    lyt = QtWidgets.QGridLayout()
    lyt.addWidget(QtWidgets.QLabel(question), 0, 0, 1, 2)
    lyt.addWidget(yes, 1, 0)
    lyt.addWidget(no, 1, 1)
    dlg.setLayout(lyt)
    return dlg.exec_()
