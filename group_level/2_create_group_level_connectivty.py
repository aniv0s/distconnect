# -*- coding: utf-8 -*-



import glob, os, pandas as pd, nibabel as nib, numpy as np
import scipy.io

docDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/documents'
dataDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands'
fsDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"
sample_f = max(glob.iglob('%s/distconnect_sample_20*.csv' % docDir), key=os.path.getctime)
subjects = pd.read_csv(sample_f, header=None, converters={0:str})[0].tolist()

thr = 90
for hemi in ['lh', 'rh']:
    
    cort = np.sort(nib.freesurfer.io.read_label('%s/fsaverage5/label/%s.cortex.label' % (fsDir, hemi)))
    group_sum = np.zeros((10242,10242))
    
    for sub in subjects:
        
        # sum over four connectivity matrices per subject
        individ_mat_concat = np.zeros((len(cort), len(cort)))
        for scan in ['1a', '1b', '2a', '2b']:
            individ_mat = np.load('%s/%s/correlation_maps/%s_lsd_corr_interp_%s_fsa5_%s.npy' 
                                  % (dataDir,sub,sub, scan, hemi))[cort,:][:,cort]
            individ_mat_concat = individ_mat_concat + individ_mat
        del individ_mat
        
        # take top 10% per node, binarize, and add to group matrix
        for n_node, node in enumerate(cort):
            cutoff = np.percentile(individ_mat_concat[n_node], thr)
            group_sum[node][individ_mat_concat[n_node] > cutoff] += 1 
        
    group_avg = group_sum / len(subjects)
    scipy.io.savemat('/scr/liberia1/data/lsd/corr/corrmat_group_%s.mat' 
                     % hemi, mdict={'corrmat_group_%s' % hemi: group_avg})