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

        print(ROI['ROIName'], ' --- ', ROI['ROINumber'])

        ROI['vector'][-1].setPen(color=ROI['ROIColor'][0:3],
                                 width=ROI['lineWidth'])
        self.plotWidge.addItem(ROI['vector'][-1])

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
            pros = Patient.StructureSet.ROI_byName['prostate']['DataVolume']
            bounds, size = ARF.findBoundingCuboid(pros)
            self.prostateStart = bounds[0, 2]
            self.prostateStop = bounds[1, 2]
        except:
            print("no ARF")

    # def editor2Patient(self):
    #     # pass
    #     print('\n~~~~~~~~~~~~ Exporting ~~~~~~~~~~~~')
    #     for ROI in self.ROIs:
    #         print(ROI['ROIName'])
    #         if ROI['ROIName'] in self.Patient.StructureSet.ROI_byName.keys():
    #             print("update ROI {}".format(ROI['ROIName']))
    #             # print('color', ROI['ROIColor'])
    #             # for ROI
    #             # update ROI
    #         else:
    #             print("add new ROI {}".format(ROI['ROIName']))
                # add new ROI
                # make new ROI for this one
        # if len(self.Patient.di.RTROIObservationsSequence) == len(self.ROIs):
        # for ROI in self.Patient.StructureSet.ROIs:
        # self.Patient.StructureSet
            # pass
        # return self.Patient

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
    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\WH Fx1 TEST DO NOT USE - Copy\US'
    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\2017-03-09 --- offset in US contours\MR Anonymized'

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Niranjan_Data\MR-US_Clean\MR-US_Clean\TSMRtoUScase_1\US'

    rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\Sample Data\CLEAN - Sample Data 10-05-2016 -- 3 - Copy\US_OUTPUT'

    # rootTest = r'P:\USERS\PUBLIC\Amir K\MR2USRegistartionProject\SunnybrookDataset'

    form = PatientContourDrawer(PatientPath=rootTest)
    form.show()

    sys.exit(app.exec_())
