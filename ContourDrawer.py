# ContourDrawer.py
# -*- coding: utf-8 -*-
"""
    Tool to View and Add Regions of Interest to an Image Volume
"""

import sys
from PyQt5.QtCore import (Qt,)
import pyqtgraph as pg
import numpy as np
import cv2

# from new_ROI_dialog import newROIDialog
from ContourViewer import QContourViewerWidget  # , scaleColor, getContours


class QContourDrawerWidget(QContourViewerWidget):
    """ Used to Display A Slice of 3D Image Data
    """

    # painting = False
    # imageItem = pg.ImageItem()
    # radius = 20
    # showCircle = True
    # ctrlModifier = False
    # shiftModifier = False
    # thisSlice = 0
    # hoverCount = 0
    # tableHeaders = ['ROI', 'Color', 'Slices', 'Contours']

    def __init__(self,
                 enableDraw=True,
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.circle = pg.QtGui.QGraphicsEllipseItem(-self.radius,
                                                    -self.radius,
                                                    self.radius * 2,
                                                    self.radius * 2)
        self.circle.hide()
        self.shape = self.circle
        self.plotWidge.addItem(self.circle)
        self.enablePaintingControls()

    def connectSignals(self):
        # save ORIGINAL mouse events in placeholders for later
        self.oldImageHover = self.imageItem.hoverEvent
        self.oldImageMousePress = self.imageItem.mousePressEvent
        self.oldImageWheel = self.imageItem.wheelEvent
        self.plotWidge.keyPressEvent = lambda x: self.PlotKeyPress(x)
        self.plotWidge.keyReleaseEvent = lambda x: self.PlotKeyRelease(x)

    def changeROI(self, ROI_ind):
        ROI = self.ROIs[ROI_ind]
        self.thisROI = ROI
        self.updateContours(isNewSlice=True)
        modifyBrushStyle(self.circle, ROI['color'], 2, 'additive')
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
        # self.updateSliceCount()

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
        if (self.radius + np.sign(angle)) > 1:
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

        # self.updateSliceCount()

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
        brush = pg.mkBrush(color=tuple(color) + (100,))

    shape.setPen(pen)
    shape.setBrush(brush)


def paintCircle(image, fill, x, y, radius):
    return cv2.circle(img=image.copy(),
                      center=(x, y),
                      radius=radius,
                      color=(fill, fill, fill),
                      thickness=-1,
                      lineType=cv2.LINE_AA)  # 8


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
    myImage = 55 * np.ones((700, 700, 20), dtype=np.uint16)
    # for index, thisSlice in enumerate(myImage):
        # myImage[:, :, index - 1] = myImage[:, :, index - 1] * index * 10
    # myImage = np.zeros((512, 512, 20), dtype=np.uint8)
    form = QContourDrawerWidget(imageData=myImage)
    # form.addROI
    form.addROI(name='test1', color=(240, 240, 20))
    form.addROI(name='test2', color=(20, 240, 240))
    form.show()
    sys.exit(app.exec_())
