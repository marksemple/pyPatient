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
        for key in self.StructureSet.ROI_byName:
            if 'warped_mr_prostate' in key.lower():
                MRProsKey = key.lower()
                break
        pros = self.StructureSet.ROI_byName[MRProsKey].DataVolume
        bounds, size = ARF.findBoundingCuboid(pros)
        print('prostate bounds', bounds)
        self.prostateStart = bounds[0, :]
        self.prostateStop = bounds[1, :]

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

    # rootTest = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\MR2US_Study_Data_Anonymized\P1\US'

    # rootTest = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\MR2US_Study_Data_Anonymized\P3\RTStructure'

    Patient_ImagePath = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\MR2US_Study_Data_Anonymized\P1\US'

    AL_P1_StructPath = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\US_STRUCTURE\P1\RO_AL\2.16.840.1.114362.1.6.6.6.16802.9994565197.458082905.401.1.dcm'

    # AL_P2_StructPath = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\US_STRUCTURE\P2\RO_AL\2.16.840.1.114362.1.6.6.6.16802.9994565197.458083653.212.4.dcm'

    # AL_P6_StructPath = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\US_STRUCTURE\P6\RO_AL\2.16.840.1.114362.1.6.6.6.16802.9994565197.458085609.914.9.dcm'

    # HC_P6_StructPath = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\US_STRUCTURE\P6\RO_HC\2.16.840.1.114362.1.6.6.6.16802.10477832757.458858052.741.3514.dcm'

    # LM_P2_StructPath = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\US_STRUCTURE\P2\RO_LM\2.16.840.1.114362.1.6.6.6.16802.9994565197.456957130.994.265.dcm'

    MRUS_P1_StructPath = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\output_MR2USFusion\P1\RS 1.2.528.1.1007.189.1.32899.533211654.290.dcm'

    # MRUS_P3_StructPath = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\output_MR2USFusion\P3\RS 1.2.528.1.1007.189.1.32899.543928676.282.dcm'

    # M_PLM_P3_StructPath = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\output_plastimatch_Mark\P3\rtss_1.2.826.0.1.3680043.8.274.1.1.965460910.16910.6891809880.435.dcm'

    ET_P1_StructPath = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\US_STRUCTURE\P1\RO_ET\2.16.840.1.114362.1.6.6.6.16802.10477832757.457235887.398.824.dcm'


    patient = PatientObj(Patient_ImagePath)
    # patient.StructureSet.setData(filePath=M_PLM_P3_StructPath)
    # patient.StructureSet.setData(filePath=HC_P6_StructPath)
    patient.StructureSet.setData(filePath=AL_P1_StructPath)
    # patient.StructureSet.setData(filePath=LM_P2_StructPath)
    patient.StructureSet.setData(filePath=ET_P1_StructPath)
    patient.StructureSet.setData(filePath=MRUS_P1_StructPath)

    staplefile = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\STAPLE_contours\P1\Staple 1.dat'


    import pickle

    with open(staplefile, 'rb') as filepath:
        StapleContour = pickle.load(filepath)

    print('StapleContour')
    print(StapleContour.shape)
    print(np.amax(StapleContour))
    print('n > 0', np.sum(StapleContour[StapleContour > 0.1]))

    info = patient.Image.info

    patient.StructureSet.add_ROI(name='STAPLE',
                                 color=(0, 255, 0),
                                 imageInfo=info,
                                 dataVolume=StapleContour.astype(np.uint8) * 255,
                                 enablePlotting=True)


    form = PatientContourDrawer(Patient=patient)

    form.show()

    sys.exit(app.exec_())
