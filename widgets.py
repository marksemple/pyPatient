# Third-party Modules
from PyQt4.QtCore import *
from PyQt4.QtGui import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                         QSlider, QLabel, QPushButton, QFileDialog)
from pyqtgraph import PlotWidget, ImageItem
import numpy as np

from dicomModule.dataModels import *
import sys


class dicomViewWidget(QWidget):
    """ GENERIC DICOM VIEWER WIDGET
        This class defines the layout only
        A controller is required to do anything
     """

    def __init__(self, parent=None, directory=None, **kwargs):

        super().__init__(parent=parent)
        self.showingImage = False
        self.new_slice_to_show = True
        self.thisSliceLoc = 0
        self.thisSliceIndex = 0
        self.T_MRI_Ref = np.eye(4)
        self.T_patient_pixels = np.eye(4)
        self.viewToolsLayout = depthLayout = QVBoxLayout()
        ImAxes = self.createAxes()
        self.createControls()
        depthLayout.addWidget(self.dirFinder, 0, Qt.AlignCenter)
        depthLayout.addWidget(self.depthGauge, 0, Qt.AlignCenter)
        depthLayout.addWidget(self.sliceSlider, 1, Qt.AlignHCenter)
        depthLayout.addWidget(self.sliceIndGauge, 0, Qt.AlignCenter)
        centralLayout = QHBoxLayout()
        centralLayout.addWidget(ImAxes)
        centralLayout.addLayout(depthLayout)
        self.setLayout(centralLayout)
        self.ImAxes = ImAxes

        if directory is not None:
            self.addImages(directory)

    def createAxes(self):
        ImAxes = PlotWidget()
        self.myPlot = myPlot = ImAxes.getPlotItem()
        myPlot.showAxis('bottom', False)
        myPlot.showAxis('left', False)
        myView = myPlot.getViewBox()
        myView.setAspectLocked(True)
        myView.invertY(True)
        ImAxes.setRange(xRange=(-200, 200))
        ImAxes.setBackground('#C0C0C0')
        self.PlottableImage = ImageItem(pxMode=False)
        self.myPlot.addItem(self.PlottableImage)
        return ImAxes

    def createControls(self):
        self.sliceSlider = QSlider()
        self.sliceSlider.setEnabled(True)
        self.sliceSlider.valueChanged.connect(self.sliderChanged)
        self.depthGauge = QLabel("0.0 mm")
        self.depthGauge.setMinimumWidth(50)
        self.sliceIndGauge = QLabel("Slice 0 / 0")
        self.dirFinder = QPushButton("Select Images")
        self.dirFinder.clicked.connect(self.selectImages)

    def selectImages(self):
        dicomDir = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select Dicom Directory",
            directory="P:\\USERS\\PUBLIC\\Mark Semple\\EM Navigation\\Practice DICOM Sets\\EM test")
        if dicomDir is '':
            pass
            return
        self.addImages(dicomDir)

    def addImages(self, diDir):
        try:
            self.ImVolume = DicomDataModel(diDir=diDir)
        except Exception as e:
            print(e)
            return
        self.T_patient_pixels = self.ImVolume.PP2IMTransformation
        self.PlottableImage.setImage(self.ImVolume.pixelData[:, :, 0].T)
        self.showingImage = True
        self.ImAxes.autoRange()
        self.configureSliceSlider()
        self.updateScene(0)

    def configureSliceSlider(self):
        dicomMin = min(self.ImVolume.sliceLoc2Ind.keys())
        dicomMax = max(self.ImVolume.sliceLoc2Ind.keys())
        # dicomRange = dicomMax - dicomMin
        self.sliceSlider.setEnabled(True)
        self.sliceSlider.setRange(dicomMin, dicomMax)
        self.sliceSlider.setValue(dicomMin)
        self.sliderChanged()

    def updateScene(self, sliceInd):
        if not self.showingImage:
            return
        try:
            sliceInd = self.ImVolume.sliceLoc2Ind[sliceInd]
        except KeyError as e:
            print(e)
        # update Image
        newImage = self.ImVolume.pixelData[:, :, sliceInd].T
        self.PlottableImage.setImage(image=newImage, autoDownsample=True)
        # update Contours
        # self.ContourData2Plottable(self.ImVolume.contourObjs, sliceInd)

    def sliderChanged(self):
        if not self.showingImage:
            return
        """ on change of SliceSlider value: """
        newSliderVal = self.sliceSlider.value()
        newSliceLoc = min(self.ImVolume.sliceLoc2Ind.keys(),
                          key=lambda x: abs(x - newSliderVal))
        newSliceIndex = self.ImVolume.sliceLoc2Ind[newSliceLoc]
        newSliceLoc = round(newSliceLoc * 1000) / 1000
        maxInd = max(self.ImVolume.sliceInd2Loc.keys())
        self.depthGauge.setText("{:>1.2f} mm".format(newSliceLoc))
        self.sliceIndGauge.setText(
            "Slice {}/{}".format(newSliceIndex, maxInd))
        self.thisSliceIndex = newSliceIndex
        self.thisSliceLoc = newSliceLoc
        self.updateScene(newSliceLoc)

    def updateGauges(self, newSliderVal=0):
        newSliderVal = self.dispView.sliceSlider.value()
        newSliceLocation = min(self.ImVolume.sliceLoc2Ind.keys(),
                               key=lambda x: abs(x - newSliderVal))
        newSliceIndex = self.ImVolume.sliceLoc2Ind[newSliceLocation]
        self.thisSliceIndex = newSliceIndex
        self.thisSliceLoc = newSliceLocation

    def closeEvent(self, event):
        print("Closing the app")
        self.deleteLater()


if __name__ == "__main__":

    app = QApplication(sys.argv)
    form = dicomViewWidget()
    app.setActiveWindow(form)
    form.show()

    sys.exit(app.exec_())
