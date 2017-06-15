# tester
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from new_ROI_dialog import newROIDialog


class ContourTable(QWidget):

    headers = ['ROI', 'Slices', 'Contours', 'Holes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.createLayout()

    def createLayout(self):
        table = self.table = QTableWidget()
        table.setColumnCount(len(self.headers))
        table.setHorizontalHeaderLabels(self.headers)
        table.verticalHeader().setVisible(False)
        table.cellClicked.connect(self.onCellClick)

        bttn = QPushButton("Add ROI")
        bttn.clicked.connect(self.onNewROIBttnClick)

        layout = QGridLayout()
        layout.addWidget(bttn, 0, 0)
        layout.addWidget(table, 1, 0)
        self.setLayout(layout)

    def addNewROI(self, roiName, roiColor):
        row = self.table.rowCount()
        self.table.insertRow(row)
        item = QTableWidgetItem(roiName)
        self.table.setItem(row, 0, item)
        item.setBackground(QBrush(QColor(*roiColor)))

    def onNewROIBttnClick(self):
        dlg = newROIDialog()
        dlg.exec_()
        print(dlg.makeStatus)
        if dlg.makeStatus:
            self.addNewROI(dlg.name, dlg.color)

    def onCellClick(self, row, col):
        # print(table)
        print(row, col)
        if col == 0:
            print('ROI')
        elif col == 1:
            print(col)
        elif col == 2:
            print(col)
        elif col == 3:
            print(col)




if __name__ == "__main__":

    app = QApplication(sys.argv)
    form = ContourTable()
    form.show()
    sys.exit(app.exec_())
