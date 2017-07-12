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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.Exporter = Plan_Writers()
        self.CatheterList = []

    def addCatheter(self, catheter=None):
        print('adding catheter')
        if type(catheter) is CatheterObj:
            if catheter.editable:
                print("still editable")
                return
            self.CatheterList.append(catheter)
            return

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
