#

# Build-in Modules
import os
import time
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
        self.imDir = imDir
        self.imFileList = imFileList
        self.contDir = contDir
        self.contFile = contFile

        # VOLUME INITIALIZATION
        self.staticProperties = getStaticDicomSizeProps(imFileList[0])
        self.setVaryingDicomSizeProps(imFileList)
        sliceLimits = [min(self.sliceLocationList),
                       max(self.sliceLocationList)]
        self.sliceLimits = [float(x) for x in sliceLimits]
        self.PP2IMTransformation = self.write_T_Patient2Pixels()
        self.IM2PPTransformation = self.write_T_Pixels2Patient()

        # CONTOUR INITIALIZATION
        if contFile is not None:
            self.contourObjs = self.getContours(self.contFile)
            self.prostateLimits = getProstateLimits(self.contourObjs)
        else:
            self.contourObjs = []

    def setVaryingDicomSizeProps(self, imFileList):
        # set the DICOM properties that vary for each file
        self.NSlices = len(imFileList)
        sliceIndList = []
        TempSliceLocationList = []
        self.sliceLocationList = []
        self.sliceLoc2PositionPatient = dict()
        self.UIDsliceLocDict = dict()
        self.UIDFileNameDict = dict()
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
            self.UIDsliceLocDict[entry['UID']] = entry['SliceLocation']
            self.UIDFileNameDict[entry['UID']] = entry['FileName']
            TempSliceLocationList.append(entry['SliceLocation'])
            sliceIndList.append(ind)
            TempPixelData[:, :, ind] = np.asarray(entry['PixelData'])

        UnsortedSliceLoc2Ind = dict(zip(TempSliceLocationList, sliceIndList))
        self.sliceLocationList = sorted(TempSliceLocationList)
        self.sliceLoc2Ind = dict(zip(self.sliceLocationList, sliceIndList))
        self.sliceInd2Loc = dict(zip(sliceIndList, self.sliceLocationList))

        for ind, sliceLoc in enumerate(self.sliceLocationList):
            index = UnsortedSliceLoc2Ind[sliceLoc]
            self.pixelData[:, :, ind] = TempPixelData[:, :, index]

        # PUT IN DICOM FILE
    def write_T_Patient2Pixels(self):
        """ Transformaton of Patient Coordinate to Pixel Indices
            """
        sliceLoc0 = self.sliceInd2Loc[0]

        # ROTATION
        temp = np.eye(4)
        R = self.staticProperties['ImageOrientationPatient']
        temp[0:3, 0:3] = R.T
        Rotation = temp

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
                             [0, 0, 1]])
        temp[0:3, 0:3] = scaleMat
        Scaling = temp

        return Scaling.dot(Rotation).dot(Translation)

    def write_T_Pixels2Patient(self):
        """ Transformation of Pixel Indices to Patient Coordinates
            Inverse of Above Transformation """
        sliceLoc0 = self.sliceInd2Loc[0]

        # ROTATION
        temp = np.eye(4)
        R = self.staticProperties['ImageOrientationPatient']
        temp[0:3, 0:3] = R
        Rotation = temp

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
                             [0, 0, 1]])
        temp[0:3, 0:3] = scaleMat
        Scaling = temp
        # return Scaling.dot(Rotation).dot(Translation)
        return Translation.dot(Rotation).dot(Scaling)

    def getContours(self, contFile):
        """ One Contour Object for each ROI in the structure set """
        contourObjs = {}
        di = pydicom.read_file(fp=contFile, force=True)
        contourNames = di.StructureSetROISequence
        uidSLD = self.UIDsliceLocDict
        R = self.staticProperties['ImageOrientationPatient']
        colz = {'prostate': 'g',
                'urethra': 'y',
                'rectum': 'w',
                'boost_expanded': np.array([255, 128, 0]),
                'boost': np.array([255, 64, 0]),
                'dil': np.array([255, 64, 0])}

        for ind, thisROI in enumerate(di.ROIContourSequence):
            thisName = contourNames[ind].ROIName

            # scan through colors to match with anatomical part
            thisCol = 'w'
            for anatomy in colz.keys():
                if anatomy == thisName.lower():
                    thisCol = colz[anatomy]
                    break

            try:
                contourObjs[thisName] = contourObj(thisROI=thisROI,
                                                   R=R,
                                                   filePath=contFile,
                                                   name=thisName,
                                                   ROIindex=ind,
                                                   colz=thisCol,
                                                   UID_SLD=uidSLD)
            except AttributeError as aterr:
                print("No contour data in %s" % thisName)
                print(aterr)

        return contourObjs


class contourObj(object):
    """ for each ROI, make one of these """

    def __init__(self,
                 thisROI,
                 R=np.eye(3),
                 filePath='.',
                 name='',
                 ROIindex=0,
                 colz='w',
                 UID_SLD={}):

        self.wasModified = False
        self.slice2ContCoords = dict()
        self.contNum2Slice = dict()

        self.contourName = name
        # self.colz = colz
        self.filePath = filePath
        self.ROIindex = ROIindex
        self.NLoops = 1

        self.colz = [int(x) for x in thisROI.ROIDisplayColor]

        # Make sure contour not empty.
        if not hasattr(thisROI, 'ContourSequence'):
            print("No Contours in %s" % name)
            raise AttributeError

        # print("%s is ROI number: " % name, ROIindex)

        numberOfLoops = dict()
        # READ THROUGH DICOM FILE ROI, GET SLICES AND CONTOUR DATA
        for sliceInd, thisSlice in enumerate(thisROI.ContourSequence):
            # GET CONTOUR COORDINATE LIST, RESHAPE TO <M/3 by 3>
            thisData = np.asarray(thisSlice.ContourData)
            howMany = len(thisData)
            TransformedConDat = np.reshape(thisData, (howMany / 3, 3))

            try:
                contourNumber = thisSlice.ContourNumber
            except AttributeError as e:
                # print(e)
                contourNumber = thisSlice.ContourImageSequence[0].ReferencedSOPInstanceUID

            try:
                cis = thisSlice.ContourImageSequence[0]
                SOP_UID = cis.ReferencedSOPInstanceUID
                sliceLoc = UID_SLD[SOP_UID]  # from id to slice location
            except:
                sliceLoc = thisData[2]

            sliceLoc = round(sliceLoc * 1000) / 1000
            # print("Your SliceLoc is: ", sliceLoc)
            # IF ALREADY AN ENTRY THERE, APPEND ANOTHER:
            numberOfLoops[sliceLoc] = 1
            if sliceLoc in self.slice2ContCoords.keys():
                numberOfLoops[sliceLoc] += 1
                self.slice2ContCoords[sliceLoc].append(TransformedConDat)
                self.contNum2Slice[contourNumber].append(sliceLoc)
            else:
                self.slice2ContCoords[sliceLoc] = [TransformedConDat]
                self.contNum2Slice[contourNumber] = [sliceLoc]

        # PAD SLICE LISTS WITH EMPTIES SO ALL WITH SAME AMOUNT OF DATA
        maxLoops = max(numberOfLoops.values())
        self.NLoops = maxLoops
        for sliceLoc in self.slice2ContCoords:
            if numberOfLoops[sliceLoc] < maxLoops:
                diff = maxLoops - numberOfLoops[sliceLoc]
                for i in range(diff):
                    self.slice2ContCoords[sliceLoc].append(np.array([[],
                                                                     [],
                                                                     []]))

    def writeToFile(self):
        di = pydicom.read_file(self.filePath)
        print("writing to file:", self.contourName)
        # rInd = self.ROIindex
        thisROI = di.ROIContourSequence[self.ROIindex]
        for thisContSeq in thisROI.ContourSequence:
            try:
                contNum = thisContSeq.ContourNumber
            except:
                contNum = thisContSeq.ContourImageSequence[0].ReferencedSOPInstanceUID

            upData = self.slice2ContCoords[self.contNum2Slice[contNum][0]][0]
            print("shape: ", upData.shape)
            upDataStr = FormatForDicom(upData)
            thisContSeq.ContourData = upDataStr
            npts = len(upDataStr) / 3
            print("N_Points: ", npts)
            # print(npts)
            thisContSeq.NumberOfContourPoints = str(int(npts))
            # print(str(len(upDataStr)/3))
            # print(contNum)

            # print("contour number:", contourNumber)
        # for contour in di.ROIContourSequence[self.ROIindex].ContourSequence:
        #     if len(contour.ContourData) > 100:
        #         print(contour.ContourData)

        pydicom.write_file(self.filePath, di)
        time.sleep(1)


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
    if hasattr(dcm, "StructureSetROISequence"):
        return True
    else:
        return False


def getDicomFileData(filePath):
    di = pydicom.read_file(filePath)
    try:
        imageOrientation = getImOrientation(di)
        imPos = np.array([float(x) for x in di.ImagePositionPatient])
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
    staticProps['Rows'] = di.Rows
    staticProps['Cols'] = di.Columns
    staticProps['PixelSpacing'] = [float(pxsp) for pxsp in di.PixelSpacing]
    return staticProps


def getImOrientation(di):
    # get the Volume Rotation from file (remains const)
    if isinstance(di, str):
        di = pydicom.read_file(di)
    imOr = di.ImageOrientationPatient  # Field exists in both US and MR
    v1Str = imOr[0:3]
    v2Str = imOr[3:]
    V1 = np.array([float(x) for x in v1Str])
    V1 = V1 / np.linalg.norm(V1)
    V2 = np.array([float(x) for x in v2Str])
    V2 = V2 / np.linalg.norm(V2)
    V3 = np.cross(V1, V2)
    R = np.array([V1, V2, V3])
    return R  # a 3x3 Rotation matrix


def getProstateLimits(contourDict):
    for contour in contourDict.values():
        if contour.contourName.lower() == 'prostate':
            sliceLocs = [float(x) for x in contour.slice2ContCoords.keys()]
            sliceLocs.sort()
            sliceLims = [min(sliceLocs), max(sliceLocs)]
            return sliceLims
        else:
            return [None, None]


if __name__ == "__main__":
    pass

    myPath = r"P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\2016-07__Studies (as will appear)"
    dcm = DicomDataModel(diDir=myPath)

    # myPoint = np.array([1, 2, 3, 1])
    # myPt2 = dcm.PP2IMTransformation.dot(myPoint)
    # myPt3 = dcm.IM2PPTransformation.dot(myPt2)

    # slks = list(dcm.contourObjs['prostate'].slice2ContCoords.keys())
    # contData = dcm.contourObjs['prostate'].slice2ContCoords[slks[0]][0]
    # stringOut = FormatForDicom(contData)
    # print(stringOut)
