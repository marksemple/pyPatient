# Third-party Modules
from PyQt4 import QtCore
from PyQt4.QtGui import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                         QSlider, QLabel, QPushButton, QFileDialog,
                         QDialogButtonBox, QMessageBox, QIcon, QDialog)
from pyqtgraph import PlotWidget, ImageItem, mkPen, LegendItem, ImageItem
import numpy as np

from dicomModule.dataModels import *
from dicomModule.plottables import DicomImagePlotItem, DicomContourPlotItem
# from dicomModule.ContourDataItem import contourPlotModel
import sys


class dicomViewWidget(QWidget):
    """ GENERIC DICOM VIEWER WIDGET
        This class defines the layout only
        A controller is required to do anything
     """

    def __init__(self, parent=None, directory=None, **kwargs):
        super().__init__(parent=parent)

        self.parent = parent
        self.showingImage = False
        self.new_slice_to_show = True
        self.startingDirectory = "C:\\"  # Where to begin dicom im search

        self.createControls()
        self.createAxes()
        self.PlottableImage = ImageItem()
        self.initializeModel()

        centralLayout = QHBoxLayout()
        centralLayout.addWidget(self.PlotWidge)
        centralLayout.addLayout(self.viewToolsLayout)
        self.setLayout(centralLayout)

    def createAxes(self):
        PlotWidge = self.PlotWidge = self.getPlotWidgeObject()
        myPlot = self.myPlot = PlotWidge.getPlotItem()
        # myPlot.showAxis('bottom', False)
        # myPlot.showAxis('left', False)
        myView = myPlot.getViewBox()
        myView.setAspectLocked(True)
        myView.invertY(True)
        PlotWidge.setRange(xRange=(-200, 200))
        PlotWidge.setBackground('#C0C0C0')
        PlotWidge.hideButtons()
        legend = self.legend = LegendItem()
        legend.setParentItem(myPlot)

    def getPlotWidgeObject(self):
        # For Default DicomViewWidget: use Default pyqtgraph Plot Widget
        # Can be overrode using this function in subclasses of DicomViewWidget
        return PlotWidget()

    def createControls(self):
        self.viewToolsLayout = depthLayout = QVBoxLayout()
        self.sliceSlider = QSlider()
        self.sliceSlider.setEnabled(True)
        self.sliceSlider.valueChanged.connect(self.sliderChanged)
        self.depthGauge = QLabel("0.0 mm")
        self.depthGauge.setMinimumWidth(50)
        self.sliceIndGauge = QLabel("Slice 0 / 0")
        self.dirFinder = QPushButton("Select Images")
        self.dirFinder.clicked.connect(self.selectImages)

        depthLayout.addWidget(self.dirFinder, 0, QtCore.Qt.AlignCenter)
        depthLayout.addWidget(self.depthGauge, 0, QtCore.Qt.AlignCenter)
        depthLayout.addWidget(self.sliceSlider, 1, QtCore.Qt.AlignHCenter)
        depthLayout.addWidget(self.sliceIndGauge, 0, QtCore.Qt.AlignCenter)

    def initializeModel(self, sliceLoc=0, sliceIndex=0):
        self.thisSliceLoc = sliceLoc
        self.thisSliceIndex = 0
        self.T_MRI_Ref = np.eye(4)
        self.T_patient_pixels = np.eye(4)
        self.T_pixels_patient = np.eye(4)
        self.PlottableContours = {}
        self.sliceIndGauge.setText("Slice 0 / 0")
        self.depthGauge.setText("0.0 mm")

    def setupAddDataModel(self):
        self.dirFinder.setText("Select Images")
        self.dirFinder.clicked.disconnect()
        self.dirFinder.clicked.connect(self.selectImages)

    def selectImages(self):
        """ Open Dialog to find directory with Dicom Files """
        dicomDir = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select Dicom Directory",
            directory=self.startingDirectory)
        if dicomDir is '':
            return
        try:
            self.ImVolume = DicomDataModel(diDir=dicomDir)
        except Exception as e:
            print(e)
            return

        self.addImages(self.ImVolume)

    def addImages(self, imageModel):
        # Get DicomData Pixel Transformations
        self.T_patient_pixels = imageModel.PP2IMTransformation
        self.T_pixels_patient = imageModel.IM2PPTransformation

        # Add Image Object (for DICOM pixel array)
        self.PlottableImage = DicomImagePlotItem(dicomModel=imageModel)
        self.myPlot.addItem(self.PlottableImage)

        # Add Contour Object
        if imageModel.contourObjs:
            self.createContourPlottables(contourDict=imageModel.contourObjs)

        # Tidy Up
        self.showingImage = True
        self.PlotWidge.autoRange()
        self.configureSliceSlider()
        self.updateScene(0)
        self.setupClearDataModel()

    def createContourPlottables(self, contourDict):
        """ create/store dict of 'active contour objects' for plotting
        also make, but don't store list of projections of contours """

        indRange = range(0, max(self.ImVolume.sliceInd2Loc.keys())+1)
        print('iRange', list(indRange))

        for contour in contourDict.values():
            self.PlottableContours[contour.contourName] = []
            pen = mkPen(color=contour.colz, width=2)

            for loop in range(contour.NLoops):

                contourLine = DicomContourPlotItem(
                    contourDataModel=contour,
                    loopInd=loop,
                    Pat2PixTForm=self.T_patient_pixels,
                    sliceIndList=list(indRange),
                    pen=pen, symbol=None)

                # END HERE, STUFF BELOW ADD ELSEWHERE
                self.myPlot.addItem(contourLine)
                self.PlottableContours[contour.contourName].append(contourLine)

        self.populateLegend(self.legend)

    def setupClearDataModel(self):
        """ Change bttn function to be CLEAR DATA """
        self.dirFinder.setText("Clear Data")
        self.dirFinder.clicked.disconnect()
        self.dirFinder.clicked.connect(self.clearImagesWarning)

    def clearImagesWarning(self, **kwargs):
        """ Confirm with User that they want to Clear Plot"""
        qbb = QDialog(**kwargs)
        qbb.setWindowTitle("Clear Data?")
        qbb.setWindowModality(QtCore.Qt.ApplicationModal)
        ok = QPushButton("Clear")
        no = QPushButton("Cancel")
        ok.clicked.connect(self.clearImages)
        ok.clicked.connect(qbb.close)
        no.clicked.connect(qbb.close)
        layout = QVBoxLayout(qbb)
        layout.addWidget(QLabel("Are you sure you want to clear data?"))
        layout.addSpacing(20)
        bttnLayout = QHBoxLayout()
        bttnLayout.addWidget(ok)
        bttnLayout.addWidget(no)
        layout.addLayout(bttnLayout)
        qbb.exec_()

    def clearImages(self):
        """ Reset and Clear Axes """
        self.myPlot.clear()
        # for item in [self.PlottableImage]:
            # del item
        self.showingImage = False
        self.clearLegend(self.legend)
        self.initializeModel()
        self.setupAddDataModel()

    def configureSliceSlider(self):
        dicomMin = min(self.ImVolume.sliceLoc2Ind.keys())
        dicomMax = max(self.ImVolume.sliceLoc2Ind.keys())
        # dicomRange = dicomMax - dicomMin
        self.sliceSlider.setEnabled(True)
        self.sliceSlider.setRange(dicomMin, dicomMax)
        self.sliceSlider.setValue(dicomMin)
        self.sliderChanged()

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
        # print("Slice: ", newSliceIndex)
        self.updateScene(sliceInd=newSliceIndex)

    def updateScene(self, sliceInd):
        if not self.showingImage:
            return
        self.PlottableImage.updatePlottable(sliceIndex=sliceInd)
        for contour in self.PlottableContours.values():
            for loop in contour:
                loop.updatePlottable(sliceIndex=sliceInd)

    def updateGauges(self, newSliderVal=0):
        newSliderVal = self.dispView.sliceSlider.value()
        newSliceLocation = min(self.ImVolume.sliceLoc2Ind.keys(),
                               key=lambda x: abs(x - newSliderVal))
        newSliceIndex = self.ImVolume.sliceLoc2Ind[newSliceLocation]
        self.thisSliceIndex = newSliceIndex
        self.thisSliceLoc = newSliceLocation

    def populateLegend(self, legend):
        for contourName in self.PlottableContours:
            thisLine = self.PlottableContours[contourName][0]
            legend.addItem(item=thisLine,
                           name=('   ' + contourName))

    def clearLegend(self, legend):
        legend.items = []
        while legend.layout.count() > 0:
            legend.layout.removeAt(0)
        self.myPlot.removeItem(legend)

    def closeEvent(self, event):
        print("Closing the app")
        self.deleteLater()


if __name__ == "__main__":

    app = QApplication(sys.argv)
    form = dicomViewWidget(directory=r"C:\Users\MarkSemple\Documents\Sunnybrook Research Institute\DeformableRegistration\CLEAN - Sample Data 10-02-2016\MRtemp")
    app.setActiveWindow(form)
    form.show()

    sys.exit(app.exec_())
