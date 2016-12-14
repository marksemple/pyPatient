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
        self.currentUID = 0
        self.UID_zero = 0
        self.PlottableImage = ImageItem()

    def updateScene(self, sliceUID):
        if self.showingImage:
            self.PlottableImage.updatePlottable(UID=sliceUID)
            for contour in self.PlottableContours.values():
                contour.updatePlottable(UID=sliceUID)

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
        # try:
        self.ImVolume = DicomDataModel(diDir=dicomDir)
        # except Exception as e:
            # print(e)
            # print("error in making IMVolume")
            # return

        self.addImages(imageModel=self.ImVolume)

    def addImages(self, imageModel):
        # Get DicomData Pixel Transformations
        # self.T_patient_pixels = imageModel.PP2IMTransformation
        # self.T_pixels_patient = imageModel.IM2PPTransformation
        TPat2Pix = imageModel.TPat2Pix
        self.UID_zero = imageModel.Ind2UID[0]
        self.currentUID = self.UID_zero

        # Add Image Object (for DICOM pixel array)
        self.PlottableImage = DicomImagePlotItem(dicomModel=imageModel)
        self.myPlot.addItem(self.PlottableImage)

        # Add Contour Object (if there are any!)
        if bool(imageModel.contourObjs):
            self.createContourPlottables(contourDict=imageModel.contourObjs,
                                         Pat2PixTForm=TPat2Pix,
                                         UID2IndDict=imageModel.UID2Ind)

        # Tidy Up
        self.showingImage = True
        self.PlotWidge.autoRange()
        self.configureSliceSlider()
        self.setupClearDataModel()

    def createContourPlottables(self, contourDict, *args, **kwargs):
        """ create/store list of 'active contour objects' for plotting
        also make, but don't store list of projections of contours """

        self.PlottableContours = {}
        for ROI in contourDict['ROI']:
            contourP = self.getContourPlottable(ROIDict=ROI, *args, **kwargs)
            self.PlottableContours[ROI['ROIName']] = contourP
            self.myPlot.addItem(contourP)

        self.populateLegend(legend=self.legend,
                            contourDict=self.PlottableContours)

    def getContourPlottable(self, *args, **kwargs):
        return DicomContourPlotItem(*args, **kwargs)

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
        dicomMin = min(self.ImVolume.Loc2Ind.keys())
        dicomMax = max(self.ImVolume.Loc2Ind.keys())
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
        newSliceLoc = min(self.ImVolume.Loc2Ind.keys(),
                          key=lambda x: abs(x - newSliderVal))
        newSliceIndex = self.ImVolume.Loc2Ind[newSliceLoc]
        newSliceLoc = round(newSliceLoc * 1000) / 1000
        maxInd = max(self.ImVolume.Ind2Loc.keys())
        self.depthGauge.setText("{:>1.2f} mm".format(newSliceLoc))
        self.sliceIndGauge.setText(
            "Slice {}/{}".format(newSliceIndex, maxInd))

        newUID = self.ImVolume.Ind2UID[newSliceIndex]
        if not newUID == self.currentUID:
            self.currentUID = newUID
            self.updateScene(sliceUID=newUID)

    def updateGauges(self, newSliderVal=0):
        newSliderVal = self.dispView.sliceSlider.value()
        newSliceLocation = min(self.ImVolume.sliceLoc2Ind.keys(),
                               key=lambda x: abs(x - newSliderVal))
        newSliceIndex = self.ImVolume.sliceLoc2Ind[newSliceLocation]
        self.thisSliceIndex = newSliceIndex
        self.thisSliceLoc = newSliceLocation

    def populateLegend(self, legend, contourDict={}):
        for thisContour in contourDict:
            legend.addItem(item=contourDict[thisContour],
                           name=('   ' + thisContour))

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
    form = dicomViewWidget(
        directory=r"C:\Users\MarkSemple\Documents\Sunnybrook Research Institute\DeformableRegistration\CLEAN - Sample Data 10-02-2016\MRtemp")
    app.setActiveWindow(form)
    form.show()

    sys.exit(app.exec_())
