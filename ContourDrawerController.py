""" Integrate Contour Editing with Patient Data """

from ContourDrawer import QContourDrawerWidget
from Patient import Patient as PatientObj
import sys


class ContourDrawingController(QContourDrawerWidget):

    def __init__(self, Patient=None, *args, **kwargs):

        self.Patient = Patient

        super().__init__(imageData=Patient.Image.data,
                         *args, **kwargs)

        for thisROI in Patient.StructureSet.ROIs:
            self.addROI(name=thisROI['ROIName'],
                        color=thisROI['ROIColor'],
                        data=thisROI['DataVolume'])

        self.changeROI(0)


    def sliderChanged(self, newValue):
        super().sliderChanged(newValue)
        newPosn = self.Patient.Image.info['Ind2Loc'][newValue]
        self.sliceDistLabel.setText("%.1fmm" % newPosn)


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # rootTest = r'C:\Users\MarkSemple\Documents\Sunnybrook Research Institute\Deformable Registration Project\clean sample data 10-19-2016\MRtemp'

    rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\WH Fx1 TEST DO NOT USE - Copy\MR'

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\WH Fx1 TEST DO NOT USE - Copy\US'


    myPatient = PatientObj(rootTest)
    # print(myPatient.Image.info['ImageOrientationPatient'])
    # print(myPatient.Image.info)
    form = ContourDrawingController(Patient=myPatient)
    form.show()
    sys.exit(app.exec_())
