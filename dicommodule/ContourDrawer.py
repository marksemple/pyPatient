# ContourDrawer.py
# -*- coding: utf-8 -*-
"""
    Tool to View and Add Regions of Interest to an Image Volume
"""

import sys
from PyQt5.QtCore import (Qt, pyqtSignal)
from PyQt5.QtWidgets import (QDialog,)

import pyqtgraph as pg
import numpy as np
import cv2

from dicommodule.ContourViewer import QContourViewerWidget


class QContourDrawerWidget(QContourViewerWidget):
    """ Used to Display A Slice of 3D Image Data
    """
    enteredContour = pyqtSignal()
    leftContour = pyqtSignal()

    def __init__(self,
                 enableDraw=True,
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.editingFlag = False
        self.inContour = False
        self.prevInContour = False
        self.ctrlModifier = False
        self.paintingEnabled = False
        self.isActive = False
        self.fill = 0
        self.circle = pg.QtGui.QGraphicsEllipseItem(-self.radius,
                                                    -self.radius,
                                                    self.radius * 2,
                                                    self.radius * 2)
        self.circle.hide()
        self.plotWidge.addItem(self.circle)
        # self.enablePaintingControls()
        # self.collapseControls.click()
        self.enteredContour.connect(self.primeToFill)
        self.leftContour.connect(self.primeToWipe)

    def connectSignals(self):
        # save ORIGINAL mouse events in placeholders for later
        self.oldImageHover = self.imageItem.hoverEvent
        self.oldImageMousePress = self.imageItem.mousePressEvent
        # self.oldImageWheel = self.wheelEvent
        self.oldWheelEvent = self.wheelEvent
        self.oldPlotWidgeWheelEvent = self.plotWidge.wheelEvent
        self.plotWidge.keyPressEvent = lambda x: self.PlotKeyPress(x)
        self.plotWidge.keyReleaseEvent = lambda x: self.PlotKeyRelease(x)

    def changeROI(self, ROI_ind):
        super().changeROI(ROI_ind)
        thisROI = self.StructureSet.activeROI
        modifyBrushStyle(self.circle, thisROI.Color, 2, 'additive')

    def hideControls(self, val):
        super().hideControls(val)
        # print(val)
        if val:
            # print("enabling motion controls")
            self.enableMotionControls()
            self.paintingEnabled = False
        else:
            # print("enabling painting controls")
            self.enablePaintingControls()
            self.paintingEnabled = True

    def enablePaintingControls(self):
        self.plotWidge.setCursor(Qt.CrossCursor)

        self.imageItem.hoverEvent = self.PaintHoverEvent
        self.imageItem.mousePressEvent = self.PaintClickEvent
        self.imageItem.mouseReleaseEvent = self.PaintReleaseEvent

        # WHEEL
        # no scrolling, no zooming -- > only pen size
        self.wheelEvent = self.oldWheelEvent
        self.plotWidge.wheelEvent = self.oldPlotWidgeWheelEvent
        self.imageItem.wheelEvent = self.PaintWheelEvent

        # self.paintingEnabled = True

    def enableMotionControls(self):
        self.plotWidge.setCursor(Qt.OpenHandCursor)
        self.imageItem.hoverEvent = self.oldImageHover
        self.imageItem.mousePressEvent = self.oldImageMousePress

        # WHEEL
        # no pen size, no zooming -> only scrolling
        self.wheelEvent = self.scrollWheelEvent
        self.plotWidge.wheelEvent = self.dummyFunc
        self.imageItem.wheelEvent = self.dummyFunc
        # self.paintingEnabled = False

    def dummyFunc(self, *args, **kwargs):
        pass

    def primeToFill(self):
        self.fill = 255
        thisROI = self.StructureSet.activeROI
        modifyBrushStyle(self.circle, thisROI.Color,
                         self.contThickness, 'additive')

    def primeToWipe(self):
        self.fill = 0
        thisROI = self.StructureSet.activeROI
        modifyBrushStyle(self.circle, thisROI.Color,
                         self.contThickness, 'subtractive')

    def PaintClickEvent(self, event):
        """ When mouse clicks on IMAGE ITEM """
        if self.hasContourData is not True:
            return

        self.editingFlag = True

        self.tempCoordList = []
        ts = self.thisSlice

        x, y = (int(event.pos().x()), int(event.pos().y()))
        self.tempCoordList.append([[y, x]])

        # see if any contours exist on this slice
        oldImVol = self.StructureSet.activeROI.DataVolume
        isEmpty = checkEmpty(oldImVol[:, :, ts])

        if isEmpty or self.inContour:
            self.primeToFill()
        else:
            self.primeToWipe()

        oldImVol[:, :, ts] = paintCircle(image=oldImVol[:, :, ts],
                                         fill=self.fill,
                                         x=y, y=x,
                                         radius=self.radius)
        self.updateContours(isNewSlice=True)

    def PaintReleaseEvent(self, event):
        """ When Mouse Button is Lifted"""
        if self.hasContourData is not True:
            return

        self.editingFlag = False

        if checkEmpty(self.StructureSet.activeROI.DataVolume[:, :,
                                                             self.thisSlice]):
            self.primeToFill()

    def scrollWheelEvent(self, event):
        x, y = (int(event.pos().x()), int(event.pos().y()))
        try:
            angle = event.delta()
        except Exception as ae:
            # print(ae)
            angle = event.angleDelta().y()

        deltaWheel = np.sign(angle)
        self.slider.setSliderPosition(self.thisSlice + deltaWheel)

    def PaintHoverEvent(self, event):
        """ When cursor is over IMAGE ITEM """

        if not self.isActive:
            self.isActive = True
            self.plotWidge.setFocus()

        try:
            x, y = (int(event.pos().x()), int(event.pos().y()))
            thisROI = self.StructureSet.activeROI

            if event.isEnter():
                self.circle.show()

            elif event.isExit():
                self.circle.hide()
                self.isActive = False

            repositionShape(self.circle, x, y, self.radius)

            if not self.editingFlag:  # mouse motion without click

                binaryContIm = thisROI.DataVolume[:, :, self.thisSlice]
                NowInContour = inContourCheck((x, y), binaryContIm)

                if NowInContour is True and self.prevInContour is not True:
                    self.enteredContour.emit()
                    self.prevInContour = True
                    self.inContour = True

                elif NowInContour is not True and self.prevInContour is True:
                    self.leftContour.emit()
                    self.prevInContour = False
                    self.inContour = False
                return

            else:  # mouse motion yes click

                ts = self.thisSlice
                oldIm = thisROI.DataVolume[:, :, ts]
                self.tempCoordList.append([[y, x]])
                pts = [np.array(self.tempCoordList).astype(np.int32)]
                thisVol = thisROI.DataVolume
                thisVol[:, :, ts] = cv2.polylines(img=oldIm.copy(),
                                                  pts=pts,
                                                  isClosed=False,
                                                  color=(self.fill,
                                                         self.fill,
                                                         self.fill),
                                                  thickness=2 * self.radius)
                self.updateContours()

        except Exception as ae:
            # print(ae)
            self.circle.hide()

    def PaintWheelEvent(self, event):
        """  """
        x, y = (int(event.pos().x()), int(event.pos().y()))
        try:
            angle = event.delta()
        except Exception as ae:
            # print(ae)
            angle = event.angleDelta().y()
        if (self.radius + np.sign(angle)) > 1:
            self.radius += 2 * np.sign(angle)
        repositionShape(self.circle, x, y, self.radius)

    def PlotKeyPress(self, event):
        """ Filter key presses while plot object is active """
        # print(event.key())

        if event.key() == 65:  # 'A' -- advance one slice
            self.slider.setSliderPosition(self.thisSlice + 1)

        if event.key() == 90:  # 'Z' -- reverse one slice
            self.slider.setSliderPosition(self.thisSlice - 1)

        if bool(self.StructureSet.ROI_List):

            ss = self.StructureSet
            thisROI = ss.activeROI

            keyList = [49 + i[0] for i in enumerate(ss.ROI_List)]
            if event.key() in keyList:  # 1-9 ROI HotKeys
                ind = keyList.index(event.key())
                self.changeROI(ROI_ind=ind)

            # s, x, d, c
            if not self.paintingEnabled:
                return

            if event.key() == 83:  # s -- copy superior slice ROI
                self.unionNeighbourSlice(thisROI, -1)
            if event.key() == 88:  # x -- copy inferior slice ROI
                self.unionNeighbourSlice(thisROI, 1)
            if event.key() == 68:  # d -- dilate ROI
                self.dilate_erode_ROI(thisROI, 1)
            if event.key() == 69:  # e -- erode ROI
                self.dilate_erode_ROI(thisROI, -1)
            if event.key() == 32:  # SPACE -- Rotate through ROIs
                indList = [ROI.id for ROI in ss.ROI_List]
                ind = indList.index(thisROI.id)
                newInd = (ind + 1) % len(ss.ROI_List)
                self.changeROI(ROI_ind=newInd)

            if event.key() == 16777249:  # CTRL -- Invert Painters
                if not self.editingFlag:
                    self.doControlModifier()

            if event.key() == 16777248:  # SHIFT -- Motion Mode
                self.shiftModifier = True
                self.circle.hide()
                self.enableMotionControls()

            self.updateContours()

    def PlotKeyRelease(self, event):
        if bool(self.StructureSet.ROI_List):

            if not self.paintingEnabled:
                return

            if event.key() == 16777249:  # CTRL
                if not self.editingFlag and self.ctrlModifier:
                    self.undoControlModifier()

            if event.key() == 16777248:  # SHIFT
                self.shiftModifier = False
                self.circle.show()
                self.enablePaintingControls()

    def doControlModifier(self):
        thisROI = self.StructureSet.activeROI
        oldIm = thisROI.DataVolume[:, :, self.thisSlice]
        if checkEmpty(oldIm) or self.prevInContour:
            self.primeToWipe()
        else:
            self.primeToFill()
        self.enteredContour.disconnect()
        self.leftContour.disconnect()
        self.enteredContour.connect(self.primeToWipe)
        self.leftContour.connect(self.primeToFill)
        self.inContour = not self.inContour
        self.ctrlModifier = True

    def undoControlModifier(self):
        thisROI = self.StructureSet.activeROI
        oldIm = thisROI.DataVolume[:, :, self.thisSlice]
        if checkEmpty(oldIm) or self.prevInContour:
            self.primeToFill()
        else:
            self.primeToWipe()
        self.enteredContour.disconnect()
        self.leftContour.disconnect()
        self.enteredContour.connect(self.primeToFill)
        self.leftContour.connect(self.primeToWipe)
        self.inContour = not self.inContour
        self.ctrlModifier = False

    def unionNeighbourSlice(self, roi, direction):
        slice0 = self.thisSlice

        if slice0 == 0 and direction == -1:
            print("already at bottom!")
            return

        elif slice0 == (self.nSlices - 1) and direction == 1:
            print("already at top!")
            return

        neighbIm = roi.DataVolume[:, :, slice0 + direction].copy()
        thisIm = roi.DataVolume[:, :, slice0].copy()

        roi.DataVolume[:, :, slice0] = neighbIm + thisIm

        # ~~~~~~~~~~~~~~~ TABLE Section
    def dilate_erode_ROI(self, roi, direction):
        slice0 = self.thisSlice
        # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                           (self.morphSize, self.morphSize))
        im = roi.DataVolume[:, :, slice0].copy()
        if direction > 0:

            roi.DataVolume[:, :, slice0] = cv2.dilate(im, kernel)
        elif direction < 0:
            roi.DataVolume[:, :, slice0] = cv2.erode(im, kernel)
        self.updateContours()


def repositionShape(shape, x, y, radius):
    shape.setRect(x - radius,
                  y - radius,
                  2 * radius,
                  2 * radius)


def inContourCheck(coords, image):
    inContour = bool(int(image[coords[0], coords[1]]))
    return inContour


def checkEmpty(image):
    return not bool(np.count_nonzero(image))


def modifyBrushStyle(shape, color=(255, 100, 100), penWidth=2,
                     mode='additive'):

    penWidth = 2

    if mode == 'subtractive':
        pen = pg.mkPen(color=color, width=penWidth, style=Qt.DotLine)
        brush = pg.mkBrush(color=(0, 0, 0, 0))
    else:
        pen = pg.mkPen(color='w', width=penWidth)
        brush = pg.mkBrush(color=tuple(color) + (100,))

    shape.setPen(pen)
    shape.setBrush(brush)


class unionDialog(QDialog):
    pass


class subtractDialog(QDialog):
    pass


def doSubtraction(subtractor, subtractee):
    pass


def doUnion(one, two):
    pass


def paintCircle(image, fill, x, y, radius):
    return cv2.circle(img=image.copy(),
                      center=(x, y),
                      radius=radius,
                      color=(fill, fill, fill),
                      thickness=-1,
                      lineType=cv2.LINE_AA)  # 8


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    myImage = 55 * np.ones((700, 700, 20), dtype=np.uint16)
    form = QContourDrawerWidget() #imageData=myImage)
    form.init_Image(imageData=myImage)
    form.addROI(name='test1', color=(240, 240, 20))
    # form.addROI(name='test2', color=(20, 240, 240))
    form.show()
    sys.exit(app.exec_())
