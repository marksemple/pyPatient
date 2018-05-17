# ROI_Manipulations

import os
import numpy as np
import scipy.ndimage as spnd
from cv2 import (resize, INTER_LINEAR, GaussianBlur, findContours,
                 boundingRect, RETR_LIST, CHAIN_APPROX_SIMPLE, )
import cv2
import nrrd


def mirror_ROI_about_centroid_of_other(ROI_to_go, Ref_ROI, ax):
    """ NP Arrays must be same size
    find centroid of ref roi (eg. prostate)
    find bounding box of roi to go (eg. dil)
    mirror bounding box about an axis
    Flip ROI to go, place into new space
    return NP Array
    """

    mirroredROI = np.zeros(ROI_to_go.shape)
    ref_centroid = get_centroid(Ref_ROI)
    bb, rect_size = findBoundingCuboid(ROI_to_go)

    littleROI = ROI_to_go[bb[0, 0]:bb[1, 0],
                          bb[0, 1]:bb[1, 1],
                          bb[0, 2]:bb[1, 2]]
    newROI = np.flip(littleROI, ax)

    nbb = bb.copy()
    nbb[:, ax] = 2 * ref_centroid[ax] - bb[:, ax]
    nbb.sort(axis=0)  # axes must be in order: lowest-to-highest

    mirroredROI[nbb[0, 0]:nbb[1, 0],
                nbb[0, 1]:nbb[1, 1],
                nbb[0, 2]:nbb[1, 2]] = newROI

    mirroredROI += Ref_ROI
    mirroredROI[mirroredROI <= 1] = 0
    mirroredROI[mirroredROI > 1] = 1


    return mirroredROI


def get_centroid(imVol):
    return np.asarray(spnd.measurements.center_of_mass(imVol))


# def findBoundingCuboid(imVol):
#     """ bounds: [[x0, y0, z0],
#                  [x1, y1, z1]] """

#     rows, cols, slices = imVol.shape
#     imVol = np.swapaxes(imVol, 0, 2)
#     x, y, w, h = (imVol.shape[1], imVol.shape[2], 0, 0)
#     start, end = (0, slices - 1)
#     lastSliceEmpty = True

#     for index, thisSlice in enumerate(imVol):

#         im = thisSlice.astype(np.uint8).copy()
#         outim, contours, hierarcy = findContours(im, RETR_LIST,
#                                                  CHAIN_APPROX_SIMPLE)

#         if len(contours) > 0 and lastSliceEmpty is True:
#             start = index

#         if len(contours) == 0 and lastSliceEmpty is False:
#             end = index - 1

#         for cnt in contours:
#             # lastSliceEmpty = False
#             x0, y0, w0, h0 = boundingRect(cnt)
#             x = x0 if (x0 < x) else x
#             y = y0 if (y0 < y) else y
#             w = (x0 + w0) if ((x0 + w0) > w) else w
#             h = (y0 + h0) if ((y0 + h0) > h) else h

#         lastSliceEmpty = True if len(contours) == 0 else False

#     bounds = np.array([[x, y, start], [w + 1, h + 1, end + 1]])
#     rectSize = np.array([w - x, h - y, end - start])
#     # print(out)

#     return bounds, rectSize


def findBoundingCuboid(imVol):
    rows, cols, slices = imVol.shape
    imVol = np.swapaxes(imVol, 0, 2)
    x, y, w, h = (imVol.shape[1], imVol.shape[2], 0, 0)
    # start, end = (0, slices - 1)
    # lastSliceEmpty = True

    start = find_first_occupied_slice(imVol)
    end = slices - find_first_occupied_slice(np.flip(imVol, axis=0)) + 1
    lilImVol = imVol[start:end, :, :]

    for index, thisSlice in enumerate(lilImVol):

        im = thisSlice.astype(np.uint8).copy()
        outim, contours, hierarcy = findContours(im, RETR_LIST,
                                                 CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            # lastSliceEmpty = False
            x0, y0, w0, h0 = boundingRect(cnt)
            x = x0 if (x0 < x) else x
            y = y0 if (y0 < y) else y
            w = (x0 + w0) if ((x0 + w0) > w) else w
            h = (y0 + h0) if ((y0 + h0) > h) else h

    bounds = np.array([[x, y, start], [w + 1, h + 1, end + 1]])
    rectSize = np.array([w - x, h - y, end - start])
    # print(out)

    return bounds, rectSize


def find_first_occupied_slice(imVol):
    # assuming to search along first dimension
    # return index of first slice with stuff on it

    for index, thisSlice in enumerate(imVol):

        im = thisSlice.astype(np.uint8).copy()
        outim, contours, hierarchy = findContours(im, RETR_LIST,
                                                  CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            return index

    return 0  # ??
    # return False

if __name__ == "__main__":

    from dicommodule.Patient import Patient

    ppath = r'P:\USERS\PUBLIC\Mark Semple\radiomics\code\sample_files\MR'

    myPatient = Patient(patientPath=ppath)

    prostate = myPatient.StructureSet.ROI_byName['prostate'].DataVolume
    dil = myPatient.StructureSet.ROI_byName['dil'].DataVolume

    mirrorROI = mirror_ROI_about_centroid_of_other(ROI_to_go=dil,
                                                   Ref_ROI=prostate,
                                                   ax=0)


    newROI = (mirrorROI + dil)

    spacings = [myPatient.Image.info['PixelSpacing'][1],
                myPatient.Image.info['PixelSpacing'][0],
                myPatient.Image.info['SliceSpacing']]

    Opts = {'spacings': spacings}

    rootpath = r'P:\USERS\PUBLIC\Mark Semple\radiomics\code\sample_files'
    filename = os.path.join(rootpath, 'control_mask.nrrd')
    nrrd.write(filename=filename, data=mirrorROI,
               options=Opts)

    # cv2.imshow('newROI', np.swapaxes(newROI[:, :, 7], 0, 1))
    # cv2.waitKey(0)
    # save as nrrd here, fine
    # myPatient.addROI()



    # COM_prostate = get_centroid(prostate)
    # COM_dil = get_centroid(dil)

    # diff = COM_prostate - COM_dil

    # print(COM_prostate[0] + diff[0])

