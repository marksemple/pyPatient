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
    Properties:
        Rows, Cols, Slices
        Data (ND pixel array)
        Pixel-Spacing, Slice-Spacing
        ImageOrientationPatient
        Patient2Pixels Transform
        Pixels2Patient Transform
        UID2IPP
    """

    info = {'UID2Loc': {},
            'UID2Ind': {},
            'UID2IPP': {},
            'Loc2UID': {},
            'Loc2Ind': {},
            'Ind2UID': {},
            'Ind2Loc': {}}

    def __init__(self, fileList):

        # must have fileList attribute
        # must all belong to same reference set
        # There are properties that describe the entire VOLUME,
        # and there are properties that describe an individual slice

        # print(self.info)

        if bool(fileList):
            self.info = getStaticDicomSizeProps(fileList[0], self.info)
            self.info['NSlices'] = len(fileList)
            self.get_sliceVariable_Properties(fileList)
            self.data = self.get_pixel_data()
            self.info['Patient2Pixels'] = self.GetPatient2Pixels()
            self.info['Pixels2Patient'] = self.GetPixels2Patient()
            self.info['Pat2Pix_noRot'] = self.GetPatient2Pixels(do_rot=False)
            self.info['Pix2Pat_noRot'] = self.GetPixels2Patient(do_rot=False)

            # print('Pat2Pix', self.info['Patient2Pixels'])
            # print('Pat2Pix2', self.info['Pat2Pix_noRot'])

        # else:
        # self.createProps()

    def __str__(self):
        strang = "Image Object: {} slices".format(self.info['NSlices'])
        return strang

    # def createProps(self):
        # self.info = {Patie}

    def get_sliceVariable_Properties(self, imFileList):
        """ a dictionary to map UID to property dictionary"""
        # sp = self.staticProperties
        info = self.info
        self.dataDict = {}
        tempIndList = []
        tempLocList = []
        tempUIDList = []
        # tempPosList = []
        pool = ThreadPool(self.info['NSlices'])
        results = pool.map(func=getDicomPixelData, iterable=imFileList)

        for ind, entry in enumerate(results):  # each dicom's data
            thisUID = entry['UID']
            tempIndList.append(ind)
            tempLocList.append(entry['SliceLocation'])
            tempUIDList.append(thisUID)

            # info['Loc2UID'][entry['SliceLocation']] = thisUID
            self.dataDict[thisUID] = entry
            info['UID2Loc'][thisUID] = entry['SliceLocation']
            info['UID2IPP'][thisUID] = entry['ImagePositionPatient']

        # print(tempUIDList)

        order = [i[0] for i in sorted(enumerate(tempLocList),
                                      key=lambda x:x[1])]

        for newIndex, oldIndex in enumerate(order):
            thisUID = tempUIDList[oldIndex]
            thisLoc = int(round(tempLocList[oldIndex]))

            info['UID2Loc'][thisUID] = thisLoc
            info['UID2Ind'][thisUID] = newIndex
            info['Ind2Loc'][newIndex] = thisLoc
            info['Ind2UID'][newIndex] = thisUID
            # TRY NOT TO USE THIS ONE:
            info['Loc2UID'][thisLoc] = thisUID

        self.UID_zero = info['Ind2UID'][0]
        ipp0 = info['UID2IPP'][self.UID_zero]
        uid1 = info['Ind2UID'][1]
        ipp1 = info['UID2IPP'][uid1]
        info['SliceSpacing'] = np.linalg.norm(ipp1 - ipp0)

    def get_pixel_data(self):
        pixelData = np.zeros([self.info['Rows'],
                              self.info['Cols'],
                              self.info['NSlices']], dtype=np.uint16)
        for uid in self.dataDict:
            ind = self.info['UID2Ind'][uid]
            pixelData[:, :, ind] = self.dataDict[uid]['PixelData']
        return pixelData

    def GetPatient2Pixels(self, do_rot=True):
        """ Transformaton of Patient Coordinate to Pixel Indices
            """
        sliceLoc0 = self.info['UID2IPP'][self.UID_zero]

        # ROTATION
        temp = np.eye(4)
        R = self.info['ImageOrientationPatient']
        if not do_rot:
            R = R.T
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
                            [0, 0, 1 / self.info['SliceSpacing'], 0],
                            [0, 0, 0, 1]])

        return Scaling.dot(Rotation).dot(Translation)

    def GetPixels2Patient(self, do_rot=True):
        """ Transformation of Pixel Indices to Patient Coordinates """
        sliceLoc0 = self.info['UID2IPP'][self.UID_zero]

        # ROTATION
        # if Rotation:
        temp = np.eye(4)
        R = self.info['ImageOrientationPatient']
        if not do_rot:
            R = R.T
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
                            [0, 0, self.info['SliceSpacing'], 0],
                            [0, 0, 0, 1]])

        return Translation.dot(Rotation).dot(Scaling)

    def prettyFormatIPP(self):
        nSlices = len(self.info['Ind2UID'])
        prettyString = ''
        for i in range(0, nSlices):

            ipp = self.info['UID2IPP'][self.info['Ind2UID'][i]]

            prettyString += str(ipp) + '\n'

        print(prettyString)


def getStaticDicomSizeProps(imFile, staticProps={}):
    # set the DICOM properties that remain constant for all image files
    di = dicom.read_file(imFile)
    # staticProps = {}
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
    sliceLoc = imageOrientation.dot(imPos)[2]
    # print(sliceLoc)
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
    try:
        imOr = di.ImageOrientationPatient  # Field exists in both US and MR
    except AttributeError:
        imOr = [1, 0, 0, 0, 1, 0]
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
        return R
    return R


if __name__ == "__main__":
    pass
