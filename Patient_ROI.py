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

        for contourSequence in contour.ContourSequence:
            cis = contourSequence.ContourImageSequence[0]
            associatedImageUID = cis.ReferencedSOPInstanceUID
            contData = ContourList2Array(contourSequence.ContourData)
            new_ROI['UID2Data'][associatedImageUID] = contData

            ones = np.ones((contData.shape[0], 1))
            padded_contData = np.hstack((contData, ones))
            # contData2 = padded_contData.dot(self.imageInfo['Patient2Pixels'])
            contData2 = self.imageInfo['Patient2Pixels'].dot(padded_contData.T)
            print(contData2.astype(int))


        return new_ROI

    def write_file(self, filepath):
        """ """
        pass

    def vector2raster(self):
        """ """
        pass

    def Contours_as_Raster(self):
        pass



def ContourList2Array(strList):
    """ Turn DICOM's list of contour pts to useful numpy array """
    floatArray = np.asarray([float(x) for x in strList])
    nPts = int(len(floatArray) / 3)
    return np.reshape(floatArray, (nPts, 3))

def ContourArray2List(npArray):
    """ Turn contours from numpy array to DICOM list format """
    rows, cols = npArray.shape
    flatArray = npArray.flatten()
    return [str(x) for x in flatArray]




if __name__ == "__main__":

    testList = ['1','3','4','5','1','2', '4', '2', '7']
    print(testList)

    aa = ContourList2Array(testList)
    print(aa)

    bb = ContourArray2List(aa)
    print(bb)

    # myROI = Patient_ROI_Set(file=r'P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\2016-07__Studies (as will appear)\YU, YAN_3138146_RTst_2016-07-14_121417_mrgb1F_EMTEST_n1__00000\2.16.840.1.114362.1.6.5.4.15706.9994565197.426983378.1037.53.dcm')
