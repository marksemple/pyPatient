""" dicom """

# Built-ins
import os
import time
from multiprocessing.pool import ThreadPool

# Third-parties
try:
    import dicom as dicom
except ImportError:
    import pydicom as dicom

# Locals
from dicommodule.Patient_StructureSet import Patient_StructureSet
from dicommodule.Patient_Image import Patient_Image
from dicommodule.Patient_Plan import Patient_Plan


class Patient(object):
    """ Primary container class responsible for reading and writing DCM
            to file. Can have image data, ROI data, and Plan/Catheter data.
        Initialize with the filepath to the patient's dicom files.
        It will automatically crawl the folder and sort the various data files.
    """

    def __init__(self, patientPath=None, reverse_rotation=False):
        super().__init__()

        # self.hasImage = False
        # self.hasROI = False
        # self.hasPlan = False

        self.patientContents = {'image': False,
                                'ROI': False,
                                'plan': False}

        self.reverseRotation = reverse_rotation

        self.Image = Patient_Image(revRot=reverse_rotation)
        self.StructureSet = Patient_StructureSet()
        self.Plan = Patient_Plan()
        self.add_data(patientPath)

    def __str__(self):
        if True in self.patientContents.values():
            strang = "Patient Object with: "
            for datatype in self.patientContents:
                if self.patientContents[datatype]:
                    strang += '{}, '.format(datatype)
        else:
            strang = 'Empty patient object'

        return strang

    def add_data(self, patientPath):
        if patientPath is not None:
            dcmFiles = find_DCM_files_serial(patientPath)
            for key in dcmFiles.keys():
                print('Patient has {}'.format(key))

            if bool(dcmFiles):
                self.loadPatientData(dcmFiles)
            else:
                print("No DICOM Files Found at {}".format(patientPath))

    def hasData(self):
        if True in self.patientContents.values():
            return True
        else:
            return False

    def hasImage(self):
        return self.patientContents['image']

    def hasROI(self):
        return self.patientContents['ROI']

    def hasPlan(self):
        return self.patientContents['plan']

    def loadPatientData(self, dcmFiles={}):
        # print(dcmFiles)
        # MR = 'MR Image Storage'
        # RTST = 'RT Structure Set Storage'

        MR = '1.2.840.10008.5.1.4.1.1.4'
        RTST = '1.2.840.10008.5.1.4.1.1.481.3'
        US = '1.2.840.10008.5.1.4.1.1.6.1'
        CT = '1.2.840.10008.5.1.4.1.1.2'

        if MR in dcmFiles.keys():
            self.Image.setData(fileList=dcmFiles[MR])
            self.patientContents['image'] = True

        elif US in dcmFiles.keys():
            self.Image.setData(fileList=dcmFiles[US])
            self.patientContents['image'] = True

        elif CT in dcmFiles.keys():
            self.Image.setData(fileList=dcmFiles[CT])
            self.patientContents['image'] = True

        if RTST in dcmFiles.keys():
            self.StructureSet.setData(filePath=dcmFiles[RTST][0],
                                      imageInfo=self.Image.info)
            self.patientContents['ROI'] = True

        if 'unknown' in dcmFiles.keys():
            self.StructureSet.setData(filePath=dcmFiles['unknown'][0],
                                      imageInfo=self.Image.info)
            self.patientContents['ROI'] = True

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
        return {}

    for fullpath in dcmList:
        try:
            modality = dicom.read_file(fullpath, force=True).SOPClassUID
        except AttributeError:
            modality = 'unknown'
        if modality not in dcmDict:
            dcmDict[modality] = []

        dcmDict[modality].append(fullpath)

    return dcmDict


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

    emptyRoot = r'P:\USERS\PUBLIC\Mark Semple\volumecapture\volumecapture\res'

    MRRoot = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\MR2US_Study_Data_Anonymized\P1\MR'

    MRRoot2 = r'P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\2016-07_Studies_practice_GYN_DCM\2016-07__Studies (same data, shorter names)'

    USRoot = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\MR2US_Study_Data_Anonymized\P1\US'

    noneRoot = None

    patient = Patient(patientPath=USRoot)
    print(patient)
    print("has data:", patient.hasData())
    # rootTest = r'X:\MR_to_US_Fusion\Curran_John'
    # backupFile_finder(rootTest)
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
