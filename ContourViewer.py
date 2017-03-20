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
                             QSizePolicy, QStyle, QHeaderView,
                             QGroupBox, QCheckBox, QFormLayout)
from PyQt5.QtGui import (QBrush, QColor,)
from PyQt5.QtCore import (Qt,)
import pyqtgraph as pg
import numpy as np
import cv2
from new_ROI_dialog import newROIDialog

# from Patient import Patient as PatientObj



class QContourViewerWidget(QWidget):
    """ Used to Display A Slice of 3D Image Data
    """

    contThickness = 2
    contOpacity = 0.20
    contCompression = 0.70
    hideContours = False
    painting = False
    imageItem = pg.ImageItem()
    radius = 20
    showCircle = True
    ctrlModifier = False
    shiftModifier = False
    thisSlice = 0
    hoverCount = 0
    TableSliceCount = []
    TableContCount = []
    tableHeaders = ['ROI         ',
                    'Color       ',
                    'Slices      ',
                    'This slice  ']

    def __init__(self,
                 imageData=None,
                 ROIs=[],
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        assert(type(imageData) == np.ndarray)

        self.imageData = np.swapaxes(imageData, 0, 1)
        self.contourImg = np.zeros(imageData.shape)
        self.nRows, self.nCols, self.nSlices = imageData.shape
        self.backgroundIm = np.array((self.nRows, self.nCols))

        self.ROIs = ROIs
        for ROI in ROIs:
            self.addROI(name=ROI.name, color=ROI.color)

        # ~ Add Image Item to Plot Widget
        self.imageItem.setImage(self.imageData[:, :, 0], autoLevels=True)

        # ~ Create Widget parts
        self.applyLayout()
        self.connectSignals()
        self.resize(1200, 700)

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
        viewBox = plotWidge.getViewBox()
        viewBox.invertY(True)
        viewBox.setAspectLocked(1.0)
        viewBox.setBackgroundColor('#FFFFFF')

        # ~~~~~~~~~~~~~~~ SLIDER SECTION
        # Controls for scanning through slices, and some labels
        sliderLayout = QVBoxLayout()
        MW = 40  # minimumWidth
        self.slider = QSlider()
        self.slider.valueChanged.connect(self.sliderChanged)
        self.slider.setMinimum(0)
        self.slider.setPageStep(1)
        self.slider.setMaximum(self.nSlices - 1)
        self.slider.setMinimumWidth(MW)
        self.sliceNumLabel = QLabel("1 / %d" % (self.nSlices))
        self.sliceDistLabel = QLabel("0.00")

        sliderLayout.addWidget(self.slider)
        sliderLayout.addWidget(self.sliceNumLabel, 0, Qt.AlignCenter)
        sliderLayout.addWidget(self.sliceDistLabel, 0, Qt.AlignCenter)


        # ~~~~~~~~~~~~~~~ CONTROLS Section
        contourControls = QGroupBox()
        self.contourHide = QCheckBox()
        self.contourHide.stateChanged.connect(self.hideContoursFcn)

        self.contourFillOpacity = QSlider(Qt.Horizontal)
        self.contourFillOpacity.setRange(0, 10)
        self.contourFillOpacity.valueChanged.connect(self.opacityChange)

        self.contourEdgeThickness = QSlider(Qt.Horizontal)
        self.contourEdgeThickness.setRange(0, 10)
        self.contourEdgeThickness.valueChanged.connect(self.thicknessChange)
        contourControlLayout = QFormLayout()
        contourControlLayout.addRow(QLabel("Hide Contours"), self.contourHide)
        contourControlLayout.addRow(QLabel("Fill Opacity"),
                                    self.contourFillOpacity)
        contourControlLayout.addRow(QLabel("Line Width"),
                                    self.contourEdgeThickness)
        contourControls.setLayout(contourControlLayout)


        # ~~~~~~~~~~~~~~~ TABLE Section
        # interactive summary of ROIs in this image/ patient
        tableWidge = QWidget()
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
                            QSizePolicy.Preferred)

        # table.horizontalHeader().setStretchLastSection(True)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        hHeader = table.horizontalHeader()
        vHeader = table.verticalHeader()

        hwidth = hHeader.length()
        vwidth = vHeader.width()
        fwidth = table.frameWidth() * 2
        table.setFixedWidth(vwidth + hwidth + 0 + fwidth)
        table.setFixedHeight(hHeader.height() + vHeader.height())

        table.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        # table.verticalHeader().setResizeMode(QHeaderView.ResizeToContents)
        # table.setFixedHeight(vwidth + hwidth + 0 + fwidth)

        bttn = QPushButton(" + New ROI")
        bttn.clicked.connect(self.addROI)
        bttn.setFixedWidth(vwidth + hwidth + fwidth)

        tableWidgeLayout.addWidget(bttn)
        tableWidgeLayout.addWidget(table)
        tableWidgeLayout.addWidget(contourControls)
        tableWidgeLayout.addStretch()

        layout = QHBoxLayout()
        layout.addLayout(sliderLayout)
        layout.addWidget(plotWidge, 16)
        layout.addWidget(tableWidge, 1)
        self.setLayout(layout)

    def connectSignals(self):
        # save ORIGINAL mouse events in placeholders for later
        pass

    def hideContoursFcn(self, val):
        if bool(val):
            self.hideContours = True
        else:
            self.hideContours = False
        self.updateContours()
        self.plotWidge.setFocus()

    def thicknessChange(self, val):
        self.contThickness = val
        self.updateContours()
        self.plotWidge.setFocus()

    def opacityChange(self, val):
        self.contOpacity = float(val) / 10.0
        self.updateContours()
        self.plotWidge.setFocus()

    def sliderChanged(self, newValue):
        self.thisSlice = int(newValue)
        self.sliceNumLabel.setText("%d / %d" % (newValue + 1, self.nSlices))
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

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
                          'sliceCount': counter})

        self.add_ROI_to_Table(self.ROIs[-1])
        self.changeROI(ROI_ind=len(self.ROIs) - 1)
        self.plotWidge.setFocus()

    def add_ROI_to_Table(self, ROI):
        row = self.tablePicker.rowCount()
        self.tablePicker.insertRow(row)
        name = QTableWidgetItem(ROI['name'])
        color = QTableWidgetItem(' ')
        color.setBackground(QBrush(QColor(*ROI['color'])))
        sliceCount = QTableWidgetItem(str(sum(ROI['sliceCount'])))
        contCount = QTableWidgetItem()
        self.TableSliceCount.append(sliceCount)
        self.TableContCount.append(contCount)
        self.tablePicker.setItem(row, 0, name)
        self.tablePicker.setItem(row, 1, color)
        self.tablePicker.setItem(row, 2, self.TableSliceCount[-1])
        self.tablePicker.setItem(row, 3, self.TableContCount[-1])
        self.plotWidge.setFocus()

    def updateSliceCount(self, nContours):
        # if np.any(self.thisROI['raster'][:, :, self.thisSlice]):
        #     contBool = True
        # else:
        #     contBool = False

        self.thisROI['sliceCount'][self.thisSlice] = nContours
        # counter = sum(self.thisROI['sliceCount'])
        bools = sum([bool(entry) for entry in self.thisROI['sliceCount']])
        # thisSlice = self.thisROI['sliceCount'][self.thisSlice]
        self.TableSliceCount[self.thisROI['index']].setText(str(bools))
        self.TableContCount[self.thisROI['index']].setText(str(nContours))

    def onCellClick(self, row, col):
        # print(table)
        print('ROI')
        # roi = self.ROIs[row]
        self.changeROI(ROI_ind=row)
        if col == 0:
            pass
        elif col == 1:
            print(col)
        elif col == 2:
            print(col)
        elif col == 3:
            print(col)
        self.plotWidge.setFocus()

    def changeROI(self, ROI_ind):
        ROI = self.ROIs[ROI_ind]
        self.thisROI = ROI
        self.updateContours(isNewSlice=True)

    def updateContours(self, isNewSlice=False):
        if not bool(self.ROIs):
            return
        imageData = self.imageData[:, :, self.thisSlice].copy()

        if self.hideContours:
            self.imageItem.setImage(imageData, autoLevels=False)
            return
        else:
            pass

        if len(imageData.shape) == 2:
            imageData = cv2.cvtColor(imageData, cv2.COLOR_GRAY2BGR)
        if isNewSlice:
            backgroundIm = imageData.copy()

            for ROI in self.ROIs:
                if ROI['id'] == self.thisROI['id']:
                    continue

                contBinaryIm = ROI['raster'][:, :, self.thisSlice].copy()
                contours, hi = getContours(inputImage=contBinaryIm,
                                           compression=self.contCompression)
                color = scaleColor(ROI['color'], self.imageItem.levels)
                # show contours on empty image
                backgroundIm = cv2.drawContours(image=backgroundIm,
                                                contours=contours,
                                                contourIdx=-1,
                                                color=color,
                                                thickness=0,
                                                lineType=cv2.LINE_AA)  # 8

            self.backgroundIm = backgroundIm

        contBinaryIm = self.thisROI['raster'][:, :, self.thisSlice].copy()
        contours, hierarchy = getContours(inputImage=contBinaryIm,
                                          compression=self.contCompression)
        bgIm = self.backgroundIm.copy()
        color = scaleColor(self.thisROI['color'], self.imageItem.levels)

        # activeContourIm = cv2.drawContours(image=bgIm,
        #                                    contours=contours,
        #                                    contourIdx=-1,
        #                                    color=color,
        #                                    thickness=self.contThickness,
        #                                    lineType=cv2.LINE_AA)  # 8

        overlayIm = cv2.drawContours(image=imageData,
                                     contours=contours,
                                     contourIdx=-1,
                                     color=color,
                                     thickness=-1,
                                     lineType=cv2.LINE_AA)  # 8

        alph = self.contOpacity

        cv2.addWeighted(overlayIm, alph,
                        activeContourIm, 1 - alph,
                        0, imageData)

        # imageData = cv2.GaussianBlur(imageData, (9, 9), 0)

        cv2.drawContours

        self.imageItem.setImage(imageData, autoLevels=False)
        # self.imageItem.setImage(newContourIm, autoLevels=False)

        self.updateSliceCount(nContours=len(contours))


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

    # for ind in range(0, volume.shape[2]):
        # if np.any(volume[:, :, ind]):
            # hasContour = True
        # else:
            # hasContour = False
        # contourCount.append(hasContour)

    return contourCount


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # myImage = np.random.randint(0, 128, (750, 750, 20), dtype=np.uint16)
    myImage = 55 * np.ones((700, 700, 20), dtype=np.uint16)
    # for index, thisSlice in enumerate(myImage):
        # myImage[:, :, index - 1] = myImage[:, :, index - 1] * index * 10
    # myImage = np.zeros((512, 512, 20), dtype=np.uint8)
    form = QContourViewerWidget(imageData=myImage)
    form.addROI(name='test1', color=(240, 20, 20))
    form.addROI(name='test2', color=(20, 240, 20))
    form.show()
    sys.exit(app.exec_())
