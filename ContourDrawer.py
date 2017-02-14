# ContourDrawer.py


# -*- coding: utf-8 -*-
"""
General Widgets for Dicom-related Programs
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout,
                             QSlider, QLabel,)
from PyQt5.QtCore import (Qt, pyqtSignal,)
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
        self.thisSlice = 0

        self.circle = pg.QtGui.QGraphicsEllipseItem(-self.radius,
                                                    -self.radius,
                                                    self.radius * 2,
                                                    self.radius * 2)
        # self.circle.setPen(pg.mkPen(color='w', width=2))
        # self.circle.setBrush(pg.mkBrush(color=(255, 100, 100, 200)))
        additiveCircleStyle(self.circle)
        self.circle.hide()

        # ~ Add Image Item to Plot Widget
        self.plotWidge = self.createViewPortal()
        self.imageItem = pg.ImageItem(self.imageData[:, :, self.thisSlice])
        # self.imageItem = DrawableImageObject(self.imageData[:, :, 0])
        self.plotWidge.addItem(self.imageItem)
        self.plotWidge.addItem(self.circle)

        # ~ Create Widget parts
        self.applyLayout()
        self.connectSignals()

    def connectSignals(self):
        self.imageItem.hoverEvent = lambda x: self.ImageHoverEvent(x)
        self.imageItem.mousePressEvent = lambda x: self.ImageClickEvent(x)
        self.imageItem.wheelEvent = lambda x: self.ImageWheelEvent(x)
        # vb = self.plotWidge.getViewBox()
        self.plotWidge.keyPressEvent = lambda x: self.PlotKeyPress(x)
        self.plotWidge.keyReleaseEvent = lambda x: self.PlotKeyRelease(x)

    def ImageHoverEvent(self, event):
        """ When cursor is over IMAGE ITEM """
        x, y = (int(event.pos().x()), int(event.pos().y()))
        if event.isEnter():
            print("Hover Enter")
            self.circle.show()
        elif event.isExit():
            print("Hover Leave")
            self.circle.hide()

        if event.buttons() == Qt.LeftButton:
            print("Paint")
            self.paintHere(x, y)

        elif event.buttons() == Qt.RightButton:
            print("Erase")
            self.paintHere(x, y, fill=0)

        repositionCircle(self.circle, x, y, self.radius)

    def ImageWheelEvent(self, event):
        """  """
        x, y = (int(event.pos().x()), int(event.pos().y()))
        try:
            angle = event.delta()
        except:
            angle = event.angleDelta().y()
        if (self.radius + np.sign(angle)) > 0:
            self.radius += np.sign(angle)
        repositionCircle(self.circle, x, y, self.radius)
        # self.updateCircle(centre=self.centre, radius=self.radius)

    def PlotKeyPress(self, event):
        if event.key() == 16777249:  # ctrl?
            # event.key() == 16777248
            print("CTRL down")
            self.keyModifier = True
            subtractiveCircleStyle(self.circle)

        if event.key() == 16777248:
            # SHIFT FOCUS TO SCROLL WHEEL?
            print("SHIFT")

    def PlotKeyRelease(self, event):
        if event.key() == 16777249:  # ctrl
            # event.key() == 16777248 or
            print("CTRL up")
            self.keyModifier = False
            additiveCircleStyle(self.circle)

    def ImageClickEvent(self, event):
        """ When mouse clicks on IMAGE ITEM """
        x, y = (int(event.pos().x()), int(event.pos().y()))
        print('Click at:', x, ', ', y)

        if event.buttons() == Qt.LeftButton:
            print("Paint")
            self.paintHere(x, y)

        elif event.buttons() == Qt.RightButton:
            print("Erase")
            self.paintHere(x, y, fill=0)

    def paintHere(self, x, y, fill=255):
        image = paintCircle(image=self.imageData[:, :, self.thisSlice],
                            fill=fill, x=x, y=y, radius=self.radius)
        self.imageData[:, :, self.thisSlice] = image
        contIm = getContourIm(image)
        self.imageItem.setImage(contIm.T)

    def createViewPortal(self, backgroundCol='#FFFFFF'):
        plotWidge = pg.PlotWidget()
        plotWidge.showAxis('left', False)
        plotWidge.showAxis('bottom', False)
        viewBox = plotWidge.getViewBox()
        viewBox.invertY(True)
        viewBox.setAspectLocked(1.0)
        viewBox.setBackgroundColor(backgroundCol)
        return plotWidge

    def applyLayout(self):
        # ~ Create "Controls" Panel Layout for Slider
        layout = QGridLayout()
        layout.addWidget(self.plotWidge, 1, 1)
        self.setLayout(layout)

    def sliderChanged(self, newValue):
        self.imageItem.setImage(self.imageData[:, :, newValue])
        self.sliceNumLabel.setText("%d / %d" % (newValue + 1, self.nSlices))

    def toggleCircle(self):
        self.showCircle = not self.showCircle


def repositionCircle(circle, x, y, radius):
    circle.setRect(x - radius,
                   y - radius,
                   2 * radius,
                   2 * radius)


def additiveCircleStyle(circle, penCol='w',
                        brushCol=(255, 100, 100, 100), penWid=2):
    pen = pg.mkPen(color=penCol, width=penWid)
    brush = pg.mkBrush(color=brushCol)
    circle.setPen(pen)
    circle.setBrush(brush)


def subtractiveCircleStyle(circle, penCol=(255, 100, 100),
                           brushCol=(0, 0, 0, 0), penWid=2):
    pen = pg.mkPen(color=penCol, width=penWid)
    brush = pg.mkBrush(color=brushCol)
    circle.setPen(pen)
    circle.setBrush(brush)


def paintCircle(image, fill, x, y, radius):

    # Make 3-Channel
    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # Draw Circle
    outIm = cv2.circle(img=image,
                       center=(x, y),
                       radius=radius,
                       color=(fill, fill, fill),
                       thickness=-1)

    # cv2.imshow('name', outIm)

    # Make Greyscale
    imgray = cv2.cvtColor(outIm, cv2.COLOR_BGR2GRAY)

    return imgray


def getContourIm(im):

    if len(im.shape) == 3:
        im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

    im2, contours, hierarchy = cv2.findContours(im, cv2.RETR_TREE,
                                                cv2.CHAIN_APPROX_SIMPLE)

    doodle = np.zeros((im2.shape[0], im2.shape[1], 3), dtype=np.uint8)

    print(doodle.shape)

    cv2.drawContours(doodle, contours, -1, (200, 200, 255), 1)

    imgray = cv2.cvtColor(doodle, cv2.COLOR_BGR2GRAY)

    return imgray

    # cv2.imshow('im2', im2)
    # cv2.imshow('im3', doodle)



class DrawableImageObject(pg.ImageItem):

    mouseEnter = pyqtSignal()
    mouseExit = pyqtSignal()
    mouseHover = pyqtSignal(tuple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        x, y = (int(event.pos().x()), int(event.pos().y()))
        print('Click at:', x, ', ', y)
        # super().mousePressEvent(event)

    def hoverEvent(self, event):

        x, y = (int(event.pos().x()), int(event.pos().y()))
        self.mouseHover.emit((x, y))

        # if event.buttons() == Qt.LeftButton:
        #     print("LEFT CLICK")

        # elif event.buttons() == Qt.RightButton:
        #     print("RIGHT CLICK")

        if event.isExit():
            self.mouseExit.emit()
            # print("Hover leave")

        elif event.isEnter():
            self.mouseEnter.emit()
            # print("Hover enter")

        super().hoverEvent(event)


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # myImage = np.random.random((500, 500, 20)) * 255
    myImage = np.zeros((500, 500, 20), dtype=np.uint8)
    form = QContourDrawerWidget(imageData=myImage)
    form.show()
    sys.exit(app.exec_())
