# -*- coding: utf-8 -*-

"""
Models for displaying certain types of data (related to Dicom)
(2016)

    Classes:
- DicomImagePlotItem (image item)
- DicomContourPlotItem (plot data item)
- DicomDataPlotItem (scatter item)
- SliceDataPlotItem (DicomDataPlotItem)
- contourProjectionItem (DicomDataPlotItem):
- editableContourPlotItem (DicomContourPlotItem)
"""

import pyqtgraph as pg
import numpy as np
from shapely.geometry import Polygon, Point


class DicomImagePlotItem(pg.ImageItem):
    """ ImageItem to be in scene """

    def __init__(self, dicomModel=None, *args, **kwargs):
        super().__init__(pxMode=False, *args, **kwargs)

        if bool(dicomModel):
            self.pixelData = dicomModel.getPixelData()
            self.UID2IndDict = dicomModel.UID2Ind
            self.updatePlottable(dicomModel.UID_zero)

        self.setZValue(-1)

    def setImage(self, sliceIndex=0):
        image = self.pixelData[:, :, sliceIndex].T
        super().setImage(image)

    def addModel(self, model):
        self.pixelData = model.PixelData

    def updatePlottable(self, UID):
        sliceIndex = self.UID2IndDict[UID]
        self.setImage(sliceIndex)


class DicomContourPlotItem(pg.PlotDataItem):
    """ Line for each Contour Object
        One per ROI
        Store each slice's data in a dictionary
    """

    def __init__(self,
                 ROIDict={},
                 Pat2PixTForm=np.eye(4),
                 UID2IndDict={},
                 *args, **kwargs):

        self.setPat2PixTForm(tform=Pat2PixTForm)
        pen = pg.mkPen(color=ROIDict['ROICol'], width=2)
        self.myPen = pen
        self.ROIDict = ROIDict
        # self.name = ROIDict['ROIName']
        self.UID2IndDict = UID2IndDict
        self.populateSliceDict(list(UID2IndDict.keys()))
        super().__init__(pen=pen, *args, **kwargs)

    def populateSliceDict(self, sliceList):
        """ use sliceList to create dictionary linking index to data """

        if not sliceList:
            self.sliceDict = {0: []}
            return

        self.sliceDict = dict.fromkeys(sliceList)

        for entry in self.sliceDict:
            if entry in self.ROIDict['ContourData']:
                self.sliceDict[entry] = self.ROIDict['ContourData'][entry]
            else:
                self.sliceDict[entry] = np.asarray([[], [], []]).T

    def setPat2PixTForm(self, tform):
        self.Pat2PixTForm = tform

    def updatePlottable(self, UID):
        """ update data being shown with Slice Index """
        if len(self.sliceDict[UID]) > 0:
            sliceData = self.sliceDict[UID]
            x = sliceData[:, 0]
            y = sliceData[:, 1]
            z = sliceData[:, 2]
        else:
            x = []
            y = []
            z = []
        self.setData(x=x, y=y, z=z)

    def setData(self, x=[], y=[], z=[], tForm=True, *args, **kwargs):
        """ Overwrites ScatterPlotItem setData() method to
            apply transformation before setting data """
        if tForm:
            temp = np.ones((4, len(x)))
            temp[0, :] = x
            temp[1, :] = y
            temp[2, :] = z
            temp2 = self.Pat2PixTForm.dot(temp)
            x = temp2[0, :]
            y = temp2[1, :]
            z = temp2[2, :]
        super().setData(x=x, y=y, *args, **kwargs)


class DicomDataPlotItem(pg.PlotDataItem):
    """ Abstract ScatterPlotItem that shows same regardless of slice
    Inputs:
        - symbolDict: dictionary describing the markers and lines
        - Pat2PixTForm: 4x4 numpy array that describes transformation
            that is applied to data (meant for patient space to pixel space)
        - sliceIndList: list of slices (indicies)
        - **kwargs: anything else that can go into a scatter plot item
    """

    def __init__(self, symbolDict={},
                 Pat2PixTForm=np.eye(4),
                 *args, **kwargs):

        self.setPat2PixTForm(Pat2PixTForm)
        super().__init__(pxMode=False,
                         antialias=True,
                         *args, **kwargs)
        self.setSymbolDict(symbolDict)

    def setSymbolDict(self, symbolDict={}):
        """ apply marker/line symbol style from dictionary entries """
        if not bool(symbolDict):
            return

        s = symbolDict['symbol']
        ss = symbolDict['symbolSize']
        sp = symbolDict['symbolPen']
        sb = symbolDict['symbolBrush']

        self.setPen(None)
        self.setSymbol(s)
        self.setSymbolSize(ss)
        self.setSymbolPen(sp)
        self.setSymbolBrush(sb)

    def populateSliceDict(self, *args, **kwargs):
        pass

    def setPat2PixTForm(self, tform):
        self.Pat2PixTForm = tform

    def setData(self, x=[], y=[], z=[], tForm=True, *args, **kwargs):
        """ Overwrites ScatterPlotItem setData() method to
            apply transformation before setting data """
        if tForm:
            temp = np.zeros((4, len(x)))
            temp[0, :] = x
            temp[1, :] = y
            # temp[2, :] = np.zeros((1,len(x)))
            temp[3, :] = np.ones((1, len(x)))
            temp2 = self.Pat2PixTForm.dot(temp)
            x = temp2[0, :]
            y = temp2[1, :]
            # print('<x = ', x,' , y = ', y, ' >')
        super().setData(x=x, y=y, *args, **kwargs)

    def updatePlottable(self, *args, **kwargs):
        pass

    def hide(self):
        super().setData(x=[], y=[])
        pass


class SliceDataPlotItem(DicomDataPlotItem):
    """ Abstract ScatterPlotItem that can show different scatters for
        different slices of a DICOM. Useful for contour slider, etc.
    Inputs:
        - symbolDict: dictionary describing the markers and lines
        - Pat2PixTForm: 4x4 numpy array that describes transformation
            that is applied to data (meant for patient space to pixel space)
        - sliceIndList: list of slices (indicies)
        - **kwargs: anything else that can go into a scatter plot item
    """

    def __init__(self, UID2IndDict={}, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.populateSliceDict(UID2IndDict)
        self.UID2IndDict = UID2IndDict
        self.nPts = 0

    def populateSliceDict(self, UID2IndDict):
        """ use sliceList to create dictionary linking index to data """
        if bool(UID2IndDict):
            self.sliceDict = dict.fromkeys(UID2IndDict)
            for entry in self.sliceDict:
                self.sliceDict[entry] = []
        else:
            self.sliceDict = {0: []}

    def addPoint(self, sliceUID=0, x=[], y=[]):
        """ append point to certain slice """
        self.nPts += 1
        point = [x, y]
        self.sliceDict[sliceUID].append(point)
        self.updatePlottable(sliceUID=sliceUID)
        # print("Refs at: ", self.sliceDict)

    def clearPoints(self, sliceUID=0):
        """ Refresh sliceDict """
        self.nPts = 0
        self.populateSliceDict(UID2IndDict=self.sliceDict.keys())
        self.updatePlottable(sliceUID=sliceUID)

    def updatePlottable(self, sliceUID):
        """ update data being shown with Slice Index """
        # print("Update Slice , uid:", sliceUID)
        # try:
        if len(self.sliceDict[sliceUID]) > 0:
            sliceData = np.asarray(self.sliceDict[sliceUID])
            self.setData(x=sliceData[:, 0], y=sliceData[:, 1])
        else:
            self.setData(x=[], y=[])
        # except Exception as e:
            # print(e, "in slicer updater")
            # self.setData(x=[], y=[])

class contourProjectionItem(DicomDataPlotItem):
    """ docstring """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Shapely UNION
        pass


class editableContourPlotItem(DicomContourPlotItem):
    """ A contour object that can be altered """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("EDITABLE THO")

    def setDefaultData(self):
        self.defaultData = np.asarray(self.getData()).T

    def CheckPtInsidePoly(self, point):
        recurrentPoly = PlotItemToPolygon(self)
        return(recurrentPoly.contains(Point([point.x(), point.y()])))

    def addPoint(self, circle, newPt, size):
        polydata = painterCircle.transformData(circle, newPt, size)
        newPoly = Polygon(polydata)
        try:
            recurrentPoly = PlotItemToPolygon(self)
            recurrentPoly = recurrentPoly.union(newPoly)
            X, Y = PolygonToPlotItem(recurrentPoly)
            self.setData(x=X, y=Y)
        except AttributeError as e:
            print(e)

    def subPoint(self, circle, newPt, size):
        polydata = painterCircle.transformData(circle, newPt, size)
        newPoly = Polygon(polydata)
        try:
            recurrentPoly = PlotItemToPolygon(self)
            recurrentPoly = recurrentPoly.difference(newPoly)
            X, Y = PolygonToPlotItem(recurrentPoly)
            self.setData(x=X, y=Y, z=np.ones(len(X)))
        except AttributeError as e:
            print(e)

    def TransformBy(self, thisPos, translation, rotation):
        # allData = self.getData()
        # npData = np.asarray(allData).T
        # print(len(npData))

        # tempData = self.defaultData[:, 0:2].copy()
        tempData = np.ones([len(self.defaultData), 3])
        tempData[:, 0:2] = self.defaultData[:, 0:2]
        transl0 = np.eye(3)
        transl0[0:2, 2] = - (thisPos - translation)
        tempData = transl0.dot(tempData.T).T
        Trotation = np.eye(3)
        Trotation[0:2, 0:2] = np.array([[np.cos(rotation), - np.sin(rotation)],
                                        [np.sin(rotation), np.cos(rotation)]])
        tempData = Trotation.dot(tempData.T).T
        transl1 = np.eye(3)
        transl1[0:2, 2] = (thisPos - translation)
        # tempData = transl1.dot(transl1).dot(tempData.T).T
        tempData = transl1.dot(tempData.T).T
        transl1 = np.eye(3)
        transl1[0:2, 2] = translation
        # tempData = transl1.dot(transl1).dot(tempData.T).T
        tempData = transl1.dot(tempData.T).T
        self.setData(x=tempData[:, 0], y=tempData[:, 1])

    def ContourPlottable2Data(self):
        contourPlottable = self.PlotWidge.activeContourPlottable
        pts_ = np.asarray(contourPlottable.getData()).T
        temp = np.ones([len(pts_[:, 1]), 4])
        temp[:, 0:2] = pts_
        temp[:, 2] = self.thisSliceIndex
        pts = self.ImVolume.IM2PPTransformation.dot(temp.T).T
        for contour in self.ImVolume.contourObjs.values():
            if contour.contourName == contourPlottable.contourName:
                contour.slice2ContCoords[self.thisSliceLoc][0] = pts[:, 0:3]


class painterCircle(pg.PlotDataItem):
    def __init__(self, color='w', centre=(0, 0),
                 radius=1, res=80, penWidth=2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.x0 = np.array([np.cos(i) for i in np.linspace(0, 2 * np.pi, res)])
        self.y0 = np.array([np.sin(i) for i in np.linspace(0, 2 * np.pi, res)])
        self.setCircleData(centre, radius)
        self.myPen = pg.mkPen(color=color, width=penWidth)
        self.setPen(self.myPen)

    def setCircleData(self, centre=(0, 0), radius=1, *args, **kwargs):
        self.dataPts = self.transformData(self, centre, radius)
        super().setData(x=self.dataPts[:, 0],
                        y=self.dataPts[:, 1],
                        *args, **kwargs)

    @staticmethod
    def transformData(self, centre, radius):
        ptList = np.array([radius * self.x0 + centre[0],
                           radius * self.y0 + centre[1]])
        return ptList.T


def PolygonToPlotItem(polygon):
    npPoly = np.array(polygon.exterior)
    return npPoly[:, 0], npPoly[:, 1]


def PlotItemToPolygon(plotItem):
    # print(plotItem.getData())
    allData = plotItem.getData()
    npData = np.asarray(allData).T
    if npData.any():
        return Polygon(npData)
    else:
        return Polygon()


if __name__ == "__main__":
    pass
