"""
    RegionOfInterest

"""

# Built-In Modules
import os
import sys

# Third-Party Modules
import numpy as np
import cv2
try:
    import dicom as dicom
except:
    import pydicom as dicom


class Patient_ROI_Set(object):

    Name = 'ROI'
    Color = (230, 230, 20)
    Contour_Sequences = []

    def __init__(self, file=None, dcm=None, *args, **kwargs):

        if file is not None:
            if self.read_file(file):
                print('got data from file!')
                return
            else:
                print("something went wrong reading file")
                return

        # Has:
        # ROI OBJECTS
        # filePath
        # modality - RTSTRUCT
        # ROI Color
        # ROI Number
        # ROI Name
        # Frame of Reference
        # contour data
        # referenced frame of reference
        # contour image sequence
        pass


    def __str__(self):
        return "Contour Object"


    def read_file(self, filepath):
        """ """
        # print(filepath)
        di = dicom.read_file(filepath)

        for ContourSeq in di.ROIContourSequence:
            self.add_ROI(ContourSeq)
        return True

    def write_file(self, filepath):
        """ """
        pass

    def vector2raster(self):
        """ """
        pass

    def raster2vector(self):
        """ """
        pass

    def add_ROI(self, ContourSequence, *args, **kwargs):
        pass
        # self.Contour_Sequences.append(ROI_Object(*args, **kwargs))



# class ROI_Object(object):
#     """ per structure_set_ROI_sequence """
#     def __init__(self, ContourSequence=None, *args, **kwargs):
#         pass

#         # GET Polygon / Raster data
#         # Transform to Mask!


if __name__ == "__main__":
    # pass
    myROI = Patient_ROI_Set(file=r'P:\USERS\PUBLIC\Mark Semple\EM Navigation\Practice DICOM Sets\EM test\2016-07__Studies (as will appear)\YU, YAN_3138146_RTst_2016-07-14_121417_mrgb1F_EMTEST_n1__00000\2.16.840.1.114362.1.6.5.4.15706.9994565197.426983378.1037.53.dcm')
