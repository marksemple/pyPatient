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

    def __init__(self, parent=None, diDir=None):
        # FILE IO STUFF
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
        self.PP2IMTransformation = self.write_T_Patient2Pixels()
        self.IM2PPTransformation = self.write_T_Pixels2Patient()

        # CONTOUR INITIALIZATION
        self.contourObjs = contourDCM2Dict(RTSTFilePath=contFile)
        self.prostateLimits = getProstateLimits(contourDict=self.contourObjs,
                                                uid2loc=self.UID2Loc)

    def setVaryingDicomSizeProps(self, imFileList):
        # set the DICOM properties that vary for each file
        self.NSlices = len(imFileList)
        sliceIndList = []
        TempSliceLocationList = []
        self.sliceLocationList = []
        self.sliceLoc2PositionPatient = dict()

        self.UID2Loc = UID2Loc = dict()
        self.UID2FileName = UID2FileName = dict()

        # slice2Pix = dict()
        TempPixelData = np.empty([self.staticProperties['Rows'],
                                  self.staticProperties['Cols'],
                                  self.NSlices])
        self.pixelData = np.empty([self.staticProperties['Rows'],
                                   self.staticProperties['Cols'],
                                   self.NSlices])

        threads = len(imFileList)
        pool = ThreadPool(threads)
        results = pool.map(func=getDicomFileData, iterable=imFileList)

        for ind, entry in enumerate(results):  # each dicom's data
            self.sliceLoc2PositionPatient[
                entry['SliceLocation']] = entry['ImagePositionPatient']

            UID2Loc[entry['UID']] = entry['SliceLocation']
            UID2FileName[entry['UID']] = entry['FileName']
            TempSliceLocationList.append(entry['SliceLocation'])
            sliceIndList.append(ind)
            TempPixelData[:, :, ind] = np.asarray(entry['PixelData'])

        UnsortedSliceLoc2Ind = dict(zip(TempSliceLocationList, sliceIndList))
        self.sliceLocationList = sorted(TempSliceLocationList)
        self.sliceLoc2Ind = dict(zip(self.sliceLocationList, sliceIndList))
        self.sliceInd2Loc = dict(zip(sliceIndList, self.sliceLocationList))

        self.UID2Ind = UID2Ind = deepcopy(UID2Loc)
        for UID in UID2Ind:
            UID2Ind[UID] = self.sliceLoc2Ind[UID2Loc[UID]]

        for ind, sliceLoc in enumerate(self.sliceLocationList):
            index = UnsortedSliceLoc2Ind[sliceLoc]
            self.pixelData[:, :, ind] = TempPixelData[:, :, index]

        self.Ind2UID = {y: x for x, y in UID2Ind.items()}
        self.Loc2UID = {y: x for x, y in UID2Loc.items()}
        self.FileName2UID = {y: x for x, y in UID2FileName.items()}
        self.UID_zero = self.Ind2UID[0]

        print("Slices at: ", self.sliceLocationList)

        # PUT IN DICOM FILE
    def write_T_Patient2Pixels(self):
        """ Transformaton of Patient Coordinate to Pixel Indices
            """
        sliceLoc0 = self.sliceInd2Loc[0]
        sliceSpan = self.sliceInd2Loc[1] - self.sliceInd2Loc[0]
        # SEE IF TRUE: that we can assume to use IM Pos Pat of slice 1 only

        # ROTATION
        temp = np.eye(4)
        R = self.staticProperties['ImageOrientationPatient']
        # temp[0:3, 0:3] = R.T  # HFS
        temp[0:3, 0:3] = R  # FFS
        Rotation = temp
        # print("pat2pix R = \n", Rotation)

        # TRANSLATION
        temp = np.eye(4)
        offset = self.sliceLoc2PositionPatient[sliceLoc0]
        temp[0:3, -1] = - offset[0:3]
        Translation = temp

        # SCALING
        temp = np.eye(4)
        scales = self.staticProperties['PixelSpacing']
        scaleMat = np.array([[1 / scales[0], 0, 0],
                             [0, 1 / scales[1], 0],
                             [0, 0, 1 / sliceSpan]])
        temp[0:3, 0:3] = scaleMat
        Scaling = temp

        return Scaling.dot(Rotation).dot(Translation)

    def write_T_Pixels2Patient(self):
        """ Transformation of Pixel Indices to Patient Coordinates
            Inverse of Above Transformation """
        sliceLoc0 = self.sliceInd2Loc[0]
        sliceSpan = self.sliceInd2Loc[1] - self.sliceInd2Loc[0]

        # ROTATION
        temp = np.eye(4)
        R = self.staticProperties['ImageOrientationPatient']
        # if self.staticProperties[
        # temp[0:3, 0:3] = R  # HFS
        temp[0:3, 0:3] = R.T  # FFS
        Rotation = temp
        # Rotation = np.eye(4)
        # print("pix2pat R = \n", Rotation)

        # TRANSLATION
        temp = np.eye(4)
        offset = self.sliceLoc2PositionPatient[sliceLoc0]
        temp[0:3, -1] = offset[0:3]
        Translation = temp

        # SCALING
        temp = np.eye(4)
        scales = self.staticProperties['PixelSpacing']
        scaleMat = np.array([[scales[0], 0, 0],
                             [0, scales[1], 0],
                             [0, 0, sliceSpan]])
        temp[0:3, 0:3] = scaleMat
        Scaling = temp
        # return Scaling.dot(Rotation).dot(Translation)
        return Translation.dot(Rotation).dot(Scaling)
        # return np.eye(4)

    def getContours(self, contFile):
        pass
        """ One Contour Object for each ROI in the structure set """
        # contourObjs = {}
        # di = pydicom.read_file(fp=contFile, force=True)
        # contourNames = di.StructureSetROISequence
        # uidSLD = self.UID2LocDict
        # uidSIND = self.UID2IndDict
        # R = self.staticProperties['ImageOrientationPatient']
        # colz = {'prostate': 'g',
        #         'urethra': 'y',
        #         'rectum': 'w',
        #         'boost_expanded': np.array([255, 128, 0]),
        #         'boost': np.array([255, 64, 0]),
        #         'dil': np.array([255, 64, 0])}

        # for ind, thisROI in enumerate(di.ROIContourSequence):
        #     thisName = contourNames[ind].ROIName

        #     # scan through colors to match with anatomical part
        #     thisCol = 'w'
        #     for anatomy in colz.keys():
        #         if anatomy == thisName.lower():
        #             thisCol = colz[anatomy]
        #             break

        #     try:
        #         contourObjs[thisName] = contourObj(thisROI=thisROI,
        #                                            R=R,
        #                                            filePath=contFile,
        #                                            name=thisName,
        #                                            ROIindex=ind,
        #                                            colz=thisCol,
        #                                            UID_SLD=uidSLD,
        #                                            UID_SIND=uidSIND)
        #     except AttributeError as aterr:
        #         print("No contour data in %s" % thisName)
        #         print(aterr)

        # return contourObjs


# class contourObj(object):
#     """ for each ROI, make one of these """

#     def __init__(self,
#                  thisROI,
#                  R=np.eye(3),
#                  filePath='.',
#                  name='',
#                  ROIindex=0,
#                  colz='w',
#                  UID_SLD={},
#                  UID_SIND={}):

#         self.UID_SIND = UID_SIND
#         self.contourName = name
#         self.filePath = filePath
#         self.ROIindex = ROIindex

#         print(name, ' - ', ROIindex)

#         self.wasModified = False
#         self.slice2ContCoords = dict()
#         self.contNum2Slice = dict()
#         self.colz = [int(x) for x in thisROI.ROIDisplayColor]
#         self.NLoops = 1

#         try:
#             contourNumber = thisROI.ContourSequence[0].ReferencedROINumber
#         except AttributeError:
#             contourNumber = thisROI.ContourSequence[0].ContourImageSequence[0].ReferencedSOPInstanceUID
#         self.contourNumber = contourNumber

#         if hasattr(thisROI, 'ContourSequence'):
#             self.populateSliceDict(thisROI.ContourSequence)
#         else:
#             print("No Contours in %s" % name)
#             raise AttributeError


#     def populateSliceDict(self, cs):
#         """ Iterate through this ROI's contour sequences, put into dict """

#         # loopDict = dict()

#         # for thisSlice in cs:
#         #     # Reshape coordinates to <M/3 by 3>
#         #     thisData = np.asarray(thisSlice.ContourData)
#         #     TransformedConDat = np.reshape(thisData, (len(thisData) / 3, 3))
#         #     # replicate contour first point in last point (to close loop)
#         #     TransformedConDat = np.append(TransformedConDat,
#         #                                   [TransformedConDat[0, :]], 0)

#         #     # try:
#         #     cis = thisSlice.ContourImageSequence[0]
#         #     SOP_UID = cis.ReferencedSOPInstanceUID
#         #     sliceInd = self.UID_SIND[SOP_UID]  # from id to slice location
#         #     # except:
#         #     #     print("ERROR making CONTOUR")
#         #     #     return
#         #         # sliceLoc = thisData[2]

#         #     # Keep track of loops per slice
#         #     loopDict[sliceInd] = 1

#         #     if sliceInd in self.slice2ContCoords.keys():
#         #         loopDict[sliceInd] += 1
#         #         self.slice2ContCoords[sliceInd].append(TransformedConDat)
#         #         self.contNum2Slice[self.contourNumber].append(sliceInd)
#         #     else:
#         #         self.slice2ContCoords[sliceInd] = [TransformedConDat]
#         #         self.contNum2Slice[self.contourNumber] = [sliceInd]

#         # # PAD SLICE LISTS WITH EMPTIES SO ALL WITH SAME AMOUNT OF DATA
#         # maxLoops = max(loopDict.values())
#         # self.NLoops = maxLoops
#         # for sliceInd in self.slice2ContCoords:
#         #     if loopDict[sliceInd] < maxLoops:
#         #         diff = maxLoops - loopDict[sliceInd]
#         #         for i in range(diff):
#         #             self.slice2ContCoords[sliceInd].append(np.array([[],
#         #                                                              [],
#         #                                                              []]).T)

#         # print("NL:",  loopDict)


def FormatForDicom(contourData):
    flatData = contourData.flatten()
    stringData = [str(item) for item in flatData]
    return stringData


def organizeDirectory(directory):
    # Sift through directory to get list of files, return: imFile contFile
    # Expecting to see two dirs: one for Images, one for Contours

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

    print('Total of %d dicom image files' % len(imFileList))
    print("Org time: ", time.time() - tt0)

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

        try:
            sliceLoc = round(1000 * di.SliceLocation) / 1000
        except:
            sliceLoc = round(1000 * imageOrientation.dot(imPos[2])) / 1000
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
        return R
    if patPos == "HFS":  # ims taken Backwards!
        return R.T
    return R


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
    pathn = r"P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\2016-07__Studies (as will appear)\YU, YAN_3138146_RTst_2016-07-14_121417_mrgb1F_EMTEST_n1__00000\2.16.840.1.114362.1.6.5.4.15706.9994565197.426983378.1037.53.dcm"

    rtst = contourDCM2Dict(pathn)

    print(rtst)
