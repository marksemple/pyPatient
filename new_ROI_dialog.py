from PyQt5.QtWidgets import (QDialog, QLineEdit, QPushButton,
                             QGridLayout, QLabel, QColorDialog)
from PyQt5.QtCore import (Qt,)


class newROIDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.color = (238, 108, 108)
        self.name = 'contour'
        self.makeStatus = False

        okBttn = QPushButton("Create")
        okBttn.clicked.connect(self.onAccept)
        cancelBttn = QPushButton("Cancel")
        cancelBttn.clicked.connect(self.close)

        self.nameEdit = QLineEdit()
        self.nameEdit.textChanged.connect(self.onNameEdit)
        self.colorPick = QPushButton()
        self.colorPick.clicked.connect(self.onChooseColor)
        self.styleColorBttn(self.color)

        layout = QGridLayout()
        layout.addWidget(QLabel("ROI Name"), 0, 0)
        layout.addWidget(self.nameEdit, 0, 1, 1, 2)
        layout.addWidget(QLabel("ROI Color"), 1, 0)
        layout.addWidget(self.colorPick, 1, 1, 1, 2)
        layout.addWidget(QLabel(''), 2, 0, 1, 3)
        layout.addWidget(okBttn, 3, 1)
        layout.addWidget(cancelBttn, 3, 2)

        self.setLayout(layout)
        self.setWindowTitle("Create ROI")
        self.setWindowFlags(Qt.FramelessWindowHint)

    def onNameEdit(self, newName):
        # print(newName)
        self.name = newName

    def onChooseColor(self):
        colorDiag = QColorDialog()
        colorDiag.exec_()
        color = colorDiag.selectedColor()
        self.color = color.getRgb()
        self.styleColorBttn(self.color)

    def styleColorBttn(self, color):
        self.colorPick.setStyleSheet("background-color: rgb(%i, %i, %i);" %
                                     (self.color[0],
                                      self.color[1],
                                      self.color[2]))

    def getProperties(self):
        return (self.nameEdit.text(), self.color)

    def onAccept(self):
        self.makeStatus = True
        self.close()

