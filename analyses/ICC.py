__author__ = 'oligschlager'

import os.path
import pandas as pd
import numpy as np
import nibabel as nib
from nipype.algorithms.icc import ICC_rep_anova
#import sys


hemi = 'lh'
#scans = ['1a', '1b', '2a', '2b']
scans = ['1ab', '2ab']

dataDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands'
fsDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"

subjects_incl = # read in qc file
subcort = np.sort(nib.freesurfer.io.read_label('%s/fsaverage5/label/%s.Medial_wall.label' % (fsDir, hemi)))


for thr in ['70', '75', '80', '85', '90', '95', '98']:

    # subjects
    columns = []
    for scan in scans:
        columns.append(dataDir + '/%s/meanDist/%s' + '_lsd_meanDist_%s_%s_fsa5_%s.npy' % (thr, scan, hemi))
    df = pd.DataFrame(index=subjects_incl, columns=columns)
    for sub in subjects_incl:
        for c in columns:
            if os.path.isfile(c %(sub, sub)):
                df[c].loc[sub] = 1
    subjects = list(df.index[df.sum(1) == len(scans)])
    print len(subjects)


    # ICC
    ICC_map = np.zeros((10242))
    dict = {}

    for node in range(10242):
        for n_col, col in enumerate(columns):
            concat = np.load(col %(subjects[0], subjects[0]))[node]
            for subject in subjects[1::]:
                new = np.load(col %(subject, subject))[node]
                concat = np.vstack((concat, new))
            dict[n_col] = concat

        if len(scans) == 2:
            merged = np.vstack((dict[0].T, dict[1].T)).T
        if len(scans) == 4:
            merged = np.vstack((dict[0].T, dict[1].T, dict[2].T, dict[3].T)).T
        ICC, r_var, e_var, session_effect_F, dfc, dfe = ICC_rep_anova(merged)
        print thr, node, ICC
        ICC_map[node] = ICC

    ICC_map[subcort] = 0
    np.save('/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/results/ICC_lsd_meanDist_%s_1ab2ab_fsa5_%s_qcincl' % (thr, hemi), ICC_map)

