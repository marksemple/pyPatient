# ContourDrawer.py
# -*- coding: utf-8 -*-
"""
    Tool to View and Add Regions of Interest to an Image Volume
"""

import sys
import uuid

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QSlider, QPushButton,
                             QTableWidget, QTableWidgetItem,
                             QSizePolicy,)
from PyQt5.QtGui import (QBrush, QColor,)
from PyQt5.QtCore import (Qt,)
import pyqtgraph as pg
import numpy as np
import cv2
from new_ROI_dialog import newROIDialog


contThickness = 1
contOpacity = 0.2


class QContourDrawerWidget(QWidget):
    """ Used to Display A Slice of 3D Image Data
    """

    painting = False
    imageItem = pg.ImageItem()
    radius = 40
    showCircle = True
    ctrlModifier = False
    shiftModifier = False
    thisSlice = 0
    hoverCount = 0
    tableHeaders = ['ROI', 'Type', 'Slices', 'Contours', 'Holes']

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
        if bool(self.ROIs):
            self.enablePaintingControls()

        for ROI in ROIs:
            self.addROI(name=ROI.name, color=ROI.color)

        # ~ Add Image Item to Plot Widget
        self.imageItem.setImage(self.imageData[:, :, 0], autoLevels=True)

        self.circle = pg.QtGui.QGraphicsEllipseItem(-self.radius,
                                                    -self.radius,
                                                    self.radius * 2,
                                                    self.radius * 2)
        self.circle.hide()
        self.shape = self.circle

        # ~ Create Widget parts
        self.applyLayout()
        self.connectSignals()
        self.resize(1200, 700)
        self.enableMotionControls()

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
        plotWidge.addItem(self.circle)
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
        bttn = QPushButton(" + New ROI")
        bttn.clicked.connect(self.addROI)

        tableWidgeLayout.addWidget(bttn)
        tableWidgeLayout.addWidget(table)
        tableWidgeLayout.addStretch()

        layout = QHBoxLayout()
        layout.addLayout(sliderLayout)
        layout.addWidget(plotWidge, 16)
        layout.addWidget(tableWidge, 9)
        self.setLayout(layout)

    def connectSignals(self):
        # save ORIGINAL mouse events in placeholders for later
        self.oldImageHover = self.imageItem.hoverEvent
        self.oldImageMousePress = self.imageItem.mousePressEvent
        self.oldImageWheel = self.imageItem.wheelEvent
        self.plotWidge.keyPressEvent = lambda x: self.PlotKeyPress(x)
        self.plotWidge.keyReleaseEvent = lambda x: self.PlotKeyRelease(x)

    def sliderChanged(self, newValue):
        self.thisSlice = int(newValue)
        self.sliceNumLabel.setText("%d / %d" % (newValue + 1, self.nSlices))
        self.updateContours(isNewSlice=True)

    def addROI(self, ev=None, name=None, color=None, *args):
        # First, name and choose color for ROI
        # print('name', name)
        # print('color', color)
        if name is None and color is None:
            roiDialog = newROIDialog()
            roiDialog.exec_()
            if not roiDialog.makeStatus:
                print("cancelled")
                return
            name, color = roiDialog.getProperties()
        else:
            name = name
            color = color

        # add make ROI object
        self.ROIs.append({'color': color[0:3],
                          'name': name,
                          'id': uuid.uuid4(),
                          'raster': np.zeros((self.nRows, self.nCols,
                                              self.nSlices), dtype=np.uint8)})

        self.add_ROI_to_Table(self.ROIs[-1])

        self.enablePaintingControls()
        # self.tablePicker.cellClicked.emit(len(self.ROIs) - 1, 0)
        self.changeROI(ROI_ind=len(self.ROIs) - 1)
        self.plotWidge.setFocus()

    def add_ROI_to_Table(self, ROI):
        row = self.tablePicker.rowCount()
        self.tablePicker.insertRow(row)
        item = QTableWidgetItem(ROI['name'])
        self.tablePicker.setItem(row, 0, item)
        item.setBackground(QBrush(QColor(*ROI['color'])))

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

    def changeROI(self, ROI_ind):
        ROI = self.ROIs[ROI_ind]
        print(ROI_ind)

        # tableitem = self.tablePicker.item(ROI_ind, 0)
        # print(dir(self.tablePicker))
        # styl = """QTableView
        #           {selection-background-color: rgb%s;}""" % (ROI['color'],)
        # self.tablePicker.setStyleSheet(styl)

        self.thisROI = ROI
        modifyBrushStyle(self.circle, ROI['color'], 2, 'additive')
        self.updateContours(isNewSlice=True)
        # self.tablePicker.setItemSelected()

    def enablePaintingControls(self):
        self.shape = self.circle
        # self.circle.show()
        self.plotWidge.setCursor(Qt.CrossCursor)
        self.imageItem.hoverEvent = lambda x: self.PaintHoverEvent(x)
        self.imageItem.mousePressEvent = lambda x: self.PaintClickEvent(x)
        self.imageItem.mouseReleaseEvent = lambda x: self.PaintReleaseEvent(x)
        self.imageItem.wheelEvent = lambda x: self.PaintWheelEvent(x)

    def enableMotionControls(self):
        self.plotWidge.setCursor(Qt.OpenHandCursor)
        self.imageItem.hoverEvent = lambda x: self.oldImageHover(x)
        self.imageItem.mousePressEvent = lambda x: self.oldImageMousePress(x)
        self.imageItem.wheelEvent = lambda x: self.oldImageWheel(x)

    def PaintClickEvent(self, event):
        """ When mouse clicks on IMAGE ITEM """

        self.tempCoordList = []
        ts = self.thisSlice
        self.paintCount = 0
        self.painting = True

        x, y = (int(event.pos().x()), int(event.pos().y()))
        self.tempCoordList.append([[y, x]])
        fill = paintFillCheck(event, self.ctrlModifier)
        oldIm = self.thisROI['raster'][:, :, ts]
        self.thisROI['raster'][:, :, ts] = paintCircle(image=oldIm,
                                                       fill=fill,
                                                       x=y, y=x,
                                                       radius=self.radius)
        self.updateContours()

    def PaintReleaseEvent(self, event):
        self.painting = False

    def PaintHoverEvent(self, event):
        """ When cursor is over IMAGE ITEM """
        try:
            if event.isEnter():
                self.circle.show()
            elif event.isExit():
                self.circle.hide()

            x, y = (int(event.pos().x()), int(event.pos().y()))
            repositionShape(self.circle, x, y, self.radius)
            fill = paintFillCheck(event, self.ctrlModifier)

            if fill is not False:
                ts = self.thisSlice
                self.tempCoordList.append([[y, x]])
                pts = [np.array(self.tempCoordList).astype(np.int32)]
                thisVol = self.thisROI['raster']
                thisVol[:, :, ts] = cv2.polylines(img=thisVol[:, :, ts].copy(),
                                                  pts=pts,
                                                  isClosed=False,
                                                  color=(fill, fill, fill),
                                                  thickness=2 * self.radius)

                # self.imageItem.setImage(thisVol[:, :, ts])
                # print('o')
                self.updateContours()
                # self.paintHere(x, y, fill)

            # self.hoverCount += 1

        except AttributeError as ae:
            self.circle.hide()

    def PaintWheelEvent(self, event):
        """  """
        x, y = (int(event.pos().x()), int(event.pos().y()))
        try:
            angle = event.delta()
        except:
            angle = event.angleDelta().y()
        if (self.radius + np.sign(angle)) > 0:
            self.radius += 2 * np.sign(angle)
        repositionShape(self.circle, x, y, self.radius)

    def paintHere(self, x, y, fill):
        ts = self.thisSlice
        self.tempCoordList.pop(0)
        self.tempCoordList.append([[y, x]])
        contArray = [np.array(self.tempCoordList).astype(np.int32)]
        thisVol = self.thisROI['raster']
        oldIm = thisVol[:, :, ts]
        thisVol[:, :, ts] = cv2.polylines(img=oldIm.copy(),
                                          pts=contArray,
                                          isClosed=False,
                                          color=(fill, fill, fill),
                                          thickness=2 * self.radius)
        self.imageItem.setImage(thisVol[:, :, ts])
        self.updateContours()

    def updateContours(self, isNewSlice=False):

        if not bool(self.ROIs):
            return

        imageData = self.imageData[:, :, self.thisSlice].copy()

        if len(imageData.shape) == 2:
            imageData = cv2.cvtColor(imageData, cv2.COLOR_GRAY2BGR)

        if isNewSlice:
            backgroundIm = imageData.copy()

            for ROI in self.ROIs:
                if ROI['id'] == self.thisROI['id']:
                    continue

                contBinaryIm = ROI['raster'][:, :, self.thisSlice].copy()

                contours = getContours(inputImage=contBinaryIm)
                color = scaleColor(ROI['color'], self.imageItem.levels)
                # show contours on empty image
                backgroundIm = cv2.drawContours(image=backgroundIm,
                                                contours=contours,
                                                contourIdx=-1,
                                                color=color,
                                                thickness=contThickness,
                                                lineType=cv2.LINE_AA)  # 8

            self.backgroundIm = backgroundIm

        contBinaryIm = self.thisROI['raster'][:, :, self.thisSlice].copy()

        contours = getContours(inputImage=contBinaryIm)

        bgIm = self.backgroundIm.copy()
        color = scaleColor(self.thisROI['color'], self.imageItem.levels)

        newContourIm = cv2.drawContours(image=bgIm,
                                        contours=contours,
                                        contourIdx=-1,
                                        color=color,
                                        thickness=contThickness,
                                        lineType=cv2.LINE_AA)  # 8
        overlayIm = cv2.drawContours(image=imageData,
                                     contours=contours,
                                     contourIdx=-1,
                                     color=color,
                                     thickness=-1,
                                     lineType=cv2.LINE_AA)  # 8

        alph = contOpacity
        cv2.addWeighted(overlayIm, alph, newContourIm, 1 - alph, 0, imageData)
        self.imageItem.setImage(imageData, autoLevels=False)

    def PlotKeyPress(self, event):
        """ Filter key presses while plot object is active """
        # print(event.key())

        if event.key() == 65:  # 'A' -- advance one slice
            self.slider.setSliderPosition(self.thisSlice + 1)

        if event.key() == 90:  # 'Z' -- reverse one slice
            self.slider.setSliderPosition(self.thisSlice - 1)

        if bool(self.ROIs):

            keyList = [49 + i[0] for i in enumerate(self.ROIs)]
            if event.key() in keyList:  # 1-9 ROI HotKeys
                ind = keyList.index(event.key())
                self.changeROI(ROI_ind=ind)

            # s, x, d, c
            if event.key() == 83:  # s -- copy superior slice ROI
                self.unionNeighbourSlice(self.thisROI, 1)
            if event.key() == 88:  # x -- copy inferior slice ROI
                self.unionNeighbourSlice(self.thisROI, -1)
            if event.key() == 68:  # d -- dilate ROI
                self.dilate_erode_ROI(self.thisROI, 1)
            if event.key() == 69:  # e -- erode ROI
                self.dilate_erode_ROI(self.thisROI, -1)
            if event.key() == 32:  # SPACE -- Rotate through ROIs
                indList = [ROI['id'] for ROI in self.ROIs]
                ind = indList.index(self.thisROI['id'])
                newInd = (ind + 1) % len(self.ROIs)
                self.changeROI(ROI_ind=newInd)

            if event.key() == 16777249:  # CTRL -- Invert Painters
                self.ctrlModifier = True
                modifyBrushStyle(self.circle, self.thisROI['color'],
                                 2, 'subtractive')

            if event.key() == 16777248:  # SHIFT -- Motion Mode
                self.shiftModifier = True
                self.circle.hide()
                self.enableMotionControls()

    def PlotKeyRelease(self, event):

        if bool(self.ROIs):
            if event.key() == 16777249:  # CTRL
                self.ctrlModifier = False
                modifyBrushStyle(self.circle, self.thisROI['color'],
                                 2, 'additive')

            if event.key() == 16777248:  # SHIFT
                self.shiftModifier = True
                self.circle.show()
                self.enablePaintingControls()

    def unionNeighbourSlice(self, roi, direction):
        slice0 = self.thisSlice

        if slice0 == 0 and direction == -1:
            print("already at bottom!")
            return

        elif slice0 == (self.nSlices - 1) and direction == 1:
            print("already at top!")
            return

        neighbIm = roi['raster'][:, :, slice0 + direction].copy()
        thisIm = roi['raster'][:, :, slice0].copy()
        # union!

        # roi['raster'][:, :, slice0] = cv2.bitwise_and(neighbIm, thisIm)
        roi['raster'][:, :, slice0] = neighbIm + thisIm

        self.updateContours()

    def dilate_erode_ROI(self, roi, direction):
        slice0 = self.thisSlice
        # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        im = roi['raster'][:, :, slice0].copy()
        if direction > 0:
            roi['raster'][:, :, slice0] = cv2.dilate(im, kernel)
        elif direction < 0:
            roi['raster'][:, :, slice0] = cv2.erode(im, kernel)
        self.updateContours()


def scaleColor(color, levels):
    scale = (levels[1] - levels[0]) / 255
    newColor = tuple([(scale * x + levels[0]) for x in color])
    return newColor


def repositionShape(shape, x, y, radius):
    shape.setRect(x - radius,
                  y - radius,
                  2 * radius,
                  2 * radius)


def modifyBrushStyle(shape, color=(255, 100, 100), penWidth=2,
                     mode='additive'):

    if mode == 'subtractive':
        pen = pg.mkPen(color=color, width=penWidth)
        brush = pg.mkBrush(color=(0, 0, 0, 0))
    else:
        pen = pg.mkPen(color='w', width=penWidth)
        brush = pg.mkBrush(color=color + (100,))

    shape.setPen(pen)
    shape.setBrush(brush)


def paintCircle(image, fill, x, y, radius):
    return cv2.circle(img=image.copy(),
                      center=(x, y),
                      radius=radius,
                      color=(fill, fill, fill),
                      thickness=-1,
                      lineType=cv2.LINE_AA)  # 8


def getContours(inputImage=np.zeros([500, 500, 3], dtype=np.uint8)):
    # if we have a color-channel, convert to grayscale

    if len(inputImage.shape) == 3:
        inputImage = cv2.cvtColor(inputImage, cv2.COLOR_BGR2GRAY)

    # Chain Approx Simple
    im, contours, hierarchy = cv2.findContours(inputImage, cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)

    # print(contours)

    if bool(contours):
        print("num hoops:", len(contours))
        print("cont1 shape:", contours[0].shape)
        # print('hier:', hierarchy)

    for ind, contour in enumerate(contours):
        contours[ind] = cv2.approxPolyDP(contour, 0.75, True)

    if bool(contours):
        print("num hoops:", len(contours))
        print("cont1 shape:", contours[0].shape)
        print('hier:', hierarchy)

    return contours


# def getContours2(inputImage=np.zeros([500, 500, 3], dtype=np.uint8)):
#     # if we have a color-channel, convert to grayscale

#     print("alt")

#     if len(inputImage.shape) == 3:
#         inputImage = cv2.cvtColor(inputImage, cv2.COLOR_BGR2GRAY)

#     # Chain Approx Simple
#     # im, contours, hierarchy = cv2.findContours(inputImage, cv2.RETR_TREE,
#     #                                            cv2.CHAIN_APPROX_SIMPLE)

#     im, contours, hierarchy = cv2.findContours(inputImage, cv2.RETR_TREE,
#                                                cv2.CHAIN_APPROX_TC89_L1)

#     for contour in contours:
#         contour = cv2.approxPolyDP(contour, 1, True)

#     return contours


def paintFillCheck(event, modifier):
    # probes button clicks to see if we should be painting, erasing, or not
    doPaint = False

    if event.buttons() == Qt.LeftButton:
        doPaint = True
        fill = 255

    if event.buttons() == Qt.RightButton:
        doPaint = True
        fill = 0

    if doPaint:
        if modifier:
            fill = 1 - fill
        return fill

    return False


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # myImage = np.random.randint(0, 128, (750, 750, 20), dtype=np.uint16)
    myImage = 55 * np.ones((700, 700, 20), dtype=np.uint16)
    # for index, thisSlice in enumerate(myImage):
        # myImage[:, :, index - 1] = myImage[:, :, index - 1] * index * 10
    # myImage = np.zeros((512, 512, 20), dtype=np.uint8)
    form = QContourDrawerWidget(imageData=myImage)
    form.addROI(name='test1', color=(240, 20, 20))
    form.addROI(name='test2', color=(20, 240, 20))
    form.show()
    sys.exit(app.exec_())
