"""
Patient Plan Object (for brachyTherapy)
Contains list of <CatheterObjs>
"""

# Built-In Modules

# Third-Party Modules
import numpy as np
# import cv2

# Local Modules
from dicommodule.Oncentra_Plan_Writers import Plan_Writers
from dicommodule.Patient_Catheter import CatheterObj


class Patient_Plan(object):

    def __init__(self, patient=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.Exporter = Plan_Writers()
        self.CatheterList = []
        self.activeCath = None

        self.Pat2Cath = np.eye(4)

        if patient is not None:
            self.setPatient(patient)

    def setPatient(self, patient):
        self.patient = patient
        origin = patient.Image.info['Pix2Pat'].dot(np.array([0, 0, 0, 1]))
        self.Pat2Cath[0:2, 3] = -origin[0:2]
        print("PAT 2 CATH {}".format(self.Pat2Cath))

    def addCatheter(self, catheter=None, coords=None):
        print("cathType {}".format(type(catheter)))

        if catheter is None:
            row, col = coords
            catheter = CatheterObj(rowNumber=float(row), colLetter=col)
            catheter.makePlottable()

        if type(catheter) is tuple:
            catheter = catheter[0]

        if type(catheter) is CatheterObj:
            catheter.setParent(self)

            self.CatheterList.append(catheter)
            print('adding catheter {} {}'.format(len(self.CatheterList),
                                                 self.CatheterList))

        self.activeCath = catheter

        return catheter

    def setActiveCath(self, UID=None, index=None, coords=None):
        # Activate a catheter by either UID, index in list, or its coords

        if len(self.catheterList) == 0:
            print("No Catheters to Activate!")
            return

        if UID is not None:
            for cath in self.catheterList:
                if UID == cath.uid:
                    self.activeCath = cath
                    return cath

        if index is not None:
            if len(self.catheterList) >= (index + 1):
                self.activeCath = self.catheterList[index]
                return cath

        if coords is not None:
            print("FILL IN HERE")
            pass


    def removeCatheter(self, catheter=None):
        targetUID = catheter.uid
        for ind, cath in enumerate(self.CatheterList):
            if cath.uid == targetUID:
                print("a match! catheter being removed")
                del(self.CatheterList[ind])

        N = len(self.CatheterList)
        print("There are {} catheters remaining".format(N))

    def export_as_CHA(self, sourcePath, destPath):
        # self.plan_exporter. DO THING ()
        # sort catheters by bottom row, left to right, then up
        #
        pass


if __name__ == "__main__":
    myPlan = Patient_Plan()
    myCath = CatheterObj()
    myCath.setTemplatePosition_byCode(row=4, col='B')
    myCath.addDescribingPoint([44, 39, -40])
    myCath.finishMeasuring()
    myPlan.addCatheter(myCath)

    print(myPlan.CatheterList[0].measurements)
