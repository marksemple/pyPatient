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
                             QGroupBox, QCheckBox, QFormLayout, QSplitter,
                             QComboBox,)
from PyQt5.QtGui import (QBrush, QColor,)
from PyQt5.QtCore import (Qt, pyqtSignal)
import pyqtgraph as pg
import numpy as np
import cv2

from dicommodule.new_ROI_dialog import newROIDialog
from dicommodule.Patient_ROI import CVContour2VectorArray
from dicommodule.Patient_StructureSet import Patient_StructureSet

pg.setConfigOptions(antialias=True)


class QContourViewerWidget(QWidget):
    """ Used to Display A Slice of 3D Image Data; plus ROI contour data"""
    # contOpacity = 0.20

    viewChanged = pyqtSignal(int)

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
        self.contOpacity = 0.00
        self.contThickness = 2
        self.contCompression = 0.00
        self.radius = 20
        self.thisSlice = 0
        self.hoverCount = 0
        self.planeInd = 2
        self.modality = modality

        # Lists
        self.TableSliceCount = []
        self.TableHideCheck = []
        self.tableHeaders = ['ROI', 'Color', 'Show']

        # Data Items
        self.imageItem = pg.ImageItem()
        self.StructureSet = Patient_StructureSet()

        # Widget parts
        self.applyLayout()
        self.setModality(modality)
        self.connectSignals()
        self.resize(1200, 700)

        if imageData is not None:
            print("Image is {}".format(imageData.shape))
            self.init_Image(imageData)

        if bool(ROIs):
            print("Has {} Contours".format(len(ROIs)))
            self.init_ROIs(ROIs)

    def setModality(self, modality):
        self.modality = modality
        htmlOpener = '<font size="12" color="white"><b>'
        htmlCloser = '</b></font>'
        htmlString = htmlOpener + ' ' + str(self.modality) + htmlCloser
        self.axText.setHtml('{}'.format(htmlString))

    def init_Image(self, imageData):
        """ registers imageData to Viewer, extracts some more variables;
        such as image dimensions"""
        self.originalImage = np.swapaxes(imageData, 0, 1)
        self.imageData = self.originalImage.copy()
        # self.imageData = np.swapaxes(self.imageData, 0, 2)
        self.contourImg = np.zeros(self.imageData.shape)
        self.nRows, self.nCols, self.nSlices = self.imageData.shape
        self.backgroundIm = np.array((self.nRows, self.nCols))
        self.imageItem.setImage(self.imageData[:, :, 0], autoLevels=True)
        self.StructureSet.setImageInfo({'Cols': self.nCols,
                                        'Rows': self.nRows,
                                        'NSlices': self.nSlices})
        self.init_Slider(self.slider)
        self.morphSize = int(self.nCols / 50)
        self.plotWidge.getViewBox().autoRange(padding=-0.05)
        self.hasImageData = True

    def init_ROIs(self, ROIs):
        """ adds all ROIs from a list;
        ROIs must be have a name and a color, in the least """
        # self.ROIs = ROIs
        for ROI in ROIs:
            self.StructureSet.add_ROI()

    def init_Slider(self, slider):
        """ Sets slider range and step based on dimensions of image volume """
        slider.setPageStep(1)
        slider.setRange(0, self.originalImage.shape[self.planeInd] - 1)
        self.sliceNumLabel.setText("1 / {}".format(self.nSlices))
        # self.sliceDistLabel = QLabel("0.00")

    def addROI(self, event=None, name=None, color=None,
               data=None, RefUID=uuid.uuid4(), lineWidth=1, *args):
        """ Registers a new ROI """

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

        new_ROI = self.StructureSet.add_ROI(name=name,
                                            color=color,
                                            enablePlotting=True)

        self.register_ROI(new_ROI)

    def register_ROI(self, new_ROI):
        if not bool(new_ROI.vector):
            new_ROI.makePlottable()

        self.plotWidge.addItem(new_ROI.vector[-1])
        self.add_ROI_to_Table(new_ROI)
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
        for ROI in self.StructureSet.ROI_List:
            ROI.hidden = bool(val)
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
        self.StructureSet.activeROI.linewidth = thicknessValue
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
        newComp = float(compressionValue) / 10
        self.StructureSet.activeROI.polyCompression = newComp
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def sliderChanged(self, newValue):
        """ Fcn called upon motion of the main slider;
        Changes the current index through the data volume"""
        if not self.hasImageData:
            return
        self.thisSlice = int(newValue)
        self.sliceNumLabel.setText("%d / %d" % (newValue,
                                                self.imageData.shape[2] - 1))
        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def updateEntireTable(self):
        # for ROI in self.ROIs:
            # self.updateTableFields(ROI=ROI)
        pass

    def updateTableFields(self, ROI, contours=[]):
        """ """

        nConts = 0
        ROI_Index = ROI.Number
        # print('present ROI_index', ROI_Index)
        # print(ROI['ROIName'], ROI['ROINumber'])
        # if bool(contours):
        #     for contour in contours:
        #         nConts += 1
        #     ROI['sliceCount'][self.thisSlice] = nConts
        # Nbools = sum([bool(entry) for entry in ROI.sliceCount)
        # self.TableSliceCount[ROI_Index].setText(str(Nbools))

        if ROI.hidden:
            self.TableHideCheck[ROI_Index].setText('Hidden')
        else:
            self.TableHideCheck[ROI_Index].setText('Shown')

        qCol = QBrush(QColor(*ROI.Color[0:3]))
        self.tablePicker.item(ROI_Index, 1).setBackground(qCol)

        # self.TableContCount[ROI['ROINumber']].setText(str(nConts))
        # self.TableVertCount[ROI['ROINumber']].setText(str(nVerts))

    def onCellClick(self, row, col):
        """ Handler for clicks on the TABLE object;
        different cells have different functions; organized here """

        self.changeROI(ROI_ind=row)
        thisROI = self.StructureSet.activeROI
        if col == 0:  # NAME
            pass

        elif col == 1:  # COLOR
            color = self.chooseColor()
            thisROI.Color = color[0:3]
            qCol = QBrush(QColor(*color[0:3]))
            myItem = self.tablePicker.item(row, col)
            myItem.setBackground(qCol)

        elif col == 3:  # SLICES
            pass

        elif col == 2:  # VISIBLE
            thisROI.hidden = not thisROI.hidden

        self.updateContours(isNewSlice=True)
        self.plotWidge.setFocus()

    def chooseColor(self):
        colorDiag = QColorDialog()
        colorDiag.exec_()
        color = colorDiag.selectedColor()
        return color.getRgb()

    def changeROI(self, ROI_ind):
        ROI = self.StructureSet.ROI_List[ROI_ind]
        self.StructureSet.select_ROI(number=ROI_ind)
        newWidth = int(ROI.linewidth)
        newComp = 10 * int(ROI.polyCompression)
        self.contourEdgeThickness.setSliderPosition(newWidth)
        self.contourEdgeCompression.setSliderPosition(newComp)
        self.updateContours(isNewSlice=True)
        self.roiText.setHtml(formatHTML(ROI))

    def add_ROI_to_Table(self, ROI):

        row = self.tablePicker.rowCount()
        self.tablePicker.insertRow(row)
        ROI.Number = row

        # ROI NAME
        name = QTableWidgetItem(ROI.Name)
        name.setFlags(Qt.ItemIsEnabled)
        self.tablePicker.setItem(row, 0, name)

        # ROI COLOR (clickable)
        color = QTableWidgetItem(' ')
        color.setFlags(Qt.ItemIsEnabled)
        color.setBackground(QBrush(QColor(*ROI.Color)))
        self.tablePicker.setItem(row, 1, color)

        # ROI Slice Count
        # sliceCount = QTableWidgetItem(str(sum(ROI['sliceCount'])))
        # sliceCount.setFlags(Qt.ItemIsEnabled)
        # self.TableSliceCount.append(sliceCount)
        # self.tablePicker.setItem(row, 2, sliceCount)

        # Show/Hide ROI
        visibleCheck = QTableWidgetItem("Shown")
        visibleCheck.setFlags(Qt.ItemIsEnabled)
        self.TableHideCheck.append(visibleCheck)
        self.tablePicker.setItem(row, 2, visibleCheck)

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

        autoLevs = False

        if self.hideImage is False:
            self.imageItem.show()
            medicalIm = self.imageData[:, :, self.thisSlice].copy()
        else:
            self.imageItem.hide()
            imDtype = self.imageData[:, :, self.thisSlice].dtype
            medicalIm = np.zeros(self.imageData[:, :, self.thisSlice].shape,
                                 dtype=imDtype)

        # print(medicalIm.dtype)
        # medicalIm = medicalIm.astype(np.uint)

        if self.hideContours or not bool(self.StructureSet):
            self.imageItem.setImage(medicalIm, autoLevels=autoLevs)
            return

        if isNewSlice:  # create new Background Im
            # if len(medicalIm.shape) == 2:
                # try:
                    # medicalIm = cv2.cvtColor(medicalIm, cv2.COLOR_GRAY2BGR)
                # except cv2.error:
                    # print("Somtehing wrong with pixel data type")

            for ROI in self.StructureSet.ROI_List:

                if ROI.hidden:
                    for vector in ROI.vector:
                        vector.setData(x=[], y=[])
                    continue

                if ROI is self.StructureSet.activeROI:
                    continue

                # roiDataVolume = np.swapaxes(myROI_self.planeInd)

                myROI = np.swapaxes(ROI.DataVolume, self.planeInd, 2)
                contBinaryIm = myROI[:, :, self.thisSlice].copy()
                contours, hi = getContours(inputImage=contBinaryIm,
                                           compression=ROI.polyCompression)

                self.updateOutlines(ROI,
                                    contours,
                                    ROI.linewidth,
                                    ROI.Color)

                self.updateTableFields(ROI, contours)

            self.backgroundIm = medicalIm.copy()

        backgroundIm = self.backgroundIm.astype(np.uint8)

        if len(backgroundIm.shape) == 2:
            try:
                backgroundIm = cv2.cvtColor(backgroundIm, cv2.COLOR_GRAY2BGR)
            except cv2.error:
                print("Something ELSE wrong iwth pixel data type")

        if self.StructureSet.activeROI is not None:
            thisROI = self.StructureSet.activeROI

            activeColor = scaleColor(thisROI.Color, self.imageItem.levels)
            myROI = np.swapaxes(thisROI.DataVolume, self.planeInd, 2)
            contBinaryIm = myROI[:, :, self.thisSlice].copy()
            activeCompression = thisROI.polyCompression
            activeCont, hierarchy = getContours(inputImage=contBinaryIm,
                                                compression=activeCompression)

            if not thisROI.hidden:
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

                self.updateOutlines(thisROI,
                                    activeCont,
                                    thisROI.linewidth,
                                    thisROI.Color)

            self.updateTableFields(thisROI, activeCont)

        self.imageItem.setImage(backgroundIm, autoLevels=autoLevs)

    def updateOutlines(self, ROI, contours, thickness, color):
        """ """
        if len(ROI.vector) < len(contours):
            Vs = len(ROI.vector)
            Cs = len(contours)
            for ind in range(0, (Cs - Vs)):
                ROI.vector.append(pg.PlotDataItem(antialias=True))
                self.plotWidge.addItem(ROI.vector[-1])

        for vector in ROI.vector:
            vector.setData([], [])

        if bool(contours):
            for index, contour in enumerate(contours):
                ROI.vector[index].setPen(color=color, width=thickness)
                vect = CVContour2VectorArray(contour, 0)
                ROI.vector[index].setData(x=vect[1, :] + 0.5,
                                          y=vect[0, :] + 0.5)

    def viewPick(self, index):
        if index == self.planeInd:
            return

        viewBox = self.plotWidge.getViewBox()

        if index == 0:  # axial
            viewBox.setAspectLocked(lock=True, ratio=1.0)
            self.planeInd = 2

        elif index == 1:  # saggital
            viewBox.setAspectLocked(lock=True, ratio=7)
            self.planeInd = 0

        elif index == 2:  # coronal
            viewBox.setAspectLocked(lock=True, ratio=(1 / 7))
            self.planeInd = 1

        self.imageData = np.swapaxes(self.originalImage, self.planeInd, 2)
        self.init_Slider(self.slider)
        self.updateContours(isNewSlice=True)
        viewBox.autoRange(items=[self.imageItem, ])
        self.viewChanged.emit(index)

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
        viewBox.setAspectLocked(ratio=1.0)
        viewBox.setBackgroundColor('#FFFFFF')
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

        self.viewSelect = QComboBox()
        self.viewSelect.activated.connect(self.viewPick)
        self.viewSelect.addItem('Axial View')
        self.viewSelect.addItem('Saggital View')
        self.viewSelect.addItem('Coronal View')

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
        contourControlLayout.addRow(QLabel("View"), self.viewSelect)
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
    htmlOpener = '<font size="6" color=%s>' % ColorDec2Hex(ROI.Color)
    htmlCloser = '</font>'
    htmlString = htmlOpener + ROI.Name + htmlCloser
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

    # myImage = 150 * np.random.random((500, 700, 13))
    # myImage = myImage.astype(np.uint16)

    import pickle

    staplefile = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\STAPLE_contours\P1\Staple 0.5.dat'

    with open(staplefile, 'rb') as filepath:
        StapleContour = pickle.load(filepath)


    print('StapleContour')
    print(StapleContour.shape)
    print(np.amax(StapleContour))


    form = QContourViewerWidget()  # imageData=myImage)
    form.init_Image(StapleContour.astype(np.uint16) * 255)
    form.viewPick(0)

    # form.addROI(name='test1', color=(240, 20, 20))
    # form.addROI(name='test2', color=(20, 240, 20))

    form.show()
    sys.exit(app.exec_())
