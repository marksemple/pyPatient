"""
Catheters
"""

# Built-In Modules
# import os
# import sys
# import datetime

# Third-Party Modules
# import numpy as np
# import cv2

# Local Modules
from dicommodule.Oncentra_Plan_Writers import Plan_Writers
from dicommodule.Patient_Catheter import CatheterObj


class Patient_Plan(object):

    def __init__(self, patient=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.Exporter = Plan_Writers()
        self.CatheterList = []
        if patient is not None:
            self.setPatient(patient)

    def setPatient(self, patient):
        self.patient = patient

    def addCatheter(self, catheter=None, coords=None):
        print("cathType {}".format(type(catheter)))

        if catheter is None:
            row, col = coords
            catheter = CatheterObj(rowInt=float(row), colLetter=col)
            catheter.makePlottable()

        if type(catheter) is tuple:
            catheter = catheter[0]

        if type(catheter) is CatheterObj:
            catheter.setParent(self)

            self.CatheterList.append(catheter)
            print('adding catheter {} {}'.format(len(self.CatheterList),
                                                 self.CatheterList))

        return catheter

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
        pass


if __name__ == "__main__":
    myPlan = Patient_Plan()
    myCath = CatheterObj()
    myCath.setTemplatePosition_byCode(row=4, col='B')
    myCath.addDescribingPoint([44, 39, -40])
    myCath.finishMeasuring()
    myPlan.addCatheter(myCath)

    print(myPlan.CatheterList[0].measurements)
