import numpy as np
from pyqtgraph import PlotDataItem, mkPen
from shapely.geometry import Polygon, Point


class contourPlotModel(PlotDataItem):
    def __init__(self, contourName, pen=mkPen(color='w', width=2),
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contourName = contourName
        self.recurrentPoly = PlotItemToPolygon(self)
        self.defaultData = None
        self.setBrush([200, 0, 0])
        self.myPen = pen
        self.setPen(pen)
        self.firstTime = True

    def setData(self, *args, **kwargs):
        super().setData(*args, **kwargs)

    def setDefaultData(self):
        self.defaultData = np.asarray(self.getData()).T

    def CheckPtInsidePoly(self, point):
        recurrentPoly = PlotItemToPolygon(self)
        return(recurrentPoly.contains(Point([point.x(), point.y()])))

    def addPoint(self, circle, newPt, size):
        polydata = MarkPGPlotCircle.transformData(circle, newPt, size)
        newPoly = Polygon(polydata)
        try:
            recurrentPoly = PlotItemToPolygon(self)
            recurrentPoly = recurrentPoly.union(newPoly)
            X, Y = PolygonToPlotItem(recurrentPoly)
            self.setData(x=X, y=Y)
        except AttributeError as e:
            print(e)

    def subPoint(self, circle, newPt, size):
        polydata = MarkPGPlotCircle.transformData(circle, newPt, size)
        newPoly = Polygon(polydata)
        try:
            recurrentPoly = PlotItemToPolygon(self)
            recurrentPoly = recurrentPoly.difference(newPoly)
            X, Y = PolygonToPlotItem(recurrentPoly)
            self.setData(x=X, y=Y)
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


class MarkPGPlotCircle(PlotDataItem):
    def __init__(self, color='w', centre=(0, 0),
                 radius=1, res=80, penWidth=2, *args, **kwargs):
        super(MarkPGPlotCircle, self).__init__(*args, **kwargs)
        self.x0 = np.array([np.cos(i) for i in np.linspace(0, 2 * np.pi, res)])
        self.y0 = np.array([np.sin(i) for i in np.linspace(0, 2 * np.pi, res)])
        self.setCircleData(centre, radius)
        self.myPen = mkPen(color=color, width=penWidth)
        self.setPen(self.myPen)

    def setCircleData(self, centre=(0, 0), radius=1, *args, **kwargs):
        self.dataPts = self.transformData(self, centre, radius)
        super(MarkPGPlotCircle, self).setData(x=self.dataPts[:, 0],
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
