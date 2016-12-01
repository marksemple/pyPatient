# Third-party Modules
from PyQt4.QtCore import *
from PyQt4.QtGui import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                         QSlider, QLabel, QPushButton, QFileDialog)
from pyqtgraph import PlotWidget, ImageItem, mkPen, LegendItem
import numpy as np

from dicomModule.dataModels import *
from dicomModule.ContourDataItem import contourPlotModel
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
        centralLayout.addWidget(self.ImAxes)
        centralLayout.addLayout(self.viewToolsLayout)
        self.setLayout(centralLayout)

        if directory is not None:
            self.addImages(directory)

    def createAxes(self):
        ImAxes = self.ImAxes = self.getImAxesObject()
        myPlot = self.myPlot = ImAxes.getPlotItem()
        myPlot.showAxis('bottom', False)
        myPlot.showAxis('left', False)
        myView = myPlot.getViewBox()
        myView.setAspectLocked(True)
        myView.invertY(True)
        ImAxes.setRange(xRange=(-200, 200))
        ImAxes.setBackground('#C0C0C0')
        legend = self.legend = LegendItem()
        legend.setParentItem(myPlot)

    def getImAxesObject(self):
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

        depthLayout.addWidget(self.dirFinder, 0, Qt.AlignCenter)
        depthLayout.addWidget(self.depthGauge, 0, Qt.AlignCenter)
        depthLayout.addWidget(self.sliceSlider, 1, Qt.AlignHCenter)
        depthLayout.addWidget(self.sliceIndGauge, 0, Qt.AlignCenter)

    def initializeModel(self):
        self.thisSliceLoc = 0
        self.thisSliceIndex = 0
        self.T_MRI_Ref = np.eye(4)
        self.T_patient_pixels = np.eye(4)
        self.PlottableContours = {}
        self.sliceIndGauge.setText("Slice 0 / 0")
        self.depthGauge.setText("0.0 mm")

    def selectImages(self):
        dicomDir = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select Dicom Directory",
            directory=self.startingDirectory)

        if dicomDir is '':
            return

        self.addImages(diDir=dicomDir)

    def setupAddImages(self):
        self.dirFinder.setText("Select Images")
        self.dirFinder.clicked.disconnect()
        self.dirFinder.clicked.connect(self.selectImages)

    def addImages(self, diDir):
        try:
            self.ImVolume = DicomDataModel(diDir=diDir)
        except Exception as e:
            print(e)
            return

        self.initializeModel()  # slices, transforms, etc.
        self.PlottableImage = ImageItem(pxMode=False)
        self.PlottableImage.setZValue(-1)  # put at background
        self.myPlot.addItem(self.PlottableImage)

        self.T_patient_pixels = self.ImVolume.PP2IMTransformation
        self.PlottableImage.setImage(self.ImVolume.pixelData[:, :, 0].T)
        if self.ImVolume.contourObjs:
            self.createContourPlottables(contourDict=self.ImVolume.contourObjs)
        self.showingImage = True
        self.ImAxes.autoRange()
        self.configureSliceSlider()
        self.updateScene(0)
        self.setupClearImages()

    def setupClearImages(self):
        self.dirFinder.setText("Clear Data")
        self.dirFinder.clicked.disconnect()
        self.dirFinder.clicked.connect(self.clearImages)

    def clearImages(self):
        self.myPlot.clear()
        # self.myPlot.removeItem(self.PlottableImage)
        self.initializeModel()

        self.showingImage = False
        self.clearLegend(self.legend)
        self.setupAddImages()

    def createContourPlottables(self, contourDict):
        """ create/store dict of 'active contour objects' for plotting
        also make, but don't store list of projections of contours """
        for contour in contourDict.values():
            self.PlottableContours[contour.contourName] = []
            for loops in range(contour.NLoops):
                pen = mkPen(color=contour.colz, width=2)
                contourLine = contourPlotModel(contourName=contour.contourName,
                                               pen=pen, symbol=None)
                self.myPlot.addItem(contourLine)
                self.PlottableContours[contour.contourName].append(contourLine)
        self.populateLegend(self.legend)

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
        self.updateScene(newSliceLoc)

    def updateScene(self, sliceInd):
        if not self.showingImage:
            return

        try:
            sliceInd = self.ImVolume.sliceLoc2Ind[sliceInd]
        except KeyError as e:
            print(e)

        self.updateImage(sliceInd)
        self.updateContours(sliceInd)

    # def updateScene(self, sliceInd):
    #     try:
    #         sliceInd = self.ImVolume.sliceLoc2Ind[sliceInd]
    #     except KeyError as e:
    #         print(e)
    #     # update Image
    #     newImage = self.ImVolume.pixelData[:, :, sliceInd].T
    #     self.PlottableImage.setImage(image=newImage, autoDownsample=True)
    #     # update Contours
    #     self.ContourData2Plottable(self.ImVolume.contourObjs, sliceInd)
    #     for contour in list(self.activeContours.values())[0]:
    #         contour.setDefaultData()

    def updateImage(self, sliceInd):
        newImage = self.ImVolume.pixelData[:, :, sliceInd].T
        self.PlottableImage.setImage(image=newImage, autoDownsample=True)

    def updateContours(self, sliceInd):
        self.ContourData2Plottable(modelDict=self.ImVolume.contourObjs,
                                   plottableDict=self.PlottableContours,
                                   sliceInd=sliceInd)

    def updateGauges(self, newSliderVal=0):
        newSliderVal = self.dispView.sliceSlider.value()
        newSliceLocation = min(self.ImVolume.sliceLoc2Ind.keys(),
                               key=lambda x: abs(x - newSliderVal))
        newSliceIndex = self.ImVolume.sliceLoc2Ind[newSliceLocation]
        self.thisSliceIndex = newSliceIndex
        self.thisSliceLoc = newSliceLocation

    def ContourData2Plottable(self, modelDict, plottableDict, sliceInd):
        """ update active contour objects """
        sliceLoc = self.thisSliceLoc

        for contour in modelDict:
            thisDataModel = modelDict[contour]
            thisPlottable = plottableDict[contour]

            for loop in range(thisDataModel.NLoops):
                if sliceLoc in thisDataModel.slice2ContCoords:
                    pts = thisDataModel.slice2ContCoords[sliceLoc][loop]
                    ptShape = pts.shape
                    if ptShape[1] == 3:  # if a bunch of row-vectors:
                        pts = pts.T
                        ptShape = pts.shape
                    placeholder = np.ones((4, ptShape[1]))
                    placeholder[:-1, :] = pts
                    pts = placeholder
                    pts = self.ImVolume.PP2IMTransformation.dot(pts)
                    xs = pts[:][0]
                    ys = pts[:][1]
                    zs = pts[:][2]
                else:
                    xs = []
                    ys = []
                    zs = []

                # print(zs)

                thisPlottable[loop].setData(x=xs, y=ys, z=zs)
    #             thesePlottables[loop].setDefaultData()

    def ContourPlottable2Data(self):
        contourPlottable = self.ImAxes.activeContourPlottable
        pts_ = np.asarray(contourPlottable.getData()).T
        temp = np.ones([len(pts_[:, 1]), 4])
        temp[:, 0:2] = pts_
        temp[:, 2] = self.thisSliceIndex
        pts = self.ImVolume.IM2PPTransformation.dot(temp.T).T
        for contour in self.ImVolume.contourObjs.values():
            if contour.contourName == contourPlottable.contourName:
                contour.slice2ContCoords[self.thisSliceLoc][0] = pts[:, 0:3]

    # def ContourPlottable2Data(self):
    #     contourPlottable = self.ImAxes.activeContour
    #     contourPlottable.setDefaultData()
    #     pts_ = np.asarray(contourPlottable.getData()).T
    #     temp = np.ones([len(pts_[:, 1]), 4])
    #     temp[:, 0:2] = pts_
    #     temp[:, 2] = self.thisSliceIndex
    #     pts = self.ImVolume.IM2PPTransformation.dot(temp.T).T
    #     try:
    #         for cont in self.ImVolume.contourObjs.values():
    #             if cont.contourName == contourPlottable.contourName:
    #                 cont.slice2ContCoords[self.thisSliceLoc][0] = pts[:, 0:3]
    #     except KeyError as ke:
    #         pass

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
