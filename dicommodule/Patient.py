""" dicom """

# Built-ins
import os
import time
from multiprocessing.pool import ThreadPool

# Third-parties
try:
    import dicom as dicom
except:
    import pydicom as dicom

# Locals
# try:
    # from Patient_ROI import Patient_ROI_Set
    # from Patient_Image import Patient_Image
# except ImportError:
from dicommodule.Patient_ROI import Patient_ROI_Set
from dicommodule.Patient_Image import Patient_Image
from dicommodule.Patient_Plan import Patient_Plan

# from Image import Image
# from Contour import contour
# from VolumeViewer import QVolumeViewerWidget


class Patient(object):
    """ container class responsible for reading and writing DCM to file """

    # Name = None
    # DOB = None
    # Position = None

    def __init__(self, patientPath, reverse_rotation=False):
        super().__init__()

        self.hasImage = False
        self.hasROI = False
        self.hasPlan = False

        self.Image = Patient_Image()
        self.ROI = Patient_ROI_Set()
        self.Plan = Patient_Plan()

        self.reverseRotation = reverse_rotation

        # Scan given patient folder for dicom image files,
        # return dict by modality
        dcmFiles = self.scanPatientFolder(patientPath)

        if bool(dcmFiles):
            self.loadPatientData(dcmFiles)
        else:
            print("No DICOM Files Found at {}".format(patientPath))

        # print("Image Position Patient")
        # self.Image.prettyFormatIPP()
        # print("Image Orientation Patient")
        # print(self.Image.info['ImageOrientationPatient'])

    def scanPatientFolder(self, patient_directory):
        """ Scan directory for dicom files """
        # myFiles = find_DCM_files_parallel(patient_directory)

        dcmFiles = []
        print(patient_directory)
        for root, dirs, files in os.walk(patient_directory):
            for file in files:
                if file.endswith('.dcm'):
                    dcmFiles.append(file)

        if len(dcmFiles) == 0:
            print('NO FILES')
            raise IOError

        myFiles = find_DCM_files_serial(patient_directory)

        for key in myFiles.keys():
            print('Patient has %s' % key)
        return myFiles

    def loadPatientData(self, dcmFiles={}):
        # print(dcmFiles)
        # MR = 'MR Image Storage'
        # RTST = 'RT Structure Set Storage'
        MR = '1.2.840.10008.5.1.4.1.1.4'
        RTST = '1.2.840.10008.5.1.4.1.1.481.3'
        US = '1.2.840.10008.5.1.4.1.1.6.1'
        CT = '1.2.840.10008.5.1.4.1.1.2'

        # print(dcmFiles)

        if MR in dcmFiles.keys():
            self.Image = Patient_Image(dcmFiles[MR],
                                       revRot=self.reverseRotation)
            self.hasImage = True

        elif US in dcmFiles.keys():
            self.Image = Patient_Image(dcmFiles[US],
                                       revRot=self.reverseRotation)
            self.hasImage = True

        elif CT in dcmFiles.keys():
            self.Image = Patient_Image(dcmFiles[CT],
                                       revRot=self.reverseRotation)
            self.hasImage = True

        if RTST in dcmFiles.keys():
            self.StructureSet = Patient_ROI_Set(file=dcmFiles[RTST][0],
                                                imageInfo=self.Image.info)
            self.hasROI = True

        if 'unknown' in dcmFiles.keys():
            self.StructureSet = Patient_ROI_Set(file=dcmFiles['unknown'][0],
                                                imageInfo=self.Image.info)
            self.hasROI = True

    def getPatient_specific_data(self):
        pass

    def savePatientData(self, patient_directory=None):
        pass

    def setPatientName(self, name):
        pass


def find_DCM_files_parallel(rootpath=None):
    """ Walk rootpath input directory, find all '*.dcm' files """
    time_zero = time.time()
    dcmFileList = []

    # ~~ Walk directory, add all '*.dcm' files to list
    for root, dirs, files in os.walk(rootpath):
        for file in files:
            if file.endswith('.dcm'):
                fullpath = os.path.join(root, file)
                dcmFileList.append(fullpath)

    print("Found {} files".format(len(dcmFileList)))

    if len(dcmFileList) > 300:
        print('Too many files!')
        return

    # ~~ Create Threadpool same size as dcm list, get modality for each file
    if not bool(dcmFileList):
        return {}

    pool = ThreadPool(len(dcmFileList))
    results = pool.map(func=lambda x: (dicom.read_file(x, force=True).Modality, x),
                       iterable=dcmFileList)

    # ~~ sort into a dictionary by modality type
    dcmDict = {}
    for result in results:
        mode, filepath = result
        if mode not in dcmDict:
            dcmDict[mode] = []
        dcmDict[mode].append(filepath)

    print("parallel took %.2fs to sort DCMs" % (time.time() - time_zero))
    return dcmDict


def find_DCM_files_serial(rootpath=None):
    """ Walk rootpath input directory, find all '*.dcm' files """
    time_zero = time.time()
    dcmList = []
    dcmDict = {}

    # ~~ Walk directory, add all '*.dcm' files to dict by modality
    for root, dirs, files in os.walk(rootpath):
        for file in files:
            if file.endswith('.dcm'):
                fullpath = os.path.join(root, file)
                dcmList.append(fullpath)

    if len(dcmList) > 300:
        print('Too many files!')
        return

    for fullpath in dcmList:
        try:
            modality = dicom.read_file(fullpath, force=True).SOPClassUID
        except:
            modality = 'unknown'
        if modality not in dcmDict:
            dcmDict[modality] = []

        dcmDict[modality].append(fullpath)

    print("serial took %.2fs to sort DCMS for %s" % (time.time() - time_zero,
                                                     modality))
    return(dcmDict)


def backupFile_finder(path):

    MR = None
    US = None

    for root, dirs, files in os.walk(path):

        for folder in dirs:

            fullfolder = os.path.join(root, folder)
            print(os.path.join(root, folder))

            if 'MR' in folder.upper():

                print("THIS THE MR")
                MR = fullfolder

            elif 'US' in folder.upper():

                print("THIS THE US")
                US = fullfolder


    if MR is not None:
        for root, dirs, files in os.walk(MR):
            print(files)


    if US is not None:
        for root, dirs, files in os.walk(US):
            print(files)



if __name__ == "__main__":

    print('pass')
    pass

    # rootTest = r'X:\MR_to_US_Fusion\Curran_John'

    # backupFile_finder(rootTest)


    # rootTest = r'P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\2016-07__Studies (as will appear)'

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\WH Fx1 TEST DO NOT USE\MRtemp'

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\WH Fx1 TEST DO NOT USE\MRtemp'

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\TroubleData\MR'

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\TroubleData\RTStructureSet'

    # rootTest = r'P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\test_out_1.6.4'

    # rootTest = r'P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\2016-07__Studies (HFS)'

    # patient = Patient('')  #patientPath=rootTest)

    # # print(patient.Image.info['UID2IPP'].values())
    # # ippVals = list(patient.Image.info['UID2IPP'].values())
    # # print(patient.Image.info['ImageOrientationPatient'])
    # # print(patient.Image)
    # # print(patient.StructureSet)

    # from PyQt5.QtWidgets import QApplication
    # from ContourDrawer import QContourDrawerWidget
    # import sys


    # app = QApplication(sys.argv)
    # # myImage = np.random.randint(0, 128, (750, 750, 20), dtype=np.uint8)
    # # myImage = np.zeros((512, 512, 20), dtype=np.uint8)
    # form = QContourDrawerWidget(imageData=patient.Image.data)
    # for thisROI in patient.StructureSet.ROIs:
    #     form.addROI(name=thisROI['ROIName'],
    #                 color=thisROI['ROIColor'],
    #                 data=thisROI['DataVolume'])


    # form.show()
    # sys.exit(app.exec_())
