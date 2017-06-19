""" Integrate Contour Editing with Patient Data """

import sys
import uuid
import numpy as np
import pyqtgraph as pg
try:
    from ContourDrawer import QContourDrawerWidget
    from ContourViewer import countContourSlices
    from Patient import Patient as PatientObj
except ImportError:
    from dicommodule.ContourDrawer import QContourDrawerWidget
    from dicommodule.ContourViewer import countContourSlices
    from dicommodule.Patient import Patient as PatientObj
try:
    from deformableregistration import Affine_Registration_Fcns as ARF
except ImportError:
    print("NO ARF")

# import SimpleITK as sitk


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

        if Patient is not None:
            self.patient2Editor(Patient)

        self.addROIbttn.hide()

    def addROI(self, ROI):
        sliceCount = countContourSlices(ROI['DataVolume'])

        ROI.update({'id': uuid.uuid4(),
                    'vector': [pg.PlotDataItem()],
                    'sliceCount': sliceCount,
                    'polyCompression': 0.7,
                    'hidden': False})

        if 'lineWidth' not in ROI:
            ROI['lineWidth'] = 3

        self.ROIs.append(ROI)
        self.ROIs_byName[ROI['ROIName']] = ROI

        # print(ROI['ROIName'], ' --- ', ROI['ROINumber'])

        ROI['vector'][-1].setPen(color=ROI['ROIColor'][0:3],
                                 width=ROI['lineWidth'])
        self.plotWidge.addItem(ROI['vector'][-1])

        # self.Patient.StructureSet.add_new_ROI(ROI)

        self.add_ROI_to_Table(ROI)
        self.changeROI(ROI_ind=ROI['tableInd'])
        self.hasContourData = True
        self.plotWidge.setFocus()

    def patient2Editor(self, Patient):
        self.Patient = Patient
        self.init_Image(Patient.Image.data)
        for thisROI in Patient.StructureSet.ROIs:
            self.addROI(thisROI)

        try:
            MRProsKey = 'prostate'
            for key in Patient.StructureSet.ROI_byName:
                if 'warped_mr_prostate' in key.lower():
                    MRProsKey = key.lower()
                    break
            pros = Patient.StructureSet.ROI_byName[MRProsKey]['DataVolume']
            bounds, size = ARF.findBoundingCuboid(pros)
            print('prostate bounds', bounds)
            self.prostateStart = bounds[0, :]
            self.prostateStop = bounds[1, :]

        except:
            print("no ARF")

    def viewPick(self, index):

        if index == 0:  # axial
            if self.planeInd == 2:
                return
            self.planeInd = 2

        elif index == 1:  # saggital
            if self.planeInd == 0:
                return
            self.planeInd = 0

        elif index == 2:  # saggital
            if self.planeInd == 1:
                return
            self.planeInd = 1

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


    # rootTest = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\Niranjan Sample Data MR-US_Clean\MR-US_Clean\Mode 1 - MR2USFusion\Sub4 - RTStructure'


    # rootTest = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\Niranjan Sample Data MR-US_Clean\MR-US_Clean\Mode 3 - Mark Deformable Registration\Sub1 - RTStructure'
    # rootTest = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\Niranjan Sample Data MR-US_Clean\MR-US_Clean\Mode 1 - MR2USFusion\Sub1 - RTStructure'
    # rootTest = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\output_MR2USFusion\sample 1'
    # rootTest = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\Input Data\sample 1\MR_anon'
    # rootTest = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\output_MR2USFusion\sample 1 _anon'

    rootTest = r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\MR2US Baseline Dataset 2017\output_plastimatch_Mark\sample 2'

    rootTest =r'P:\USERS\PUBLIC\Mark Semple\MR2USRegistration\Validation Data\AMANI ANONYMIZED DATA\P9\MR'

    form = PatientContourDrawer(PatientPath=rootTest)
    form.show()

    print(form.Patient.StructureSet.ROI_byName.keys())

    sys.exit(app.exec_())
