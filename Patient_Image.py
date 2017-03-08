# Patient_Image.py

import numpy as np
import os

from copy import deepcopy
from multiprocessing.pool import ThreadPool
# import

try:
    import dicom as dicom
except:
    import pydicom as dicom


class Patient_Image(object):
    """
    """

    info = {}
    UID2Loc = {}
    Loc2UID = {}
    UID2Ind = {}
    Ind2UID = {}
    Loc2Ind = {}
    Ind2Loc = {}

    def __init__(self, fileList):

        # must have fileList attribute
        # must all belong to same reference set
        # There are properties that describe the entire VOLUME,
        # and there are properties that describe an individual slice

        # self.
        self.info = getStaticDicomSizeProps(fileList[0])
        self.NSlices = len(fileList)
        self.get_sliceVariable_Properties(fileList)
        self.data = self.get_pixel_data()
        print(self.data.shape)

    def get_sliceVariable_Properties(self, imFileList):
        """ a dictionary to map UID to property dictionary"""
        # sp = self.staticProperties
        self.dataDict = {}
        tempIndList = []
        tempLocList = []
        pool = ThreadPool(self.NSlices)
        results = pool.map(func=getDicomPixelData, iterable=imFileList)
        for ind, entry in enumerate(results):  # each dicom's data
            # imPos, pix = entry
            UID = entry['UID']
            self.dataDict[UID] = entry
            tempLocList.append(entry['SliceLocation'])
            tempIndList.append(ind)
            self.Loc2UID[entry['SliceLocation']] = entry['UID']
            self.UID2Loc[entry['UID']] = entry['SliceLocation']

        # UnsortedSliceLoc2Ind = dict(zip(tempLocList, tempIndList))
        self.sliceLocationList = sorted(tempLocList)
        self.Loc2Ind = dict(zip(self.sliceLocationList, tempIndList))
        self.Ind2Loc = dict(zip(tempIndList, self.sliceLocationList))
        self.UID2Ind = deepcopy(self.UID2Loc)
        for UID in self.UID2Ind:
            thisInd = self.Loc2Ind[self.UID2Loc[UID]]
            self.UID2Ind[UID] = thisInd
            self.Ind2UID[thisInd] = UID
        start = self.sliceLocationList[0]
        end = self.sliceLocationList[1]
        self.info['SliceSpacing'] = end - start
        self.UID_zero = self.Ind2UID[0]
        # ippo = self.dataDict[UID_zero]['ImagePositionPatient']

    def get_pixel_data(self):
        pixelData = np.zeros([self.info['Rows'],
                              self.info['Cols'],
                              self.NSlices], dtype=np.uint16)
        for uid in self.dataDict:
            ind = self.UID2Ind[uid]
            pixelData[:, :, ind] = self.dataDict[uid]['PixelData']
        return pixelData


def getStaticDicomSizeProps(imFile):
    # set the DICOM properties that remain constant for all image files
    di = dicom.read_file(imFile)
    staticProps = {}
    staticProps['ImageOrientationPatient'] = getImOrientationMatrix(di)
    # print("IOP: ", staticProps['ImageOrientationPatient'])
    staticProps['Rows'] = di.Rows
    staticProps['Cols'] = di.Columns
    staticProps['PixelSpacing'] = [float(pxsp) for pxsp in di.PixelSpacing]
    try:
        staticProps['PatientPosition'] = di.PatientPosition
    except:
        staticProps['PatientPosition'] = ''
    return staticProps


def getDicomPixelData(filePath):
    di = dicom.read_file(filePath)
    imageOrientation = getImOrientationMatrix(di)
    imPos = np.array([float(x) for x in di.ImagePositionPatient])
    sliceLoc = float(imageOrientation.dot(imPos)[2])
    pixelData = np.asarray(di.pixel_array)
    thisDiDict = {'UID': di.SOPInstanceUID,
                  'ImagePositionPatient': imPos,
                  'SliceLocation': sliceLoc,
                  'PixelData': pixelData,
                  'FileName': filePath}
    return thisDiDict
    # return imPos, pixelData


def getImOrientationMatrix(di):
    # get the Volume Rotation from file (remains const)
    if isinstance(di, str):
        di = dicom.read_file(di)
    try:
        patPos = di.PatientPosition
    except AttributeError as AE:
        patPos = None
    imOr = di.ImageOrientationPatient  # Field exists in both US and MR
    v1Str = imOr[0:3]
    v2Str = imOr[3:]
    V1 = np.array([float(x) for x in v1Str])
    V1 = V1 / np.linalg.norm(V1)
    V2 = np.array([float(x) for x in v2Str])
    V2 = V2 / np.linalg.norm(V2)
    V3 = np.cross(V1, V2)
    R = np.array([V1, V2, V3])  # a 3x3 Rotation matrix
    if patPos == "FFS":
        # print("FFS")
        return R
    if patPos == "HFS":  # ims taken Backwards!
        # print("HFS")
        return R.T
    return R



if __name__ == "__main__":
    pass
