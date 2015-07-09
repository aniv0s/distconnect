__author__ = 'oligschlager'

import glob
import os.path
import nibabel as nib
import numpy as np
import h5py
from sklearn import preprocessing
from surfproc import run_meanDist

'''directories'''
baseDir = "/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands"
fsDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"
#subjects = [sub for sub in os.listdir(baseDir) if os.path.isdir(os.path.join(baseDir, sub))]
subjects = ['03820', '23734']

for hemi in ['lh', 'rh']:
    cort = np.sort(nib.freesurfer.io.read_label('%s/fsaverage5/label/%s.cortex.label' % (fsDir, hemi)))

    for sub in subjects:
        print sub, hemi

        distFile = '{0:s}/{1:s}/distance_maps/{2:s}_{3:s}_geoDist_fsa5.mat'.format(baseDir, sub, sub, hemi)
        corrFiles = glob.glob('{0:s}/{1:s}/correlation_maps/{2:s}_lsd_corr_2ab_fsa5_{3:s}.npy'.format(baseDir, sub, sub, hemi))

        if os.path.isfile(distFile):

            # distance matrix
            with h5py.File(distFile, 'r') as f:
                dist = f['dataAll'][()]
            dist = dist[cort, :][:, cort]
            min_max_scaler = preprocessing.MinMaxScaler()
            dist_scaled = min_max_scaler.fit_transform(dist)
            del dist

            # correlation matrices
            for corrFile in corrFiles:
                print corrFile
                corr = np.load(corrFile)
                corr[np.diag_indices_from(corr)] = 0

                # mean distance
                for thr in [70, 75, 80, 85, 90, 95, 98]:
                    print thr
                    meanDist = run_meanDist(corr, dist_scaled, cort, thr)
                    np.save(corrFile.replace('/correlation_maps/', '/meanDist/').replace('_corr_', '_meanDist_%s_' % thr), meanDist)




