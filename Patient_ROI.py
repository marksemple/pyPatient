"""
    RegionOfInterest

"""

# Built-In Modules
import os
import sys

# Third-Party Modules
import numpy as np
import cv2

try:
    import dicom as dicom
except:
    import pydicom as dicom


class Patient_ROI_Set(object):

    Name = 'ROI'
    Color = (230, 230, 20)
    Contour_Sequences = []

    def __init__(self, file=None, dcm=None, imageInfo=None,
                 *args, **kwargs):

        self.imageInfo = imageInfo

        if file is not None:
            if self.read_file(file):
                print('got data from file!')
                return
            else:
                print("something went wrong reading file")
                return

        # how many Regions of Interest are there?
        pass

    def __str__(self):
        return "Contour Structure Set"

    def read_file(self, filepath):
        """ """
        # print(filepath)
        self.di = di = dicom.read_file(filepath)

        # for sequence in di.StructureSetROISequence:
        #     print("Sequence: ", sequence.ROIName)
        # print("there are:", len(di.StructureSetROISequence), " ROIs")

        self.ROIs = []

        for index, structure in enumerate(di.StructureSetROISequence):
            # self.Contours
            newROI = self.add_ROI(structure, di.ROIContourSequence[index])
            self.ROIs.append(newROI)

        return True

    # def getROIVolume(self, ROI, UID2Index):
        # for contourSequence in ROI:
            # for index in
        # for UID in self.
        # UID2Index[UID]
        # return ContourVolume

    def add_ROI(self, structure, contour):

        volSize = (self.imageInfo['Rows'],
                   self.imageInfo['Cols'], self.imageInfo['NSlices'])

        new_ROI = {'ROINumber': int(structure.ROINumber),
                   'ROIName': structure.ROIName,
                   'FrameRef_UID': structure.ReferencedFrameOfReferenceUID,
                   'ROIColor': [int(x) for x in contour.ROIDisplayColor],
                   'DataVolume': np.zeros(volSize)}

        for contourSequence in contour.ContourSequence:
            PA = ContourData2PatientArray(contourSequence.ContourData)
            VA = Patient2VectorArray(PA, self.imageInfo['Patient2Pixels'])
            CA = VectorArray2CVContour(VA)
            ImSlice = CVContour2ImageArray(CA, volSize[0], volSize[1])
            ind = int(VA[2, 0])
            print('index {} has {}'.format(ind, ImSlice.shape))
            new_ROI['DataVolume'][:, :, ind] = ImSlice

        print("NEW ROI: {}".format(structure.ROIName))
        return new_ROI

    def write_file(self, filepath):
        """ """
        pass

""" Helper functions to transform between contour representations """
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def ContourData2PatientArray(contourData):
    """ Transforms data found in DICOM file into usable vector array
    input: a contour sequence right from a dicom file
    output: Numpy vector array in patient coordinates
    """
    try:
        floatArray = np.asarray([float(x) for x in contourData])
    except TypeError as te:
        print(te)
        print(contourData)
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
    vectorArray = np.around(vectorArray, decimals=1)
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

    return CVContour


def CVContour2VectorArray(CVContour, sliceZ):
    """ transform OpenCV contour format to regular vector format
    input: (N x 1 x 2) numpy array of Xs and Ys for OpenCV Contours
    output: transformable vector array
    """
    flatArray = CVContour.flatten(order='F')
    nPts = int(len(flatArray) / 2)
    vectArray = flatArray.reshape((2, nPts), order='F')
    ones = np.ones((1, nPts))
    paddedVectArray = np.vstack((vectArray, ones * sliceZ, ones))
    return paddedVectArray

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def CVContour2ImageArray(CVContour, rows, cols):
    """ Transforms vector sequence to binary image
    input: List of contours points (as opencv likes them)
    output: binary image
    """
    contourImage = np.zeros((rows, cols)) #, dtype=np.uint8)

    for cont in CVContour:
    # cont = CVContour[0]
        contourImageOut = cv2.drawContours(image=contourImage.copy(),
                                           contours=[cont],
                                           contourIdx=0,
                                           color=(255, 255, 255),
                                           thickness=-1,
                                           lineType=cv2.LINE_AA).astype(np.uint8)

    print(cont)

    return contourImageOut


def ImageArray2CVContour(ImageArray, compression=None):
    """ Transforms binary ImageArray to list of vectors
    input: ImageArray must be a binary image/raster of the contour object
    output: vector list of contours
    """
    im, contours, hierarchy = cv2.findContours(ImageArray,
                                               cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)

    if type(compression) == int:
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

    # myROI = Patient_ROI_Set(file=r'P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\2016-07__Studies (as will appear)\YU, YAN_3138146_RTst_2016-07-14_121417_mrgb1F_EMTEST_n1__00000\2.16.840.1.114362.1.6.5.4.15706.9994565197.426983378.1037.53.dcm')
