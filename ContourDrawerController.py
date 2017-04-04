""" Integrate Contour Editing with Patient Data """

import sys
import numpy as np
try:
    from ContourDrawer import QContourDrawerWidget
    from Patient import Patient as PatientObj
except ImportError:
    from dicommodule.ContourDrawer import QContourDrawerWidget
    from dicommodule.Patient import Patient as PatientObj
try:
    import Affine_Registration_Fcns as ARF
except ImportError:
    pass

class PatientContourDrawer(QContourDrawerWidget):

    def __init__(self, Patient=None, PatientPath=None, *args, **kwargs):

        # give either: a Patient Object
        # OR
        # A path to a patient directory: then do the patient-making
        # OR
        # nothing

        super().__init__(*args, **kwargs)

        if PatientPath is not None:
            Patient = PatientObj(patientPath=PatientPath)

        self.Patient = Patient
        if Patient is not None:
            self.patient2Editor(Patient)

        # self.changeROI(0)

    def patient2Editor(self, Patient):
        self.Patient = Patient
        self.init_Image(Patient.Image.data)
        for thisROI in Patient.StructureSet.ROIs:
            self.addROI(name=thisROI['ROIName'],
                        color=thisROI['ROIColor'],
                        data=thisROI['DataVolume'],
                        RefUID=thisROI['FrameRef_UID'],
                        num=thisROI['ROINumber'])

        try:
            pros = Patient.StructureSet.ROI_byName['prostate']['DataVolume']
            bounds, size = ARF.findBoundingCuboid(pros)
            self.prostateStart = bounds[0, 2]
            self.prostateStop = bounds[1, 2]
        except:
            print("no ARF")

    # def editor2Patient(self):
    #     for ROI in  self.Patient.StructureSet.ROIs
    #     self.Patient.StructureSet

    #     return self.Patient


    def sliderChanged(self, newValue):
        super().sliderChanged(newValue)
        if self.Patient.hasImage:
            # print('{} trigger!'.format(self.Patient.Image.info['NSlices']))
            newPosn = self.Patient.Image.info['Ind2Loc'][newValue]
            self.sliceDistLabel.setText("%.1fmm" % newPosn)


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\WH Fx1 TEST DO NOT USE - Copy\MR'
    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\TroubleData - Copy\US'
    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\TroubleData\MRtemp'
    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\Jan 11 - bad data\Cutler_Douglas _ in python - Copy\US'
    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Niranjan-ArticlesAndCommandFiles\Input\MR'
    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Report\Report\TSMRtoUScase_3\RTStructrureSet'
    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\CLEAN - Sample Data 10-19-2016\MR'
    rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\WH Fx1 TEST DO NOT USE - Copy\US'
    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\MR Anonymized'

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Niranjan_Data\MR-US_Clean\MR-US_Clean\TSMRtoUScase_1\US'

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\SunnybrookDataset'

    form = PatientContourDrawer(PatientPath=rootTest)
    form.show()

    sys.exit(app.exec_())
