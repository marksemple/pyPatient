# RegionOfInterest.py
"""

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


class Patient_ROI(object):

    name = 'ROI'
    color = (255, 255, 255)

    def __init__(self, file=None, dcm=None, *args, **kwargs):

        if file is not None:
            self.read_file(file)

        # Has:
        # filePath
        # modality - RTSTRUCT
        # ROI Color
        # ROI Number
        # ROI Name
        # contour data
        # referenced frame of reference
        # contour image sequence
        #
        pass

    def read_file(self, filepath):
        print(filepath)
        di = dicom.read_file(filepath)
        print(di)
        pass

    def write_file(self, filepath):
        pass

    def vector2raster(self):
        pass

    def raster2vector(self):
        pass



if __name__ == "__main__":
    pass
    # myROI = PatientROI(file=)
