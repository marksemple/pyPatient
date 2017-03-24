""" Integrate Contour Editing with Patient Data """

import sys
try:
    from ContourDrawer import QContourDrawerWidget
    from Patient import Patient as PatientObj
except ImportError:
    from dicommodule.ContourDrawer import QContourDrawerWidget
    from dicommodule.Patient import Patient as PatientObj


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
            self.initializePatient(Patient)

        # self.changeROI(0)

    def initializePatient(self, Patient):
        self.init_Image(Patient.Image.data)
        for thisROI in Patient.StructureSet.ROIs:
            self.addROI(name=thisROI['ROIName'],
                        color=thisROI['ROIColor'],
                        data=thisROI['DataVolume'])


    def sliderChanged(self, newValue):
        super().sliderChanged(newValue)
        if self.Patient.hasImage:
            newPosn = self.Patient.Image.info['Ind2Loc'][newValue]
            self.sliceDistLabel.setText("%.1fmm" % newPosn)


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # rootTest = r'C:\Users\MarkSemple\Documents\Sunnybrook Research Institute\Deformable Registration Project\clean sample data 10-19-2016\MRtemp'

    rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\WH Fx1 TEST DO NOT USE - Copy\MR'

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\CLEAN - Sample Data 10-19-2016\MR'

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\WH Fx1 TEST DO NOT USE - Copy\US'

    # myPatient = PatientObj(rootTest)

    form = PatientContourDrawer(PatientPath=rootTest)
    form.show()
    sys.exit(app.exec_())
