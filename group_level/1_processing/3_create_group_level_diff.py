# -*- coding: utf-8 -*-

import pandas as pd
import glob, os, datetime
import nibabel as nib
import numpy as np
import scipy



fsDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"
annotDir = '/scr/liberia1/data/Yeo_JNeurophysiol11_FreeSurfer'
dataDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands'
docDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/documents'
hemis = ['lh', 'rh']
thrs = [70, 75, 80, 85, 90, 95, 98]

# input
samples = {}
sample_f = max(glob.iglob('%s/sample/distconnect_lsd_sample_20*.csv' % docDir), key=os.path.getctime)
samples['LSD subjects'] = pd.read_csv(sample_f, header=None, converters={0:str})[0].tolist()

# output
date = datetime.datetime.now().strftime("%Y%m%d")
df_f = '%s/data_grouplevel/lsd_data_grouplevel_diff_%s.pkl' % (docDir,date)



def run_grmean(subjects, dataDir, thr, hemi, scan, session, disttype):
    concat = np.zeros((len(subjects), 10242))
    for n_sub, sub in enumerate(subjects):
        concat[n_sub] = np.load('%s/%s/meanDist/%s_%s_meanDist_%s_interp_%s%s_fsa5_%s.npy' 
                                % (dataDir, sub, sub, session, disttype, thr, scan, hemi))
    return concat.mean(axis=0)
    
    
    
    
df_main = pd.DataFrame(columns=['sample', 'threshold', 'hemisphere', 'node', 
                                'mean distance (diff) - group mean'])

for sample in samples.keys():
    for hemi in hemis:
        print hemi
        
        cort = np.sort(nib.freesurfer.io.read_label('%s/fsaverage5/label/%s.cortex.label' % (fsDir, hemi)))
        
        for thr in thrs:
            print thr
            meanDist_geo = run_grmean(samples[sample], dataDir, thr, hemi, '_1ab2ab', 'lsd', 'diff')
                          
            for node in range(10242):
                df_main.loc[len(df_main)] = [sample, str(thr), 
                                            hemi, node, meanDist_geo[node]]

df_main.to_pickle(df_f)





