import numpy as np
from rdp import rdp  # Ramer-Douglas-Peucker algorithm
import uuid

templateCols = ['A', 'a', 'B', 'b',
                'C', 'c', 'D', 'd',
                'E', 'e', 'F', 'f', 'G']
templateRows = [7, 6.5, 6, 5.5,
                5, 4.5, 4, 3.5,
                3, 2.5, 2, 1.5, 1]


class CatheterObj(object):
    """ Container for CATHETER data. Has a BUFFER for measurements,
        can filter and simplify these points. Has a unique location ID
        for keeping track of self in template.

        <raw_measurements> holds all measurements directly from system
        < >
    """

    def __init__(self, rowNumber, colLetter,
                 coords=(None, None),
                 parent=None,
                 catheterLength=240.00):
        super().__init__()

        self.editable = True
        self.template_X = None
        self.template_Y = None
        self.templateCode = [None, None]
        self.templateCoordinates = coords
        self.uid = uuid.uuid4()
        self.plottable = {}
        self.Color = (255, 0, 255)
        self.linewidth = 4
        self.CatheterNumber = None
        self.raw_measurements = []
        self.interp_measurements = []
        self.template_index2location = calculateTemplateTransform()
        self.setTemplatePosition_byCode(row=rowNumber, col=colLetter)
        # self.setTemplateCoords(coords)
        # self.patient_Transform = np.eye(4)
        # self.setParent(parent)

    def __str__(self):
        string = "Catheter Object at {}".format(self.getTemplateCoordinates())
        return string

    def has_data(self):
        """ returns BOOL for whether data exists here """
        return bool(self.raw_measurements)

    def has_template_spot(self):
        """ returns BOOL for whether cath has been assigned a template loc """
        templateBool = False if self.template_X is None else True
        return templateBool

    def getTemplateAlphanumeric(self):
        """ returns alpha-numeric string indicating template position """
        if self.has_template_spot():
            return "{}{}".format(*self.templateCode)
        else:
            return "<Template Location Unassigned>"

    def get_N_raw_pts(self):
        """ how many unfiltered points did this catheter collect """
        return len(self.raw_measurements)

    def get_raw_data(self):
        """ """
        return np.asarray(self.raw_measurements)

    def is_editable(self):
        """ BOOL for if we can add more points """
        return self.editable

    def add_raw_measurement(self, measurement):
        """ Add unfiltered Probe-Tip measurements to BUFFER
            Probe Tip Measurement is expected to be a (Nx3) NUMPY array. """
        if not self.is_editable():
            print("this catheter can no longer accept new measurements")
            return False

        if measurement.ndim == 1:
            self.raw_measurements.append(measurement)
        elif measurement.ndim == 2:
            for pt in measurement:
                self.raw_measurements.append(pt)
        return True

    def setTemplatePosition_byCode(self, row=1, col='A'):
        """ TRANSLATE ALPHA-NUMERIC TEMPLATE CODE INTO ARRAY COORDINATES """
        self.templateCode = [col, row]

        try:
            colInd = templateCols.index(col)
            rowInd = templateRows.index(row)
        except ValueError as ve:
            print(ve)
            return -1
        self.setTemplateCoords((rowInd, colInd))

    def setCatheterNumber(self, number):
        if type(number) is not int:
            raise TypeError
        else:
            self.CatheterNumber = number

    # def setParent(self, parent):
    #     self.parent = parent
    #     if parent is None:
    #         return
    #     self.patient_Transform = parent.patient.Image.info['Pix2Pat']

    # def addDescribingPoint(self, pointCoordinates):
    #     """ If this """
    #     if not self.editable:
    #         print("this Catheter can no longer be edited")
    #         return

    #     if pointCoordinates.ndim == 1:
    #         self.measurements.append(pointCoordinates)
    #     elif pointCoordinates.ndim == 2:
    #         for

    def getLength(self):
        return

    def setTemplateCoords(self, coords):
        self.templateCoordinates = coords
        indexCoords = np.array([coords[0], coords[1], 1])
        tempCoords = self.template_index2location.dot(indexCoords)
        self.template_X = tempCoords[0]
        self.template_Y = tempCoords[1]

    def finishMeasuring(self, compress=True):
        """ Closes Catheter to prevent adding any more points
            IF compress is TRUE, use RDP to simplify point line.
        """
        # let measurements *just* be all points north of the template
        # we then add our corresponding template points, and our free end

        if not self.has_data():
            return False

        # if not self.has_patient():
            # return False

        if compress is True:
            self.describingPoints = rdp(self.get_raw_data(),
                                        epsilon=2.0)
        else:
            self.describingPoints = self.get_raw_data()


        # self.interp_measurements = interpolateMeasurements(self.describing)

        self.editable = False
        return True


    def to_virtual_catheter(self):
        """ return ND array for VirtualCatheter points
            VCs consist of 4 CDPs (tip + the 3 special CDPs) and are
            always straight
        """

        x_0 = self.template_X
        y_0 = self.template_Y
        return np.array([[x_0, y_0, 4.0],
                         [x_0, y_0, -117.5],
                         [x_0, y_0, -131.0],
                         [x_0, y_0, -236.0]])


        # if not self.is_editable():
        #     print("this Catheter is already finished")
        #     return

        # if compress is True:
        #     self.simplifyPoints(epsilon=2.0)

        # self.interp_measurements = interpolateMeasurements(self.measurements,
        #                                                    1)

        # tx = self.template_X
        # ty = self.template_Y
        # templatePoints = np.array([[tx, ty, -117.75],
        #                            [tx, ty, -131.00]])

        # patientCoordinates = self.toPatientCoordinates(self.measurements)
        # alt_pat_coords = self.alt_toPatientCoordinates(self.measurements)
        # final_measurements = np.vstack((patientCoordinates, templatePoints))
        # self.length = calculateLength(final_measurements)
        # self.depth = final_measurements[0, 2]
        # freeLength = getFreeLength(final_measurements)
        # freePosn = final_measurements[-1, 2] - freeLength
        # lastPt = np.array([[tx, ty, freePosn]])
        # final_measurements = np.vstack((final_measurements, lastPt))

        # print("New Catheter at {}: \nL = {}".format(self.label, self.length))

        # self.editable = False
        # print('final_measurements \n', final_measurements)
        # print('alt meas:\n', alt_pat_coords)


    def toPatientCoordinates(self, PixCoords):
        rows, cols = PixCoords.shape
        tempMeas = np.hstack((PixCoords, np.ones((rows, 1))))
        return self.patient_Transform.dot(tempMeas.T).T[:, 0:3]

    def alt_toPatientCoordinates(self, PixCoords):
        rows, cols = PixCoords.shape
        tempMeas = np.hstack((PixCoords, np.ones((rows, 1))))
        altMeas = self.patient_Transform.dot(tempMeas.T).T[:, 0:3]
        return altMeas


    def getPointCoordinate(self):
        """ """
        return self.templateCoordinates

    def getPointList(self):
        """ """
        if self.measurements is None:
            self.addMeasurements(np.array([[self.template_X,
                                            self.template_Y,
                                            4.0]]))
        return self.measurements.tolist()

    def getVirtualPoints(self):
        """ """


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
        pts = interpolateMeasurements(self.measurements, spacing)
        return pts

    def makePlottable(self):
        pen = pg.mkPen(color=self.Color, width=self.linewidth)

        axial = pg.PlotDataItem([], [],
                                antialias=True,
                                pen=None,
                                symbol='o',
                                symbolBrush=pg.mkBrush(color=(255, 255, 255)),
                                symbolSize=15,
                                symbolPen=pen)
        axial.setZValue(3)

        saggi = pg.PlotDataItem([], [],
                                antialias=True,
                                pen=pg.mkPen(color=(255, 255, 255),
                                             width=3),
                                shadowPen=pg.mkPen(color=self.Color,
                                                   width=7),
                                connect='finite',
                                symbol=None)

        self.plottable['axial'] = axial
        self.plottable['saggital'] = saggi

    def updatePlottable(self, view, currentPosn):
        if 'axial' in view:
            nearPt = self.getNearestPoint(currentPosn, idx=2)
            if nearPt.size > 0:
                self.plottable[view].setData(x=[nearPt[0], ],
                                             y=[nearPt[1], ])
            else:
                self.plottable[view].setData(x=[], y=[])
            return
        elif 'saggital' in view:
            nearestSegments = self.getNearestSegment(currentPosn)
            self.plottable[view].setData(x=nearestSegments[:, 2],
                                         y=nearestSegments[:, 1])

    def getNearestPoint(self, posn, idx=2):
        measArray = np.asarray(self.interp_measurements)

        # if its an exact match:
        if posn[idx] in measArray[:, idx]:
            outIdx = np.where(measArray[:, idx] == posn[idx])[0][0]
            return measArray[outIdx, :]

        # SORT by idx-th column
        measArray = measArray[measArray[:, idx].argsort()]
        pos = measArray[(measArray[:, idx] - posn[idx]) >= 0, :]
        neg = measArray[(measArray[:, idx] - posn[idx]) < 0, :]

        # If we are past the boundaries
        if neg.size == 0:  # NO POINTS MORE NEGATIVE THAN MINE, empty
            return np.array([])
        elif pos.size == 0:  # NO POINTS MORE POSITIVE THAN MIND, empty
            return np.array([])

        # do linear interpolation:
        bound1 = neg[-1, :]
        bound2 = pos[0, :]
        R = (bound2[idx] - posn[idx]) / (bound2[idx] - bound1[idx])
        nearestPt = bound2 + R * (bound1 - bound2)

        return nearestPt

    def getNearestSegment(self, posn, bandwidth=20, idx=0):
        # COULD ADD INTERPOLATION TYPE THING HERE

        measArray = np.asarray(self.interp_measurements)
        thresh = (posn[idx] - bandwidth / 2, posn[idx] + bandwidth / 2)

        colVect = measArray[:, idx]
        GT = colVect > thresh[0]
        LT = colVect < thresh[1]
        inRange = -(LT - GT)
        outRange = -inRange

        relevantData = measArray.copy().astype(np.float)

        nanshape = relevantData[outRange, :].shape
        nanarray = np.empty(nanshape)
        nanarray[:] = np.NAN

        relevantData[outRange, :] = nanarray

        return relevantData


def interpolatrix(point1, point2, value, idx):
    """ find 3d point (with idx entry Value) between point1 and point2 """
    P1P2 = point1 - point2
    V = (value - point1[idx]) / P1P2[idx]

    if np.isnan(V) or np.isinf(V):
        print("UNINTERPOLABLE")
        return (point1 + point2) / 2

    return point1 + V * P1P2


def newHoverEvent(event, accept):
    print('WOW HOVER')


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


def calculateTemplateTransform(indCoord1=np.array([0, 0]),
                               indCoord2=np.array([12, 12]),
                               location1=np.array([34.329114, 8.75]),
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

    # a = np.array([-1, 0, 0])
    # b = np.array([1, 1, 1])
    # value = 0.25
    # idx = 1
    # out = interpolatrix(a, b, value, idx)
    # print('out', out)

    cath = CatheterObj(rowNumber=4, colLetter='D')
    print(cath.to_virtual_catheter())

    # aa = CatheterObj(rowNumber=1, colLetter='b')

    # aa.addDescribingPoint([0, 0, 0])
    # aa.addDescribingPoint([-1, 0, -1])
    # aa.addDescribingPoint([-2, 1, -2])
    # aa.addDescribingPoint([-3, 2, -3])
    # aa.addDescribingPoint([-4, 3, -4])
    # aa.addDescribingPoint([-5, 4, -5])
    # aa.addDescribingPoint([-4, 4, -6])
    # aa.addDescribingPoint([-3, 4, -7])
    # aa.addDescribingPoint([-2, 4, -8])
    # aa.addDescribingPoint([-1, 4, -9])
    # aa.addDescribingPoint([-0, 4, -10])
    # aa.addDescribingPoint([1, 4, -11])

    # # bb = aa.getNearestPoint([0, 0, 1.75], idx=2)
    # aa.finishMeasuring()

    # cc = aa.getNearestSegment([-2, 0, 1], idx=0, bandwidth=3)
    # print('thresh', cc)
    # del aa
    # print("my returned point {}".format(bb))
