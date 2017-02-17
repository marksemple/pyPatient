# ContourDrawer.py
# -*- coding: utf-8 -*-
"""
    Tool to View and Add Regions of Interest to an Image Volume
"""

import sys
# import time
import threading
# import itertools
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout,
                             QLabel, QSlider, QPushButton, QLineEdit,
                             QDialog, QColorDialog, QFormLayout,)
from PyQt5.QtCore import (Qt, )
import pyqtgraph as pg
import numpy as np
import uuid
import cv2


class QContourDrawerWidget(QWidget):
    """ Used to Display A Slice of 3D Image Data
    """

    def __init__(self,
                 imageData=None,
                 ROIs=[],
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        assert(type(imageData) == np.ndarray)

        self.imageData = imageData
        print(imageData.shape)
        self.contourImg = np.zeros(imageData.shape)
        self.nRows, self.nCols, self.nSlices = imageData.shape

        self.backgroundIm = np.array((self.nRows, self.nCols))
        self.radius = 40
        # self.draggingRect = False
        self.showCircle = True
        self.ctrlModifier = False
        self.shiftModifier = False
        self.thisSlice = 0
        self.hoverCount = 0
        self.ROIs = ROIs

        if bool(self.ROIs):
            self.enablePaintingControls()

        # ~ Add Image Item to Plot Widget
        self.plotWidge = self.createViewPortal()

        self.imageItem = pg.ImageItem()
        self.imageItem.setImage(self.imageData[:, :, 0], autoLevels=False)
        self.plotWidge.addItem(self.imageItem)

        self.circle = pg.QtGui.QGraphicsEllipseItem(-self.radius,
                                                    -self.radius,
                                                    self.radius * 2,
                                                    self.radius * 2)
        self.circle.hide()
        self.plotWidge.addItem(self.circle)
        self.shape = self.circle
        # self.plotWidge.addItem(self.rect)

        # ~ Create Widget parts
        self.createControls()
        self.applyLayout()
        self.connectSignals()
        self.resize(700, 700)

        self.enableMotionControls()

        # self.enableRectControls()

    def createViewPortal(self, backgroundCol='#FFFFFF'):
        plotWidge = pg.PlotWidget()
        plotWidge.showAxis('left', False)
        plotWidge.showAxis('bottom', False)
        plotWidge.setAntialiasing(True)
        viewBox = plotWidge.getViewBox()
        viewBox.invertY(True)
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

        self.addROIbttn = QPushButton("+ ROI")
        self.addROIbttn.clicked.connect(self.addROI)

        self.sliceNumLabel = QLabel("1 / %d" % (self.nSlices))
        self.sliceDistLabel = QLabel("0.00")

    def applyLayout(self):
        # ~ Create "Controls" Panel Layout for Slider
        sliderLayout = QVBoxLayout()
        sliderLayout.addWidget(self.addROIbttn)
        sliderLayout.addWidget(self.slider)
        sliderLayout.addWidget(self.sliceNumLabel, 0, Qt.AlignCenter)
        sliderLayout.addWidget(self.sliceDistLabel, 0, Qt.AlignCenter)
        # ~ Create widget-wide grid layout
        layout = QGridLayout()
        layout.addWidget(self.plotWidge, 1, 1)
        layout.addLayout(sliderLayout, 1, 2)
        self.setLayout(layout)

    def sliderChanged(self, newValue):
        self.thisSlice = int(newValue)
        self.sliceNumLabel.setText("%d / %d" % (newValue + 1, self.nSlices))
        self.updateContours(isNewSlice=True)

    def addROI(self, name='contour', color=(240, 240, 240), *args):
        roiDialog = newROIDialog()
        roiDialog.exec_()
        if not roiDialog.makeStatus:
            print("cancelled")
            return

        name, color = roiDialog.getProperties()
        self.ROIs.append({'color': color[0:3],
                          'name': name,
                          'id': uuid.uuid4(),
                          'raster': np.zeros((self.nRows, self.nCols,
                                              self.nSlices), dtype=np.uint8)})
        self.enablePaintingControls()
        self.changeROI(self.ROIs[-1])
        self.plotWidge.setFocus()

    def changeROI(self, ROI):
        self.thisROI = ROI
        additiveShapeStyle(self.circle, brushCol=ROI['color'])
        self.updateContours(isNewSlice=True)

    def connectSignals(self):
        # save ORIGINAL mouse events in placeholders for later
        self.oldImageHover = self.imageItem.hoverEvent
        self.oldImageMousePress = self.imageItem.mousePressEvent
        self.oldImageWheel = self.imageItem.wheelEvent
        self.plotWidge.keyPressEvent = lambda x: self.PlotKeyPress(x)
        self.plotWidge.keyReleaseEvent = lambda x: self.PlotKeyRelease(x)

    def enablePaintingControls(self):
        self.shape = self.circle
        # self.circle.show()
        self.plotWidge.setCursor(Qt.CrossCursor)
        self.imageItem.hoverEvent = lambda x: self.PaintHoverEvent(x)
        self.imageItem.mousePressEvent = lambda x: self.PaintClickEvent(x)
        self.imageItem.wheelEvent = lambda x: self.PaintWheelEvent(x)

    # def enableRectControls(self):
    #     self.shape = self.rect
    #     self.rect.show()
    #     self.RectOrigin = (0, 0)
    #     self.plotWidge.setCursor(Qt.CrossCursor)
    #     # self.imageItem.hoverEvent = lambda x: self.RectHoverEvent(x)
    #     self.imageItem.mousePressEvent = lambda x: self.RectClickEvent(x)
    #     self.imageItem.mouseDragEvent = lambda x: self.RectHoverEvent(x)

    def enableMotionControls(self):
        self.plotWidge.setCursor(Qt.OpenHandCursor)
        self.imageItem.hoverEvent = lambda x: self.oldImageHover(x)
        self.imageItem.mousePressEvent = lambda x: self.oldImageMousePress(x)
        self.imageItem.wheelEvent = lambda x: self.oldImageWheel(x)

    def PaintClickEvent(self, event):
        """ When mouse clicks on IMAGE ITEM """
        x, y = (int(event.pos().x()), int(event.pos().y()))
        fill = paintFillCheck(event, self.ctrlModifier)
        self.paintHere(x, y, fill)

    def PaintHoverEvent(self, event):
        """ When cursor is over IMAGE ITEM """
        try:
            if event.isEnter():
                self.circle.show()
            elif event.isExit():
                self.circle.hide()

            # if not self.hoverCount % 2:
            x, y = (int(event.pos().x()), int(event.pos().y()))
            fill = paintFillCheck(event, self.ctrlModifier)
            repositionShape(self.circle, x, y, self.radius)
            
            # On Every THIRD Hover-Event:
            if not self.hoverCount % 3 and fill is not False:
                self.paintHere(x, y, fill)
            
            self.hoverCount += 1

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

    def paintHere(self, x, y, fill=255):
        # draw circle on (hidden) Binary ROI Image
        thisVol = self.thisROI['raster']
        image = paintCircle(image=thisVol[:, :, self.thisSlice],
                            fill=fill, x=y, y=x, radius=self.radius)
        thisVol[:, :, self.thisSlice] = image
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

                # show contours on empty image
                backgroundIm = cv2.drawContours(image=backgroundIm,
                                                contours=contours,
                                                contourIdx=-1,
                                                color=ROI['color'],
                                                thickness=2,
                                                lineType=cv2.LINE_AA)  # 8

            self.backgroundIm = backgroundIm

        contBinaryIm = self.thisROI['raster'][:, :, self.thisSlice].copy()
        contours = getContours(inputImage=contBinaryIm)

        bgIm = self.backgroundIm.copy()

        newContourIm = cv2.drawContours(image=bgIm,
                                        contours=contours,
                                        contourIdx=-1,
                                        color=self.thisROI['color'],
                                        thickness=2,
                                        lineType=cv2.LINE_AA)  # 8
        overlayIm = cv2.drawContours(image=imageData,
                                     contours=contours,
                                     contourIdx=-1,
                                     color=self.thisROI['color'],
                                     thickness=-1,
                                     lineType=cv2.LINE_AA)  # 8

        alph = 0.3
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
                self.changeROI(ROI=self.ROIs[ind])

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
                self.changeROI(ROI=self.ROIs[newInd])

            if event.key() == 16777249:  # CTRL -- Invert Painters
                self.ctrlModifier = True
                subtractiveShapeStyle(self.circle,
                                      penCol=self.thisROI['color'])

            if event.key() == 16777248:  # SHIFT -- Motion Mode
                self.shiftModifier = True
                self.circle.hide()
                self.enableMotionControls()

    def PlotKeyRelease(self, event):

        if bool(self.ROIs):
            if event.key() == 16777249:  # CTRL
                self.ctrlModifier = False
                additiveShapeStyle(self.circle,
                                   brushCol=self.thisROI['color'])

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

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))

        im = roi['raster'][:, :, slice0 ].copy()

        if direction > 0:
            roi['raster'][:, :, slice0 ] = cv2.dilate(im, kernel)

        elif direction < 0:
            roi['raster'][:, :, slice0 ] = cv2.erode(im, kernel)

        self.updateContours()

def repositionShape(shape, x, y, radius):
    shape.setRect(x - radius,
                  y - radius,
                  2 * radius,
                  2 * radius)


def additiveShapeStyle(shape, penCol='w',
                       brushCol=(255, 100, 100), penWid=2):
    pen = pg.mkPen(color=penCol, width=penWid)
    brush = pg.mkBrush(color=brushCol + (100,))
    shape.setPen(pen)
    shape.setBrush(brush)


def subtractiveShapeStyle(shape, penCol=(255, 100, 100),
                          brushCol=(0, 0, 0, 0), penWid=3):
    pen = pg.mkPen(color=penCol, width=penWid)
    brush = pg.mkBrush(color=brushCol)
    shape.setPen(pen)
    shape.setBrush(brush)


def paintCircle(image, fill, x, y, radius):
    # Make 3-Channel
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # Draw Circle
    outIm = cv2.circle(img=image,
                       center=(x, y),
                       radius=radius,
                       color=(fill, fill, fill),
                       thickness=-1,
                       lineType=cv2.LINE_AA)  # 8

    # Make Greyscale
    imgray = cv2.cvtColor(outIm, cv2.COLOR_BGR2GRAY)

    return imgray


def getContours(inputImage=np.zeros([500, 500, 3], dtype=np.uint8)):
    # if we have a color-channel, convert to grayscale
    if len(inputImage.shape) == 3:
        inputImage = cv2.cvtColor(inputImage, cv2.COLOR_BGR2GRAY)

    im, contours, hierarchy = cv2.findContours(inputImage, cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)

    return contours


def paintFillCheck(event, modifier):
    # probes button clicks to see if we should be painting, erasing, or not
    doPaint = False

    if event.buttons() == Qt.LeftButton:
        doPaint = True
        fill = 1

    if event.buttons() == Qt.RightButton:
        doPaint = True
        fill = 0

    if doPaint:
        if modifier:
            fill = 1 - fill
        return fill

    return False


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


# def RectClickEvent(self, event):
#     print("rect click!")
#     self.RectOrigin = (int(event.pos().x()), int(event.pos().y()))
#     self.draggingRect = True
#     # self.RectOrigin = (x, y)
# def RectHoverEvent(self, event):
#     if not self.draggingRect:
#         return
#     print("rect hver")
#     x0, y0 = self.RectOrigin
#     x1, y1 = (int(event.pos().x()), int(event.pos().y()))
#     dx, dy = (x1 - x0, y1 - y0)
#     origin = [0, 0]
#     if dx > 0:
#         origin[0] = x0
#     else:
#         origin[0] = x1
#     if dy > 0:
#         origin[1] = y0
#     else:
#         origin[1] = y1
#     dx = abs(dx)
#     dy = abs(dy)
#     self.rect.setRect(origin[0], origin[1], dx, dy)
#     # self.rect = pg.QtGui.QGraphicsRectItem(origin[0], origin[1], dx, dy)


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    myImage = np.random.randint(0, 128, (750, 750, 20), dtype=np.uint8)
    # myImage = np.zeros((512, 512, 20), dtype=np.uint8)
    form = QContourDrawerWidget(imageData=myImage)
    form.show()
    sys.exit(app.exec_())
