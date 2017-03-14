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
        di = dicom.read_file(filepath)

        # for sequence in di.StructureSetROISequence:
        #     print("Sequence: ", sequence.ROIName)
        # print("there are:", len(di.StructureSetROISequence), " ROIs")

        for index, structure in enumerate(di.StructureSetROISequence):
            # self.Contours
            aa = self.add_ROI(structure, di.ROIContourSequence[index])
        print(aa)
        return True

    def add_ROI(self, structure, contour):
        new_ROI = {'ROINumber': int(structure.ROINumber),
                   'ROIName': structure.ROIName,
                   'FrameRef_UID': structure.ReferencedFrameOfReferenceUID,
                   'ROIColor': [int(x) for x in contour.ROIDisplayColor],
                   'UID2Data': {}}

        print("NEW ROI: {}".format(structure.ROIName))

        for contourSequence in contour.ContourSequence:
            VA = self.ContourSequence2VectorArray(contourSequence)
            print(VA)
        return VA

    def write_file(self, filepath):
        """ """
        pass


""" Helper functions to transform between contour representations """


def ContourData2PatientArray(contourData):
    """ Transforms data found in DICOM file into usable vector array
    input: a contour sequence right from a dicom file
    output: Numpy vector array in patient coordinates
    """
    floatArray = np.asarray([float(x) for x in contourData])
    nPts = int(len(floatArray) / 3)
    contData = np.reshape(floatArray, (3, nPts), order='F')
    ones = np.ones((1, nPts))

    print("cont:", contData.shape)
    print("ones:", ones.shape)

    patientArray = np.vstack((contData, ones))
    return patientArray


def PatientArray2ContourData(VectorArray):
    """ Turn contours from numpy array to DICOM list format """
    rows, cols = VectorArray.shape
    flatArray = VectorArray.flatten()
    return [str(x) for x in flatArray]


def Patient2VectorArray(PatientArray, transform):
    vectorArray = transform.dot(PatientArray)
    vectorArray = np.around(vectorArray, decimals=1)
    return vectorArray


def Vector2PatientArray(vectorArray, transform):
    patientArray = transform.dot(vectorArray)
    return patientArray


def VectorArray2CVContour(VectorArray):
    inputShape = VectorArray.shape
    nPts = inputShape[1]

    if inputShape[0] == 4:
        VectorArray = VectorArray[0:2, :]
    elif inputShape[0] == 3:
        VectorArray = VectorArray[0:2, :]

    FlatArray = VectorArray.flatten()
    CVContour = FlatArray.reshape((nPts, 1, 2), order='F')
    return CVContour


def CVContour2VectorArray(CVContour, sliceZ):
    """ transform OpenCV contour format to regular vector format
    input: (N x 1 x 2) numpy array of Xs and Ys for OpenCV Contours
    output: transformable vector array
    """
    flatArray = CVContour.flatten()
    nPts = len(flatArray) / 2
    vectArray = flatArray.reshape((2, nPts), order='F')
    ones = np.ones((1, nPts))
    paddedVectArray = np.vstack((vectArray, ones * sliceZ, ones))
    return paddedVectArray


def CVContour2ImageArray(CVContour, rows, cols):
    """ Transforms vector sequence to binary image
    input: List of contours points (as opencv likes them)
    output: binary image
    """
    contourImage = np.zeros((rows, cols), dtype=np.uint8)
    contourImage = cv2.drawContours(image=contourImage.copy(),
                                    contours=CVContour,
                                    contourIdx=-1,
                                    color=[255, 255, 255],
                                    thickness=-1,
                                    lineType=cv2.LINE_AA)
    return contourImage


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
                '6', '6', '0',
                '1', '6', '0']

    print('InputData\n', testList)

    TForm = np.eye(4)

    PatientArray = ContourData2PatientArray(testList)
    print('PatientArray\n', PatientArray)

    VectorArray = Patient2VectorArray(PatientArray, TForm)
    print('VectorArray\n', VectorArray)

    CVContour = VectorArray2CVContour(VectorArray)
    print('CVContour\n', CVContour)


    ImgArray = CVContour2ImageArray(CVContour, 10, 10)
    print('ImgArray\n', ImgArray)

    CS = PatientArray2ContourData(PatientArray)
    print('ContourData\n', CS)

    # myROI = Patient_ROI_Set(file=r'P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\2016-07__Studies (as will appear)\YU, YAN_3138146_RTst_2016-07-14_121417_mrgb1F_EMTEST_n1__00000\2.16.840.1.114362.1.6.5.4.15706.9994565197.426983378.1037.53.dcm')
