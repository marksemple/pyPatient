"""
Catheters
"""

# Built-In Modules
import os
import sys
import datetime

# Third-Party Modules
import numpy as np
import cv2

try:
    import dicom as dicom
except:
    import pydicom as dicom


class Patient_Plan_Set(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.path = r'P:\USERS\PUBLIC\Mark Semple\Dicom Module'
        self.Catheters = [0, 1]
        self.export_as_CHA()

    def export_as_CHA(self):

        # plan_writers()



    def get_header(self, lastName='last',
                   firstName='first',
                   pat_ID='#####',
                   nCaths=0):

        _date_time = datetime.datetime.now().strftime("%m/%d/%y, %H:%M:%S")
        header = """#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Reconstructed Catheters Data File
#  Oncentra Prostate (TM), Vs. 4.2.2.4, Serial 302
#  (C)opyrights MedCom GmbH and Pi-Medical Ltd.
#  All Rights protected
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Catheter Describing Points:  X-, Y-, Z-
#               Image
#   Image:  The number of the Image [0, N-1]
#               with N the total number of Images
#               -1 if the Catheter Describing Point doesn't lie on a Image
#
#  All coordinates according to the Patient-Coordinate-System
#  Defined in Document # 000-00004-01
#  All dimensions are in mm
#  Density values are given in g/cm³
#  Date is given in mm/dd/yy
#  Time is given in hh:mm:ss
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
CHARISMA Software Version
\t\t4.2.2.4
Reconstruction File Version

File creation date and time
\t\t{}

Patient Name
\t\t{}, {}
Patient ID
\t\t{}
Catheter Template Mode
\tTemplate Pos Fixed

Number of Catheters
\t{}\n\n""".format(_date_time,
                   lastName,
                   firstName,
                   pat_ID,
                   len(self.Catheters))

        return header

    def get_catheter_data(self, cathNum, reconLen=130.811511):
        Cath_Data = """\tCatheter {}
\tBegin
\t\tCategory
\t\t\t0
\t\tCathStatus
\t\t\t2
\t\tLocked
\t\t\t4
\t\tName
\t\t\tProGuide 6F Trocar L=240mm Flexitron
\t\tType
\t\t\tFLEXIBLE
\t\tMaterial
\t\t\tPlastic
\t\tDensity
\t\t\t1.400000
\t\tOuter Diameter
\t\t\t1.980000
\t\tInner Diameter
\t\t\t1.480000
\t\tLength
\t\t\t240.000000
\t\tmin Free Length
\t\t\t50.000000
\t\tDistance Tip 1st Source Position
\t\t\t6.000000
\t\tChannel Length
\t\t\t1234.000000
\t\tDistance 1st Reconstructed Point Tip
\t\t\t0.000
\t\tReconstructed Length
\t\t\t{}
\t\tFree Length
\t\t\t{}
\t\tRetraction Length
\t\t\t-6.586000
\t\tDepth
\t\t\t-0.624802
\tEnd\n""".format(cathNum, reconLen, 240 - reconLen)
        return Cath_Data


    def get_catheter_description(self, cathNum):
        Cath_Description = """\tCatheter {}
\tBegin
\t\tTemplate Row
\t\t\t{}
\t\tTemplate Column
\t\t\t{}
\t\tPoint i
\t\tBegin
\t\t\tCoordinates
\t\t\t\t11, 22, 33
\t\t\tType
\t\t\t\t0
\tEnd\n""".format(cathNum, 8, 11)

        return Cath_Description

if __name__ == "__main__":
    myPlan = Patient_Plan_Set()

