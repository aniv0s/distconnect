__author__ = 'oligschlager'

import glob
import os.path
import nibabel as nib
import numpy as np


'''directories'''
baseDir = "/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands"
fsDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"


for hemi in ['lh', 'rh']:

    cort = np.sort(nib.freesurfer.io.read_label('%s/fsaverage5/label/%s.cortex.label' % (fsDir, hemi)))

    file_list = glob.glob('%s/*/resting/*_lemon_fsaverage5_%s.mgz' % (baseDir, hemi))
    for n, restFile in enumerate(file_list):

        corrFile = restFile.replace('resting', 'correlation_maps').replace('_lemon_', '_lemon_corr_').replace('fsaverage5', 'fsa5').replace('.mgz', '')
        if not os.path.isfile(corrFile):

            print str(n+1) + ' out of ' + str(len(file_list))
            print os.path.basename(corrFile)

            data = nib.load(restFile).get_data().squeeze()
            corr = np.corrcoef(data[cort])
            bigCorr = np.zeros((len(data), len(data)))
            bigCorr[np.ix_(cort, cort)] = corr
            np.save(corrFile, bigCorr)