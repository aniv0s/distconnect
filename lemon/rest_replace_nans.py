__author__ = 'oligschlager'

from surfproc import nan_replace_interpolation
import nibabel as nib
import numpy as np
import os
import os.path

'''directories'''
inputDir = "/scr/liberia1/data/lemon/lemon_rest_surf"
fsDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"
outputDir = "/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands"

subList = [sub for sub in os.listdir(outputDir) if os.path.isdir(os.path.join(outputDir, sub))]

for sub in subList:
    for template in ['fsaverage4', 'fsaverage5']:
        for hemi in ['lh', 'rh']:

            funcFile = '%s/%s_lemon_%s_%s.mgz' % (inputDir, sub, template, hemi)
            newFile = '%s/%s/resting/%s_lemon_%s_%s.mgz' % (outputDir, sub, sub, template, hemi)

            try:
                if not os.path.isfile(newFile):
                    surf_img = nib.load(funcFile)
                    surf_data = surf_img.get_data()

                    if True in np.isnan(surf_data):
                        surface = '%s/%s/surf/%s.orig' % (fsDir, template, hemi)
                        surf_img._data = nan_replace_interpolation(surf_data.squeeze(), surface)
                    else:
                        surf_img._data = surf_data

                    surf_img.to_filename(newFile)
            except:
                pass