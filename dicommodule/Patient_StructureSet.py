# Patient_StructureSet.py


# BUILT-INs
import os

# Third-Party Modules

try:
    import dicom as dicom
except ImportError:
    import pydicom as dicom

from dicommodule.Patient_ROI import (Patient_ROI_Obj, mkNewROIObs_dataset,
                                     mkNewContour,
                                     PatientArray2ContourData,
                                     Vector2PatientArray,
                                     CVContour2VectorArray,
                                     ImageArray2CVContour)


# from dicommodule.Patient_Catheter import CatheterObj


class Patient_StructureSet(object):

    def __init__(self, file=None, dcm=None, imageInfo={},
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ROI_List = []
        self.ROI_byName = {}
        self.setImageInfo(imageInfo)
        self.lineWidth = 1
        self.activeROI = None

        if file is not None:
            try:
                self.setData(filePath=file)
            except AttributeError as ae:
                print("something went wrong reading file: {}".format(ae))
                raise Exception

    def __str__(self):
        return "Contour Structure Set"

    def makePlottable(self):
        for ROI in self.ROI_List:
            ROI.makePlottable()

    def select_ROI(self, name=None, number=None):
        if name is not None:
            self.activeROI = self.ROI_byName[name]
        elif number is not None:
            self.activeROI = self.ROI_List[number]

    def setImageInfo(self, imageInfo):
        self.imageInfo = imageInfo
        for ROI in self.ROI_List:
            self.setImageInfo(imageInfo)

    def setData(self, filePath=None, imageInfo=None):
        if bool(imageInfo):
            self.setImageInfo(imageInfo)

        self.di = di = dicom.read_file(filePath, force=True)
        (self.fileroot, self.SSFile) = os.path.split(filePath)

        for index, contour in enumerate(di.ROIContourSequence):
            try:
                structure = di.StructureSetROISequence[index]
                self.FrameRef_UID = structure.ReferencedFrameOfReferenceUID
            except AttributeError as ae:
                structure = 0
            self.add_ROI(structure=structure, contour=contour,
                         imageInfo=self.imageInfo)

        return True

    # def create_ROI(self, **kwargs):
    #     ROI = Patient_ROI_Obj(**kwargs)

    def get_similar_ROI(self, targetName):
        myROI = None
        for ROI in self.ROI_List:
            if targetName.lower() in ROI.Name.lower():
                myROI = ROI
                break
            elif ROI.Name.lower() in targetName.lower():
                myROI = ROI
                break
        return myROI


    def add_ROI(self, new_ROI=None, **kwargs):
        if new_ROI is None:
            num = len(self.ROI_List)
            new_ROI = Patient_ROI_Obj(number=num, **kwargs)
        print("Adding {} ROI {}".format(new_ROI.Name, new_ROI))
        self.ROI_List.append(new_ROI)
        self.ROI_byName[new_ROI.Name] = new_ROI
        self.select_ROI(name=new_ROI.Name)
        return new_ROI

    def over_write_file(self, outputDir):

        print("over writing ROI file! ")
        pix2pat = self.imageInfo['Pix2Pat']
        ind2loc = self.imageInfo['Ind2Loc']

        for ROI in self.ROI_List:
            print('{}: {}'.format(ROI.Number, ROI.Name))

        ROInames_in_file = []
        for SSROISeq in self.di.StructureSetROISequence:
            ROInames_in_file.append(SSROISeq.ROIName.lower())
        fileROI_set = set(ROInames_in_file)

        PatientROI_set = set(self.ROI_byName.keys())
        patient_not_file = list(PatientROI_set.difference(fileROI_set))
        print('ROIs in pat but not file', patient_not_file)

        for patientName in patient_not_file:
            thisROI = self.ROI_byName[patientName]

            ROIObsSeq = mkNewROIObs_dataset(thisROI)
            self.di.RTROIObservationsSequence.append(ROIObsSeq)

            SSROI = mkNewStructureSetROI_dataset(thisROI,
                                                 self.FrameRef_UID)
            self.di.StructureSetROISequence.append(SSROI)

            ROIContour = mkNewROIContour_dataset(thisROI)
            self.di.ROIContourSequence.append(ROIContour)

        for index, SS in enumerate(self.di.StructureSetROISequence):

            thisROI = self.ROI_byName[SS.ROIName.lower()]

            ContourSequence = mkNewContour_Sequence(thisROI, ind2loc, pix2pat)

            self.di.ROIContourSequence[index].ContourSequence = ContourSequence

        outFile = self.SSFile
        outpath = os.path.join(outputDir, outFile)
        print('saving to {}'.format(outpath))
        dicom.write_file(outpath, self.di)


def mkNewROIContour_dataset(ROI):
    # Create a new DataSet for the RT ROI OBSERVATIONS SEQUENCE

    ROIContour = dicom.dataset.Dataset()
    ROIContour.ROIDisplayColor = [str(x) for x in ROI.Color]
    ROIContour.ReferencedROINumber = ROI.Number
    # ROIContour.ContourSequence = dicom.sequence.Sequence()
    return ROIContour


def mkNewStructureSetROI_dataset(ROI, FrameOfRefUID):
    # Create a new DataSet for the Structure Set ROI Sequence

    SSROI = dicom.dataset.Dataset()
    SSROI.ROINumber = ROI.Number
    SSROI.ReferencedFrameOfReferenceUID = str(FrameOfRefUID)
    SSROI.ROIName = ROI.Name
    SSROI.ROIDescription = ROI.Name
    SSROI.ROIGenerationAlgorithm = 'WARPED_MR'

    return SSROI


def mkNewContour_Sequence(ROI, index2location, pix2patTForm):

    # ROI['DataVolume']
    contourSequence = dicom.sequence.Sequence()
    contourCount = 0

    # iterate through slices of image volume
    for sliceIndex in range(0, ROI.DataVolume.shape[2]):

        compression = ROI.polyCompression
        # else:
        #     compression = 0

        CvContour = ImageArray2CVContour(ROI.DataVolume[:, :, sliceIndex].T,
                                         compression)

        if not bool(CvContour):
            # print("no contours on slice {}".format(sliceIndex))
            continue

        # thisLocation = index2location[sliceIndex]

        # ** how to do multiple contours????
        for thisContour in CvContour:

            VectorArray = CVContour2VectorArray(thisContour, sliceIndex)
            PatientArray = Vector2PatientArray(VectorArray, pix2patTForm)
            ContourData = PatientArray2ContourData(PatientArray)
            contourCount += 1
            DCMContour = mkNewContour(ContourData, contourCount)

            contourSequence.append(DCMContour)

        # print(Contour)

    return contourSequence


if __name__ == "__main__":
    pass
