# -*- coding: utf-8 -*-


import pandas as pd
import glob, os, datetime
import nibabel as nib
import numpy as np
from nipype.algorithms.icc import ICC_rep_anova
from sklearn import mixture
from sklearn.metrics.cluster import homogeneity_score


fsDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"
annotDir = '/scr/liberia1/data/Yeo_JNeurophysiol11_FreeSurfer'
dataDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands'
docDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/documents'
hemis = ['lh', 'rh']
thrs = [70, 75, 80, 85, 90, 95, 98]
num_gmm_comps = [4,5,6,7,8,9]


# input
samples = {}
sample_f = max(glob.iglob('%s/distconnect_sample_20*.csv' % docDir), key=os.path.getctime)
samples['all subjects'] = pd.read_csv(sample_f, header=None, converters={0:str})[0].tolist()
sample_nonan_f = max(glob.iglob('%s/distconnect_sample_nonan_*.csv' % docDir), key=os.path.getctime)
samples['non-nan subjects'] = pd.read_csv(sample_nonan_f, header=None, converters={0:str})[0].tolist()

# output
date = datetime.datetime.now().strftime("%Y%m%d")
df_f = '%s/data_grouplevel_%s.pkl' % (docDir,date)
df_gmm_eval_f = '%s/gmm_evaluations_%s.pkl' % (docDir,date)


###############################################################################
############################## functions ######################################
###############################################################################

def run_grmean_meanDist(subjects, dataDir, thr, hemi):
    concat = np.zeros((len(subjects), 10242))
    for n_sub, sub in enumerate(subjects):
        concat[n_sub] = np.load('%s/%s/meanDist/%s_lsd_meanDist_interp_%s_1ab2ab_fsa5_%s.npy' 
                                % (dataDir, sub, sub, thr, hemi))
    return concat.mean(axis=0)

def run_stdev_meanDist(subjects, dataDir, thr, hemi):
    concat = np.zeros((len(subjects), 10242))
    for n_sub, sub in enumerate(subjects):
        concat[n_sub] = np.load('%s/%s/meanDist/%s_lsd_meanDist_interp_%s_1ab2ab_fsa5_%s.npy' 
                                % (dataDir, sub, sub, thr, hemi))
    return concat.std(axis=0)

def run_icc_meanDist(subjects, dataDir, fsDir, thr, hemi, scan_list):
    concat = np.zeros((len(subjects), len(scan_list), 10242))
    results = np.zeros((6,10242))
    subcort = np.sort(nib.freesurfer.io.read_label('%s/fsaverage5/label/%s.Medial_wall.label' % (fsDir, hemi)))
    for n_scan, scan in enumerate(scan_list):
        for n_sub, sub in enumerate(subjects):
            concat[n_sub, n_scan] = np.load('%s/%s/meanDist/%s_lsd_meanDist_interp_%s_%s_fsa5_%s.npy' 
                                    % (dataDir, sub, sub, thr, scan, hemi))
    for node in range(10242):
        results[:, node] = ICC_rep_anova(concat[:, : , node])
    results[:, subcort] = 0
    return results

def run_nan_grmask(subjects, dataDir, hemi):
    concat = np.zeros((4, len(subjects), 10242))
    for n_scan, scan in enumerate(['1a', '1b', '2a', '2b']):
        for n_sub, sub in enumerate(subjects):
            f = '%s/%s/resting/%s_lsd_nan_mask_%s_fsa5_%s.npy' % (dataDir, sub, sub, scan, hemi)
            if os.path.isfile(f):
                concat[n_scan, n_sub] = np.load(f)
            else:
                concat[n_scan, n_sub] = np.zeros(10242)
    return concat.sum(axis=0).sum(axis=0)    
    
    
###############################################################################
################ create group level dataframe #################################
###############################################################################
    

df_gmm_eval = pd.DataFrame(columns=['threshold', 'hemisphere', 'number of components', 
                                    'bayesian information criterion', 'akaike information criterion', 
                                    'homogeneity score', 'converged?'])


df = pd.DataFrame(columns=['sample', 'threshold', 'hemisphere', 'node', 
                           'region in Desikan-Killiany Atlas',
                           'region in Destrieux Atlas',
                           'networks of Yeo 2011 (7 networks solution)',
                           'networks of sample (7 networks solution)',
                           'networks of Yeo 2011 (17 networks solution)',
                           'mean distance - group mean',
                           'normalized mean distance - group mean',
                           'mean distance - standard deviation across subjects',
                           'trt4_icc', 'trt4_rvar', 'trt4_evar', 'trt4_ses_eff_F', 'trt4_dfc', 'trt4_dfe',
                           'trt2_icc', 'trt2_rvar', 'trt2_evar', 'trt2_ses_eff_F', 'trt2_dfc', 'trt2_dfe',
                           'gmm_comp4', 'gmm_comp5', 'gmm_comp6', 'gmm_comp7', 'gmm_comp8', 'gmm_comp9',
                           'nan mask'])

for sample in samples.keys():
    print sample
    for hemi in hemis:
        print hemi
        
        aparc = nib.freesurfer.io.read_annot('%s/fsaverage5/label/%s.aparc.annot' % (annotDir, hemi))
        aparca2009s = nib.freesurfer.io.read_annot('%s/fsaverage5/label/%s.aparc.a2009s.annot' % (annotDir, hemi))
        yeo7 = nib.freesurfer.io.read_annot('%s/fsaverage5/label/%s.Yeo2011_7Networks_N1000.annot' % (annotDir, hemi))
        yeo7_names = ['medial wall', 'visual', 'somatomotor', 'dorsal attention', 'ventral attention', 'limbic', 'frontoparietal', 'default']
        clus7 = np.load('/scr/liberia1/data/lsd/corr/clus7.%s.npy' % hemi) 
        yeo17 = nib.freesurfer.io.read_annot('%s/fsaverage5/label/%s.Yeo2011_17Networks_N1000.annot' % (annotDir, hemi))
        cort = np.sort(nib.freesurfer.io.read_label('%s/fsaverage5/label/%s.cortex.label' % (fsDir, hemi)))
        
        for thr in thrs:
            print thr
            meanDist = run_grmean_meanDist(samples[sample], dataDir, thr, hemi)
            stdev = run_stdev_meanDist(samples[sample], dataDir, thr, hemi)
            meanDist_norm = np.zeros((10242))
            meanDist_norm[cort] = (meanDist[np.nonzero(meanDist)] - meanDist[np.nonzero(meanDist)].mean()) / meanDist[np.nonzero(meanDist)].std()
            trt_4 = run_icc_meanDist(samples[sample], dataDir, fsDir, thr, hemi, ['1a', '1b', '2a', '2b'])
            trt_2 = run_icc_meanDist(samples[sample], dataDir, fsDir, thr, hemi, ['1ab', '2ab'])
            nan_mask = run_nan_grmask(samples[sample], dataDir, hemi)
            
            data_gmm = {}
            for n_comp in num_gmm_comps:
                data = meanDist * 1000
                gmm = mixture.GMM(n_components=n_comp, n_iter=1000)
                gmm.fit(data[cort])
                bic = gmm.bic(data[cort])
                aic = gmm.aic(data[cort])
                res = np.zeros(10242)
                res[cort] = gmm.predict(data[cort])
                res[cort] = res[cort] +1
                data_gmm[n_comp] = res
                homogeneity = homogeneity_score(res[cort],yeo7[0][cort])
                df_gmm_eval.loc[len(df_gmm_eval)] = [str(thr), hemi, n_comp, bic, aic, homogeneity, gmm.converged_]

            for node in range(10242):
                df.loc[len(df)] = [sample, str(thr), hemi, node, 
                                   aparc[2][aparc[0][node]],
                                   aparca2009s[2][aparca2009s[0][node]],
                                   yeo7_names[yeo7[0][node]],
                                   clus7[node],
                                   yeo17[2][yeo17[0][node]],
                                   meanDist[node], meanDist_norm[node],
                                   stdev[node],
                                   trt_4[0, node], trt_4[1, node], trt_4[2, node], trt_4[3, node], trt_4[4, node], trt_4[5, node],
                                   trt_2[0, node], trt_2[1, node], trt_2[2, node], trt_2[3, node], trt_2[4, node], trt_2[5, node],
                                   data_gmm[num_comps[0]][node], data_gmm[num_comps[1]][node], data_gmm[num_comps[2]][node],
                                   data_gmm[num_comps[3]][node], data_gmm[num_comps[4]][node], data_gmm[num_comps[5]][node], 
                                   nan_mask[node]]
df.to_pickle(df_f)
df_gmm_eval.to_pickle(df_gmm_eval_f)
