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
from dicommodule.Patient_Dose import Patient_Dose


class Patient(object):
    """ Primary container class responsible for reading and writing DICOM
        to file. Can have image data, ROI data, and Plan/Catheter data.
        Minimum requirement is an Image.

        ~~ INPUTS ~~
        - patientPath (str): path to directory containing all data
        - imagefiles (list of strs): paths to patient image files
        - structureset (str): path to patient structureset file
        - reverse_rotation (bool): a patch for mis-rotated dicoms, ignore.

        If initialized with patientPath: will scan the directory for DICOM
        files, and will attempt to populate Patient Object with data from
        those files.
        Can also be initialized with an explicit list of imagefile paths,
        and a structureset file path.
        Images are required at a minimum (since structureset doesn't contain
        any pixel information!).
        Initialize with the filepath to the patient's dicom files.
        It will automatically crawl the folder and sort the various data files.
    """

    def __init__(self,
                 patientPath=None,
                 imagefiles=None,
                 structureset=None,
                 dosefile=None,
                 reverse_rotation=False):
        super().__init__()

        self.patientContents = {'image': False,
                                'ROI': False,
                                'plan': False,
                                'dose': False}

        self.reverseRotation = reverse_rotation

        self.Image = Patient_Image(revRot=reverse_rotation)
        self.StructureSet = Patient_StructureSet()
        self.Plan = Patient_Plan(patient=self)
        self.Dose = Patient_Dose()

        if patientPath is not None:
            self.add_data(patientPath)
            return

        if imagefiles is not None:
            self.add_images(imagefiles)

        if structureset is not None:
            self.add_rtst(structureset)

        if dosefile is not None:
            self.add_dose(dosefile)

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
            # for key in dcmFiles.keys():
                # print('Patient has {}'.format(key))

            if bool(dcmFiles):
                self.loadPatientData(dcmFiles)
            else:
                print("No DICOM Files Found at {}".format(patientPath))
                raise IOError

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

    def hasDose(self):
        return self.patientContents['dose']

    def add_images(self, filelist):
        self.Image.setData(fileList=filelist)
        self.patientContents['image'] = True

    def add_rtst(self, file):
        self.StructureSet.setData(filePath=file,
                                  imageInfo=self.Image.info)
        self.patientContents['ROI'] = True

    def add_dose(self, dosefile):
        self.Dose.setData(filePath=dosefile)
        self.patientContents['dose'] = True

    def loadPatientData(self, dcmFiles={}):
        # print(dcmFiles)
        # MR = 'MR Image Storage'
        # RTST = 'RT Structure Set Storage'

        MR = '1.2.840.10008.5.1.4.1.1.4'
        RTST = '1.2.840.10008.5.1.4.1.1.481.3'
        US = '1.2.840.10008.5.1.4.1.1.6.1'
        US_Multiframe = '1.2.840.10008.5.1.4.1.1.3.1'
        CT = '1.2.840.10008.5.1.4.1.1.2'
        DO = '1.2.840.10008.5.1.4.1.1.481.2'

        # IMAGES
        if MR in dcmFiles.keys():
            self.add_images(filelist=dcmFiles[MR])

        elif US in dcmFiles.keys():
            self.add_images(filelist=dcmFiles[US])

        elif US_Multiframe in dcmFiles.keys():
            self.add_images(filelist=dcmFiles[US_Multiframe])

        elif CT in dcmFiles.keys():
            self.add_images(filelist=dcmFiles[CT])

        # STRUCTURE SET
        if RTST in dcmFiles.keys():
            self.add_rtst(file=dcmFiles[RTST][0])

        # DOSE
        if DO in dcmFiles.keys():
            self.add_dose(dosefile=dcmFiles[DO][0])

        # SOMETHING ELSE?
        if 'unknown' in dcmFiles.keys():
            self.StructureSet.setData(filePath=dcmFiles['unknown'][0],
                                      imageInfo=self.Image.info)
            self.patientContents['ROI'] = True

        for item in self.patientContents.keys():
            if self.patientContents[item]:
                print("Patient has {}".format(item))

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
        return {}

    # ~~ Create Threadpool same size as dcm list, get modality for each file
    if not bool(dcmFileList):
        return {}

    pool = ThreadPool(len(dcmFileList))
    results = pool.map(func=lambda x: (dicom.read_file(x, force=True).Modality, x),
                       iterable=dcmFileList)
    pool.close()
    pool.join()

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

    # test_root = r'P:\USERS\PUBLIC\Mark Semple\Dicom Module\sample_one_file\US'
    # fname = r'2.16.840.1.114362.1.6.7.7.17914.9994565197.469319163.1074.11.dcm'
    # test_file = os.path.join(test_root, fname)


    # pathname = r'P:\USERS\PUBLIC\Ananth\Research Projects\1 - CLINICAL TRIALS\PRIVATE\Trials\Active\Radiogenomics HDR - retro\Data - Working\Pt_3\US\fx1 (with warped structures)'

    ppath = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\mr2us-code\mr2us-data\MR2US Baseline Dataset 2017\0_INPUT_DATA\P1\MR'

    import pprint


    t0 = time.time()

    patient = Patient(patientPath=ppath)
    # print(patient)

    pprint.pprint(patient.Dose.info)
    pprint.pprint(patient.Image.info)

    # print('dose', patient.Dose.DoseGrid.shape)
    # print('dose', patient.Dose.info['PixelSpacing'])

    print('im', patient.Image.data.shape)
    print('im', patient.Image.info['PixelSpacing'])

    print("Finished in {} seconds".format(time.time() - t0))

    # LD = patient.Dose.DoseGrid.shape[1] * patient.Dose.info['PixelSpacing'][1]
    # print(LD)

    # LIM = patient.Image.data.shape[0] * patient.Image.info['PixelSpacing'][0]
    # print(LIM)


    # print("has data:", patient.hasData())
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
