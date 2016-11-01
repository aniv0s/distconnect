# -*- coding: utf-8 -*-


import pandas as pd
import glob, os, datetime
import nibabel as nib
import numpy as np
import scipy
from nipype.algorithms.icc import ICC_rep_anova
from sklearn import mixture
from sklearn.metrics.cluster import homogeneity_score


fsDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"
annotDir = '/scr/liberia1/data/Yeo_JNeurophysiol11_FreeSurfer'
dataDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands'
docDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/documents'
hemis = ['lh', 'rh']
thrs = [70, 75, 80, 85, 90, 95, 98]
num_gmm_comps = [2,3,4,5,6,7,8,9]


# input
samples = {}
sample_f = max(glob.iglob('%s/sample/distconnect_lsd_sample_20*.csv' % docDir), key=os.path.getctime)
samples['LSD subjects'] = pd.read_csv(sample_f, header=None, converters={0:str})[0].tolist()
sample_nonan_f = max(glob.iglob('%s/sample/distconnect_lsd_sample_nonan_*.csv' % docDir), key=os.path.getctime)
samples['LSD non-nan subjects'] = pd.read_csv(sample_nonan_f, header=None, converters={0:str})[0].tolist()
sample_lemon_f = max(glob.iglob('%s/sample/distconnect_lsd_lemon_sample_20*.csv' % docDir), key=os.path.getctime)
samples['LSD-LEMON subjects'] = pd.read_csv(sample_lemon_f, header=None, converters={0:str})[0].tolist()

# output
date = datetime.datetime.now().strftime("%Y%m%d")
df_f = '%s/data_grouplevel/lsd_data_grouplevel_%s.pkl' % (docDir,date)
df_gmm_eval_f = '%s/data_grouplevel/gmm_evaluations_%s.pkl' % (docDir,date)
df_lsdlemon_f = '%s/data_grouplevel/lsd_lemon_data_grouplevel_%s.pkl' % (docDir,date)


###############################################################################
############################## functions ######################################
###############################################################################

def run_grmean_meanDist(subjects, dataDir, thr, hemi, scan, session, disttype):
    concat = np.zeros((len(subjects), 10242))
    for n_sub, sub in enumerate(subjects):
        concat[n_sub] = np.load('%s/%s/meanDist/%s_%s_meanDist_%s_interp_%s%s_fsa5_%s.npy' 
                                % (dataDir, sub, sub, session, disttype, thr, scan, hemi))
    return concat.mean(axis=0)

def run_stdev_meanDist(subjects, dataDir, thr, hemi, disttype):
    concat = np.zeros((len(subjects), 10242))
    for n_sub, sub in enumerate(subjects):
        concat[n_sub] = np.load('%s/%s/meanDist/%s_lsd_meanDist_%s_interp_%s_1ab2ab_fsa5_%s.npy' 
                                % (dataDir, sub, sub, disttype, thr, hemi))
    return concat.std(axis=0)
    
def run_coefvariation_meanDist(subjects, dataDir, thr, hemi, disttype, cort):
    concat = np.zeros((len(subjects), 10242))
    for n_sub, sub in enumerate(subjects):
        concat[n_sub] = np.load('%s/%s/meanDist/%s_lsd_meanDist_%s_interp_%s_1ab2ab_fsa5_%s.npy' 
                                % (dataDir, sub, sub, disttype, thr, hemi))
    res = scipy.stats.variation(concat, axis=0)
    res[cort] = 0
    return res

def run_icc_meanDist(subjects, dataDir, fsDir, thr, hemi, scan_list, disttype):
    concat = np.zeros((len(subjects), len(scan_list), 10242))
    results = np.zeros((6,10242))
    subcort = np.sort(nib.freesurfer.io.read_label('%s/fsaverage5/label/%s.Medial_wall.label' % (fsDir, hemi)))
    for n_scan, scan in enumerate(scan_list):
        for n_sub, sub in enumerate(subjects):
            concat[n_sub, n_scan] = np.load('%s/%s/meanDist/%s_lsd_meanDist_%s_interp_%s_%s_fsa5_%s.npy' 
                                    % (dataDir, sub, sub, disttype, thr, scan, hemi))
    for node in range(10242):
        results[:, node] = ICC_rep_anova(concat[:, : , node])
    results[:, subcort] = 0
    return results

def run_icc_interses_meanDist(subjects, dataDir, fsDir, thr, hemi):
    concat = np.zeros((len(subjects), 2, 10242))
    results = np.zeros((6,10242))
    subcort = np.sort(nib.freesurfer.io.read_label('%s/fsaverage5/label/%s.Medial_wall.label' % (fsDir, hemi)))
    for n_sub, sub in enumerate(subjects):
        for n_ses, session in enumerate(['%s/%s/meanDist/%s_lsd_meanDist_geo_interp_%s_1a_fsa5_%s.npy' 
                                            % (dataDir, sub, sub, thr, hemi),
                                         '%s/%s/meanDist/%s_lemon_meanDist_geo_interp_%s_fsa5_%s.npy' 
                                             % (dataDir, sub, sub, thr, hemi)]):     
            concat[n_sub, n_ses] = np.load(session)
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


df_main = pd.DataFrame(columns=['sample', 'threshold', 'hemisphere', 'node', 
                                   'region in Desikan-Killiany Atlas',
                                   'region in Destrieux Atlas',
                                   'networks of Yeo & Krienen 2011 (7 networks solution)',
                                   'networks of sample (7 networks solution)',
                                   'networks of Yeo & Krienen 2011 (17 networks solution)',
                                   'mean distance (geodesic) - group mean',
                                   'mean distance (euclidean) - group mean',
                                   'difference between geodesic and euclidean meanDist',
                                   'normalized mean distance (geodesic) - group mean',
                                   'normalized mean distance (euclidean) - group mean',
                                   'difference between normalized geodesic and euclidean meanDist',
                                   'mean distance (geodesic) - standard deviation across subjects',
                                   'mean distance (geodesic) - coefficient of variation across subjects',
                                   'mean distance (euclidean) - standard deviation across subjects',
                                   'mean distance (euclidean) - coefficient of variation across subjects',
                                   'trt4_geo_icc', 'trt4_geo_rvar', 'trt4_geo_evar', 'trt4_geo_ses_eff_F', 'trt4_geo_dfc', 'trt4_geo_dfe',
                                   'trt2_geo_icc', 'trt2_geo_rvar', 'trt2_geo_evar', 'trt2_geo_ses_eff_F', 'trt2_geo_dfc', 'trt2_geo_dfe',
                                   'trt4_eucl_icc', 'trt4_eucl_rvar', 'trt4_eucl_evar', 'trt4_eucl_ses_eff_F', 'trt4_eucl_dfc', 'trt4_eucl_dfe',
                                   'trt2_eucl_icc', 'trt2_eucl_rvar', 'trt2_eucl_evar', 'trt2_eucl_ses_eff_F', 'trt2_eucl_dfc', 'trt2_eucl_dfe',
                                   'gmm_comp2', 'gmm_comp3', 'gmm_comp4', 'gmm_comp5', 
                                   'gmm_comp6', 'gmm_comp7', 'gmm_comp8', 'gmm_comp9',
                                   'LSD group nan mask'])

for sample in ['LSD subjects', 'LSD non-nan subjects']:
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
            meanDist_geo = run_grmean_meanDist(samples[sample], dataDir, thr, hemi, '_1ab2ab', 'lsd', 'geo')
            meanDist_eucl = run_grmean_meanDist(samples[sample], dataDir, thr, hemi, '_1ab2ab', 'lsd', 'eucl')
            meanDist_diff = meanDist_geo - meanDist_eucl
            stdev_geo = run_stdev_meanDist(samples[sample], dataDir, thr, hemi, 'geo')
            coefvar_geo = run_coefvariation_meanDist(samples[sample], dataDir, thr, hemi, 'geo', cort)
            stdev_eucl = run_stdev_meanDist(samples[sample], dataDir, thr, hemi, 'eucl')
            coefvar_eucl = run_coefvariation_meanDist(samples[sample], dataDir, thr, hemi, 'eucl', cort)
            meanDist_geo_norm = np.zeros((10242))
            meanDist_geo_norm[cort] = (meanDist_geo[cort] - meanDist_geo[cort].mean()) / meanDist_geo[cort].std()
            meanDist_eucl_norm = np.zeros((10242))
            meanDist_eucl_norm[cort] = (meanDist_eucl[cort] - meanDist_eucl[cort].mean()) / meanDist_eucl[cort].std()
            meanDist_norm_diff = meanDist_geo_norm - meanDist_eucl_norm
            trt_4_geo = run_icc_meanDist(samples[sample], dataDir, fsDir, thr, hemi, ['1a', '1b', '2a', '2b'], 'geo')
            trt_2_geo = run_icc_meanDist(samples[sample], dataDir, fsDir, thr, hemi, ['1ab', '2ab'], 'geo')
            trt_4_eucl = run_icc_meanDist(samples[sample], dataDir, fsDir, thr, hemi, ['1a', '1b', '2a', '2b'], 'eucl')
            trt_2_eucl = run_icc_meanDist(samples[sample], dataDir, fsDir, thr, hemi, ['1ab', '2ab'], 'eucl')
            nan_mask = run_nan_grmask(samples[sample], dataDir, hemi)
                        
            data_gmm = {}
            for n_comp in num_gmm_comps:
                data = meanDist_geo * 1000
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
                df_main.loc[len(df_main)] = [sample, str(thr), hemi, node, 
                                   aparc[2][aparc[0][node]],
                                   aparca2009s[2][aparca2009s[0][node]],
                                   yeo7_names[yeo7[0][node]],
                                   clus7[node],
                                   yeo17[2][yeo17[0][node]],
                                   meanDist_geo[node], meanDist_eucl[node], meanDist_diff[node],
                                   meanDist_geo_norm[node], meanDist_eucl_norm[node], meanDist_norm_diff[node],
                                   stdev_geo[node], coefvar_geo[node],
                                   stdev_eucl[node], coefvar_eucl[node], 
                                   trt_4_geo[0, node], trt_4_geo[1, node], trt_4_geo[2, node], trt_4_geo[3, node], trt_4_geo[4, node], trt_4_geo[5, node],
                                   trt_2_geo[0, node], trt_2_geo[1, node], trt_2_geo[2, node], trt_2_geo[3, node], trt_2_geo[4, node], trt_2_geo[5, node],
                                   trt_4_eucl[0, node], trt_4_eucl[1, node], trt_4_eucl[2, node], trt_4_eucl[3, node], trt_4_eucl[4, node], trt_4_eucl[5, node],
                                   trt_2_eucl[0, node], trt_2_eucl[1, node], trt_2_eucl[2, node], trt_2_eucl[3, node], trt_2_eucl[4, node], trt_2_eucl[5, node],
                                   data_gmm[num_gmm_comps[0]][node], data_gmm[num_gmm_comps[1]][node], data_gmm[num_gmm_comps[2]][node],
                                   data_gmm[num_gmm_comps[3]][node], data_gmm[num_gmm_comps[4]][node], data_gmm[num_gmm_comps[5]][node],
                                   data_gmm[num_gmm_comps[6]][node], data_gmm[num_gmm_comps[7]][node], 
                                   nan_mask[node]]

df_main.to_pickle(df_f)
df_gmm_eval.to_pickle(df_gmm_eval_f)




###############################################################################
############################ for intersession TRT ############################
###############################################################################

df_lsdlemon = pd.DataFrame(columns=['threshold', 'hemisphere', 'node', 
                                   'region in Desikan-Killiany Atlas',
                                   'region in Destrieux Atlas',
                                   'networks of Yeo & Krienen 2011 (7 networks solution)',
                                   'networks of sample (7 networks solution)',
                                   'networks of Yeo & Krienen 2011 (17 networks solution)',
                                   'LSD mean distance - group mean',
                                   'LEMON mean distance - group mean',
                                   'trt_intersession_icc', 'trt_intersession_rvar', 'trt_intersession_evar', 
                                   'trt_intersession_ses_eff_F', 'trt_intersession_dfc', 'trt_intersession_dfe',
                                   'trt_intrasession_icc', 'trtt_intrasession_rvar', 'trtt_intrasession_evar', 
                                   'trtt_intrasession_ses_eff_F', 'trtt_intrasession_dfc', 'trtt_intrasession_dfe',
                                    ])

sample = 'LSD-LEMON subjects'
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
        meanDist_lsd = run_grmean_meanDist(samples[sample], dataDir, thr, hemi, '_1a', 'lsd', 'geo')
        meanDist_lemon = run_grmean_meanDist(samples[sample], dataDir, thr, hemi, '', 'lemon', 'geo')
        trt_interses = run_icc_interses_meanDist(samples[sample], dataDir, fsDir, thr, hemi)
        trt_intrases = run_icc_meanDist(samples[sample], dataDir, fsDir, thr, hemi, ['1a', '1b'], 'geo')
        
        for node in range(10242):
            df_lsdlemon.loc[len(df_lsdlemon)] = [str(thr), hemi, node, 
                                                   aparc[2][aparc[0][node]],
                                                   aparca2009s[2][aparca2009s[0][node]],
                                                   yeo7_names[yeo7[0][node]],
                                                   clus7[node],
                                                   yeo17[2][yeo17[0][node]],
                                                   meanDist_lsd[node], meanDist_lemon[node],
                                                   trt_interses[0, node], trt_interses[1, node], trt_interses[2, node], 
                                                   trt_interses[3, node], trt_interses[4, node], trt_interses[5, node],
                                                   trt_intrases[0, node], trt_intrases[1, node], trt_intrases[2, node], 
                                                   trt_intrases[3, node], trt_intrases[4, node], trt_intrases[5, node]]
df_lsdlemon.to_pickle(df_lsdlemon_f) 

