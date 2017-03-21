# ContourDrawer.py
# -*- coding: utf-8 -*-
"""
    Tool to View and Add Regions of Interest to an Image Volume
"""

import sys
from PyQt5.QtCore import (Qt, pyqtSignal)

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
    editingFlag = False
    doPaintFlag = False
    prevInContour = False
    enteredContour = pyqtSignal()
    leftContour = pyqtSignal()

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
        self.morphSize = int(self.nCols / 50)
        self.enteredContour.connect(self.onEnterContour)
        self.leftContour.connect(self.onExitContour)

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

    def primeToFill(self):
        self.fill = 255
        pass

    def primeToWipe(self):
        self.fill = 0
        pass

    def paintFillCheck(self, event, modifier):
        # probes button clicks to see if we should be painting, erasing, or not
        # doPaint = False
        # print(dir(event))
        # print(event.pos().x())

        if event.buttons() == Qt.LeftButton:

            # doPaint = True
            myPixel = [int(event.pos().y()), int(event.pos().x())]
            myImage = self.thisROI['raster'][:, :, self.thisSlice]
            pixelValue = myImage[myPixel[0], myPixel[1]]

            if pixelValue == 0:
                fill = 255
                self.doPaint = True
            else:
                fill = 0
                self.doPaint = False

            # if myPixel
            # fill = 255

        # if event.buttons() == Qt.LeftButton:
            # doPaint = True
            # fill = 255

        # if event.buttons() == Qt.RightButton:
            # doPaint = True
            # fill = 0

        # if self.doPaint:
        if modifier:
            fill = 1 - fill
        return fill

        return False

    def PaintClickEvent(self, event):
        """ When mouse clicks on IMAGE ITEM """
        self.tempCoordList = []
        ts = self.thisSlice
        self.paintCount = 0
        self.editingFlag = True

        x, y = (int(event.pos().x()), int(event.pos().y()))
        self.tempCoordList.append([[y, x]])



        oldIm = self.thisROI['raster'][:, :, ts]
        __outIm, cont, __hier = cv2.findContours(oldIm.astype(np.uint8),
                                                 cv2.RETR_TREE,
                                                 cv2.CHAIN_APPROX_SIMPLE)

        isEmpty = not bool(len(cont))

        if oldIm[x, y] > 0 or isEmpty:
            fill = 255
            self.doPaint = True
        else:
            fill = 0
            self.doPaint = False

        self.thisROI['raster'][:, :, ts] = paintCircle(image=oldIm,
                                                       fill=fill,
                                                       x=y, y=x,
                                                       radius=self.radius)
        self.updateContours(isNewSlice=True)

    def PaintReleaseEvent(self, event):
        self.editingFlag = False
        # self.updateSliceCount()

    def onEnterContour(self):
        print('enter')
        modifyBrushStyle(self.circle, self.thisROI['color'],
                         self.contThickness, 'additive')
        self.primeToFill()

    def onExitContour(self):
        print('exit :_:')
        modifyBrushStyle(self.circle, self.thisROI['color'],
                         self.contThickness, 'subtractive')
        self.primeToWipe()

    def PaintHoverEvent(self, event):
        """ When cursor is over IMAGE ITEM """
        try:
            x, y = (int(event.pos().x()), int(event.pos().y()))
            print(x, y)
            inContour = bool(int(self.thisROI['raster'][x, y, self.thisSlice]))

            # print("your re:", y, x, inContour)
            print("incontour:", inContour,' prev:', self.prevInContour)

            if inContour is True and self.prevInContour is not True:
                self.enteredContour.emit()
                self.prevInContour = True

            elif inContour is not True and self.prevInContour is True:
                self.leftContour.emit()
                self.prevInContour = False

            if event.isEnter():
                self.circle.show()

            elif event.isExit():
                self.circle.hide()

            repositionShape(self.circle, x, y, self.radius)

            # modifyBrushStyle(self.circle, self.thisROI['color'],
            # 2, 'subtractive')

            if not self.editingFlag:
                return

            ts = self.thisSlice
            oldIm = self.thisROI['raster'][:, :, ts]

            if self.doPaint:
                fill = 255
            else:
                fill = 0

            self.tempCoordList.append([[y, x]])
            pts = [np.array(self.tempCoordList).astype(np.int32)]
            thisVol = self.thisROI['raster']
            thisVol[:, :, ts] = cv2.polylines(img=oldIm.copy(),
                                              pts=pts,
                                              isClosed=False,
                                              color=(fill, fill, fill),
                                              thickness=2 * self.radius)

            self.updateContours()
            # self.paintHere(x, y, fill)
            # self.hoverCount += 1

        except Exception as ae:
            print(ae)
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



        # ~~~~~~~~~~~~~~~ TABLE Section

    def dilate_erode_ROI(self, roi, direction):
        slice0 = self.thisSlice
        # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                           (self.morphSize, self.morphSize))
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
