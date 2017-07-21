"""
    ROI (Region Of Interest)

"""

# Built-In Modules
import os
# import sys

# Third-Party Modules
import numpy as np
import cv2
import uuid

try:
    import dicom as dicom
except ImportError:
    import pydicom as dicom

import pyqtgraph as pg


class Patient_ROI_Obj(object):

    def __init__(self,
                 name='ROI_Name',
                 number=None,
                 color=(0, 0, 0),
                 linewidth=2,
                 frameRef_UID=None,
                 structure=None,
                 contour=None,
                 hidden=False,
                 enablePlotting=False,
                 dataVolume=np.zeros([10, 10, 10]),
                 imageInfo=None):

        self.Name = name
        self.Number = number
        self.Color = color
        self.linewidth = linewidth
        self.FrameRef_UID = frameRef_UID
        self.hidden = hidden
        self.id = uuid.uuid4()
        self.polyCompression = 0.7
        self.vector = []  # list of plottable items
        self.DataVolume = dataVolume

        if enablePlotting:
            self.makePlottable()

        self.setImageInfo(imageInfo)
        self.setData(structure, contour)

    def __str__(self):
        return "Region of Interest {}: {}".format(self.Number, self.Name)

    def setImageInfo(self, imageInfo):
        if not bool(imageInfo):
            return

        self.imageInfo = imageInfo
        self.volSize = (self.imageInfo['Cols'], self.imageInfo['Rows'],
                        self.imageInfo['NSlices'])
        self.DataVolume = np.zeros(self.volSize)

    def setData(self, structure, contour):
        if structure is not None:

            self.Name = structure.ROIName.lower()
            self.Number = int(structure.ROINumber)

            self.FrameRef_UID = structure.ReferencedFrameOfReferenceUID
            self.FrameOfReferenceUID = structure.ReferencedFrameOfReferenceUID

        if contour is not None:

            self.Color = [int(x) for x in contour.ROIDisplayColor]
            contourSequence = contour.ContourSequence
            self.nContours = len(contourSequence)

            for contour in contourSequence:
                PA = ContourData2PatientArray(contour.ContourData)
                VA = Patient2VectorArray(PA, self.imageInfo['Pat2Pix'])

                CA = [VectorArray2CVContour(VA)]
                ImSlice = CVContour2ImageArray(CA, self.volSize[1],
                                               self.volSize[0])
                ind = int(np.around(VA[2, 0]))
                self.DataVolume[:, :, ind] += ImSlice.copy()

    def makePlottable(self):
        plottable = pg.PlotDataItem(antialias=True,
                                    pen=pg.mkPen(color=self.Color,
                                                 width=self.linewidth))
        self.vector.append(plottable)
        # pass



def mkNewROIObs_dataset(ROI):
    # Create a new DataSet for the RT ROI OBSERVATIONS SEQUENCE

    ROIObsSeq = dicom.dataset.Dataset()
    ROIObsSeq.ObservationNumber = ROI.Number
    ROIObsSeq.ReferencedROINumber = ROI.Number
    ROIObsSeq.ROIObservationDescription = ROI.Name
    ROIObsSeq.RTROIInterpretedType = 'REGION_OF_INTEREST'
    ROIObsSeq.ROIInterpreter = 'admin'

    return ROIObsSeq


def mkNewContour(ContourData, contourNumber=1):

    contour = dicom.dataset.Dataset()
    contour.ContourGeometricType = 'CLOSED_PLANAR'
    contour.NumberOfContourPoints = int(len(ContourData) / 3)
    contour.ContourNumber = contourNumber
    contour.ContourData = ContourData

    return contour


def ContourData2PatientArray(contourData):
    """ Transforms data found in DICOM file into usable vector array
    input: a contour sequence right from a dicom file
    output: Numpy vector array in patient coordinates
    """
    try:
        floatArray = np.asarray([float(x) for x in contourData])
    except TypeError as te:
        print(te)
    nPts = int(len(floatArray) / 3)
    contData = np.reshape(floatArray, (3, nPts), order='F')
    ones = np.ones((1, nPts))
    patientArray = np.vstack((contData, ones))
    return patientArray


def PatientArray2ContourData(VectorArray):
    """ Turn contours from numpy array to DICOM list format (for saving!)
            Remove the bottom row of ONES (needed for transform), ...
            Save as list of strings
    input: 4xN 2-D numpy array <X..; Y..; Z..; 1..>
    output: 1-D list of strings ['x','y','z','x','y','z'...]
    """
    rows, cols = VectorArray.shape
    flatArray = VectorArray[0:3, :].flatten(order='F')
    return [str(x) for x in flatArray]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def Patient2VectorArray(PatientArray, transform):
    """ Transform contours from Patient-Space to Pixel-Space
            Rounds to nearest single-decimal place
    input: 4xN 2-D numpy array (in patient space),  4x4 linear transformation
    output: 4xN 2-D numpy array (in pixel space)
    """

    vectorArray = transform.dot(PatientArray)
    vectorArray = np.around(vectorArray, decimals=2)

    # dummy = np.ones((1, vectorArray.shape[1])) * vectorArray[2, 0]
    # same = np.allclose(vectorArray[2, :], dummy)

    # if same is not True:
        # raise Exception

    return vectorArray


def Vector2PatientArray(vectorArray, transform):
    """ Transform contours from Pixel-Space to Patient-Space
    input: 4xN 2-D numpy array (in pixel space), 4x4 linear transformation
    output: 4xN 2-D numpy array (in patient space)
    """
    patientArray = transform.dot(vectorArray)
    return patientArray

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def VectorArray2CVContour(VectorArray):
    """ """
    inputShape = VectorArray.shape
    nPts = inputShape[1]

    if inputShape[0] == 4:
        VectorArray = VectorArray[0:2, :]
    elif inputShape[0] == 3:
        VectorArray = VectorArray[0:2, :]

    FlatArray = VectorArray.flatten(order='C')
    CVContour = FlatArray.reshape((nPts, 1, 2), order='F').astype(np.int32)

    assert(type(CVContour) == np.ndarray)
    assert(CVContour.dtype == np.int32)

    return CVContour


def CVContour2VectorArray(CVContour, sliceZ):
    """ transform OpenCV contour format to regular vector format
    input: (N x 1 x 2) numpy array of Xs and Ys for OpenCV Contours
    output: transformable vector array
    """
    flatArray = CVContour.flatten(order='C')
    nPts = int(len(flatArray) / 2)
    vectArray = flatArray.reshape((2, nPts), order='F')
    ones = np.ones((1, nPts))
    paddedVectArray = np.vstack((vectArray, ones * sliceZ, ones))
    paddedVectArray = np.hstack((paddedVectArray,
                                 np.array([paddedVectArray[:, 0]]).T))
    return paddedVectArray

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def CVContour2ImageArray(CVContour, rows, cols):
    """ Transforms vector sequence to binary image
    input: List of contours points (as opencv likes them)
    output: binary image
    """

    assert(type(CVContour) == list)
    assert(type(rows) == int)
    assert(type(cols) == int)

    contourImageOut = np.zeros((rows, cols))  # , dtype=np.uint8)

    contourImageOut = cv2.drawContours(image=contourImageOut.copy(),
                                       contours=CVContour,
                                       contourIdx=-1,
                                       color=(255, 255, 255),
                                       thickness=-1,
                                       lineType=cv2.LINE_AA).astype(np.uint8)

    return contourImageOut.T


def ImageArray2CVContour(ImageArray, compression=0):
    """ Transforms binary ImageArray to list of vectors
    input: ImageArray must be a binary image/raster of the contour object
    output: vector list of contours
    """
    _imageArray = ImageArray.copy().astype(np.uint8)
    im, contours, hierarchy = cv2.findContours(_imageArray,
                                               cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)

    if not compression == 0:
        # compression = int(compression)
        for ind, contour in enumerate(contours):
            contours[ind] = cv2.approxPolyDP(contour, compression, True)

    return contours


if __name__ == "__main__":

    testList = ['1', '1', '0',
                '6', '1', '0',
                '6', '7', '0',
                '1', '7', '0']

    print('InputData\n', testList)

    TForm = np.eye(4)

    PatientArray = ContourData2PatientArray(testList)
    print('PatientArray\n', PatientArray)

    VectorArray = Patient2VectorArray(PatientArray, TForm)
    print('VectorArray\n', VectorArray)

    CVContour = [VectorArray2CVContour(VectorArray)]
    print('CVContour\n', CVContour)

    ImgArray = CVContour2ImageArray(CVContour, 10, 10)
    print('ImgArray\n', ImgArray)

    CVContour2 = ImageArray2CVContour(ImgArray)
    print('OutContour\n', CVContour2)

    VectorArray2 = CVContour2VectorArray(CVContour2[0], 0)
    print('OutVector\n', VectorArray2)

    PatientArray2 = Vector2PatientArray(VectorArray2, TForm)
    print('VectorArray2\n', PatientArray2)

    CS = PatientArray2ContourData(PatientArray2)
    print('ContourData\n', CS)

