#
"""
    Object Representation for a CATHETER object
"""

import numpy as np


class CatheterObj(object):
    def __init__(self, rowInt=None, colLetter=None,
                 rowIndex=None, colIndex=None):
        super().__init__()

        self.measurements = None
        self.template_index2location = calculateTemplateTransform()

        self.templateCols = ['A', 'a', 'B', 'b',
                             'C', 'c', 'D', 'd',
                             'E', 'e', 'F', 'f', 'G']

        self.templateRows = [1, 1.5, 2, 2.5,
                             3, 3.5, 4, 4.5,
                             5, 5.5, 6, 6.5, 7]

        if rowInt is not None and colLetter is not None:
            self.setTemplatePosition(row=rowInt, col=colLetter)

    def addMeasurements(self, measurements):
        # let measurements *just* be all points north of the template
        # we then add our corresponding template points, and our free end
        tx = self.template_X
        ty = self.template_Y
        templatePoints = np.array([[tx, ty, -117.75],
                                   [tx, ty, -131.00]])
        measurements = np.vstack((measurements, templatePoints))
        self.length = calculateLength(measurements)
        self.depth = measurements[0, 2]
        freeLength = getFreeLength(measurements)
        freePosn = measurements[-1, 2] - freeLength
        lastPt = np.array([[tx, ty, freePosn]])
        measurements = np.vstack((measurements, lastPt))
        self.measurement = measurements

    def setTemplatePosition(self, row=1, col='A'):
        self.templateCode = [col, row]
        try:
            colInd = self.templateCols.index(col)
            rowInd = self.templateRows.index(row)
        except ValueError as ve:
            print(ve)
            return -1
        self.templateCoordinates = [rowInd, colInd]
        indexCoords = np.array([colInd, rowInd, 1])
        tempCoords = self.template_index2location.dot(indexCoords)
        self.template_X = tempCoords[0]
        self.template_Y = tempCoords[1]

    def getPointCoordinate(self):
        return self.templateCoordinates

    def getPointList(self):
        if self.measurements is None:
            self.addMeasurements(np.array([[self.template_X,
                                            self.template_Y,
                                            4.0]]))
        return self.measurement.tolist()

    def getVirtualPoints(self):
        x_0 = self.template_X
        y_0 = self.template_Y
        return np.array([[x_0, y_0, 4.0],
                         [x_0, y_0, -117.5],
                         [x_0, y_0, -131.0],
                         [x_0, y_0, -236.0]])

    def getVirtualInterpolatedPoints(self, spacing):
        if self.measurements is None:
            self.addMeasurements(np.array([[self.template_X,
                                            self.template_Y,
                                            4.0]]))
        pts = self.getVirtualPoints()
        return interpolateMeasurements(pts, spacing)

    def getInterpolatedPoints(self, spacing):
        if self.measurements is None:
            self.addMeasurements(np.array([[self.template_X,
                                            self.template_Y,
                                            4.0]]))
        pts = interpolateMeasurements(self.measurement, spacing)
        return pts


def getFreeLength(measurement):
    length = calculateLength(measurement)
    freeLength = 240 - length
    return freeLength


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

            startingPt = point + 6 * unitVects[ind]
            remainder = 0

        elif ind == (len(pointlist) - 1):
            if remainder > 0:
                lastPt = interpolated_points[-1] + spacing * unitVects[-1]
                interpolated_points.append(lastPt)

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


def calculateTemplateTransform(indCoord1=np.array([0, 4]),
                               indCoord2=np.array([12, 12]),
                               location1=np.array([34.329114, 28.75]),
                               location2=np.array([94.329114, 68.75])):

    scale = (location2 - location1) / (indCoord2 - indCoord1)
    scaleMat = np.array([[scale[0], 0],
                         [0, scale[1]]])
    translation = location1 - scaleMat.dot(indCoord1)
    T = np.eye(3)
    T[0, 2] = translation[0]
    T[1, 2] = translation[1]
    T[0:2, 0:2] = scaleMat

    return T


if __name__ == "__main__":
    pass
