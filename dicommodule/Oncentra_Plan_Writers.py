"""
Catheter Plan File Writers
"""

# Built-In Modules
import os
import sys
import datetime
from shutil import copy

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

    def setCatheterList(self, catheterlist):
        self.CatheterList = catheterlist

    def import_plan(self, path):
        """ copy an exported-plan from Oncentra into my software """

        self.pathDict = {}
        for dirName, subdirList, fileList in os.walk(path):

            # Validate selection
            if len(fileList) > 13:
                print("Too many file to import")
                return

            elif len(fileList) < 13:
                print("Not enough files to import")
                return

            for filename in fileList:
                fullname = os.path.join(dirName, filename)

                copy(fullname, self.root)

                newPath = os.path.join(self.root, filename)
                self.pathDict[filename.split('.')[0]] = newPath


    def execute(self):

        for index, fileWriter in enumerate([self.write_LiveCatheters,
                                            self.write_LiveTemplateLoading,
                                            self.write_LiveLoading,
                                            self.write_VirtualCatheters,
                                            self.write_VirtualTemplateLoading,
                                            self.write_VirtualLoading]):
                                            # self.write_Settings,
                                            # self.write_Patient,
                                            # self.write_Afterloader,
                                            # self.write_Source,
                                            # self.write_DVHS,
                                            # self.write_Markers]):

            # try:
            filepath, content = fileWriter()
            print(index, filepath)

            with open(filepath, 'w') as text_file:
                text_file.write(content)

            # except Exception as e:
                # print('error: ', e)

    #  _          _____       _______ _    _  _____
    # | |        / ____|   /\|__   __| |  | |/ ____|
    # | |       | |       /  \  | |  | |__| | (___
    # | |       | |      / /\ \ | |  |  __  |\___ \
    # | |____   | |____ / ____ \| |  | |  | |____) |
    # |______|   \_____/_/    \_\_|  |_|  |_|_____/

    def write_LiveCatheters(self):
        """ Construct new LiveCatheters.CHA file with our own data
        Consists of 3 sections: Header, CatheterData, CatheterDescribingPts
        Header we copy directly from the exported file.
        Both CatheterData and CatheterDescribingPts sections are determined
        from measurements, and there is one section for each cathter
        """

        filepath = self.pathDict['LiveCatheters']
        nCaths = len(self.CatheterList)
        content = ''

        # ~~~~~~~~~~~~~~~~~~~~~~~~ HEADER COPY
        with open(filepath, 'r') as textfile:
            old_text = textfile.read()
            index = old_text.index('Number of Catheters')
            content += old_text[0:index]

        content += """Number of Catheters
\t{}

""".format(nCaths)

        # ~~~~~~~~~~~~~~~~~~~~~~~~ CATHETER DATA
        content += """Catheter Data
Begin
"""

        for ind, catheter in enumerate(self.CatheterList):
            content += """\tCatheter {}
""".format(ind + 1)
            content += self.getCathData(catheter)

        # ~~~~~~~~~~~~~~~~~~~~~~~~ CATHETER DESCRIPTION
        content += """End
Catheter Describing Points
Begin
"""
        for ind, catheter in enumerate(self.CatheterList):
            content += """\tCatheter {}
""".format(ind + 1)
            content += self.getCathDescribingPts(catheter)

        return filepath, content

    # _        _______ ______ __  __ _____  _            _______ ______
    # | |      |__   __|  ____|  \/  |  __ \| |        /\|__   __|  ____|
    # | |         | |  | |__  | \  / | |__) | |       /  \  | |  | |__
    # | |         | |  |  __| | |\/| |  ___/| |      / /\ \ | |  |  __|
    # | |____     | |  | |____| |  | | |    | |____ / ____ \| |  | |____
    # |______|    |_|  |______|_|  |_|_|    |______/_/    \_\_|  |______|

    def write_LiveTemplateLoading(self):

        filepath = self.pathDict['LiveTemplateLoading']
        nCaths = len(self.CatheterList)
        content = ''

        # ~~~~~~~~~~~~~~~~~~~~~~~~ HEADER COPY
        with open(filepath, 'r') as textfile:
            old_text = textfile.read()
            index = old_text.index('Number of Catheters')
            content += old_text[0:index]

        content += """Number of Catheters
\t{}

""".format(nCaths)

        # ~~~~~~~~~~~~~~~~~~~~~~~~ LOADING DATA
        content += """Template Loading Data
Begin
"""

        for ind, catheter in enumerate(self.CatheterList):
            content += """\tCatheter {}
\tBegin
\t\tTemplate Coordinates
\t\t\t{} {}
\tEnd
""".format(ind, 'B', '2.5')
        # format(catheter.template_code())

        content += """End
"""

        # Template Loading Data
        # Begin
        # """.format(self._date, self._time, self.nCatheters)

        #         for ind in range(0, self.nCatheters):
        #             content += """\tCatheter {}
        # \tBegin
        # \t\tTemplate Coordinates
        # \t\t\t{} {}
        # \tEnd
        # """.format(ind, 'A', '0')

        return filepath, content

    # _         _      ____          _____ _____ _   _  _____
    # | |       | |    / __ \   /\   |  __ \_   _| \ | |/ ____|
    # | |       | |   | |  | | /  \  | |  | || | |  \| | |  __
    # | |       | |   | |  | |/ /\ \ | |  | || | | . ` | | |_ |
    # | |____   | |___| |__| / ____ \| |__| || |_| |\  | |__| |
    # |______|  |______\____/_/    \_\_____/_____|_| \_|\_____|

    def write_LiveLoading(self):
        filepath = os.path.join(self.root, 'LiveLoading.cha')
        content = ''
        return filepath, content

    # __      __   _____       _______ _    _  _____
    # \ \    / /  / ____|   /\|__   __| |  | |/ ____|
    #  \ \  / /  | |       /  \  | |  | |__| | (___
    #   \ \/ /   | |      / /\ \ | |  |  __  |\___ \
    #    \  /    | |____ / ____ \| |  | |  | |____) |
    #     \/      \_____/_/    \_\_|  |_|  |_|_____/

    def write_VirtualCatheters(self):
        """ Construct new VirtualCatheters.CHA file with our own data
        Consists of 3 sections: Header, CatheterData, CatheterDescribingPts
        Header we copy directly from the exported file.
        Both CatheterData and CatheterDescribingPts sections are determined
        from measurements, and there is one section for each cathter
        """

        filepath = self.pathDict['VirtualCatheters']
        nCaths = len(self.CatheterList)
        content = ''

        # ~~~~~~~~~~~~~~~~~~~~~~~~ HEADER COPY
        with open(filepath, 'r') as textfile:
            old_text = textfile.read()
            index = old_text.index('Number of Catheters')
            content += old_text[0:index]

        content += """Number of Catheters
\t{}

""".format(nCaths)

        # ~~~~~~~~~~~~~~~~~~~~~~~~ CATHETER DATA
        content += """Catheter Data
Begin
"""

        for ind, catheter in enumerate(self.CatheterList):
            content += """\tCatheter {}
""".format(ind + 1)
            content += self.getCathData(catheter, virtual=True)

        # ~~~~~~~~~~~~~~~~~~~~~~~~ CATHETER DESCRIPTION
        content += """End
Catheter Describing Points
Begin
"""
        for ind, catheter in enumerate(self.CatheterList):
            content += """\tCatheter {}
""".format(ind + 1)
            content += self.getCathDescribingPts(catheter, virtual=True)

        return filepath, content
    # __      __  _______ ______ __  __ _____  _            _______ ______
    # \ \    / / |__   __|  ____|  \/  |  __ \| |        /\|__   __|  ____|
    #  \ \  / /     | |  | |__  | \  / | |__) | |       /  \  | |  | |__
    #   \ \/ /      | |  |  __| | |\/| |  ___/| |      / /\ \ | |  |  __|
    #    \  /       | |  | |____| |  | | |    | |____ / ____ \| |  | |____
    #     \/        |_|  |______|_|  |_|_|    |______/_/    \_\_|  |______|

    def write_VirtualTemplateLoading(self):
        filepath = os.path.join(self.root, 'VirtualTemplateLoading.cha')
        content = ''
        return filepath, content

    # __      __   _      ____          _____ _____ _   _  _____
    # \ \    / /  | |    / __ \   /\   |  __ \_   _| \ | |/ ____|
    #  \ \  / /   | |   | |  | | /  \  | |  | || | |  \| | |  __
    #   \ \/ /    | |   | |  | |/ /\ \ | |  | || | | . ` | | |_ |
    #    \  /     | |___| |__| / ____ \| |__| || |_| |\  | |__| |
    #     \/      |______\____/_/    \_\_____/_____|_| \_|\_____|

    def write_VirtualLoading(self):
        filepath = os.path.join(self.root, 'VirtualLoading.cha')
        content = ''
        return filepath, content


    def getCathData(self, catheterObj, virtual=False):

        if virtual:
            reconstr_len = 135
            depth = 4
            free_len = 240 - reconstr_len
            retr_len = depth - 6
        else:
            reconstr_len = catheterObj.calculateLength()
            depth = 4
            free_len = 240 - reconstr_len
            retr_len = depth - 6

        Cath_Data = """\tBegin
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
\t\t\t{:.6f}
\t\tFree Length
\t\t\t{:.6f}
\t\tRetraction Length
\t\t\t{:.6f}
\t\tDepth
\t\t\t{:.6f}
\tEnd\n""".format(reconstr_len, free_len, retr_len, depth)
        return Cath_Data

    def getCathDescribingPts(self, catheter, virtual=False):
        if virtual:
            points = catheter.getVirtualPoints()
            nPts = 4

        else:
            points = catheter.pointList
            nPts = len(points)

        row, col = catheter.getPointCoordinate()

        Cath_Description = """\tBegin
\t\tTemplate Row
\t\t\t{}
\t\tTemplate Column
\t\t\t{}
\t\tNumber of Points
\t\t\t{}
""".format(row, col, nPts)

        for index, point in enumerate(points):

            # Point Type: 0, 2, 3, 4
            if (index + 1) <= (len(points) - 3):
                ptType = 0
            elif (index + 1) == (len(points) - 2):
                ptType = 2
            elif (index + 1) == (len(points) - 1):
                ptType = 3
            elif (index + 1) == len(points):
                ptType = 4

            Cath_Description += """\t\tPoint {}
\t\tBegin
\t\t\tCoordinates
\t\t\t\t{:.6f}, {:.6f}, {:.6f}
\t\t\tType
\t\t\t\t{}
\t\tEnd
""".format(index, point[0], point[1], point[2], ptType)

        Cath_Description += """\tEnd
"""
        return Cath_Description


if __name__ == "__main__":
    writer = Plan_Writers()

    from dicommodule.Patient_Catheter import CatheterObj
    cathList = []

    for i in range(0, 5):
        newCath = CatheterObj()
        newCath.addMeasurements(np.random.random((5, 3)))
        newCath.setTemplatePosition(row=4, col='b')
        cathList.append(newCath)

    writer.setCatheterList(cathList)

    exported_plan_path = r'P:\USERS\PUBLIC\Mark Semple\EARTh\tests for importing plans\exported sample plan'

    writer.import_plan(exported_plan_path)

    writer.execute()
