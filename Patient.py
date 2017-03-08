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


class Patient(object):
    """ container responsible for reading and writing DCM to file"""

    def __init__(self, patientPath=None, makeImage=False, makeContour=False):
        super().__init__()

        myFiles = find_DCM_files_parallel(patientPath)
        # myFiles = find_DCM_files_serial(patientPath)
        for key in myFiles.keys():
            print('Patient has %s' % key)

        # Initialize Image Object
        if 'MR' in myFiles.keys():
            self.Image = Patient_Image(myFiles['MR'])
            # print(self.Image)

        # Initialize ROI/Contour Object
        if 'RTSTRUCT' in myFiles.keys():
            self.StructureSet = Patient_ROI_Set(file=myFiles['RTSTRUCT'][0])


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

    rootTest = r'P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\2016-07__Studies (as will appear)'

    # dcmFiles = find_DCM_files_serial(rootTest)
    # dcmFiles = find_DCM_files_parallel(rootTest)

    myPatient = Patient(patientPath=rootTest)

    print(myPatient.Image.data)

    from PyQt5.QtWidgets import QApplication
    from ContourDrawer import QContourDrawerWidget
    import sys

    app = QApplication(sys.argv)
    # myImage = np.random.randint(0, 128, (750, 750, 20), dtype=np.uint8)
    # myImage = np.zeros((512, 512, 20), dtype=np.uint8)
    form = QContourDrawerWidget(imageData=myPatient.Image.data)
    form.show()
    sys.exit(app.exec_())
