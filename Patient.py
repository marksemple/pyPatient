""" dicom """

# Built-ins
import os
import time
from multiprocessing.pool import ThreadPool

# Third-parties
import dicom

# Locals
# from Image import Image
# from Contour import contour


class Patient(object):
    def __init__(self, patientPath=None, makeImage=False, makeContour=False):
        super().__init__()
        myFiles = find_DCM_files_parallel(patientPath)
        for key in myFiles.keys():
            print('Patient has %s' % key)

        print(len(myFiles['MR']))

        if makeImage and 'MR' in myFiles.keys():
            # self.Image = Image(myFiles[])
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

    rootTest = r'P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\2016-07__Studies (as will appear)'

    # dcmFiles = find_DCM_files_serial(rootTest)
    # dcmFiles = find_DCM_files_parallel(rootTest)

    myPatient = Patient(patientPath=rootTest)
