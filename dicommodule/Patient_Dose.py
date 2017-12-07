# Patient_Dose.py
"""
    Dose Object
"""

import os
import sys
import numpy as np
try:
    import dicom as dicom
except ImportError:
    import pydicom as dicom


class Patient_Dose(object):

    def __init__(self, file=None):
        super().__init__()

        self.info = {}

        if file is not None:
            self.setData(filePath=file)

    def setData(self, filePath):
        # pass
        # if type(filePath) is not str:
            # raise
        # print('got file {}'.format(filePath))
        di = dicom.read_file(filePath)
        self.DoseGrid = di.pixel_array * di.DoseGridScaling
        self.info['ImagePositionPatient'] = di.ImagePositionPatient
        self.info['ImageOrientationPatient'] = di.ImageOrientationPatient
        self.info['PixelSpacing'] = di.PixelSpacing
        self.info['DoseUnits'] = di.DoseUnits

    def thresholdDose(self):
        Image = self.DoseGrid


if __name__ == "__main__":

    from dicommodule.ContourViewer import QContourViewerWidget
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    testFilePath = r'P:\USERS\PUBLIC\Ananth\Research Projects\1 - CLINICAL TRIALS\PRIVATE\Trials\Active\MOPP Phase I\ACTIVE DATA\MOPP Trial\Data\0002\50324b43\DO001.dcm'

    DO = Patient_Dose(file=testFilePath)

    myIm = np.swapaxes(DO.DoseGrid, 0, 2)
    myIm = np.swapaxes(myIm, 0, 1)

    binIm = myIm.copy()

    thresh = 218
    binIm[myIm > thresh] = 255
    binIm[myIm <= thresh] = 0

    form = QContourViewerWidget(imageData=binIm.astype(np.uint8))

    form.show()
    sys.exit(app.exec_())
