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
from VolumeViewer import QVolumeViewerWidget


class Patient(object):
    """ container class responsible for reading and writing DCM to file """

    Name = None
    DOB = None
    Position = None

    def __init__(self, patientPath=None, makeImage=False, makeContour=False):
        """ if patient initialized with """
        super().__init__()

        """ Scan given patient folder for dicom image files,
            return dict by modality """
        if patientPath is not None:
            dcmFiles = self.scanPatientFolder(patientPath)

        """ Load medical data from found dicom files """
        if bool(dcmFiles):
            # Verify these are all same series!
            # pass
            self.loadPatientData(dcmFiles)

    def scanPatientFolder(self, patient_directory=None):
        """ Scan directory for dicom files """
        myFiles = find_DCM_files_parallel(patient_directory)
        for key in myFiles.keys():
            print('Patient has %s' % key)
        return myFiles

    def loadPatientData(self, dcmFiles={}):
        if 'MR' in dcmFiles.keys():
            self.Image = Patient_Image(dcmFiles['MR'])

        if 'RTSTRUCT' in dcmFiles.keys():
            self.StructureSet = Patient_ROI_Set(file=dcmFiles['RTSTRUCT'][0],
                                                imageInfo=self.Image.info)

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
    pool = ThreadPool(len(dcmFileList))
    results = pool.map(func=lambda x: (dicom.read_file(x).Modality, x),
                       iterable=dcmFileList)

    # ~~ sort into a dictionary by modality type
    dcmDict = {}
    for result in results:
        mode, filepath = result
        if mode not in dcmDict:
            dcmDict[mode] = []
        dcmDict[mode].append(filepath)

    print("parallel took %.2fs to sort DCMs" % (time.time() - time_zero))
    return(dcmDict)


def find_DCM_files_serial(rootpath=None):
    """ Walk rootpath input directory, find all '*.dcm' files """
    time_zero = time.time()
    dcmDict = {}

    # ~~ Walk directory, add all '*.dcm' files to dict by modality
    for root, dirs, files in os.walk(rootpath):
        for file in files:
            if file.endswith('.dcm'):
                fullpath = os.path.join(root, file)
                modality = dicom.read_file(fullpath).Modality
                if modality not in dcmDict:
                    dcmDict[modality] = []
                dcmDict[modality].append(fullpath)

    print("serial took %.2fs to sort DCMS" % (time.time() - time_zero))
    return(dcmDict)



if __name__ == "__main__":

    # rootTest = r'P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\2016-07__Studies (as will appear)'

    rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\WH Fx1 TEST DO NOT USE\MRtemp'

    # rootTest = r'C:\Users\MarkSemple\Documents\Sunnybrook Research Institute\Deformable Registration Project\CLEAN - Sample Data 10-02-2016 - backup\MRtemp'

    patient = Patient(patientPath=rootTest)

    print(patient.Image)
    print(patient.StructureSet)

    # dcmFiles = find_DCM_files_parallel(rootTest)
    # di = []
    # i = 0
    # for value in dcmFiles['MR']:
    #     di.append(dicom.read_file(value))

    # import sys
    # for obj in di:
    #     print(i, obj.ImagePositionPatient, obj.PatientPosition, sys.getsizeof(obj))
    #     i += 1

    # dcmFiles = find_DCM_files_serial(rootTest)

    # myPatient = Patient(patientPath=rootTest)

    # print(myPatient.Image.data)

    from PyQt5.QtWidgets import QApplication
    from ContourDrawer import QContourDrawerWidget
    import sys

    app = QApplication(sys.argv)
    # myImage = np.random.randint(0, 128, (750, 750, 20), dtype=np.uint8)
    # myImage = np.zeros((512, 512, 20), dtype=np.uint8)
    form = QContourDrawerWidget(imageData=patient.Image.data)

    form.show()
    sys.exit(app.exec_())
