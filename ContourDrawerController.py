#

from ContourDrawer import QContourDrawerWidget
from Patient import Patient as PatientObj
# from PyQt5.QtWidgets import QApplication
# from ContourDrawer import QContourDrawerWidget
import sys

class ContourDrawingController(QContourDrawerWidget):

    def __init__(self, Patient=None, *args, **kwargs):

        self.Patient = Patient

        # myImage = np.random.randint(0, 128, (750, 750, 20), dtype=np.uint8)
        # myImage = np.zeros((512, 512, 20), dtype=np.uint8)
        # form = QContourDrawerWidget(imageData=patient.Image.data)

        super().__init__(imageData=Patient.Image.data,

                         *args, **kwargs)

        for thisROI in Patient.StructureSet.ROIs:
            self.addROI(name=thisROI['ROIName'],
                         color=thisROI['ROIColor'],
                         data=thisROI['DataVolume'])



if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    rootTest = r'C:\Users\MarkSemple\Documents\Sunnybrook Research Institute\Deformable Registration Project\clean sample data 10-19-2016\MRtemp'

    myPatient = PatientObj(rootTest)
    form = ContourDrawingController(Patient=myPatient)
    form.show()
    sys.exit(app.exec_())
