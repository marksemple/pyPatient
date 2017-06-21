#
"""
    Object Representation for a CATHETER object
"""

import numpy as np


class CatheterObj(object):
    def __init__(self, row=None, col=None):
        super().__init__()

        self.templateCols = ['A', 'a', 'B', 'b',
                             'C', 'c', 'D', 'd',
                             'E', 'e', 'F', 'f', 'G']

        self.templateRows = [1, 1.5, 2, 2.5,
                             3, 3.5, 4, 4.5,
                             5, 5.5, 6, 6.5, 7]

        if type(col) == str:
            if col in self.templateCols


    def addMeasurements(self, measurements):
        self.pointList = measurements.tolist()
        self.measurement = measurements
        self.length = calculateLength(measurements)

        self.interpolatedPts = self.getInterpolatedPoints(spacing=1)

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

    def getVirtualInterpolatedPoints(self, spacing):
        return interpolateMeasurements(self.virtual_measurements, spacing)

    def getInterpolatedPoints(self, spacing):
        return interpolateMeasurements(self.measurement, spacing)

    def resampleMeasurements(self, factor):
        pass

    def template_code(self):
        # return 'A a B b C c D d E e F f G g ' + '1 1.5 2 2.5 3 3.5 4 4.5 ...'
        pass


def calculateLength(pointlist):
        rolled = np.roll(pointlist, axis=0, shift=1)
        diff = pointlist - rolled
        length = np.sum(np.linalg.norm(diff[1:], axis=1))
        return length


def interpolateMeasurements(pointlist, spacing):
    """ Linear interpolation between catheter key points """
    rolled = np.roll(pointlist, axis=0, shift=1)
    vects = (pointlist - rolled)[1:]
    lengths = np.linalg.norm(vects, axis=1)
    unitVects = np.divide(vects.T, lengths).T
    interpolated_points = []

    for ind, point in enumerate(pointlist):
        if ind == 0:
            # first point
            startingPt = point + 6 * unitVects[ind]
            remainder = 0
            print('FIRST POINT')
        elif ind == (len(pointlist) - 1):
            # last point
            if remainder > 0:
                print("SOME LEFTOVER")
                lastPt = interpolated_points[-1] + spacing * unitVects[-1]
                interpolated_points.append(lastPt)
            print('LAST POINT')
            print('Total of {} points in this segment'.format(len(interpolated_points)))
            # print('Remainder:', remainder)
            print('total length:', calculateLength(interpolated_points))
            return interpolated_points

        else:
            startingPt = point + unitVects[ind] * (spacing - remainder)

        interpolated_points.append(startingPt)
        targetPt = pointlist[ind + 1]
        residualLen = np.linalg.norm(targetPt - startingPt)
        nPts = int((residualLen / spacing))
        remainder = (residualLen / spacing) - nPts

        for pt in range(0, nPts):
            thisPt = interpolated_points[-1]
            newPt = thisPt + unitVects[ind] * spacing
            interpolated_points.append(newPt)

    print("this should never be printedd...")
    # return interpolated_points

