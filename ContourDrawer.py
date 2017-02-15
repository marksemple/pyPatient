# ContourDrawer.py


# -*- coding: utf-8 -*-
"""
General Widgets for Dicom-related Programs
"""

import sys
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout,
                             QLabel, QSlider)
from PyQt5.QtCore import (Qt, )
import pyqtgraph as pg
import numpy as np

import cv2


class QContourDrawerWidget(QWidget):
    """ Used to Display A Slice of 3D Image Data
    """

    def __init__(self,
                 imageData=None,
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        assert(type(imageData) == np.ndarray)

        self.imageData = imageData
        self.contourImg = np.zeros(imageData.shape)
        self.nRows, self.nCols, self.nSlices = imageData.shape

        self.radius = 40
        self.showCircle = True
        self.ctrlModifier = False
        self.shiftModifier = False
        self.thisSlice = 0
        self.ROIs = []

        self.addROI(name='fourth', color=(255, 48, 48))
        self.addROI(name='third', color=(255, 165, 0))
        self.addROI(name='fifth', color=(255, 215, 0))
        self.addROI(name='second', color=(0, 238, 0))
        self.addROI(name='first', color=(0, 238, 238))

        self.thisROI = self.ROIs[0]

        self.circle = pg.QtGui.QGraphicsEllipseItem(-self.radius,
                                                    -self.radius,
                                                    self.radius * 2,
                                                    self.radius * 2)
        additiveCircleStyle(self.circle, brushCol=self.thisROI['color'])
        self.circle.hide()

        # ~ Add Image Item to Plot Widget
        self.plotWidge = self.createViewPortal()
        self.imageItem = pg.ImageItem()
        self.imageItem.setImage(self.imageData[:, :, self.thisSlice].T,
                                autoLevels=False)
        self.plotWidge.addItem(self.imageItem)
        self.plotWidge.addItem(self.circle)

        # ~ Create Widget parts
        self.createControls()
        self.applyLayout()
        self.connectSignals()
        self.resize(700, 700)

    def createViewPortal(self, backgroundCol='#FFFFFF'):
        plotWidge = pg.PlotWidget()
        plotWidge.showAxis('left', False)
        plotWidge.showAxis('bottom', False)
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
        self.thisSlice = int(newValue)
        self.sliceNumLabel.setText("%d / %d" % (newValue + 1, self.nSlices))
        self.updateContours()

    def addROI(self, name='contour', color=(240, 240, 240)):
        self.ROIs.append({'color': color,
                          'name': name,
                          'raster': np.zeros((self.nRows, self.nCols,
                                              self.nSlices), dtype=np.uint8)})

    def connectSignals(self):
        # save ORIGINAL mouse events in placeholders for later
        self.oldImageHover = self.imageItem.hoverEvent
        self.oldImageMousePress = self.imageItem.mousePressEvent
        self.oldImageWheel = self.imageItem.wheelEvent

        self.enablePaintingControls()

        self.plotWidge.keyPressEvent = lambda x: self.PlotKeyPress(x)
        self.plotWidge.keyReleaseEvent = lambda x: self.PlotKeyRelease(x)

    def enablePaintingControls(self):
        self.plotWidge.setCursor(Qt.CrossCursor)
        self.imageItem.hoverEvent = lambda x: self.PaintHoverEvent(x)
        self.imageItem.mousePressEvent = lambda x: self.PaintClickEvent(x)
        self.imageItem.wheelEvent = lambda x: self.PaintWheelEvent(x)

    def enableMotionControls(self):
        self.plotWidge.setCursor(Qt.OpenHandCursor)
        self.imageItem.hoverEvent = lambda x: self.oldImageHover(x)
        self.imageItem.mousePressEvent = lambda x: self.oldImageMousePress(x)
        self.imageItem.wheelEvent = lambda x: self.oldImageWheel(x)

    def PaintClickEvent(self, event):
        """ When mouse clicks on IMAGE ITEM """
        x, y = (int(event.pos().x()), int(event.pos().y()))
        # print('Click at:', x, ', ', y)
        fill = paintFillCheck(event, self.ctrlModifier)
        self.paintHere(x, y, fill)

    def PaintHoverEvent(self, event):
        """ When cursor is over IMAGE ITEM """
        try:

            x, y = (int(event.pos().x()), int(event.pos().y()))

            if event.isEnter():
                self.circle.show()
            elif event.isExit():
                self.circle.hide()

            # check to see if we need to paint
            fill = paintFillCheck(event, self.ctrlModifier)
            if fill is not False:
                self.paintHere(x, y, fill)

            repositionCircle(self.circle, x, y, self.radius)

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
        repositionCircle(self.circle, x, y, self.radius)

    def paintHere(self, x, y, fill=255):
        # draw circle on (hidden) Binary ROI Image
        thisVol = self.thisROI['raster']
        image = paintCircle(image=thisVol[:, :, self.thisSlice],
                            fill=fill, x=x, y=y, radius=self.radius)
        thisVol[:, :, self.thisSlice] = image
        self.updateContours()

    def updateContours(self):
        dataImage = self.imageData[:, :, self.thisSlice].copy()
        doFill = False

        for ROI in self.ROIs:

            if ROI['name'] == self.thisROI['name']:
                doFill = True

            contBinaryIm = ROI['raster'][:, :, self.thisSlice].copy()
            contours = getContours(inputImage=contBinaryIm)

            if len(dataImage.shape) == 2:
                dataImage = cv2.cvtColor(dataImage, cv2.COLOR_GRAY2BGR)

            # show contours on empty image
            dataImage = cv2.drawContours(image=dataImage,
                                         contours=contours,
                                         contourIdx=-1,
                                         color=ROI['color'],
                                         thickness=2,
                                         lineType=cv2.LINE_AA)  # 8

            if doFill:

                blank = dataImage.copy()
                overlayIm = cv2.drawContours(image=blank,
                                             contours=contours,
                                             contourIdx=-1,
                                             color=ROI['color'],
                                             thickness=-1,
                                             lineType=cv2.LINE_AA)  # 8

                alph = 0.3
                cv2.addWeighted(overlayIm, alph, dataImage, 1 - alph,
                                0, dataImage)
                doFill = False

        dataImage = np.swapaxes(dataImage, 0, 1)
        self.imageItem.setImage(dataImage, autoLevels=False)

    def PlotKeyPress(self, event):
        # print(event.key())
        keylist = [49, 50, 51, 52, 53]
        if event.key() in keylist:
            ind = keylist.index(event.key())
            self.thisROI = self.ROIs[ind]
            additiveCircleStyle(self.circle, brushCol=self.thisROI['color'])
            self.updateContours()

        if event.key() == 16777249:  # CTRL
            # print("CTRL DOWN")
            self.ctrlModifier = True
            subtractiveCircleStyle(self.circle, penCol=self.thisROI['color'])

        if event.key() == 16777248:  # SHIFT
            # print("SHIFT DOWN")
            self.shiftModifier = True
            self.circle.hide()
            self.enableMotionControls()

    def PlotKeyRelease(self, event):
        if event.key() == 16777249:  # CTRL
            # print("CTRL UP")
            self.ctrlModifier = False
            additiveCircleStyle(self.circle, brushCol=self.thisROI['color'])

        if event.key() == 16777248:  # SHIFT
            # print("SHIFT UP")
            self.shiftModifier = True
            self.circle.show()
            self.enablePaintingControls()


def repositionCircle(circle, x, y, radius):
    circle.setRect(x - radius,
                   y - radius,
                   2 * radius,
                   2 * radius)


def additiveCircleStyle(circle, penCol='w',
                        brushCol=(255, 100, 100), penWid=2):
    pen = pg.mkPen(color=penCol, width=penWid)
    brush = pg.mkBrush(color=brushCol + (100,))
    circle.setPen(pen)
    circle.setBrush(brush)


def subtractiveCircleStyle(circle, penCol=(255, 100, 100),
                           brushCol=(0, 0, 0, 0), penWid=3):
    pen = pg.mkPen(color=penCol, width=penWid)
    brush = pg.mkBrush(color=brushCol)
    circle.setPen(pen)
    circle.setBrush(brush)


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
                       lineType=cv2.LINE_AA)

    # cv2.imshow('name', outIm)

    # Make Greyscale
    imgray = cv2.cvtColor(outIm, cv2.COLOR_BGR2GRAY)

    return imgray


def getContours(inputImage=np.zeros([500, 500, 3], dtype=np.uint8)):

    # print("get contours input image:", inputImage.shape)
    # if we have a color-channel, convert to grayscale
    if len(inputImage.shape) == 3:
        inputImage = cv2.cvtColor(inputImage, cv2.COLOR_BGR2GRAY)

    # find contour of binary image
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


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    myImage = np.random.randint(128, 200, (512, 512, 20), dtype=np.uint8)
    # myImage = np.zeros((512, 512, 20), dtype=np.uint8)
    form = QContourDrawerWidget(imageData=myImage)
    form.show()
    sys.exit(app.exec_())
