# ContourViewer.py
# -*- coding: utf-8 -*-
"""
    Interface for viewing Image Volumes and delineated Regions of Interest
    Slider bar to
"""

import sys
import uuid

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QSlider, QPushButton,
                             QTableWidget, QTableWidgetItem,
                             QSizePolicy, QHeaderView, QColorDialog,
                             QGroupBox, QCheckBox, QFormLayout, QSplitter)
from PyQt5.QtGui import (QBrush, QColor,)
from PyQt5.QtCore import (Qt,)
import pyqtgraph as pg
import numpy as np
import cv2

try:
    from new_ROI_dialog import newROIDialog  # , scaleColor, getContours
    from Patient_ROI import CVContour2VectorArray

except ImportError:
    from dicommodule.new_ROI_dialog import newROIDialog
    from dicommodule.Patient_ROI import CVContour2VectorArray


class QContourViewerWidget(QWidget):
    """ Used to Display A Slice of 3D Image Data """

    def __init__(self,
                 imageData=None,
                 ROIs=[],
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.imageItem = pg.ImageItem()
        self.ROIs = []

        self.hasImageData = False
        self.hasContourData = False
        self.hideContours = False
        self.hideImage = False
        self.showCircle = True
        self.shiftModifier = False
        self.controlsHidden = False

        self.contThickness = 2
        self.contOpacity = 0.20
        self.contCompression = 0
        self.radius = 20
        self.thisSlice = 0
        self.hoverCount = 0

        self.TableSliceCount = []
        self.TableHideCheck = []
        # self.TableContCount = []
        # self.TableVertCount = []
        self.tableHeaders = ['ROI',
                             'Color',
                             'Slices',
                             'Show']
                             # 'on Slice',
                             # 'Vertices']

        # ~ Create Widget parts
        self.applyLayout()
        self.connectSignals()
        self.resize(1200, 700)

        if imageData is not None:
            print("Image is {}".format(imageData.shape))
            self.init_Image(imageData)

        if bool(ROIs):
            print("Has {} Contours".format(len(ROIs)))
            self.init_ROIs(ROIs)

    def init_Image(self, imageData):
        self.imageData = np.swapaxes(imageData, 0, 1)
        self.contourImg = np.zeros(imageData.shape)
        self.nRows, self.nCols, self.nSlices = imageData.shape
        self.backgroundIm = np.array((self.nRows, self.nCols))
        self.imageItem.setImage(self.imageData[:, :, 0], autoLevels=True)
        self.init_Slider(self.slider)
        self.morphSize = int(self.nCols / 50)
        self.hasImageData = True

        # ~ Add Image Item to Plot Widget

    def init_ROIs(self, ROIs):
        self.ROIs = ROIs
        for ROI in ROIs:
            self.addROI(name=ROI.name, color=ROI.color)

    def init_Slider(self, slider):
        slider.setPageStep(1)
        slider.setRange(0, self.nSlices - 1)

    def addROI(self, ev=None, name=None, color=None, data=None, *args):
        # First, name and choose color for ROI
        if name is None or color is None:
            roiDialog = newROIDialog()
            roiDialog.exec_()
            if not roiDialog.makeStatus:
                print("cancelled")
                return
            name, color = roiDialog.getProperties()
        else:
            name = name
            color = color

        if data is None:
            data = np.zeros((self.nRows, self.nCols, self.nSlices),
                            dtype=np.uint8)
        counter = countContourSlices(data)
        # add make ROI object
        self.ROIs.append({'color': color[0:3],
                          'index': len(self.ROIs),
                          'name': name,
                          'id': uuid.uuid4(),
                          'raster': data,
                          'sliceCount': counter,
                          'hidden': False})

        self.add_ROI_to_Table(self.ROIs[-1])
        self.changeROI(ROI_ind=len(self.ROIs) - 1)
        self.hasContourData = True
        self.plotWidge.setFocus()


    def connectSignals(self):
        pass

    def toggleControls(self):
        print("Toggle")
        if self.controlsHidden:
            self.tableWidge.show()
            self.controlsHidden = False
            self.collapseControls.setText('>> Controls')
            # self.enablePaint
        else:
            self.tableWidge.hide()
            self.controlsHidden = True
            self.collapseControls.setText('<< Controls')
        self.plotWidge.setFocus()

    def hideContoursFcn(self, val):
        if bool(val):
            self.hideContours = True
        else:
            self.hideContours = False
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def hideImageFcn(self, val):
        if bool(val):
            self.hideImage = True
        else:
            self.hideImage = False
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def thicknessChange(self, val):
        self.contThickness = val
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def opacityChange(self, val):
        if float(val) > 0.95 * self.contourFillOpacity.maximum():
            self.contourEdgeThickness.setValue(0)
        self.contOpacity = float(val) / 10.0
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def compressChange(self, val):
        self.contCompression = float(val) / 10
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def sliderChanged(self, newValue):
        self.thisSlice = int(newValue)
        self.sliceNumLabel.setText("%d / %d" % (newValue, self.nSlices - 1))
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def updateTableFields(self, ROI, contours):
        # nVerts = 0
        nConts = 0
        # for contour in contours:
        # nConts += 1
        # nVerts += contour.shape[0]
        ROI['sliceCount'][self.thisSlice] = nConts
        Nbools = sum([bool(entry) for entry in ROI['sliceCount']])
        self.TableSliceCount[ROI['index']].setText(str(Nbools))
        if ROI['hidden']:
            self.TableHideCheck[ROI['index']].setText('N')
        else:
            self.TableHideCheck[ROI['index']].setText('Y')
        # self.TableContCount[ROI['index']].setText(str(nConts))
        # self.TableVertCount[ROI['index']].setText(str(nVerts))

    def onCellClick(self, row, col):
        self.changeROI(ROI_ind=row)

        if col == 0:  # NAME
            pass

        elif col == 1:  # COLOR
            color = self.chooseColor()
            self.thisROI['color'] = color[0:3]
            qCol = QBrush(QColor(*color[0:3]))
            myItem = self.tablePicker.item(row, col)
            myItem.setBackground(qCol)
            # self.tablePicker.item(row, col).setBackground(qCol)


        elif col == 2:  # SLICES
            pass

        elif col == 3:  # VISIBLE
            print('show/hide')
            self.thisROI['hidden'] = not self.thisROI['hidden']

        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def chooseColor(self):
        colorDiag = QColorDialog()
        colorDiag.exec_()
        color = colorDiag.selectedColor()
        return color.getRgb()

    def changeROI(self, ROI_ind):
        ROI = self.ROIs[ROI_ind]
        self.thisROI = ROI
        # styleString = """QTableView::item:selected {background: rgb(%s, %s, %s);}""" % ROI['color']
        # print(styleString)
        # styleString = """ QTableView::item:first {background: white;} """
        # self.tablePicker.setStyleSheet(styleString)
        self.updateContours(isNewSlice=True)

    def add_ROI_to_Table(self, ROI):

        row = self.tablePicker.rowCount()
        self.tablePicker.insertRow(row)

        # ROI NAME
        name = QTableWidgetItem(ROI['name'])
        name.setFlags(Qt.ItemIsEnabled)
        self.tablePicker.setItem(row, 0, name)

        # ROI COLOR (clickable)
        color = QTableWidgetItem(' ')
        color.setFlags(Qt.ItemIsEnabled)
        color.setBackground(QBrush(QColor(*ROI['color'])))
        self.tablePicker.setItem(row, 1, color)

        # ROI Slice Count
        sliceCount = QTableWidgetItem(str(sum(ROI['sliceCount'])))
        sliceCount.setFlags(Qt.ItemIsEnabled)
        self.TableSliceCount.append(sliceCount)
        self.tablePicker.setItem(row, 2, sliceCount)

        # Show/Hide ROI
        visibleCheck = QTableWidgetItem("Y")
        visibleCheck.setFlags(Qt.ItemIsEnabled)
        self.TableHideCheck.append(visibleCheck)
        self.tablePicker.setItem(row, 3, visibleCheck)

        # ROI COntours-On-Slice Count
        # contCount = QTableWidgetItem()
        # self.TableContCount.append(contCount)
        # self.tablePicker.setItem(row, 3, self.TableContCount[-1])

        # ROI Vertex Count
        # vertCount = QTableWidgetItem()
        # self.TableVertCount.append(vertCount)
        # self.tablePicker.setItem(row, 4, self.TableVertCount[-1])

        self.plotWidge.setFocus()

    def updateContours(self, isNewSlice=False):
        if not bool(self.ROIs):
            return

        if self.hideImage is False:
            medicalIm = self.imageData[:, :, self.thisSlice].copy()
        else:
            medicalIm = np.zeros(self.imageData[:, :, self.thisSlice].shape,
                                 dtype=self.imageData[:, :, self.thisSlice].dtype)

        if self.hideContours:
            self.imageItem.setImage(medicalIm, autoLevels=False)
            return

        if isNewSlice:  # create new Background Im
            if len(medicalIm.shape) == 2:
                medicalIm = cv2.cvtColor(medicalIm, cv2.COLOR_GRAY2BGR)

            for ROI in self.ROIs:

                if ROI['hidden']:
                    continue

                if ROI['id'] == self.thisROI['id']:
                    continue

                contBinaryIm = ROI['raster'][:, :, self.thisSlice].copy()
                contours, hi = getContours(inputImage=contBinaryIm,
                                           compression=self.contCompression)
                color = scaleColor(ROI['color'], self.imageItem.levels)
                medicalIm = cv2.drawContours(image=medicalIm.copy(),
                                             contours=contours,
                                             contourIdx=-1,
                                             color=color,
                                             thickness=self.contThickness,
                                             lineType=cv2.LINE_AA)  # 8

                self.updateTableFields(ROI, contours)

            self.backgroundIm = medicalIm.copy()

        backgroundIm = self.backgroundIm

        if len(backgroundIm.shape) == 2:
            backgroundIm = cv2.cvtColor(backgroundIm, cv2.COLOR_GRAY2BGR)


        activeColor = scaleColor(self.thisROI['color'], self.imageItem.levels)
        contBinaryIm = self.thisROI['raster'][:, :, self.thisSlice].copy()
        activeCont, hierarchy = getContours(inputImage=contBinaryIm,
                                            compression=self.contCompression)

        if not self.thisROI['hidden']:

            activeContourIm = cv2.drawContours(image=backgroundIm.copy(),
                                               contours=activeCont,
                                               contourIdx=-1,
                                               color=activeColor,
                                               thickness=-1,
                                               lineType=cv2.LINE_AA)  # 8

            alph = self.contOpacity
            waterMarkedIm = backgroundIm.copy()
            cv2.addWeighted(backgroundIm, 1 - alph,
                            activeContourIm, alph,
                            0, waterMarkedIm)

            backgroundIm = cv2.drawContours(image=waterMarkedIm,
                                            contours=activeCont,
                                            contourIdx=-1,
                                            color=activeColor,
                                            thickness=self.contThickness,
                                            lineType=cv2.LINE_AA)

        self.imageItem.setImage(backgroundIm, autoLevels=False)
        self.updateTableFields(self.thisROI, activeCont)

    def applyLayout(self):
        # ~ Create "Controls" Panel Layout for Slider

        # ~~~~~~~~~~~~~ VIEWER SECTION
        # Canvas for viewing and interacting with patient image data
        # self.plotWidge = plotWidge = pg.PlotWidget()
        self.plotWidge = plotWidge = pg.PlotWidget()
        plotWidge.showAxis('left', False)
        plotWidge.showAxis('bottom', False)
        plotWidge.setAntialiasing(True)
        plotWidge.addItem(self.imageItem)
        # plotWidge
        viewBox = plotWidge.getViewBox()
        viewBox.invertY(True)
        viewBox.setAspectLocked(1.0)
        viewBox.setBackgroundColor('#FFFFFF')

        # ~~~~~~~~~~~~~~~ SLIDER SECTION
        # Controls for scanning through slices, and some labels
        sliderLayout = QHBoxLayout()
        MW = 40  # minimumWidth
        self.slider = QSlider()
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.valueChanged.connect(self.sliderChanged)
        # self.slider.setMinimumWidth(MW)
        self.sliceNumLabel = QLabel("1 / N")
        self.sliceDistLabel = QLabel("0.00")

        self.collapseControls = QPushButton('<< Controls')
        self.collapseControls.clicked.connect(self.toggleControls)

        sliderLayout.addWidget(self.sliceNumLabel, 0, Qt.AlignCenter)
        sliderLayout.addWidget(self.slider)
        sliderLayout.addWidget(self.sliceDistLabel, 0, Qt.AlignCenter)
        sliderLayout.addWidget(self.collapseControls)

        viewportLayout = QVBoxLayout()
        viewportLayout.addLayout(sliderLayout)
        viewportLayout.addWidget(plotWidge)

        # ~~~~~~~~~~~~~~~ CONTROLS Section
        contourControls = QGroupBox()
        self.contourHide = QCheckBox()
        self.contourHide.stateChanged.connect(self.hideContoursFcn)

        self.imageHide = QCheckBox()
        self.imageHide.stateChanged.connect(self.hideImageFcn)

        self.contourFillOpacity = QSlider(Qt.Horizontal)
        self.contourFillOpacity.setRange(0, 10)
        self.contourFillOpacity.setValue(self.contOpacity)
        self.contourFillOpacity.valueChanged.connect(self.opacityChange)

        self.contourEdgeThickness = QSlider(Qt.Horizontal)
        self.contourEdgeThickness.setRange(0, 10)
        self.contourEdgeThickness.setValue(self.contThickness)
        self.contourEdgeThickness.valueChanged.connect(self.thicknessChange)

        self.contourEdgeCompression = QSlider(Qt.Horizontal)
        self.contourEdgeCompression.setRange(0, 20)
        self.contourEdgeCompression.setValue(self.contCompression * 10
                                             )
        self.contourEdgeCompression.valueChanged.connect(self.compressChange)

        contourControlLayout = QFormLayout()
        contourControlLayout.addRow(QLabel("Hide Image"), self.imageHide)
        contourControlLayout.addRow(QLabel("Hide Contours"), self.contourHide)
        contourControlLayout.addRow(QLabel("Fill Opacity"),
                                    self.contourFillOpacity)
        contourControlLayout.addRow(QLabel("Line Width"),
                                    self.contourEdgeThickness)
        contourControlLayout.addRow(QLabel("Line Simplification"),
                                    self.contourEdgeCompression)
        contourControls.setLayout(contourControlLayout)

        # ~~~~~~~~~~~~~~~ TABLE Section
        # interactive summary of ROIs in this image/ patient
        self.tableWidge = tableWidge = QWidget()
        tableWidgeLayout = QVBoxLayout()
        tableWidge.setLayout(tableWidgeLayout)

        table = self.tablePicker = QTableWidget()
        table.setColumnCount(len(self.tableHeaders))
        table.setHorizontalHeaderLabels(self.tableHeaders)
        table.verticalHeader().setVisible(False)
        table.cellClicked.connect(self.onCellClick)
        table.setSelectionBehavior(table.SelectRows)
        table.setSelectionMode(table.SingleSelection)
        table.setSizePolicy(QSizePolicy.Preferred,
                            QSizePolicy.Fixed)
        table.resizeColumnsToContents()

        # table.horizontalHeader().setStretchLastSection(True)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        hHeader = table.horizontalHeader()
        vHeader = table.verticalHeader()

        hwidth = hHeader.length()
        vwidth = vHeader.width()
        fwidth = table.frameWidth() * 2
        # table.setFixedWidth(vwidth + hwidth + fwidth)
        table.setFixedHeight((vwidth + hwidth + fwidth) * 1.15)

        table.horizontalHeader().setResizeMode(QHeaderView.Stretch)

        bttn = QPushButton(" + New ROI")
        bttn.clicked.connect(self.addROI)
        bttn.setFixedWidth(vwidth + hwidth + fwidth)

        tableWidgeLayout.addWidget(bttn)
        tableWidgeLayout.addWidget(table)
        tableWidgeLayout.addWidget(contourControls)
        tableWidgeLayout.addStretch()

        blankWidge = QWidget()
        # blankLayout = QHBoxLayout()
        # blankWidge.setLayout(blankLayout)
        blankWidge.setLayout(viewportLayout)

        splitta = QSplitter()
        splitta.addWidget(blankWidge)
        splitta.addWidget(tableWidge)
        # splitta.setStyleSheet()

        layout = QHBoxLayout()
        layout.addWidget(splitta)
        # layout.addWidget(plotWidge, 16)
        # layout.addLayout(viewportLayout, 16)
        # layout.addLayout(sliderLayout)
        # layout.addWidget(tableWidge, 4)
        self.setLayout(layout)


def scaleColor(color, levels):
    scale = (levels[1] - levels[0]) / 255
    newColor = tuple([(scale * x + levels[0]) for x in color])
    return newColor


def getContours(inputImage=np.zeros([500, 500, 3], dtype=np.uint8),
                compression=0):
    # if we have a color-channel, convert to grayscale

    if len(inputImage.shape) == 3:
        inputImage = cv2.cvtColor(inputImage, cv2.COLOR_BGR2GRAY)

    inputImage = inputImage.astype(np.uint8)

    # Chain Approx Simple
    im, contours, hierarchy = cv2.findContours(inputImage, cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)

    for ind, contour in enumerate(contours):
        contours[ind] = cv2.approxPolyDP(contour, compression, True)

    return contours, hierarchy  # ,nContours,


def countContourSlices(volume):
    # returns list of number of contours per slice

    contourCount = []

    for ind in range(0, volume.shape[2]):
        im = volume[:, :, ind]
        outim, cont, hier = cv2.findContours(im.astype(np.uint8),
                                             cv2.RETR_TREE,
                                             cv2.CHAIN_APPROX_SIMPLE)
        contourCount.append(len(cont))

    return contourCount


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # myImage = np.random.randint(0, 128, (750, 750, 20), dtype=np.uint16)
    myImage = 55 * np.ones((700, 700, 20), dtype=np.uint16)

    # for index, thisSlice in enumerate(myImage):
        # myImage[:, :, index - 1] = myImage[:, :, index - 1] * index * 10
    # myImage = np.zeros((512, 512, 20), dtype=np.uint8)

    form = QContourViewerWidget()  #imageData=myImage)
    form.init_Image(myImage)
    form.addROI(name='test1', color=(240, 20, 20))
    form.addROI(name='test2', color=(20, 240, 20))
    form.show()
    sys.exit(app.exec_())
