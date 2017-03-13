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
    UID2Ind = {}
    UID2IPP = {}
    Loc2UID = {}
    Loc2Ind = {}
    Ind2UID = {}
    Ind2Loc = {}


    def __init__(self, fileList):

        # must have fileList attribute
        # must all belong to same reference set
        # There are properties that describe the entire VOLUME,
        # and there are properties that describe an individual slice

        self.info = getStaticDicomSizeProps(fileList[0])
        self.NSlices = len(fileList)
        self.get_sliceVariable_Properties(fileList)
        self.data = self.get_pixel_data()

        self.info['Patient2Pixels'] = self.GetPatient2Pixels()
        self.info['Pixels2Patient'] = self.GetPixels2Patient()

    def __str__(self):
        strang = "Image Object: {} slices".format(self.NSlices)
        return strang



    def get_sliceVariable_Properties(self, imFileList):
        """ a dictionary to map UID to property dictionary"""
        # sp = self.staticProperties
        self.dataDict = {}
        tempIndList = []
        tempLocList = []
        tempPosList = []
        pool = ThreadPool(self.NSlices)
        results = pool.map(func=getDicomPixelData, iterable=imFileList)
        for ind, entry in enumerate(results):  # each dicom's data
            # imPos, pix = entry
            thisUID = entry['UID']

            self.dataDict[thisUID] = entry

            tempIndList.append(ind)
            tempLocList.append(entry['SliceLocation'])

            self.Loc2UID[entry['SliceLocation']] = thisUID
            self.UID2Loc[thisUID] = entry['SliceLocation']
            self.UID2IPP[thisUID] = entry['ImagePositionPatient']


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

    def GetPatient2Pixels(self):
        """ Transformaton of Patient Coordinate to Pixel Indices
            """
        sliceLoc0 = self.UID2IPP[self.UID_zero]

        # ROTATION
        temp = np.eye(4)
        R = self.info['ImageOrientationPatient']
        temp[0:3, 0:3] = R.T
        Rotation = temp

        # TRANSLATION
        temp = np.eye(4)
        # offset = self.sliceLoc2PositionPatient[sliceLoc0]
        offset = sliceLoc0
        temp[0:3, -1] = - offset[0:3]
        Translation = temp

        # SCALING
        scales = self.info['PixelSpacing']
        Scaling = np.array([[1 / scales[1], 0, 0, 0],
                            [0, 1 / scales[0], 0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1]])

        return Scaling.dot(Rotation).dot(Translation)

    def GetPixels2Patient(self):
        """ Transformation of Pixel Indices to Patient Coordinates """
        sliceLoc0 = self.UID2IPP[self.UID_zero]

        # ROTATION
        temp = np.eye(4)
        R = self.info['ImageOrientationPatient']
        temp[0:3, 0:3] = R
        Rotation = temp

        # TRANSLATION
        temp = np.eye(4)
        # offset = self.sliceLoc2PositionPatient[sliceLoc0]
        offset = sliceLoc0
        temp[0:3, -1] = offset[0:3]
        Translation = temp

        # SCALING
        # temp = np.eye(4)
        scales = self.info['PixelSpacing']
        Scaling = np.array([[scales[1], 0, 0, 0],
                             [0, scales[0], 0, 0],
                             [0, 0, scales[2], 0],
                             [0, 0, 0, 1]])

        return Translation.dot(Rotation).dot(Scaling)


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
