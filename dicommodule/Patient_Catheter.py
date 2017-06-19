#

"""
"""

import numpy as np


class CatheterObj(object):
    def __init__(self):
        super().__init__()

        self.templateCols = ['A', 'a', 'B', 'b', 'C', 'c', 'D', 'd',
                             'E', 'e', 'F', 'f', 'G']
        self.templateRows = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5,
                             5, 5.5, 6, 6.5, 7]

    def addMeasurements(self, measurements):
        self.pointList = measurements.tolist()
        self.measurement = measurements
        self.length = self.calculateLength()

    def calculateLength(self):
        rolled = np.roll(self.measurement, axis=0, shift=1)
        diff = self.measurement - rolled
        length = np.sum(np.linalg.norm(diff[1:], axis=1))
        return length

    def setTemplatePosition(self, row=1, col='A'):
        self.templateCode = [col, str(row)]
        colInd = self.templateCols.index(col)
        rowInd = self.templateRows.index(row)
        self.templateCoordinates = [rowInd, colInd]

    def getPointCoordinate(self):
        return self.templateCoordinates

    def getVirtualPoints(self):
        # x_0 = self.coordinatePose
        # y_0 =
        x_0 = 45.329114
        y_0 = 58.75
        return np.array([[x_0, y_0, 4.0],
                         [x_0, y_0, -117.5],
                         [x_0, y_0, -131.0],
                         [x_0, y_0, -236.0]])

    def resampleMeasurements(self, factor):
        pass

    def interpolateMeasurements(self, spacing):
        pass

    def template_code(self):
        # return 'A a B b C c D d E e F f G g ' + '1 1.5 2 2.5 3 3.5 4 4.5 ...'
        pass


    # def format_catheter_Data_str(self):
        # pass

    # def format()
