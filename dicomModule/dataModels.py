#

# Build-in Modules
import os
import time
from copy import deepcopy
from multiprocessing.pool import ThreadPool
# import sys
# import itertools

# Third-party Modules
import numpy as np

try:
    import dicom as pydicom
except:
    import pydicom as pydicom


class DicomDataModel(object):
    """
        An interface for Dicom Image Stacks (with or without contours)
        requires: a directory (with directories for images and contours)
        The instantiated object organizes the contents of the directory,
        and provides a useful interface to the data within the image volume
    """

    def __init__(self, diDir=None):
        # FILE IO STUFF
        if diDir is None:
            return None

        imDir, imFileList, contDir, contFile = organizeDirectory(diDir)
        self.dicomDir = diDir
        self.imFileList = imFileList
        self.contFile = contFile

        print("Images at: %s" % imDir)
        print("Contours at: %s" % contFile)

        # VOLUME INITIALIZATION
        self.staticProperties = getStaticDicomSizeProps(imFileList[0])
        self.setVaryingDicomSizeProps(imFileList)
        sliceLimits = [min(self.sliceLocationList),
                       max(self.sliceLocationList)]
        self.sliceLimits = [float(x) for x in sliceLimits]

        # self.PP2IMTransformation = self.write_T_Patient2Pixels(self.UID_zero)
        # self.IM2PPTransformation = self.write_T_Pixels2Patient(self.UID_zero)

        # CONTOUR INITIALIZATION
        self.contourObjs = contourDCM2Dict(RTSTFilePath=contFile)
        self.prostateLimits = getProstateLimits(contourDict=self.contourObjs,
                                                uid2loc=self.UID2Loc)

    def getPixelData(self):
        """  """
        pixelData = np.zeros([self.staticProperties['Rows'],
                              self.staticProperties['Cols'],
                              self.NSlices])
        # for ind, sliceLoc in enumerate(self.sliceLocationList):
        #     index = UnsortedSliceLoc2Ind[sliceLoc]
        for uid in self.dataDict:
            ind = self.UID2Ind[uid]
            pixelData[:, :, ind] = self.dataDict[uid]['PixelData']

        return pixelData

    def setVaryingDicomSizeProps(self, imFileList=[]):
        # set the DICOM properties that vary for each file
        sp = self.staticProperties
        self.dataDict = {}

        self.UID2Loc = {}  # check
        self.Loc2UID = {}  # check
        self.UID2Ind = {}
        self.Ind2UID = {}
        self.Loc2Ind = {}  # check
        self.Ind2Loc = {}  # check

        tempIndList = []
        tempLocList = []

        NSlices = self.NSlices = len(imFileList)
        print("N:", NSlices)
        pool = ThreadPool(NSlices)
        results = pool.map(func=getDicomFileData, iterable=imFileList)

        for ind, entry in enumerate(results):  # each dicom's data

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
        self.staticProperties['SliceSpacing'] = end - start
        print(self.staticProperties['SliceSpacing'])
        self.UID_zero = UID_zero = self.Ind2UID[0]

        ipp0 = self.dataDict[UID_zero]['ImagePositionPatient']

        # Pixel Space - Patient Space transformations
        for uid in self.dataDict:

            tpix2pat = getTPix2Pat(sp['PixelSpacing'],
                                   sp['SliceSpacing'],
                                   sp['ImageOrientationPatient'],
                                   self.dataDict[uid]['ImagePositionPatient'],
                                   ipp0)

            tpat2pix = getTPat2Pix(sp['PixelSpacing'],
                                   sp['SliceSpacing'],
                                   sp['ImageOrientationPatient'],
                                   self.dataDict[uid]['ImagePositionPatient'],
                                   ipp0)

            self.dataDict[uid]['TPix2Pat'] = tpix2pat
            self.dataDict[uid]['TPat2Pix'] = tpat2pix


def FormatForDicom(contourData):
    flatData = contourData.flatten()
    stringData = [str(item) for item in flatData]
    return stringData


def organizeDirectory(directory):
    # Sift through directory to get list of files, return: imFile contFile
    # Expecting to see two dirs: one for Images, one for Contours

    print("\n~~ Organizing ~~\n")

    tt0 = time.time()
    contFile = None
    imFileList = []
    contDir = directory
    imDir = directory
    count = 0

    for root, dirs, files in os.walk(directory):

        root = root

        for thisDir in dirs:
            if '_rtst_' in thisDir.lower():
                print('Contours directory: %s' % thisDir)
                contDir = os.path.join(root, thisDir)
            elif '_us_' in thisDir.lower() or thisDir == "US":
                print('Ultrasound directory: %s' % thisDir)
                imDir = os.path.join(root, thisDir)
            elif '_mr_' in thisDir.lower() or thisDir == "MR":
                print('MRI directory: %s' % thisDir)
                imDir = os.path.join(root, thisDir)
            else:
                print("Ignoring Unknown Directory")

        if root == imDir:
            for file in files:
                fPath = os.path.join(root, file)
                if isImageDicom(fPath):
                    imFileList.append(fPath)

        if root == contDir:
            for file in files:
                fPath = os.path.join(root, file)
                if isContourDicom(fPath):
                    contFile = fPath

    print('Found %d image files in %d s' % (len(imFileList),
                                            time.time() - tt0))
    # print("Org time: ", time.time() - tt0)

    return imDir, imFileList, contDir, contFile


def isImageDicom(filePath):
    dcm = pydicom.read_file(fp=filePath, force=True)
    if hasattr(dcm, "ImagePositionPatient"):
        return True
    else:
        return False


def isContourDicom(filePath):
    dcm = pydicom.read_file(fp=filePath, force=True)
    try:
        if dcm.Modality.lower() == "rtstruct":
            return True
        else:
            return False
    except AttributeError:
        if hasattr(dcm, "StructureSetROISequence"):
            return True
        else:
            return False


def getDicomFileData(filePath):
    di = pydicom.read_file(filePath)
    try:
        imageOrientation = getImOrientation(di)
        imPos = np.array([float(x) for x in di.ImagePositionPatient])

        #         print("overwriting patient orientation")
        #         pydicom.write_file(filePath, di)
        # except:
        #     pass

        # try:
        # sliceLoc = round(1000 * di.SliceLocation) / 1000
        # except:
        sliceLoc = float(imageOrientation.dot(imPos)[2])
        pixelData = np.asarray(di.pixel_array)

        thisDiDict = {'UID': di.SOPInstanceUID,
                      'ImagePositionPatient': imPos,
                      'ImageOrientationPatient': imageOrientation,
                      'SliceLocation': sliceLoc,
                      'PixelData': pixelData,
                      'FileName': filePath}
    except AttributeError as e:
        thisDiDict = {'ContourFile': filePath}
    return thisDiDict


def getStaticDicomSizeProps(imFile):
    # set the DICOM properties that remain constant for all image files
    di = pydicom.read_file(imFile)
    staticProps = {}
    staticProps['ImageOrientationPatient'] = getImOrientation(di)
    # print("IOP: ", staticProps['ImageOrientationPatient'])
    staticProps['Rows'] = di.Rows
    staticProps['Cols'] = di.Columns
    staticProps['PixelSpacing'] = [float(pxsp) for pxsp in di.PixelSpacing]
    try:
        staticProps['PatientPosition'] = di.PatientPosition
    except:
        staticProps['PatientPosition'] = ''
    return staticProps


def getImOrientation(di):
    # get the Volume Rotation from file (remains const)
    if isinstance(di, str):
        di = pydicom.read_file(di)
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


def getTPat2Pix(pixSpacing=[1, 1],
                sliceSpacing=1,
                ImOrPat=np.eye(3),
                ImPosPat=np.array([0, 0, 0]),
                ImPosPat0=np.array([0, 0, 0])):
    """ Transformaton of Patient Coordinate to Pixel Indices """
    # ROTATION
    temp = np.eye(4)
    temp[0:3, 0:3] = ImOrPat  # FFS
    Rotation = temp

    # TRANSLATION
    temp = np.eye(4)
    offset = ImPosPat  # - ImPosPat0
    temp[0:3, -1] = - offset[0:3]
    Translation = temp

    # SCALING
    temp = np.eye(4)
    scaleMat = np.array([[1 / pixSpacing[0], 0, 0],
                         [0, 1 / pixSpacing[1], 0],
                         [0, 0, 1 / sliceSpacing]])
    temp[0:3, 0:3] = scaleMat
    Scaling = temp

    # return Scaling.dot(Translation)
    return Scaling.dot(Rotation).dot(Translation)


def getTPix2Pat(pixSpacing=[1, 1],
                sliceSpacing=1,
                ImOrPat=np.eye(3),
                ImPosPat=np.array([0, 0, 0]),
                ImPosPat0=np.array([0, 0, 0])):
    """ Transformation of Pixel Indices to Patient Coordinates
        Inverse of Above Transformation """

    # ROTATION
    temp = np.eye(4)
    temp[0:3, 0:3] = ImOrPat.T  # FFS
    Rotation = temp

    # TRANSLATION
    temp = np.eye(4)
    offset = ImPosPat  # - ImPosPat0
    temp[0:3, -1] = offset[0:3]
    Translation = temp

    # SCALING
    temp = np.eye(4)
    scaleMat = np.array([[pixSpacing[0], 0, 0],
                         [0, pixSpacing[1], 0],
                         [0, 0, sliceSpacing]])
    temp[0:3, 0:3] = scaleMat
    Scaling = temp

    return Translation.dot(Rotation).dot(Scaling)


def getProstateLimits(contourDict, uid2loc):
    for ROI in contourDict['ROI']:
        if ROI['ROIName'].lower() == 'prostate':
            uids = ROI['ContourData'].keys()
            sliceLocs = [uid2loc[uid] for uid in uids]
            sliceLims = [min(sliceLocs), max(sliceLocs)]
            return sliceLims
        else:
            return [None, None]


# Make a Dict
def contourDCM2Dict(RTSTFilePath=''):
    """ Go from RtSt DCM Contour File to a usable Dictionary """
    try:
        di = pydicom.read_file(RTSTFilePath)
    except Exception:
        print(Exception)
        return {}

    contourDict = {'Filename': RTSTFilePath,
                   'Modality': 'RTSTRUCT',
                   'ROI': []}

    # For each ROI (ie. Region-of-Interest) in this Structure Set
    for ind, thisROI in enumerate(di.ROIContourSequence):

        # Populate ROI-Level Properties
        ROIDict = {'ROIName': di.StructureSetROISequence[ind].ROIName,
                   'ROINum': di.StructureSetROISequence[ind].ROINumber,
                   'ROICol': thisROI.ROIDisplayColor,
                   'ContourData': {}}

        # For each ContourSequence (ie. Closed-Data-Loop) in this ROI
        for CS in thisROI.ContourSequence:
            thisUID = CS.ContourImageSequence[0].ReferencedSOPInstanceUID
            thisData = np.asarray(CS.ContourData)
            # Reshape data list to be <Nx3> matrix
            reshapedData = np.reshape(thisData, (len(thisData) / 3, 3))
            # make LAST point a repeat of FIRST point (closed loop)
            reshapedData = np.append(reshapedData, [reshapedData[0, :]], 0)

            # account for Possible Multiple Loops in same ROI in same slice:
            if thisUID not in ROIDict['ContourData']:
                ROIDict['ContourData'][thisUID] = reshapedData
                # loopDict[thisUID] = 1
            else:
                existingData = ROIDict['ContourData'][thisUID]
                existingData = np.append(existingData, reshapedData, 0)

            # print(ROIDict['ContourData'])

        contourDict['ROI'].append(ROIDict)

    return contourDict


def contourDict2DCM(contourDict, pathname):
    # DO INVERSE OF ABOVE
    # def writeToFile(self):
    #     di = pydicom.read_file(self.filePath)
    #     print("writing to file:", self.contourName)
    #     # rInd = self.ROIindex
    #     thisROI = di.ROIContourSequence[self.ROIindex]
    #     for thisContSeq in thisROI.ContourSequence:
    #         try:
    #             contNum = thisContSeq.ContourNumber
    #         except:
    #             contNum = thisContSeq.ContourImageSequence[0].ReferencedSOPInstanceUID
    #         upData = self.slice2ContCoords[self.contNum2Slice[contNum]][0]
    #         print("shape: ", upData.shape)
    #         upDataStr = FormatForDicom(upData)
    #         thisContSeq.ContourData = upDataStr
    #         npts = len(upDataStr) / 3
    #         print("N_Points: ", npts)
    #         # print(npts)
    #         thisContSeq.NumberOfContourPoints = str(int(npts))
    #         # print(str(len(upDataStr)/3))
    #         # print(contNum)
    #     pydicom.write_file(self.filePath, di)
    #     time.sleep(1)
    pass


if __name__ == "__main__":
    pathn = r"P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\2016-07__Studies (as will appear)"

    di = DicomDataModel(diDir=pathn)
    # print(di)

    uid0 = di.Ind2UID[0]

    for i in range(0, 10):
        uid = di.Ind2UID[i]
        ipp = di.dataDict[uid]['ImagePositionPatient']

        ipp_ = np.append(ipp, np.array([1]))

        out = di.dataDict[uid0]['TPat2Pix'].dot(ipp_)

        print(i, ': ', out)
