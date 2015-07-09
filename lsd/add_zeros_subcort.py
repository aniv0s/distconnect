__author__ = 'oligschlager'

import os
import numpy as np
import nibabel as nib
import glob

baseDir = "/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands"
fsDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"
subjects = [sub for sub in os.listdir(baseDir) if os.path.isdir(os.path.join(baseDir, sub))]


for hemi in ['lh', 'rh']:
    cort = np.sort(nib.freesurfer.io.read_label('%s/fsaverage5/label/%s.cortex.label' % (fsDir, hemi)))

    for sub in subjects:
        corrFiles = glob.glob('%s/%s/correlation_maps/*_lsd_corr_*ab_fsa5_%s.npy' % (baseDir, sub, hemi))

        for corrFile in corrFiles:
            print corrFile
            corr_all = np.zeros((10242, 10242))
            corr_cort = np.load(corrFile)
            corr_all[np.ix_(cort, cort)] = corr_cort
            print '... done adding zeros for subcortex'
            np.save(corrFile, corr_all)
            print '... saved to disc'