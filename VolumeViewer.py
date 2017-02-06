# -*- coding: utf-8 -*-
"""
General Widgets for Dicom-related Programs
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout,
                             QSlider, QLabel,)
from PyQt5.QtCore import (Qt,)
import pyqtgraph as pg
import numpy as np


class QVolumeViewerWidget(QWidget):
    """ Used to Display A Slice of 3D Image Data
    """

    def __init__(self,
                 imageData=None,
                 TForm=np.eye(4),
                 backgroundColor="#CCCCCC",
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        assert(type(imageData) == np.ndarray)

        self.imageData = imageData
        self.TForm = TForm
        self.measureImage(imageData)

        # ~ Add Image Item to Plot Widget
        self.plotWidge = self.createViewPortal(backgroundCol=backgroundColor)
        self.imageItem = pg.ImageItem(self.imageData[:, :, 0])
        self.plotWidge.addItem(self.imageItem)

        # ~ Create Widget parts
        self.createControls()
        self.applyLayout()

    def measureImage(self, imageData):

        self.nRows, self.nCols, self.nSlices = imageData.shape
        # transform stuff here


    def createViewPortal(self, backgroundCol='#FFFFFF'):
        plotWidge = pg.PlotWidget()
        plotWidge.showAxis('left', False)
        plotWidge.showAxis('bottom', False)
        viewBox = plotWidge.getViewBox()
        viewBox.setAspectLocked(1.0)
        viewBox.setBackgroundColor(backgroundCol)
        return plotWidge

    def createControls(self):
        # ~ Create controls
        MW = 40  # minimumWidth
        self.slider = QSlider()
        self.slider.valueChanged.connect(self.sliderChanged)
        self.slider.setMinimum(0)
        self.slider.setPageStep(1)
        self.slider.setMaximum(self.nSlices - 1)
        self.slider.setMinimumWidth(MW)
        self.sliceNumLabel = QLabel("1 / %d" % (self.nSlices))
        self.sliceDistLabel = QLabel("0.00")

    def applyLayout(self):
        # ~ Create "Controls" Panel Layout for Slider
        sliderLayout = QVBoxLayout()
        sliderLayout.addWidget(self.sliceNumLabel, 0, Qt.AlignCenter)
        sliderLayout.addWidget(self.sliceDistLabel, 0, Qt.AlignCenter)
        sliderLayout.addWidget(self.slider)
        # ~ Create widget-wide grid layout
        layout = QGridLayout()
        layout.addWidget(self.plotWidge, 1, 1)
        layout.addLayout(sliderLayout, 1, 2)
        self.setLayout(layout)

    def sliderChanged(self, newValue):
        self.imageItem.setImage(self.imageData[:, :, newValue])
        self.sliceNumLabel.setText("%d / %d" % (newValue + 1, self.nSlices))


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    myImage = np.random.random((500, 500, 20)) * 255
    form = QVolumeViewerWidget(imageData=myImage,
                               backgroundColor="#ABCDEF")
    form.show()
    sys.exit(app.exec_())
