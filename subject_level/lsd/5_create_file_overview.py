# -*- coding: utf-8 -*-

import pandas as pd
import os, glob, datetime

# directories
preprocDir = '/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/probands'
surfDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands'
docDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/documents'

# input files
documentation_f = max(glob.iglob('%s/input documents/Participants_List_LargeScaleProject - Overview_*.csv' % docDir), 
                         key=os.path.getctime)
lsd_qa_f = max(glob.iglob('%s/input documents/lemon_lsd_qa - lsd rest_*.csv' % docDir), key=os.path.getctime)

# output files
date = datetime.datetime.now().strftime("%Y%m%d")
overview = '%s/data_overview_%s.pkl' % (docDir,date)
overview_tidy = '%s/data_overview_tidy_%s.pkl' % (docDir,date)




###############################################################################
#############overview - compact format (one row per subject) ##################
###############################################################################

# prep dataframe using the most recent participant documentation

df = pd.read_csv(documentation_f, converters={'DB_ID':str, 'SKID_Diagnoses':str, 'Drug_Test (nothing=negative)':str},
                 usecols=['DB_ID', 'Day 3', 'Age', 'Gender', 'SKID_Diagnoses', 'Drug_Test (nothing=negative)'])
df['DB_ID'] = df['DB_ID'].map(lambda x: x[0:5])
df.rename(columns={'DB_ID':'subject', 'SKID_Diagnoses':'skid diagnosis', 'Drug_Test (nothing=negative)':'drug test'}, inplace=True)
df = df[df['Day 3'] == 'y']
df.drop('Day 3', 1, inplace=True)
df.sort(columns='subject', inplace=True)
df.reset_index(inplace=True, drop=True)
for idx in df.index:
    if df['Gender'].iloc[idx] == 'm' or df['Gender'].iloc[idx] == 'M':
        df['Gender'].iloc[idx] = 'male'
    if df['Gender'].iloc[idx] == 'f' or df['Gender'].iloc[idx] == 'F':
        df['Gender'].iloc[idx] = 'female'
for idx in df.index:
    if 'nothing' in df['skid diagnosis'].iloc[idx]:
        df['skid diagnosis'].iloc[idx] = ''
    if 'none' in df['skid diagnosis'].iloc[idx]:
        df['skid diagnosis'].iloc[idx] = ''

# preprocessed resting data, volumes in native space
scans = ['1a', '1b', '2a', '2b']
for scan in scans:
    df['rest%s_native' %scan] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        f = '%s/%s/preprocessed/lsd_resting/rest%s/rest_preprocessed.nii.gz' % (preprocDir, subject, scan)
        if os.path.isfile(f):
            df['rest%s_native' %scan].iloc[idx] = 1
        else:
            df['rest%s_native' %scan].iloc[idx] = 0
            
# preprocessed resting data, volumes in mni
scans = ['1a', '1b', '2a', '2b']
for scan in scans:
    df['rest%s_mni' %scan] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        f = '%s/%s/preprocessed/lsd_resting/rest%s/rest_preprocessed2mni.nii.gz' % (preprocDir, subject, scan)
        if os.path.isfile(f):
            df['rest%s_mni' %scan].iloc[idx] = 1
        else:
            df['rest%s_mni' %scan].iloc[idx] = 0
            
# freesurfer surface files
for hemi in ['lh', 'rh']:
    df['fs_files_%s' %hemi] = np.nan
    for idx in df.index:   
        subject = df['subject'].iloc[idx]
        f_pial = '%s/%s/freesurfer/surf/%s.pial' % (preprocDir, subject, hemi)
        f_smwm = '%s/%s/freesurfer/surf/%s.smoothwm' % (preprocDir, subject, hemi)
        f_cort = '%s/%s/freesurfer/label/%s.cortex.label' % (preprocDir, subject, hemi)
        if (os.path.isfile(f_pial) & os.path.isfile(f_smwm) & os.path.isfile(f_cort)):
            df['fs_files_%s' %hemi].iloc[idx] = 1
        else:
            df['fs_files_%s' %hemi].iloc[idx] = 0 
        
# timeseries (raw - incl nan)
for hemi in ['lh', 'rh']:
    for scan in ['1a', '1b', '2a', '2b']:
        df['surf_raw_%s_%s' % (scan, hemi)] = np.nan
        for idx in df.index:
            subject = df['subject'].iloc[idx]
            f = '%s/%s/resting/%s_lsd_rest_raw_%s_fsa5_%s.mgz' % (surfDir, subject, subject, scan, hemi)
            if os.path.isfile(f):
                df['surf_raw_%s_%s' % (scan, hemi)].iloc[idx] = 1
            else:
                df['surf_raw_%s_%s' % (scan, hemi)].iloc[idx] = 0
                
# nan counts
for hemi in ['lh', 'rh']:
    for scan in ['1a', '1b', '2a', '2b']:
        df['surf_raw_%s_%s_nan_count' % (scan,hemi)] = np.nan
        for idx in df.index[(df['surf_raw_%s_%s' % (scan,hemi)] != 0) & (df['surf_raw_%s_%s' % (scan,hemi)].notnull())]:
            subject = df['subject'].iloc[idx]
            f1 = '%s/%s/resting/%s_lsd_rest_raw_%s_fsa5_%s.mgz' % (surfDir, subject, subject, scan, hemi)
            if os.path.isfile(f1):
                f2 = '%s/%s/resting/%s_lsd_nan_mask_%s_fsa5_%s.npy' % (surfDir, subject, subject, scan, hemi)
                if os.path.isfile(f2):
                    count = np.load(f2).sum()
                    df['surf_raw_%s_%s_nan_count' % (scan,hemi)].iloc[idx] = count
                else:
                    df['surf_raw_%s_%s_nan_count' % (scan,hemi)].iloc[idx] = 0
            
# timeseries surf (interpolated)
for hemi in ['lh', 'rh']:
    for scan in ['1a', '1b', '2a', '2b']:
        df['surf_interp_%s_%s' % (scan, hemi)] = np.nan
        for idx in df.index:
            subject = df['subject'].iloc[idx]
            f = '%s/%s/resting/%s_lsd_rest_interp_%s_fsa5_%s.mgz' % (surfDir, subject, subject, scan, hemi)
            if os.path.isfile(f):
                df['surf_interp_%s_%s' % (scan, hemi)].iloc[idx] = 1
            else:
                df['surf_interp_%s_%s' % (scan, hemi)].iloc[idx] = 0    
                
# correlation matrices
for hemi in ['lh', 'rh']:
    for scan in ['1a', '1b', '2a', '2b']:
        df['corr_%s_%s' % (scan, hemi)] = np.nan
        for idx in df.index:
            subject = df['subject'].iloc[idx]
            f = '%s/%s/correlation_maps/%s_lsd_corr_interp_%s_fsa5_%s.npy' % (surfDir, subject, subject, scan, hemi)
            if os.path.isfile(f):
                df['corr_%s_%s' % (scan, hemi)].iloc[idx] = 1
            else:
                df['corr_%s_%s' % (scan, hemi)].iloc[idx] = 0

# distance
for hemi in ['lh', 'rh']:
    df['distance_%s' %hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        f = '%s/%s/distance_maps/%s_%s_geoDist_fsa5.mat' % (surfDir, subject, subject, hemi)
        if os.path.isfile(f):
            df['distance_%s' %hemi].iloc[idx] = 1
        else:
            df['distance_%s' %hemi].iloc[idx] = 0  

# meanDist
for hemi in ['lh', 'rh']:
    for scan in ['1a', '1b', '2a', '2b', '1ab', '2ab', '1ab2ab']:
        for thr in [70, 75, 80, 85, 90, 95, 98]:
                df['meanDist_%s_%s_%s' % (scan, thr, hemi)] = np.nan
                for idx in df.index:
                    subject = df['subject'].iloc[idx]
                    f = '%s/%s/meanDist/%s_lsd_meanDist_interp_%s_%s_fsa5_%s.npy' % (surfDir, subject, subject, thr, scan, hemi)
                    if os.path.isfile(f):
                        df['meanDist_%s_%s_%s' % (scan, thr, hemi)].iloc[idx] = 1
                    else:
                        df['meanDist_%s_%s_%s' % (scan, thr, hemi)].iloc[idx] = 0
                        
# add qa metrics
old = ['rest1a ', 'rest1b', 'rest2a', 'rest2b', 'rest1a .1', 'rest1b.1', 'rest2a.1', 'rest2b.1', 
       'rest1a .2', 'rest1b.2', 'rest2a.2', 'rest2b.2', 'rest1a .3', 'rest1b.3', 'rest2a.3', 'rest2b.3',
       'rest1a .4', 'rest1b.4', 'rest2a.4', 'rest2b.4', 'subject ID']
new = ['link_1a', 'link_1b', 'link_2a', 'link_2b', 'coreg_1a', 'coreg_1b', 'coreg_2a', 'coreg_2b', 
       'meanFD_1a', 'meanFD_1b', 'meanFD_2a', 'meanFD_2b', 'maxFD_1a', 'maxFD_1b', 'maxFD_2a', 'maxFD_2b',
       'tSNR_1a', 'tSNR_1b', 'tSNR_2a', 'tSNR_2b', 'subject']
df_qa = pd.read_csv(lsd_qa_f, skiprows=1, converters={'subject ID':str})
convert = dict(zip(old, new))
df_qa = df_qa.rename(columns=convert)
df_qa = df_qa[new]
df_qa[new[:-1]] = df_qa[new[:-1]].convert_objects(convert_numeric=True)
df = pd.merge(df, df_qa, on='subject', how='left')
del df_qa
df.to_pickle(overview)


###############################################################################
#################### overview - tidy data format ##############################
###############################################################################

# prep dataframe using the most recent participant documentation
df = pd.read_csv(documentation_f, converters={'DB_ID':str, 'SKID_Diagnoses':str, 'Drug_Test (nothing=negative)':str},
                 usecols=['DB_ID', 'Day 3', 'Age', 'Gender', 'SKID_Diagnoses', 'Drug_Test (nothing=negative)'])
df['DB_ID'] = df['DB_ID'].map(lambda x: x[0:5])
df.rename(columns={'DB_ID':'subject', 'SKID_Diagnoses':'skid diagnosis', 'Drug_Test (nothing=negative)':'drug test'}, inplace=True)
df = df[df['Day 3'] == 'y']
df.drop('Day 3', 1, inplace=True)
df = pd.concat([df,df,df,df])
df.sort(columns='subject', inplace=True)
df.reset_index(inplace=True, drop=True)
df['scan'] = pd.Series(['1a', '1b', '2a', '2b'] * (len(df)/4), index=df.index)
for idx in df.index:
    if df['Gender'].iloc[idx] == 'm' or df['Gender'].iloc[idx] == 'M':
        df['Gender'].iloc[idx] = 'male'
    if df['Gender'].iloc[idx] == 'f' or df['Gender'].iloc[idx] == 'F':
        df['Gender'].iloc[idx] = 'female'
for idx in df.index:
    if 'nothing' in df['skid diagnosis'].iloc[idx]:
        df['skid diagnosis'].iloc[idx] = ''
    if 'none' in df['skid diagnosis'].iloc[idx]:
        df['skid diagnosis'].iloc[idx] = ''

# preprocessed resting data, volumes in native space
df['rest_native'] = np.nan
for idx in df.index:
    subject = df['subject'].iloc[idx]
    scan = df['scan'].iloc[idx]
    f = '%s/%s/preprocessed/lsd_resting/rest%s/rest_preprocessed.nii.gz' % (preprocDir, subject, scan)
    if os.path.isfile(f):
        df['rest_native'].iloc[idx] = 1
    else:
        df['rest_native'].iloc[idx] = 0
        
# preprocessed resting data, volumes  in mni
df['rest_mni'] = np.nan
for idx in df.index:
    subject = df['subject'].iloc[idx]
    scan = df['scan'].iloc[idx]
    f = '%s/%s/preprocessed/lsd_resting/rest%s/rest_preprocessed2mni.nii.gz' % (preprocDir, subject, scan)
    if os.path.isfile(f):
        df['rest_mni'].iloc[idx] = 1
    else:
        df['rest_mni'].iloc[idx] = 0
        
# freesurfer surface files
for hemi in ['lh', 'rh']:
    df['fs_files_%s' %hemi] = np.nan
    for idx in df.index:   
        subject = df['subject'].iloc[idx]
        f_pial = '%s/%s/freesurfer/surf/%s.pial' % (preprocDir, subject, hemi)
        f_smwm = '%s/%s/freesurfer/surf/%s.smoothwm' % (preprocDir, subject, hemi)
        f_cort = '%s/%s/freesurfer/label/%s.cortex.label' % (preprocDir, subject, hemi)
        if (os.path.isfile(f_pial) & os.path.isfile(f_smwm) & os.path.isfile(f_cort)):
            df['fs_files_%s' %hemi].iloc[idx] = 1
        else:
            df['fs_files_%s' %hemi].iloc[idx] = 0   
                        
# timeseries (raw - incl nan)
for hemi in ['lh', 'rh']:
    df['surf_raw_%s' % hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        scan = df['scan'].iloc[idx]
        f = '%s/%s/resting/%s_lsd_rest_raw_%s_fsa5_%s.mgz' % (surfDir, subject, subject, scan, hemi)
        if os.path.isfile(f):
            df['surf_raw_%s' % hemi].iloc[idx] = 1
        else:
            df['surf_raw_%s' % hemi].iloc[idx] = 0
            
# nan counts
for hemi in ['lh', 'rh']:
    df['surf_raw_%s_nan_count' % hemi] = np.nan
    for idx in df.index[(df['surf_raw_%s' % hemi] != 0) & (df['surf_raw_%s' % hemi].notnull())]:
        subject = df['subject'].iloc[idx]
        scan = df['scan'].iloc[idx]
        f1 = '%s/%s/resting/%s_lsd_rest_raw_%s_fsa5_%s.mgz' % (surfDir, subject, subject, scan, hemi)
        if os.path.isfile(f1):
            f2 = '%s/%s/resting/%s_lsd_nan_mask_%s_fsa5_%s.npy' % (surfDir, subject, subject, scan, hemi)
            if os.path.isfile(f2):
                count = np.load(f2).sum()
                df['surf_raw_%s_nan_count' % hemi].iloc[idx] = count
            else:
                df['surf_raw_%s_nan_count' % hemi].iloc[idx] = 0
              
# timeseries surf (interpolated)
for hemi in ['lh', 'rh']:
    df['surf_interp_%s' % hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        scan = df['scan'].iloc[idx]
        f = '%s/%s/resting/%s_lsd_rest_interp_%s_fsa5_%s.mgz' % (surfDir, subject, subject, scan, hemi)
        if os.path.isfile(f):
            df['surf_interp_%s' % hemi].iloc[idx] = 1
        else:
            df['surf_interp_%s' % hemi].iloc[idx] = 0
            
# correlation matrices
for hemi in ['lh', 'rh']:
    df['corr_%s' % hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        scan = df['scan'].iloc[idx]
        f = '%s/%s/correlation_maps/%s_lsd_corr_interp_%s_fsa5_%s.npy' % (surfDir, subject, subject, scan, hemi)
        if os.path.isfile(f):
            df['corr_%s' % hemi].iloc[idx] = 1
        else:
            df['corr_%s' % hemi].iloc[idx] = 0
            
# distance
for hemi in ['lh', 'rh']:
    df['distance_%s' %hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        f = '%s/%s/distance_maps/%s_%s_geoDist_fsa5.mat' % (surfDir, subject, subject, hemi)
        if os.path.isfile(f):
            df['distance_%s' %hemi].iloc[idx] = 1
        else:
            df['distance_%s' %hemi].iloc[idx] = 0    

# qa metrics
old = ['rest1a ', 'rest1b', 'rest2a', 'rest2b', 'rest1a .1', 'rest1b.1', 'rest2a.1', 'rest2b.1', 
       'rest1a .2', 'rest1b.2', 'rest2a.2', 'rest2b.2', 'rest1a .3', 'rest1b.3', 'rest2a.3', 'rest2b.3',
       'rest1a .4', 'rest1b.4', 'rest2a.4', 'rest2b.4']
new = ['link_1a', 'link_1b', 'link_2a', 'link_2b', 'coreg_1a', 'coreg_1b', 'coreg_2a', 'coreg_2b', 
       'meanFD_1a', 'meanFD_1b', 'meanFD_2a', 'meanFD_2b', 'maxFD_1a', 'maxFD_1b', 'maxFD_2a', 'maxFD_2b',
       'tSNR_1a', 'tSNR_1b', 'tSNR_2a', 'tSNR_2b']
df_qa = pd.read_csv(lsd_qa_f, skiprows=1, converters={'subject ID':str})
convert = dict(zip(old, new))
df_qa = df_qa.rename(columns=convert)
df_qa[new] = df_qa[new].convert_objects(convert_numeric=True)
for metric in  ['maxFD', 'meanFD', 'coreg', 'tSNR', 'link']:
    df[metric] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        scan = df['scan'].iloc[idx]
        try: 
            idx_qa = df_qa[df_qa['subject ID'] == subject].index[0]
            df[metric].iloc[idx] = df_qa['%s_%s' % (metric,scan)].loc[idx_qa]
        except:
            pass
del df_qa
df.to_pickle(overview_tidy)

