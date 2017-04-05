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
            try:
                self.read_file(file)
                # print('got data from file!')
                return
            except AttributeError as ae:
                print("something went wrong reading file: {}".format(ae))
                raise Exception

        # how many Regions of Interest are there?
        pass

    def __str__(self):
        return "Contour Structure Set"

    def read_file(self, filepath):
        """ """
        self.di = di = dicom.read_file(filepath, force=True)
        (head, self.SSFile) = os.path.split(filepath)
        self.ROIs = []
        self.ROI_byName = {}

        # print('test', len(di.ReferencedFrameOfReferenceSequence))
        # print("RT ROI OBSERVATIONS:", len(di.RTROIObservationsSequence))

        for index, contour in enumerate(di.ROIContourSequence):
            try:
                structure = di.StructureSetROISequence[index]
            except AttributeError as ae:
                structure = 0
            newROI = self.add_ROI(structure, contour)
            self.ROIs.append(newROI)
            # print(newROI['ROIName'])
            self.ROI_byName[newROI['ROIName']] = newROI
        return True

    def over_write_file(self, filepath):
        print('looking at {}'.format(filepath))
        di = dicom.read_file(filepath)

        for index, contour in enumerate(di.ROIContourSequence):

            try:
                structure = di.StructureSetROISequence[index]
                name = structure.ROIName
                if name in self.ROI_byName.keys():
                    print("Already got thid one:{}".format(name))
                else:
                    print("Make new one for :{}".format(name))
            except AttributeError as ae:
                structure = 0
            # ROI = self.ROIs[]
            # newROI = self.add_ROI(structure, contour)
            # self.ROIs.append(newROI)
            # print(newROI['ROIName'])
            # self.ROI_byName[newROI['ROIName']] = newROI
            # return True
        pass

    def writeToFile(self):
        # di = pydicom.read_file(self.filePath)
        # print("overwriting %s to file" % self.contourName)
        thisROI = di.ROIContourSequence[self.ROIindex]
        for thisContSeq in thisROI.ContourSequence:
            try:
                contNum = thisContSeq.ContourNumber
            except:
                contNum = thisContSeq.ContourImageSequence[0].ReferencedSOPInstanceUID

            upData = self.slice2ContCoords[self.contNum2Slice[contNum][0]][0]
            upDataStr = FormatForDicom(upData)
            thisContSeq.ContourData = upDataStr
            npts = len(upDataStr) / 3
            thisContSeq.NumberOfContourPoints = str(int(npts))

        pydicom.write_file(self.filePath, self.di)
        # time.sleep(0.25)

    def FormatForDicom(contourData):
        flatData = contourData.flatten()
        stringData = [str(item) for item in flatData]
        return stringData

    def add_ROI(self, structure, contour):
        volSize = (self.imageInfo['Cols'],
                   self.imageInfo['Rows'], self.imageInfo['NSlices'])
        new_ROI = {'ROINumber': int(structure.ROINumber),
                   'ROIName': structure.ROIName.lower(),
                   'FrameRef_UID': structure.ReferencedFrameOfReferenceUID,
                   'ROIColor': [int(x) for x in contour.ROIDisplayColor],
                   'DataVolume': np.zeros(volSize)}
        info = self.imageInfo

        if 'prostate' in new_ROI['ROIName']:
            new_ROI['ROIName'] = 'prostate'
        elif 'dil' in new_ROI['ROIName']:
            new_ROI['ROIName'] = 'dil'
        elif 'urethra' in new_ROI['ROIName']:
            new_ROI['ROIName'] = 'urethra'

        try:
            cs = contour.ContourSequence

        except AttributeError as ae:
            nContours = 0
            return new_ROI

        # print(info['UID2Ind'])

        nContours = len(cs)

        # print('UIDS that info has', info['UID2Ind'].keys())

        for contourSequence in cs:

            try:
                cis = contourSequence.ContourImageSequence[0]
                uid = cis.ReferencedSOPInstanceUID
            except AttributeError as ae:
                # some Ultrasound Contours are made differently
                sliceLoc = float(contourSequence.ContourData[2])
                sliceLoc = np.around(sliceLoc, decimals=5)
                uid = info['Loc2UID'][int(round(sliceLoc))]

            PA = ContourData2PatientArray(contourSequence.ContourData)

            try:  # axial dimension should have all the same numbers
                VA = Patient2VectorArray(PA, info['Pat2Pix_noRot'])
                # print("aligned first time")
            except Exception:
                # print("not aligned")
                VA = Patient2VectorArray(PA, info['Patient2Pixels'])

            # print('pre transformation\n', VA[:, 1:10])
            # print(PA[:, 0:5])
            # print(info['Patient2Pixels'])
            # print(info['Pat2Pix_noRot'])
            # print(VA[:, 0:5])

            nPts = VA.shape[1]
            # VA[2, :] = np.ones((1, nPts)) * info['UID2Ind'][uid]
            # print(uid)

            # print('post transformation\n', VA[:, 1:10])

            CA = [VectorArray2CVContour(VA)]
            ImSlice = CVContour2ImageArray(CA, volSize[1], volSize[0])
            ind = int(np.around(VA[2, 0]))
            new_ROI['DataVolume'][:, :, ind] += ImSlice.copy()

        print('{} has contours on {} slices'.format(structure.ROIName,
                                                    nContours))
        return new_ROI






    # def ContourSequence2BinaryVolume(self, structure, contour):
    #     """ Data from DICOM file into raster volume """

    #     volSize = (self.imageInfo['Rows'],
    #                self.imageInfo['Cols'], self.imageInfo['NSlices'])

    #     new_ROI = {'ROINumber': int(structure.ROINumber),
    #                'ROIName': structure.ROIName,
    #                'FrameRef_UID': structure.ReferencedFrameOfReferenceUID,
    #                'ROIColor': [int(x) for x in contour.ROIDisplayColor],
    #                'DataVolume': np.zeros(volSize)}

    #     for contourSequence in contour.ContourSequence:
    #         PA = ContourData2PatientArray(contourSequence.ContourData)
    #         try:
    #             VA = Patient2VectorArray(PA,
    # self.imageInfo['Patient2Pixels'])
    #             print(VA)
    #         except:
    #             VA = Patient2VectorArray(PA, self.imageInfo['Pat2Pix_noRot'])
    #             print(VA)
    #         CA = [VectorArray2CVContour(VA)]
    #         ImSlice = CVContour2ImageArray(CA, volSize[0], volSize[1])
    #         ind = int(VA[2, 0])
    #         # print('index {} has {}'.format(ind, ImSlice.shape))
    #         new_ROI['DataVolume'][:, :, ind] = ImSlice



""" Helper functions to transform between contour representations """
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# def mkStructureSetROISequence(ROI)

#     dicom.


def ContourData2PatientArray(contourData):
    """ Transforms data found in DICOM file into usable vector array
    input: a contour sequence right from a dicom file
    output: Numpy vector array in patient coordinates
    """
    try:
        floatArray = np.asarray([float(x) for x in contourData])
    except TypeError as te:
        print(te)
        # print(contourData)
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

    # print(vectorArray[2, 0])
    # print(vectorArray[2, 1])
    dummy = np.ones((1, vectorArray.shape[1])) * vectorArray[2, 0]
    same = np.allclose(vectorArray[2, :], dummy)

    # print("T", transform)
    # print(vectorArray)
    # print(dummy[0, :10])

    if same is not True:
        raise Exception

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
                                       lineType=cv2.LINE_AA).astype(np.uint8).T

    return contourImageOut


def ImageArray2CVContour(ImageArray, compression=None):
    """ Transforms binary ImageArray to list of vectors
    input: ImageArray must be a binary image/raster of the contour object
    output: vector list of contours
    """
    im, contours, hierarchy = cv2.findContours(ImageArray.copy(),
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
