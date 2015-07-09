__author__ = 'oligschlager'

import glob
import nibabel as nib
import numpy as np
from surfproc import run_corr_combined

'''directories'''
baseDir = "/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands"
fsDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"
#subjects = [sub for sub in os.listdir(baseDir) if os.path.isdir(os.path.join(baseDir, sub))]
subjects = ['03820', '23734']

for hemi in ['lh', 'rh']:
    cort = np.sort(nib.freesurfer.io.read_label('%s/fsaverage5/label/%s.cortex.label' % (fsDir, hemi)))

    for sub in subjects:
        print sub, hemi

        restFiles = '%s/%s/resting/*_lsd_rest*_fsaverage5_%s.mgz' % (baseDir, sub, hemi)
        corrFiles = '%s/%s/correlation_maps/*_lsd_corr_*ab_fsa5_%s.npy' % (baseDir, sub, hemi)
        if (len(glob.glob(restFiles)) == 4) & (len(glob.glob(corrFiles)) != 2):

            # correlation matrices
            print hemi, sub
            print '... corr 1ab'
            scan1a = '%s/%s/resting/%s_lsd_rest1a_fsaverage5_%s.mgz' % (baseDir, sub, sub, hemi)
            scan1b = '%s/%s/resting/%s_lsd_rest1b_fsaverage5_%s.mgz' % (baseDir, sub, sub, hemi)
            corr1 = run_corr_combined(scan1a, scan1b, cort)
            np.save('%s/%s/correlation_maps/%s_lsd_corr_1ab_fsa5_%s' % (baseDir, sub, sub, hemi), corr1)

            print '... corr 2ab'
            scan2a = '%s/%s/resting/%s_lsd_rest2a_fsaverage5_%s.mgz' % (baseDir, sub, sub, hemi)
            scan2b = '%s/%s/resting/%s_lsd_rest2b_fsaverage5_%s.mgz' % (baseDir, sub, sub, hemi)
            corr2 = run_corr_combined(scan2a, scan2b, cort)
            np.save('%s/%s/correlation_maps/%s_lsd_corr_2ab_fsa5_%s' % (baseDir, sub, sub, hemi), corr2)