"""
Catheter Plan File Writers
"""

# Built-In Modules
import os
# import sys
# import datetime
from shutil import copy

# Third-Party Modules
import numpy as np
# import cv2

try:
    import dicom as dicom
except:
    import pydicom as dicom


class Plan_Writers(object):
    def __init__(self, info={}, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.root =
        self.setOutputPath(r'P:\USERS\PUBLIC\Mark Semple\Dicom Module\sample_plan')

    def setInputPath(self, input_path):
        self.inputPath = input_path

    def setOutputPath(self, output_path):
        self.outputPath = output_path

    def setCatheterList(self, catheterlist):
        self.CatheterList = catheterlist

    def import_plan(self, path):
        """ copy an exported-plan from Oncentra into my software """

        self.pathDict = {}
        self.ReadPaths = {}
        self.WritePaths = {}

        if not os.path.exists(self.outputPath):
            os.mkdir(self.outputPath)

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
                copy(fullname, self.outputPath)
                newPath = os.path.join(self.outputPath, filename)
                shortname = filename.split('.')[0]
                self.pathDict[shortname] = newPath

    def execute(self):
        """ Do the heavy-lifting component, calculate data, populate ascii """

        for virtualBool in [True, False]:
            for index, fileWriter in enumerate([self.write_Catheters,
                                                self.write_TemplateLoading,
                                                self.write_Loading]):

                print(fileWriter)
                filepath, content = fileWriter(virtual=virtualBool)

                with open(filepath, 'w') as text_file:
                    text_file.write(content)

    #   _____       _______ _    _  _____
    #  / ____|   /\|__   __| |  | |/ ____|
    # | |       /  \  | |  | |__| | (___
    # | |      / /\ \ | |  |  __  |\___ \
    # | |____ / ____ \| |  | |  | |____) |
    #  \_____/_/    \_\_|  |_|  |_|_____/

    def write_Catheters(self, virtual=False):
        ''' used for both LIVE and VIRTUAL catheters '''

        if virtual:
            filepath = self.pathDict['VirtualCatheters']
        else:
            filepath = self.pathDict['LiveCatheters']

        nCaths = len(self.CatheterList)
        content = ''

        # ~~~~~~~~~~~~~~~~~~~~~~~~ HEADER COPY ~~~~~~~~~~~~~~~~~~~~~~~~
        with open(filepath, 'r') as textfile:
            old_text = textfile.read()
            index = old_text.index('Number of Catheters')
            content += old_text[0:index]

        content += "Number of Catheters\n\t{}\n\n".format(nCaths)

        # ~~~~~~~~~~~~~~~~~~~~~~~~ CATHETER DATA ~~~~~~~~~~~~~~~~~~~~~~~~
        content += "Catheter Data\nBegin\n"

        for ind, catheter in enumerate(self.CatheterList):
            content += "\tCatheter {}\n".format(ind + 1)
            content += getCathData(catheter, virtual=virtual)

        # ~~~~~~~~~~~~~~~~~~~~~~~~ CATHETER DESCRIPTION
        content += "End\nCatheter Describing Points\nBegin\n"

        for ind, catheter in enumerate(self.CatheterList):
            content += "\tCatheter {}\n".format(ind + 1)
            content += getCathDescribingPts(catheter, virtual=virtual)

        content += "End\n"

        return filepath, content

    #  _______ ______ __  __ _____  _            _______ ______
    # |__   __|  ____|  \/  |  __ \| |        /\|__   __|  ____|
    #    | |  | |__  | \  / | |__) | |       /  \  | |  | |__
    #    | |  |  __| | |\/| |  ___/| |      / /\ \ | |  |  __|
    #    | |  | |____| |  | | |    | |____ / ____ \| |  | |____
    #    |_|  |______|_|  |_|_|    |______/_/    \_\_|  |______|

    def write_TemplateLoading(self, virtual=False):
        ''' does __ '''
        if virtual:
            filepath = self.pathDict['VirtualTemplateLoading']
        else:
            filepath = self.pathDict['LiveTemplateLoading']

        nCaths = len(self.CatheterList)
        content = ''

        # ~~~~~~~~~~~~~~~~~~~~~~~~ HEADER COPY ~~~~~~~~~~~~~~~~~~~~~~~~
        with open(filepath, 'r') as textfile:
            old_text = textfile.read()
            index = old_text.index('Number of Catheters')
            content += old_text[0:index]

        content += "Number of Catheters\n\t{}\n\n".format(nCaths)

        # ~~~~~~~~~~~~~~~~~~~~~~~~ LOADING DATA ~~~~~~~~~~~~~~~~~~~~~~~~
        content += "Template Loading Data\nBegin\n"

        for ind, catheter in enumerate(self.CatheterList):
            colLetter = catheter.templateCode[0]
            rowIntegr = catheter.templateCode[1]
            content += "\tCatheter {}\n\tBegin\n".format(ind)
            content += "\t\tTemplate Coordinates\n"
            content += "\t\t\t{} {}\n\tEnd\n".format(colLetter, rowIntegr)

        content += "End\n"

        return filepath, content

    #  _      ____          _____ _____ _   _  _____
    # | |    / __ \   /\   |  __ \_   _| \ | |/ ____|
    # | |   | |  | | /  \  | |  | || | |  \| | |  __
    # | |   | |  | |/ /\ \ | |  | || | | . ` | | |_ |
    # | |___| |__| / ____ \| |__| || |_| |\  | |__| |
    # |______\____/_/    \_\_____/_____|_| \_|\_____|

    def write_Loading(self, virtual=False):
        ''' does __ '''
        if virtual:
            filepath = self.pathDict['VirtualLoading']
        else:
            filepath = self.pathDict['LiveLoading']

        nCaths = len(self.CatheterList)
        content = ''

        # ~~~~~~~~~~~~~~~~~~~~~~~~ HEADER COPY ~~~~~~~~~~~~~~~~~~~~~~~~
        with open(filepath, 'r') as textfile:
            old_text = textfile.read()
            index = old_text.index('Number of Catheters')
            content += old_text[0:index]

        content += "Number of Catheters\n\t{}\n\n".format(nCaths)

        # ~~~~~~~~~~~~~~~~~~~~~~~~ SOURCE STEP ~~~~~~~~~~~~~~~~~~~~~~~~
        content += "Source Step\nBegin\n"

        for ind, catheter in enumerate(self.CatheterList):
            content += "\tCatheter {}\n\tBegin\n".format(ind + 1)
            content += "\t\tActive Source Step\n"
            content += "\t\t\t{:.6f}\n".format(1.0)
            content += "\t\tInactive Source Step\n"
            content += "\t\t\t{:.6f}\n\tEnd\n".format(1.0)

        content += "End\n"

        # ~~~~~~~~~~~~~~~~~~~~~~~~ SOURCE POSITIONS ~~~~~~~~~~~~~~~~~~~~~~~~
        content += "Source Positions\nBegin\n"

        for ind, catheter in enumerate(self.CatheterList):
            content += "\tCatheter {}\n".format(ind + 1)
            content += getSourcePositions(catheter, virtual=virtual)

        content += "End\n"

        return filepath, content


def getCathData(catheterObj, virtual=False):
    """ Populates Catheter Data into Oncetra ASCII format """
    if virtual:
        reconstr_len = 135
        depth = 4
        free_len = 240 - reconstr_len
        retr_len = [0, 0, depth - 6]
    else:
        reconstr_len = catheterObj.length
        depth = catheterObj.depth
        free_len = 240 - reconstr_len
        dp1 = catheterObj.measurements[1, :] - catheterObj.measurements[0, :]
        unitdp1 = dp1 / np.linalg.norm(dp1)
        retr_len = catheterObj.measurements[0, :] + unitdp1 * 6

    CD = "\tBegin\n"
    CD += "\t\tCategory\n\t\t\t0\n"
    CD += "\t\tCathStatus\n\t\t\t2\n"
    CD += "\t\tLocked\n\t\t\t4\n"
    CD += "\t\tName\n\t\t\tProGuide 6F Trocar L=240mm Flexitron\n"
    CD += "\t\tType\n\t\t\tFLEXIBLE\n"
    CD += "\t\tMaterial\n\t\t\tPlastic\n"
    CD += "\t\tDensity\n\t\t\t1.400000\n"
    CD += "\t\tOuter Diameter\n\t\t\t1.980000\n"
    CD += "\t\tInner Diameter\n\t\t\t1.480000\n"
    CD += "\t\tLength\n\t\t\t240.000000\n"
    CD += "\t\tmin Free Length\n\t\t\t50.000000\n"
    CD += "\t\tDistance Tip 1st Source Position\n\t\t\t6.000000\n"
    CD += "\t\tChannel Length\n\t\t\t1234.000000\n"
    CD += "\t\tDistance 1st Reconstructed Point Tip\n\t\t\t0.000\n"
    CD += "\t\tReconstructed Length\n\t\t\t{:.6f}\n".format(reconstr_len)
    CD += "\t\tFree Length\n\t\t\t{:.6f}\n".format(free_len)
    CD += "\t\tRetraction Length\n\t\t\t{:.3f}000\n".format(retr_len[2])
    CD += "\t\tDepth\n\t\t\t{:.6f}\n".format(depth)
    CD += "\tEnd\n"

    return CD


def getCathDescribingPts(catheter, virtual=False):
    if virtual:
        points = catheter.getVirtualPoints()
        nPts = 4

    else:
        points = catheter.getPointList()
        nPts = len(points)

    row, col = catheter.getPointCoordinate()
    CD = "\tBegin\n\t\tTemplate Row\n\t\t\t{}\n".format(row)
    CD += "\t\tTemplate Column\n\t\t\t{}\n".format(col)
    CD += "\t\tNumber of Points\n\t\t\t{}\n".format(nPts)

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

        CD += "\t\tPoint {}\n\t\tBegin\n\t\t\tCoordinates\n".format(index)
        CD += "\t\t\t\t{:.6f} {:.6f} {:.6f}\n".format(point[0],
                                                      point[1],
                                                      point[2])
        CD += "\t\t\tType\n\t\t\t\t{}\n\t\tEnd\n".format(ptType)

    CD += "\tEnd\n"

    return CD


def getSourcePositions(catheter, virtual=False):

    if virtual:
        myPoints = catheter.getVirtualInterpolatedPoints(spacing=1.0)
    else:
        myPoints = catheter.getInterpolatedPoints(spacing=1.0)

    nPts = len(myPoints)
    sourcePosn = "\tBegin\n\t\tNumber of Points\n\t\t\t{}\n\n".format(nPts)

    for index, point in enumerate(myPoints):

        if (index % 3) == 0:
            status = 'Active'
            weight = 1.0
        else:
            status = 'Inactive'
            weight = 0.0

        sourcePosn += "\t\tPoint {}\n\t\tBegin\n".format(index)
        sourcePosn += "\t\t\tCoordinates\n\t\t\t\t"
        sourcePosn += "{:.3f}000 {:.3f}000 {:.3f}000\n".format(point[0],
                                                               point[1],
                                                               point[2])
        sourcePosn += "\t\t\tStatus\n\t\t\t\t{}\n".format(status)
        sourcePosn += "\t\t\tWeight\n\t\t\t\t{:.6f}\n".format(weight)
        sourcePosn += "\t\t\tIndex\n\t\t\t\t{}\n\t\tEnd\n".format(0)

    sourcePosn += "\tEnd\n"

    return sourcePosn


if __name__ == "__main__":

    writer = Plan_Writers()

    from dicommodule.Patient_Catheter import CatheterObj
    cathList = []

    # measurements = []
    # measurements.append(np.array([[37.712040, 59.296495, -0.624802],
    #                               [40.674661, 59.296495, -26.441921],
    #                               [44.429288, 59.262438, -52.932415]]))
    #                               # [44.329114, 58.750000, -117.750000],
    #                               # [44.329114, 58.750000, -131.000000],
    #                               # [44.329114, 58.750000, -240.188489]]))

    # measurements.append(np.array([[95.769797, 43.011019, 3.208849],
    #                               [90.757262, 45.965823, -14.097856],
    #                               [84.681462, 47.232167, -30.138217],
    #                               [82.403037, 48.498511, -45.967521],
    #                               [82.151345, 48.671564, -59.242360]]))
    #                               # [89.329114, 48.750000, -117.750000],
    #                               # [89.329114, 48.750000, -131.000000],
    #                               # [89.329114, 48.750000, -234.024971]]))

    # measurements.append(np.array([[79.329114, 33.750000, 4.000000]]))
    #                               # [79.329114, 33.750000, -117.750000],
    #                               # [79.329114, 33.750000, -131.000000],
    #                               # [79.329114, 33.750000, -236.000000]]))

    # measurements.append(np.array([[40.0, 20.0, 4.0]]))

    # colLetters = ['B', 'f', 'e', 'B']
    # rowInts = [6, 5, 3.5, 2]

    colLetters = ['B', 'b', 'C',
                  'c', 'D', 'd',
                  'E', 'e', 'F',
                  'C', 'C', 'E', 'E']
    rowInts = [3, 2.5, 2,
               2, 2, 2,
               2, 2.5, 3,
               5, 5.5, 5, 5.5]


    for ind, colLetter in enumerate(colLetters):
        newCath = CatheterObj(rowInt=rowInts[ind], colLetter=colLetter)
        # newCath.addMeasurements(measurements[ind])
        # newCath.setTemplatePosition(row=4, col='b')
        cathList.append(newCath)

    writer.setCatheterList(cathList)

    # exported_plan_path = r'C:\Users\Mark\Documents\Sunnybrook\semple'
    exported_plan_path = r'P:\USERS\PUBLIC\Mark Semple\EARTh\tests for importing plans\exported sample plan'

    writer.import_plan(exported_plan_path)

    writer.execute()
