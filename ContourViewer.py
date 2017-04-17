# -*- coding: utf-8 -*-
"""
    Interface for viewing Image Volumes and delineated Regions of Interest
    Odette Cancer Centre
    Sunnybrook Health Sciences Centre
    2017
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
    """ Used to Display A Slice of 3D Image Data; plus ROI contour data"""
    # contOpacity = 0.20

    def __init__(self, imageData=None, ROIs=[], modality='image',
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Booleans
        self.hasImageData = False
        self.hasContourData = False
        self.hideContours = False
        self.hideImage = False
        self.showCircle = True
        self.shiftModifier = False

        # Variables
        self.contOpacity = 0.20
        self.contThickness = 2
        self.contCompression = 0.75
        self.radius = 20
        self.thisSlice = 0
        self.hoverCount = 0

        # Lists
        self.TableSliceCount = []
        self.TableHideCheck = []
        self.tableHeaders = ['ROI', 'Color', 'Slices', 'Show']
        self.modality = modality

        # Data Items
        self.imageItem = pg.ImageItem()
        self.ROIs = []
        self.ROIs_byName = {}

        # Widget parts
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
        """ registers imageData to Viewer, extracts some more variables;
        such as image dimensions"""
        self.imageData = np.swapaxes(imageData, 0, 1)
        self.contourImg = np.zeros(imageData.shape)
        self.nRows, self.nCols, self.nSlices = imageData.shape
        self.backgroundIm = np.array((self.nRows, self.nCols))
        self.imageItem.setImage(self.imageData[:, :, 0], autoLevels=True)
        self.init_Slider(self.slider)
        self.morphSize = int(self.nCols / 50)
        self.plotWidge.getViewBox().autoRange(padding=-0.05)
        self.hasImageData = True

    def init_ROIs(self, ROIs):
        """ adds all ROIs from a list;
        ROIs must be have a name and a color, in the least """
        self.ROIs = ROIs
        for ROI in ROIs:
            self.addROI(name=ROI.name, color=ROI.color)

    def init_Slider(self, slider):
        """ Sets slider range and step based on dimensions of image volume """
        slider.setPageStep(1)
        slider.setRange(0, self.nSlices - 1)
        self.sliceNumLabel.setText("1 / {}".format(self.nSlices))
        # self.sliceDistLabel = QLabel("0.00")

    def addROI(self, event=None, name=None, color=None, num=-1,
               data=None, RefUID=uuid.uuid4(), lineWidth=1, *args):
        """ Registers a new ROI """

        # if num == -1:
        num = len(self.ROIs)

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

        # self.ROIs.append()

        # add make ROI object
        self.ROIs.append({'ROINumber': num,
                          'ROIName': name,
                          'ROIColor': color[0:3],
                          'FrameRef_UID': RefUID,
                          'DataVolume': data,
                          'id': uuid.uuid4(),
                          'vector': [pg.PlotDataItem()],
                          'sliceCount': counter,
                          'lineWidth': lineWidth,
                          'polyCompression': 0.7,
                          'hidden': False})

        self.ROIs_byName[name] = self.ROIs[-1]

        self.ROIs[-1]['vector'][-1].setPen(color=color[0:3], width=lineWidth)
        self.plotWidge.addItem(self.ROIs[-1]['vector'][-1])

        self.add_ROI_to_Table(self.ROIs[-1])
        self.changeROI(ROI_ind=len(self.ROIs) - 1)
        self.hasContourData = True
        self.plotWidge.setFocus()

    def connectSignals(self):
        pass

    def hideControls(self, val):
        """ Toggles the CONTROLS side panel into sight """
        if val:
            self.tableWidge.hide()
            self.collapseControls.setText('<< Controls')
        else:
            self.tableWidge.show()
            self.collapseControls.setText('>> Controls')
        self.plotWidge.setFocus()

    def hideContoursFcn(self, val):
        """ """
        for ROI in self.ROIs:
            ROI['hidden'] = bool(val)
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def hideImageFcn(self, isChecked):
        """ Fcn called upon check/uncheck of the 'HIDEIMAGE' checkbox;
        toggles viewer-level boolean for whether/not to display image"""
        if bool(isChecked):
            self.hideImage = True
        else:
            self.hideImage = False
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def thicknessChange(self, thicknessValue):
        """ Fcn called upon motion of the "LINE WIDTH" slider;
        adjusts the thickness of the outline for the Active Contour"""
        self.thisROI['lineWidth'] = thicknessValue
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def opacityChange(self, opacityValue):
        """ Fcn called upon motion of the "OPACITY" slider;
        adjusts how transparent the Active Contour appears on the display"""
        self.contOpacity = float(opacityValue) / 10.0
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def compressChange(self, compressionValue):
        """ Fcn called upon motion of the "LINE SIMPLIFICATION" slider;
        adjusts how much 'epsilon' to include in the Douglas-Peucker
        polynomial simplification algorithm for the contour line """
        self.thisROI['polyCompression'] = float(compressionValue) / 10
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def sliderChanged(self, newValue):
        """ Fcn called upon motion of the main slider;
        Changes the current index through the data volume"""
        if not self.hasImageData:
            return
        self.thisSlice = int(newValue)
        try:
            self.sliceNumLabel.setText("%d / %d" % (newValue,
                                                    self.nSlices - 1))
            self.updateContours(isNewSlice=True)
            self.plotWidge.setFocus()
        except:
            pass

    def updateEntireTable(self):
        for ROI in self.ROIs:
            self.updateTableFields(ROI=ROI)

    def updateTableFields(self, ROI, contours=[]):
        """ """
        nConts = 0
        ROI_Index = ROI['tableInd']
        # print('present ROI_index', ROI_Index)
        # print(ROI['ROIName'], ROI['ROINumber'])
        if bool(contours):
            for contour in contours:
                nConts += 1
            ROI['sliceCount'][self.thisSlice] = nConts

        Nbools = sum([bool(entry) for entry in ROI['sliceCount']])

        self.TableSliceCount[ROI_Index].setText(str(Nbools))

        if ROI['hidden']:
            self.TableHideCheck[ROI_Index].setText('Hidden')
        else:
            self.TableHideCheck[ROI_Index].setText('Shown')

        qCol = QBrush(QColor(*ROI['ROIColor'][0:3]))
        self.tablePicker.item(ROI_Index, 1).setBackground(qCol)

        # self.TableContCount[ROI['ROINumber']].setText(str(nConts))
        # self.TableVertCount[ROI['ROINumber']].setText(str(nVerts))

    def onCellClick(self, row, col):
        """ Handler for clicks on the TABLE object;
        different cells have different functions; organized here """

        self.changeROI(ROI_ind=row)

        if col == 0:  # NAME
            pass

        elif col == 1:  # COLOR
            color = self.chooseColor()
            self.thisROI['ROIColor'] = color[0:3]
            qCol = QBrush(QColor(*color[0:3]))
            myItem = self.tablePicker.item(row, col)
            myItem.setBackground(qCol)

        elif col == 2:  # SLICES
            pass

        elif col == 3:  # VISIBLE
            self.thisROI['hidden'] = not self.thisROI['hidden']

        self.updateContours(isNewSlice=True)
        self.roiText.setHtml(formatHTML(self.thisROI))
        self.plotWidge.setFocus()

    def chooseColor(self):
        colorDiag = QColorDialog()
        colorDiag.exec_()
        color = colorDiag.selectedColor()
        return color.getRgb()

    def changeROI(self, ROI_ind):
        ROI = self.ROIs[ROI_ind]
        self.thisROI = ROI
        newWidth = int(ROI['lineWidth'])
        newComp = 10 * int(ROI['polyCompression'])
        self.contourEdgeThickness.setSliderPosition(newWidth)
        self.contourEdgeCompression.setSliderPosition(newComp)
        self.updateContours(isNewSlice=True)
        self.roiText.setHtml(formatHTML(ROI))
        return ROI

    def add_ROI_to_Table(self, ROI):

        row = self.tablePicker.rowCount()
        self.tablePicker.insertRow(row)
        ROI['tableInd'] = row

        # ROI NAME
        name = QTableWidgetItem(ROI['ROIName'])
        name.setFlags(Qt.ItemIsEnabled)
        self.tablePicker.setItem(row, 0, name)

        # ROI COLOR (clickable)
        color = QTableWidgetItem(' ')
        color.setFlags(Qt.ItemIsEnabled)
        color.setBackground(QBrush(QColor(*ROI['ROIColor'])))
        self.tablePicker.setItem(row, 1, color)

        # ROI Slice Count
        sliceCount = QTableWidgetItem(str(sum(ROI['sliceCount'])))
        sliceCount.setFlags(Qt.ItemIsEnabled)
        self.TableSliceCount.append(sliceCount)
        self.tablePicker.setItem(row, 2, sliceCount)

        # Show/Hide ROI
        visibleCheck = QTableWidgetItem("Shown")
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
        """ *** IMPORTANT FUNCTION ***
        This is where view data is periodically updated;
        Called whenever a change is made by the user that should
        result in something different being shown on the axes;
        ie. draw new ROI, or change slice to be shown"""

        if self.hideImage is False:
            self.imageItem.show()
            medicalIm = self.imageData[:, :, self.thisSlice].copy()
        else:
            self.imageItem.hide()
            imDtype = self.imageData[:, :, self.thisSlice].dtype
            medicalIm = np.zeros(self.imageData[:, :, self.thisSlice].shape,
                                 dtype=imDtype)

        if self.hideContours or not bool(self.ROIs):
            self.imageItem.setImage(medicalIm, autoLevels=False)
            return

        if isNewSlice:  # create new Background Im
            if len(medicalIm.shape) == 2:
                medicalIm = cv2.cvtColor(medicalIm, cv2.COLOR_GRAY2BGR)

            for ROI in self.ROIs:

                if ROI['hidden']:
                    for vector in ROI['vector']:
                        vector.setData(x=[], y=[])
                    continue

                if ROI['id'] == self.thisROI['id']:
                    continue

                contBinaryIm = ROI['DataVolume'][:, :, self.thisSlice].copy()
                contours, hi = getContours(inputImage=contBinaryIm,
                                           compression=ROI['polyCompression'])

                self.updateOutlines(ROI,
                                    contours,
                                    ROI['lineWidth'],
                                    ROI['ROIColor'])

                self.updateTableFields(ROI, contours)

            self.backgroundIm = medicalIm.copy()

        backgroundIm = self.backgroundIm

        if len(backgroundIm.shape) == 2:
            backgroundIm = cv2.cvtColor(backgroundIm, cv2.COLOR_GRAY2BGR)

        activeColor = scaleColor(self.thisROI['ROIColor'], self.imageItem.levels)
        contBinaryIm = self.thisROI['DataVolume'][:, :, self.thisSlice].copy()
        activeCompression = self.thisROI['polyCompression']
        activeCont, hierarchy = getContours(inputImage=contBinaryIm,
                                            compression=activeCompression)

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

            backgroundIm = waterMarkedIm

            self.updateOutlines(self.thisROI,
                                activeCont,
                                self.thisROI['lineWidth'],
                                self.thisROI['ROIColor'])

        self.imageItem.setImage(backgroundIm, autoLevels=False)
        self.updateTableFields(self.thisROI, activeCont)

    def updateOutlines(self, ROI, contours, thickness, color):
        """ """
        if len(ROI['vector']) < len(contours):
            Vs = len(ROI['vector'])
            Cs = len(contours)
            for ind in range(0, (Cs - Vs)):
                ROI['vector'].append(pg.PlotDataItem())
                self.plotWidge.addItem(ROI['vector'][-1])

        for vector in ROI['vector']:
            vector.setData([], [])

        if bool(contours):
            for index, contour in enumerate(contours):
                ROI['vector'][index].setPen(color=color, width=thickness)
                vect = CVContour2VectorArray(contour, 0)
                ROI['vector'][index].setData(x=vect[1, :] + 0.5,
                                             y=vect[0, :] + 0.5)

    def applyLayout(self):
        """ Definition of WIDGET Layout"""
        # ~ Create "Controls" Panel Layout for Slider

        # ~~~~~~~~~~~~~ VIEWER SECTION
        # Canvas for viewing and interacting with patient image data
        # self.plotWidge = plotWidge = pg.PlotWidget()
        self.plotWidge = plotWidge = pg.PlotWidget()
        plotWidge.showAxis('left', False)
        plotWidge.showAxis('bottom', False)
        plotWidge.setAntialiasing(True)
        plotWidge.addItem(self.imageItem)
        plotWidge.setBackground((255, 255, 255))
        plotWidge.hideButtons()
        viewBox = plotWidge.getViewBox()
        viewBox.invertY(True)
        viewBox.setAspectLocked(1.0)
        viewBox.setBackgroundColor('#DDDDDD')
        # viewBox.setBackgroundColor('#888888')
        viewBox.state['autoRange'] = [False, False]
        viewBox.sigStateChanged.connect(self.on_VB_Resize)
        htmlOpener = '<font size="12" color="white"><b>'
        htmlCloser = '</b></font>'
        htmlString = htmlOpener + ' ' + str(self.modality) + htmlCloser
        self.axText = pg.TextItem(text='{}'.format('-'), html=htmlString)
        self.roiText = pg.TextItem()
        plotWidge.addItem(self.axText)
        plotWidge.addItem(self.roiText)
        plotWidge.setStyleSheet("QWidget {border: none;}")
        viewBox.autoRange()

        # ~~~~~~~~~~~~~~~ SLIDER SECTION
        # Controls for scanning through slices, and some labels
        sliderLayout = QHBoxLayout()
        # MW = 40  # minimumWidth
        self.slider = QSlider()
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.valueChanged.connect(self.sliderChanged)
        # self.slider.setMinimumWidth(MW)
        self.sliceNumLabel = QLabel("1 / N")
        self.sliceDistLabel = QLabel("0.00")

        self.collapseControls = QPushButton('<< Controls', checkable=True)
        self.collapseControls.setChecked(False)
        self.collapseControls.clicked.connect(self.hideControls)

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
        self.contourFillOpacity.setRange(0, 8.5)
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
        contourControlLayout.addRow(QLabel("Hide Contour"), self.contourHide)
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
                            QSizePolicy.Preferred)
        table.resizeColumnsToContents()

        # table.horizontalHeader().setStretchLastSection(True)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        hHeader = table.horizontalHeader()
        vHeader = table.verticalHeader()
        hwidth = hHeader.length()
        vwidth = vHeader.width()
        fwidth = table.frameWidth() * 2
        # table.setFixedWidth(vwidth + hwidth + fwidth)
        # table.setFixedHeight((vwidth + hwidth + fwidth) * 1.15)

        table.horizontalHeader().setResizeMode(QHeaderView.Stretch)

        self.addROIbttn = bttn = QPushButton(" + New ROI")
        bttn.clicked.connect(self.addROI)
        bttn.setFixedWidth(vwidth + hwidth + fwidth)

        tableWidgeLayout.addWidget(bttn)
        tableWidgeLayout.addWidget(table, 10)
        tableWidgeLayout.addWidget(contourControls)
        # tableWidgeLayout.addStretch()

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

    def on_VB_Resize(self, VB):
        VR = VB.viewRect()
        try:
            VRR = VR.bottom() - VR.y()
            self.axText.setPos(VR.x(), VR.y())
            self.roiText.setPos(VR.x(), VR.y() + VRR / 20)
        except:
            pass


def scaleColor(color, levels):
    scale = (levels[1] - levels[0]) / 255
    newColor = tuple([(scale * x + levels[0]) for x in color])
    return newColor


def formatHTML(ROI):
    htmlOpener = '<font size="6" color=%s>' % ColorDec2Hex(ROI['ROIColor'])
    htmlCloser = '</font>'
    htmlString = htmlOpener + ROI['ROIName'] + htmlCloser
    return htmlString


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


def ColorHex2Dec(hexString):
    if not len(hexString) == 7 or not hexString[0] == "#":
        return "Invalid Hex Color"
    hexList = [hexString[1:3], hexString[3:5], hexString[5:7]]
    decimalList = [int(hexStr, 16) for hexStr in hexList]
    return decimalList


def ColorDec2Hex(colorList):
    if not len(colorList) >= 3:
        return "Invalid Color List"
    hexString = '#'
    for col in colorList[0:3]:
        hexBit = hex(col)[2:].upper()
        if len(hexBit) == 1:
            hexBit = '0' + hexBit
        hexString += hexBit
    return hexString


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    myImage = 150 * np.random.random((700, 700, 3))
    myImage = myImage.astype(np.uint16)

    form = QContourViewerWidget()  # imageData=myImage)
    form.init_Image(myImage)

    # form.addROI(name='test1', color=(240, 20, 20))
    # form.addROI(name='test2', color=(20, 240, 20))

    form.show()
    sys.exit(app.exec_())
