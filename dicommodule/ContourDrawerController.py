""" Integrate Contour Editing with Patient Data """

import sys
import numpy as np
from dicommodule.ContourDrawer import QContourDrawerWidget
# from dicommodule.ContourViewer import countContourSlices
from dicommodule.Patient import Patient as PatientObj

try:
    from deformableregistration import Affine_Registration_Fcns as ARF
except ImportError:
    print("NO ARF")


class PatientContourDrawer(QContourDrawerWidget):
    def __init__(self, Patient=None, PatientPath=None, *args, **kwargs):
        # give either: a Patient Object
        # OR
        # A path to a patient directory: then do the patient-making
        # OR
        # nothing
        super().__init__(*args, **kwargs)

        # FIRST: Create a patient, if necessary
        if PatientPath is not None:
            Patient = PatientObj(patientPath=PatientPath)
            Patient.StructureSet.makePlottable()

        # SECOND: Register patient with Editor
        if Patient is not None:
            self.patient2Editor(Patient)

        self.addROIbttn.hide()
        self.hideControls(True)

    def patient2Editor(self, Patient):
        self.Patient = Patient
        self.init_Image(Patient.Image.data)
        self.StructureSet = Patient.StructureSet
        for thisROI in self.StructureSet.ROI_List:
            self.register_ROI(thisROI)
        MRProsKey = 'prostate'
        hasProstate = False
        for key in self.StructureSet.ROI_byName:
            if 'warped_mr_prostate' in key.lower():
                MRProsKey = key.lower()
                hasProstate = True
                break
        if hasProstate:
            pros = self.StructureSet.ROI_byName[MRProsKey].DataVolume
            bounds, size = ARF.findBoundingCuboid(pros)
            print('prostate bounds', bounds)
            self.prostateStart = bounds[0, :]
            self.prostateStop = bounds[1, :]
        else:
            self.prostateStart = 0
            self.prostateStop = 1

        self.setModality(Patient.Image.ImageModality)

    def viewPick(self, index):

        if index == 0:  # axial
            if self.planeInd == 2:
                return
            self.planeInd = 2

        elif index == 1:  # saggital
            if self.planeInd == 0:
                return
            self.planeInd = 0
            self.enableMotionControls()

        elif index == 2:  # saggital
            if self.planeInd == 1:
                return
            self.planeInd = 1
            self.enableMotionControls()

        try:
            info = self.Patient.Image.info
            spacing = [info['PixelSpacing'][0],
                       info['PixelSpacing'][1],
                       info['SliceSpacing']]

        except AttributeError as ae:
            print("no patient, using default spacing")
            spacing = [1, 1, 1]

        # ratio = spacing[2] / spacing[self.planeInd]

        viewBox = self.plotWidge.getViewBox()
        if index == 0:  # axial
            ratio = spacing[0] / spacing[1]
        elif index == 1:  # saggital
            ratio = spacing[2] / spacing[0]
        elif index == 2:  # coronal
            ratio = spacing[1] / spacing[2]

        viewBox.setAspectLocked(lock=True, ratio=ratio)
        self.imageData = np.swapaxes(self.originalImage, self.planeInd, 2)
        self.init_Slider(self.slider)
        self.updateContours(isNewSlice=True)
        viewBox.autoRange(items=[self.imageItem, ])
        self.viewChanged.emit(index)

    def sliderChanged(self, newValue):
        super().sliderChanged(newValue)
        try:
            if self.Patient.hasImage:
                pass
                # print('{} trigger!'.format(self.Patient.Image.info['NSlices']))
                # newPosn = self.Patient.Image.info['Ind2Loc'][newValue]
                # self.sliceDistLabel.setText("%.1fmm" % newPosn)
        except AttributeError:
            return


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Patient_ImagePath = r'P:\USERS\PUBLIC\Mark Semple\Dicom Module\sample_one_file\MR'

    # Patient_ImagePath = r'P:\USERS\PUBLIC\Mark Semple\Dicom Module\sample_one_file\US'

    # Patient_ImagePath = r'P:\USERS\PUBLIC\Mark Semple\radiomics\radiomics - data\test_p2\MR_pre (with warped structures)'

    # Patient_ImagePath = r'X:\MR_to_US_Fusion\Methven_William A_728760\RTStructure'

    # Patient_ImagePath = r'P:\USERS\PUBLIC\Ananth\Research Projects\1 - CLINICAL TRIALS\PRIVATE\Trials\Active\Radiogenomics HDR - retro\Data - Working\Pt_3\MR_post (with warped structures)'

    Patient_ImagePath = r'Z:\Public\USERS\PUBLIC\Ananth\Research Projects\1 - CLINICAL TRIALS\PRIVATE\Trials\Active\Radiogenomics HDR - retro\Data - DWI raw\Pt_1\post\imgs'
    # r'P:\USERS\PUBLIC\Mark Semple\radiomics\code\sample_files\MR'

    patient = PatientObj(Patient_ImagePath)
    # patient.StructureSet.setData(filePath=AL_P1_StructPath)

    form = PatientContourDrawer(Patient=patient)

    form.show()

    sys.exit(app.exec_())
