"""
Catheter Plan File Writers
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


class Plan_Writers(object):
    def __init__(self, info={}, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # patient name
        self.patientName = 'semple'
        self.patientID = '#####ID'
        self.nCatheters = 2
        # save location
        self.root = r'P:\USERS\PUBLIC\Mark Semple\Dicom Module\sample_plan'

        self._date = datetime.datetime.now().strftime("%m/%d/%y")
        self._time = datetime.datetime.now().strftime("%H:%M:%S")

    def execute(self):

        for index, fileWriter in enumerate([self.write_PLN_file,
                                            self.write_Settings,
                                            self.write_Patient,
                                            self.write_Afterloader,
                                            self.write_LiveCatheters,
                                            self.write_LiveTemplateLoading,
                                            self.write_LiveLoading,
                                            self.write_VirtualCatheters,
                                            self.write_VirtualTemplateLoading,
                                            self.write_VirtualLoading,
                                            self.write_Source,
                                            self.write_DVHS,
                                            self.write_Markers]):

            try:
                filepath, content = fileWriter()
                print(index, filepath)

                with open(filepath, 'w') as text_file:
                    text_file.write(content)

            except Exception as e:
                print('error: ', e)

    def write_PLN_file(self):
        filename = '{}.pln'.format(self.patientName)
        filepath = os.path.join(self.root, filename)
        content = """#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Treatment Plan Link File
#  Oncentra Prostate (TM), Vs. 4.2.2.4, Serial 302
#  (C)opyrights MedCom GmbH and Pi-Medical Ltd.
#  All Rights protected
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++

Settings
Patient
Afterloader
VirtualCatheters
LiveCatheters
VirtualTemplateLoading
LiveTemplateLoading
Source
VirtualLoading
LiveLoading
DVHS
Markers

"""
        return filepath, content

    def write_Settings(self):
        filepath = os.path.join(self.root, 'Settings.cha')
        return filepath, ''

    def write_Patient(self):
        filepath = os.path.join(self.root, 'Patient.cha')
        content = """#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Patient Data File
#  Oncentra Prostate (TM), Vs. 4.2.2.4, Serial 302
#  (C)opyrights MedCom GmbH and Pi-Medical Ltd.
#  All Rights protected
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Date is given in mm/dd/yy
#  Time is given in hh:mm:ss
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
CHARISMA Software Version
\t\t4.2.2.4
Patient File Version
\t\t4.2.2.4
File creation date and time
\t\t{}, {}

Patient Data
Begin
\tName
\t\t{} {}
\tID
\t\t{}
\tBirthdate

End""".format(self._date, self._time,
              self.patientName,
              self.patientName,
              self.patientID)
        return filepath, content

    def write_Afterloader(self):
        filepath = os.path.join(self.root, 'Afterloader.cha')
        content = """#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Afterloader Data File
#  Oncentra Prostate (TM), Vs. 4.2.2.4, Serial 302
#  (C)opyrights MedCom GmbH and Pi-Medical Ltd.
#  All Rights protected
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  #  All dimensions are in mm
#  Date is given in mm/dd/yy
#  Time is given in hh:mm:ss
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
CHARISMA Software Version
\t\t4.2.2.4
Afterloader File Version
\t\t4.1.0.0
File creation date and time
\t\t{}, {}

Afterloader Data
Begin
\tAfterloader Type File Data
\tBegin
\t\tFile Name
\t\t\tAfterloader_Type_File.cha
\t\tFrom Date
\t\t\t02/25/2011
\t\tFrom Time
\t\t\t13:00:00
\tEnd
\tAfterloader Type File Content
\tBegin
\t\tType
\t\t\tFlexitron-HDR
\t\tModel
\t\t\tFlexitron
\t\tManufacturer
\t\t\tNucletron B.V.
\t\tSystem Type
\t\t\tFlexitron-HDR
\t\tName
\t\t\tFlexitron HDR
\t\tSerial No
\t\t\tTo be specified
\t\tFirmware Software Version

\t\tNumber of Sources
\t\t\t1
\t\tNumber of Hardware Channels
\t\t\t40
\t\tNumber of Software Channels
\t\t\t40
\t\tDetection of Catheter Tip
\t\t\t0
\t\tName for Channel Length
\t\t\tSelector
\t\tmin Channel Length
\t\t\t1001.000000
\t\tmax Channel Length
\t\t\t1400.000000
\t\tSource Movement Type
\t\t\tSTEPWISE
\t\tSource Stepping Data
\t\tBegin
\t\t\tMethod
\t\t\t\tDISCRETE
\t\t\tDISCRETE
\t\t\tBegin
\t\t\t\tNumber of Possible Step Sizes
\t\t\t\t\t1
\t\t\t\tStep 0
\t\t\t\t\t1.000000
\t\t\tEnd
\t\t\tCONTINUOUSLY
\t\t\tBegin
\t\t\t\tmin Step
\t\t\t\t\t0.500000
\t\t\t\tmax Step
\t\t\t\t\t15.000000
\t\t\tEnd
\t\t\tDefault Step
\t\t\t\t1.000000
\t\tEnd
\t\tCommon Stepping for all Channels
\t\t\tYES
\t\tDrive Type
\t\t\tPUSHING
\t\tmax Number of Steps per Channel
\t\t\t400
\t\tTime Resolution
\t\t\t0.10000
\t\tmax Time
\t\t\t999.900024
\tEnd
End""".format(self._date, self._time)

        return filepath, content

    def write_LiveCatheters(self):
        filepath = os.path.join(self.root, 'LiveCatheters.cha')
        content = ''

        # text_file.write("Catheter Data\nBegin\n")
        for ind, cath in enumerate(self.Catheters):

            cath_data += self.get_catheter_data(cathNum=ind + 1)
            cath_pts += self.get_catheter_description(cathNum=ind + 1)

        return filepath, content

    def write_LiveTemplateLoading(self):
        filepath = os.path.join(self.root, 'LiveTemplateLoading.cha')
        content = """#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Template Loading Data File
#  Oncentra Prostate (TM), Vs. 4.2.2.4, Serial 302
#  (C)opyrights MedCom GmbH and Pi-Medical Ltd.
#  All Rights protected
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Catheter Template Data:
#       Template Coordinates
#  Template Coordinates:
#       X, Y
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Special case for Template Coordinates:
#       -1 -1 if the catheter has no corresponding
#           template position
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Notation of Teplate Dimensions and relation to the Teplate Axes
#       Width is the X-axis
#       Length is the Y-Axis
#       Thickness is the Z-Axis
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Notation of Columns and Rows and realtion to the Teplate Axes
#       Column is parallel to the Y-Axis and
#       the Number of Columns defines the number of holes in the X-axis
#       Row is parallel to the X-Axis and
#       the Number of Rows defines the number of holes in the Y-axis
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Following numbering types are supported
#       alphabetic: A,a,B,b,C,c,D,d,E,e,F or A,B,C,..Z
#       numeric:    0,1,2,3,4,...N or 0,0.5,1.0,1.5,2.0,..
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Date is given in mm/dd/yyyy
#  Time is given in hh:mm:ss
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
CHARISMA Software Version
\t\t4.2.2.4
Life TemplateLoading File Version

File creation date and time
\t\t{}, {}

Template Type File Data
Begin
\tType
\t\t
\tFile Name
\t\tTemplate_Type_File.cha
\tFrom Date
\t\t11/13/2015
\tFrom Time
\t\t15:26:00
End

Number of Catheters
\t{}

Template Loading Data
Begin
""".format(self._date, self._time, self.nCatheters)

        for ind in range(0, self.nCatheters):
            content += """\tCatheter {}
\tBegin
\t\tTemplate Coordinates
\t\t\t{} {}
\tEnd
""".format(ind, 'A', '0')

        return filepath, content

    def write_LiveLoading(self):
        filepath = os.path.join(self.root, 'LiveLoading.cha')
        content = ''
        return filepath, content

    def write_VirtualCatheters(self):
        filepath = os.path.join(self.root, 'VirtualCatheters.cha')
        content = """#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
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
Placement File Version
\t\t
File creation date and time
\t\t{}, {}

Patient Name
\t\t{}, {}
Patient ID
\t\t{}
Catheter Template Mode
\tTemplate Pos Fixed

Number of Catheters
\t{}
""".format('a','b','c','d','e','f')

        return filepath, content

    def write_VirtualTemplateLoading(self):
        filepath = os.path.join(self.root, 'VirtualTemplateLoading.cha')
        content = ''
        return filepath, content

    def write_VirtualLoading(self):
        filepath = os.path.join(self.root, 'VirtualLoading.cha')
        content = ''
        return filepath, content

    def write_Source(self):
        filepath = os.path.join(self.root, 'Source.cha')
        content = ''
        return filepath, content

    def write_DVHS(self):
        filepath = os.path.join(self.root, 'DVHS.cha')
        content = """#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  DVHs Data File
#  Oncentra Prostate (TM), Vs. 4.2.2.4, Serial 302
#  (C)opyrights MedCom GmbH and Pi-Medical Ltd.
#  All Rights protected
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Here only the Differencial Dose Volume Histaograms are stored
#  All doses are in Gy
#  All coordinates according to the World-DICOM-Coordinate-System
#  All dimensions are in mm
#  Date is given in mm/dd/yyyy
#  Time is given in hh:mm:ss
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
CHARISMA Software Version
\t\t4.2.2.4
DVHS File Version
\t\t4.2.2. 4
File creation date and time
\t\t{}, {}

Patient Name
\t\t{}, {}
Patient ID
\t\t{}
Number of DVH ROIS
\t0

DVH Data
Begin
\tType
\t\tCUMULATIVE
\tNormalisation Dose Value
\t\t1500.000000
\tDose Units
\t\tRELATIVE
\tDose Type
\t\tPHYSICAL
\tDose Scaling
\t\t1.00
\tVolume Units
\t\tPERCENT
End
""".format(self._date, self._time,
           self.patientName,
           self.patientName,
           self.patientID)
        return filepath, content

    def write_Markers(self):
        filepath = os.path.join(self.root, 'Markers.cha')
        content = """#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Marker Data File
#  Oncentra Prostate (TM), Vs. 4.2.2.4, Serial 302
#  (C)opyrights MedCom GmbH and Pi-Medical Ltd.
#  All Rights protected
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  All coordinates according to the World-DICOM-Coordinate-System
#  All dimensions are in mm
#  Date is given in mm/dd/yyyy
#  Time is given in hh:mm:ss
#  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
CHARISMA Software Version
\t\t4.2.2.4
Marker File Version
\t\t4.2.2. 4
File creation date and time
\t\t{}, {}

Patient Name
\t\t{}, {}
Patient ID
\t\t{}
Number of Markers
\t0
Marker Data
Begin
End
""".format(self._date, self._time,
           self.patientName,
           self.patientName,
           self.patientID)
        return filepath, content


if __name__ == "__main__":
    writer = Plan_Writers()
    writer.execute()
