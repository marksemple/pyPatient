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
from Patient_ROI import Patient_ROI_Set
from Patient_Image import Patient_Image
# from Image import Image
# from Contour import contour
# from VolumeViewer import QVolumeViewerWidget


class Patient(object):
    """ container class responsible for reading and writing DCM to file """

    Name = None
    DOB = None
    Position = None

    def __init__(self, patientPath=None, makeImage=False, makeContour=False):
        """ if patient initialized with """
        super().__init__()

        # if we're given path to existing DICOM stuff; go there to fill it out
        """ Scan given patient folder for dicom image files,
            return dict by modality """
        if patientPath is not None:
            # if self.validatePath(patientPath):
            dcmFiles = self.scanPatientFolder(patientPath)
            # else:
            # invalid path?/
            # return
        else:
            dcmFiles = []
        """ Load medical data from found dicom files """
        if bool(dcmFiles):
            self.loadPatientData(dcmFiles)
        else:
            self.createPatientData()
    # def validatePath(self, path):

    def scanPatientFolder(self, patient_directory=None):
        """ Scan directory for dicom files """
        # myFiles = find_DCM_files_parallel(patient_directory)
        myFiles = find_DCM_files_serial(patient_directory)

        for key in myFiles.keys():
            print('Patient has %s' % key)
        return myFiles

    def loadPatientData(self, dcmFiles={}):
        if 'MR' in dcmFiles.keys():
            self.Image = Patient_Image(dcmFiles['MR'])

        if 'US' in dcmFiles.keys():
            self.Image = Patient_Image(dcmFiles['US'])
            print(self.Image.Ind2Loc)

        if 'RTSTRUCT' in dcmFiles.keys():
            self.StructureSet = Patient_ROI_Set(file=dcmFiles['RTSTRUCT'][0],
                                                imageInfo=self.Image.info)

        if 'unknown' in dcmFiles.keys():
            self.StructureSet = Patient_ROI_Set(file=dcmFiles['unknown'][0],
                                                imageInfo=self.Image.info)

    def createPatientData(self):
        # self.Image = Patient_Image()
        # self.StructureSet = Patient_ROI_set()
        pass

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
    dcmDict = {}

    # ~~ Walk directory, add all '*.dcm' files to dict by modality
    for root, dirs, files in os.walk(rootpath):
        for file in files:
            if file.endswith('.dcm'):
                fullpath = os.path.join(root, file)
                try:
                    modality = dicom.read_file(fullpath, force=True).Modality
                except:
                    modality = 'unknown'
                if modality not in dcmDict:
                    dcmDict[modality] = []

                dcmDict[modality].append(fullpath)

    print("serial took %.2fs to sort DCMS" % (time.time() - time_zero))
    return(dcmDict)


if __name__ == "__main__":

    # rootTest = r'P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\2016-07__Studies (as will appear)'

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\WH Fx1 TEST DO NOT USE\MRtemp'

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\WH Fx1 TEST DO NOT USE\MRtemp'

    rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\Jan 11 - bad data\Cutler_Douglas _ in python - Copy\MRtemp'

    patient = Patient(patientPath=rootTest)

    print(patient.Image.info['UID2IPP'].values())
    # ippVals = list(patient.Image.info['UID2IPP'].values())

    print(patient.Image.info['ImageOrientationPatient'])

    # print(patient.Image)
    # print(patient.StructureSet)

    from PyQt5.QtWidgets import QApplication
    from ContourDrawer import QContourDrawerWidget
    import sys


    app = QApplication(sys.argv)
    # myImage = np.random.randint(0, 128, (750, 750, 20), dtype=np.uint8)
    # myImage = np.zeros((512, 512, 20), dtype=np.uint8)
    form = QContourDrawerWidget(imageData=patient.Image.data)
    for thisROI in patient.StructureSet.ROIs:
        form.addROI(name=thisROI['ROIName'],
                    color=thisROI['ROIColor'],
                    data=thisROI['DataVolume'])


    form.show()
    sys.exit(app.exec_())
