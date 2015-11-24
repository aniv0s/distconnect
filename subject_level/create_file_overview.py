# -*- coding: utf-8 -*-

import pandas as pd, numpy as np
import os, glob, datetime

# directories
preprocDir = '/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/probands'
surfDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands'
docDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/documents'

# input files
documentation_f = max(glob.iglob('%s/overview_subjects/Participants_List_LargeScaleProject - Overview_*.csv' % docDir), 
                         key=os.path.getctime)
lsd_qa_f = max(glob.iglob('%s/overview_subjects/lemon_lsd_qa - lsd rest_*.csv' % docDir), key=os.path.getctime)
survC_active_f = '/scr/liberia1/data/lsd/behavioral/Surveys/surveyCactive_151013.csv'
survC_inactive_f = '/scr/liberia1/data/lsd/behavioral/Surveys/surveyCinactive_151013.csv'
survC_corrected_f = '/scr/liberia1/data/lsd/behavioral/Surveys/surveyCcorrected_151013.csv'

# output files
date = datetime.datetime.now().strftime("%Y%m%d")
overview = '%s/overview_files/data_overview_%s.pkl' % (docDir,date)
overview_tidy = '%s/overview_files/data_overview_tidy_%s.pkl' % (docDir,date)




###############################################################################
############ overview - compact format (one row per subject) ##################
###############################################################################


########## prep dataframe: gender, age, diagnoses, drug test ##################

# subjects documentation
df_doc = pd.read_csv(documentation_f, skiprows=1, converters={'DB_ID':str, 'SKID_Diagnoses':str, 'Drug_Test (nothing=negative)':str},
                 usecols=['DB_ID', 'SKID_Diagnoses', 'Drug_Test (nothing=negative)'])
df_doc['DB_ID'] = df_doc['DB_ID'].map(lambda x: x[0:5])
df_doc.rename(columns={'DB_ID':'subject', 'SKID_Diagnoses':'skid diagnosis', 'Drug_Test (nothing=negative)':'drug test'}, inplace=True)
df_doc = df_doc[(df_doc['subject'] != '') & (df_doc['subject'] != ' ')]

# all subjects found in directories
subjects_preproc = [x for x in os.listdir(preprocDir) if os.path.isdir(os.path.join(preprocDir, x))]
subjects_surf = [x for x in os.listdir(surfDir) if os.path.isdir(os.path.join(surfDir, x))]
subjects = list(set(subjects_preproc).union(set(subjects_surf)))
df_subjects = pd.DataFrame(data={'subject':subjects})

# demographic data from day of scanning # get age from lemon pp
df_C_active = pd.read_csv(survC_active_f)
df_C_inactive = pd.read_csv(survC_inactive_f)
df_C_corrected = pd.read_csv(survC_corrected_f)
df_C = pd.concat([df_C_active, df_C_inactive, df_C_corrected])
df_C['subject'] = df_C['ID'].map(lambda x: str(x)[0:5])
ageC = pd.Series(pd.to_datetime(df_C['datestamp']) - pd.to_datetime(df_C['GBT']))
df_C['age'] = ageC.dt.days / 365
df_C.rename(columns={'GSH':'gender'}, inplace=True)

# add qa metrics: lsd (lemon will be added soon)
old = ['rest1a ', 'rest1b', 'rest2a', 'rest2b', 'rest1a .1', 'rest1b.1', 'rest2a.1', 'rest2b.1', 
       'rest1a .2', 'rest1b.2', 'rest2a.2', 'rest2b.2', 'rest1a .3', 'rest1b.3', 'rest2a.3', 'rest2b.3',
       'rest1a .4', 'rest1b.4', 'rest2a.4', 'rest2b.4', 'subject ID']
new = ['link_1a', 'link_1b', 'link_2a', 'link_2b', 'coreg_1a', 'coreg_1b', 'coreg_2a', 'coreg_2b', 
       'meanFD_1a', 'meanFD_1b', 'meanFD_2a', 'meanFD_2b', 'maxFD_1a', 'maxFD_1b', 'maxFD_2a', 'maxFD_2b',
       'tSNR_1a', 'tSNR_1b', 'tSNR_2a', 'tSNR_2b', 'subject']
df_qa = pd.read_csv(lsd_qa_f, skiprows=1, converters={'subject ID':str})
df_qa = df_qa.rename(columns=dict(zip(old, new)))
df_qa = df_qa[new]
df_qa[new[:-1]] = df_qa[new[:-1]].convert_objects(convert_numeric=True)

# merge
df = pd.merge(df_subjects, df_C[['subject','gender','age']], how='outer', on='subject')
df = pd.merge(df, df_doc, how='outer', on='subject')
df = pd.merge(df, df_qa, on='subject', how='outer')
del df_C, df_C_active, df_C_inactive, df_C_corrected, df_subjects, df_doc, df_qa

# clean up
df.sort(columns='subject', inplace=True)
df.reset_index(inplace=True, drop=True)

for idx in df.index:
    if df['gender'].iloc[idx] == 'm' or df['gender'].iloc[idx] == 'M':
        df['gender'].iloc[idx] = 'male'
    if df['gender'].iloc[idx] == 'f' or df['gender'].iloc[idx] == 'F':
        df['gender'].iloc[idx] = 'female'

for idx in df.index[pd.isnull(df['skid diagnosis'])]:
    df['skid diagnosis'].iloc[idx] = ''
for idx in df.index:
    if 'nothing' in df['skid diagnosis'].iloc[idx]:
        df['skid diagnosis'].iloc[idx] = ''
    if 'none' in df['skid diagnosis'].iloc[idx]:
        df['skid diagnosis'].iloc[idx] = ''



############ preprocessed resting data, volumes in native space ###############

# lsd
scans = ['1a', '1b', '2a', '2b']
for scan in scans:
    df['lsd_rest%s_native' %scan] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        f = '%s/%s/preprocessed/lsd_resting/rest%s/rest_preprocessed.nii.gz' % (preprocDir, subject, scan)
        if os.path.isfile(f):
            df['lsd_rest%s_native' %scan].iloc[idx] = 1
        else:
            df['lsd_rest%s_native' %scan].iloc[idx] = 0
            
# lemon
df['lemon_rest_native'] = np.nan
for idx in df.index:
    subject = df['subject'].iloc[idx]
    f = '%s/%s/preprocessed/lemon_resting/rest_preprocessed.nii.gz' % (preprocDir, subject)
    if os.path.isfile(f):
        df['lemon_rest_native'].iloc[idx] = 1
    else:
        df['lemon_rest_native'].iloc[idx] = 0


#################### freesurfer surface files #################################

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
            
        
####################### timeseries (raw - incl nan) ###########################

# lsd
for hemi in ['lh', 'rh']:
    for scan in ['1a', '1b', '2a', '2b']:
        df['lsd_surf_raw_%s_%s' % (scan, hemi)] = np.nan
        for idx in df.index:
            subject = df['subject'].iloc[idx]
            f = '%s/%s/resting/%s_lsd_rest_raw_%s_fsa5_%s.mgz' % (surfDir, subject, subject, scan, hemi)
            if os.path.isfile(f):
                df['lsd_surf_raw_%s_%s' % (scan, hemi)].iloc[idx] = 1
            else:
                df['lsd_surf_raw_%s_%s' % (scan, hemi)].iloc[idx] = 0
                
# lemon
for hemi in ['lh', 'rh']:
    df['lemon_surf_raw_%s' % hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        f = '%s/%s/resting/%s_lemon_rest_raw_fsa5_%s.mgz' % (surfDir, subject, subject, hemi)
        if os.path.isfile(f):
            df['lemon_surf_raw_%s' % hemi].iloc[idx] = 1
        else:
            df['lemon_surf_raw_%s' % hemi].iloc[idx] = 0         
                
                
########################### nan counts ########################################
                
# lsd
for hemi in ['lh', 'rh']:
    for scan in ['1a', '1b', '2a', '2b']:
        df['lsd_surf_raw_%s_%s_nan_count' % (scan,hemi)] = np.nan
        for idx in df.index[(df['lsd_surf_raw_%s_%s' % (scan,hemi)] != 0) & (df['lsd_surf_raw_%s_%s' % (scan,hemi)].notnull())]:
            subject = df['subject'].iloc[idx]
            f1 = '%s/%s/resting/%s_lsd_rest_raw_%s_fsa5_%s.mgz' % (surfDir, subject, subject, scan, hemi)
            if os.path.isfile(f1):
                f2 = '%s/%s/resting/%s_lsd_nan_mask_%s_fsa5_%s.npy' % (surfDir, subject, subject, scan, hemi)
                if os.path.isfile(f2):
                    count = np.load(f2).sum()
                    df['lsd_surf_raw_%s_%s_nan_count' % (scan,hemi)].iloc[idx] = count
                else:
                    df['lsd_surf_raw_%s_%s_nan_count' % (scan,hemi)].iloc[idx] = 0
            
# lemon
for hemi in ['lh', 'rh']:
    df['lemon_surf_raw_%s_nan_count' % hemi] = np.nan
    for idx in df.index[(df['lemon_surf_raw_%s' % hemi] != 0) & (df['lemon_surf_raw_%s' % hemi].notnull())]:
        subject = df['subject'].iloc[idx]
        f1 = '%s/%s/resting/%s_lemon_rest_raw_fsa5_%s.mgz' % (surfDir, subject, subject, hemi)
        if os.path.isfile(f1):
            f2 = '%s/%s/resting/%s_lemon_nan_mask_fsa5_%s.npy' % (surfDir, subject, subject, hemi)
            if os.path.isfile(f2):
                count = np.load(f2).sum()
                df['lemon_surf_raw_%s_nan_count' % hemi].iloc[idx] = count
            else:
                df['lemon_surf_raw_%s_nan_count' % hemi].iloc[idx] = 0


#################### timeseries surf (interpolated) ###########################

# lsd
for hemi in ['lh', 'rh']:
    for scan in ['1a', '1b', '2a', '2b']:
        df['lsd_surf_interp_%s_%s' % (scan, hemi)] = np.nan
        for idx in df.index:
            subject = df['subject'].iloc[idx]
            f = '%s/%s/resting/%s_lsd_rest_interp_%s_fsa5_%s.mgz' % (surfDir, subject, subject, scan, hemi)
            if os.path.isfile(f):
                df['lsd_surf_interp_%s_%s' % (scan, hemi)].iloc[idx] = 1
            else:
                df['lsd_surf_interp_%s_%s' % (scan, hemi)].iloc[idx] = 0    
                
# lemon
for hemi in ['lh', 'rh']:
    df['lemon_surf_interp_%s' % hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        f = '%s/%s/resting/%s_lemon_rest_interp_fsa5_%s.mgz' % (surfDir, subject, subject, hemi)
        if os.path.isfile(f):
            df['lemon_surf_interp_%s' % hemi].iloc[idx] = 1
        else:
            df['lemon_surf_interp_%s' % hemi].iloc[idx] = 0             


######################### correlation matrices ################################

# lsd
for hemi in ['lh', 'rh']:
    for scan in ['1a', '1b', '2a', '2b']:
        df['lsd_corr_%s_%s' % (scan, hemi)] = np.nan
        for idx in df.index:
            subject = df['subject'].iloc[idx]
            f = '%s/%s/correlation_maps/%s_lsd_corr_interp_%s_fsa5_%s.npy' % (surfDir, subject, subject, scan, hemi)
            if os.path.isfile(f):
                df['lsd_corr_%s_%s' % (scan, hemi)].iloc[idx] = 1
            else:
                df['lsd_corr_%s_%s' % (scan, hemi)].iloc[idx] = 0

# lemon
for hemi in ['lh', 'rh']:
    df['lemon_corr_%s' % hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        f = '%s/%s/correlation_maps/%s_lemon_corr_interp_fsa5_%s.npy' % (surfDir, subject, subject, hemi)
        if os.path.isfile(f):
            df['lemon_corr_%s' % hemi].iloc[idx] = 1
        else:
            df['lemon_corr_%s' % hemi].iloc[idx] = 0


######################### geodesic distance ###################################

for hemi in ['lh', 'rh']:
    df['geo_distance_%s' %hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        f = '%s/%s/distance_maps/%s_%s_geoDist_fsa5.mat' % (surfDir, subject, subject, hemi)
        if os.path.isfile(f):
            df['geo_distance_%s' %hemi].iloc[idx] = 1
        else:
            df['geo_distance_%s' %hemi].iloc[idx] = 0  

######################### euclidean distance ##################################

for hemi in ['lh', 'rh']:
    df['eucl_distance_%s' %hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        f = '%s/%s/distance_maps/%s_%s_euclDist_fsa5.npy' % (surfDir, subject, subject, hemi)
        if os.path.isfile(f):
            df['eucl_distance_%s' %hemi].iloc[idx] = 1
        else:
            df['eucl_distance_%s' %hemi].iloc[idx] = 0


############################ geo meanDist #####################################

# lsd
for hemi in ['lh', 'rh']:
    for scan in ['1a', '1b', '2a', '2b', '1ab', '2ab', '1ab2ab']:
        for thr in [70, 75, 80, 85, 90, 95, 98]:
                df['lsd_meanDist_geo_%s_%s_%s' % (scan, thr, hemi)] = np.nan
                for idx in df.index:
                    subject = df['subject'].iloc[idx]
                    f = '%s/%s/meanDist/%s_lsd_meanDist_geo_interp_%s_%s_fsa5_%s.npy' % (surfDir, subject, subject, thr, scan, hemi)
                    if os.path.isfile(f):
                        df['lsd_meanDist_geo_%s_%s_%s' % (scan, thr, hemi)].iloc[idx] = 1
                    else:
                        df['lsd_meanDist_geo_%s_%s_%s' % (scan, thr, hemi)].iloc[idx] = 0

# lemon                        
for hemi in ['lh', 'rh']:
        for thr in [70, 75, 80, 85, 90, 95, 98]:
                df['lemon_meanDist_geo_%s_%s' % (thr, hemi)] = np.nan
                for idx in df.index:
                    subject = df['subject'].iloc[idx]
                    f = '%s/%s/meanDist/%s_lemon_meanDist_geo_interp_%s_fsa5_%s.npy' % (surfDir, subject, subject, thr, hemi)
                    if os.path.isfile(f):
                        df['lemon_meanDist_geo_%s_%s' % (thr, hemi)].iloc[idx] = 1
                    else:
                        df['lemon_meanDist_geo_%s_%s' % (thr, hemi)].iloc[idx] = 0


############################ eucl meanDist ####################################

# lsd
for hemi in ['lh', 'rh']:
    for scan in ['1a', '1b', '2a', '2b', '1ab', '2ab', '1ab2ab']:
        for thr in [70, 75, 80, 85, 90, 95, 98]:
                df['lsd_meanDist_eucl_%s_%s_%s' % (scan, thr, hemi)] = np.nan
                for idx in df.index:
                    subject = df['subject'].iloc[idx]
                    f = '%s/%s/meanDist/%s_lsd_meanDist_eucl_interp_%s_%s_fsa5_%s.npy' % (surfDir, subject, subject, thr, scan, hemi)
                    if os.path.isfile(f):
                        df['lsd_meanDist_eucl_%s_%s_%s' % (scan, thr, hemi)].iloc[idx] = 1
                    else:
                        df['lsd_meanDist_eucl_%s_%s_%s' % (scan, thr, hemi)].iloc[idx] = 0

# lemon                        
for hemi in ['lh', 'rh']:
        for thr in [70, 75, 80, 85, 90, 95, 98]:
                df['lemon_meanDist_eucl_%s_%s' % (thr, hemi)] = np.nan
                for idx in df.index:
                    subject = df['subject'].iloc[idx]
                    f = '%s/%s/meanDist/%s_lemon_meanDist_eucl_interp_%s_fsa5_%s.npy' % (surfDir, subject, subject, thr, hemi)
                    if os.path.isfile(f):
                        df['lemon_meanDist_eucl_%s_%s' % (thr, hemi)].iloc[idx] = 1
                    else:
                        df['lemon_meanDist_eucl_%s_%s' % (thr, hemi)].iloc[idx] = 0


###############################################################################
# save
df.to_pickle(overview)
del df





###############################################################################
#################### overview - tidy data format ##############################
###############################################################################



########## prep dataframe: gender, age, diagnoses, drug test ##################

# subjects documentation
df_doc = pd.read_csv(documentation_f, skiprows=1, converters={'DB_ID':str, 'SKID_Diagnoses':str, 'Drug_Test (nothing=negative)':str},
                 usecols=['DB_ID', 'SKID_Diagnoses', 'Drug_Test (nothing=negative)'])
df_doc['DB_ID'] = df_doc['DB_ID'].map(lambda x: x[0:5])
df_doc.rename(columns={'DB_ID':'subject', 'SKID_Diagnoses':'skid diagnosis', 'Drug_Test (nothing=negative)':'drug test'}, inplace=True)
df_doc = df_doc[(df_doc['subject'] != '') & (df_doc['subject'] != ' ')]

# all subjects found in directories
subjects_preproc = [x for x in os.listdir(preprocDir) if os.path.isdir(os.path.join(preprocDir, x))]
subjects_surf = [x for x in os.listdir(surfDir) if os.path.isdir(os.path.join(surfDir, x))]
subjects = list(set(subjects_preproc).union(set(subjects_surf)))
df_subjects = pd.DataFrame(data={'subject':subjects})

# demographic data from day of scanning # get age from lemon pp
df_C_active = pd.read_csv(survC_active_f)
df_C_inactive = pd.read_csv(survC_inactive_f)
df_C_corrected = pd.read_csv(survC_corrected_f)
df_C = pd.concat([df_C_active, df_C_inactive, df_C_corrected])
df_C['subject'] = df_C['ID'].map(lambda x: str(x)[0:5])
ageC = pd.Series(pd.to_datetime(df_C['datestamp']) - pd.to_datetime(df_C['GBT']))
df_C['age'] = ageC.dt.days / 365
df_C.rename(columns={'GSH':'gender'}, inplace=True)

# merge
df = pd.merge(df_subjects, df_C[['subject','gender','age']], how='outer', on='subject')
df = pd.merge(df, df_doc, how='outer', on='subject')
del df_C, df_C_active, df_C_inactive, df_C_corrected, df_subjects, df_doc

# prep for 'tidy' format (5 measurements: lsd 1a, 2a, 2b, 2c, lemon)
df = pd.concat([df,df,df,df,df])

# sort
df.sort(columns='subject', inplace=True)
df.reset_index(inplace=True, drop=True)

# label measurements
df['scan'] = pd.Series(['1a', '1b', '2a', '2b', 'lemon'] * (len(df)/5), index=df.index)

# clean up
for idx in df.index:
    if df['gender'].iloc[idx] == 'm' or df['gender'].iloc[idx] == 'M':
        df['gender'].iloc[idx] = 'male'
    if df['gender'].iloc[idx] == 'f' or df['gender'].iloc[idx] == 'F':
        df['gender'].iloc[idx] = 'female'

for idx in df.index[pd.isnull(df['skid diagnosis'])]:
    df['skid diagnosis'].iloc[idx] = ''
for idx in df.index:
    if 'nothing' in df['skid diagnosis'].iloc[idx]:
        df['skid diagnosis'].iloc[idx] = ''
    if 'none' in df['skid diagnosis'].iloc[idx]:
        df['skid diagnosis'].iloc[idx] = ''


############## preprocessed resting data, volumes in native space #############

df['rest_native'] = np.nan
for idx in df.index:
    subject = df['subject'].iloc[idx]
    scan = df['scan'].iloc[idx]
    if scan == 'lemon':
        f = '%s/%s/preprocessed/lemon_resting/rest_preprocessed.nii.gz' % (preprocDir, subject)
        if os.path.isfile(f):
            df['rest_native'].iloc[idx] = 1
        else:
            df['rest_native'].iloc[idx] = 0
    else:
        f = '%s/%s/preprocessed/lsd_resting/rest%s/rest_preprocessed.nii.gz' % (preprocDir, subject, scan)
        if os.path.isfile(f):
            df['rest_native'].iloc[idx] = 1
        else:
            df['rest_native'].iloc[idx] = 0
        
        
######################## freesurfer surface files #############################

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
                        
                        
##################### timeseries (raw - incl nan) #############################
                        
for hemi in ['lh', 'rh']:
    df['surf_raw_%s' % hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        scan = df['scan'].iloc[idx]
        if scan == 'lemon':
            f = '%s/%s/resting/%s_lemon_rest_raw_fsa5_%s.mgz' % (surfDir, subject, subject, hemi)
            if os.path.isfile(f):
                df['surf_raw_%s' % hemi].iloc[idx] = 1
            else:
                df['surf_raw_%s' % hemi].iloc[idx] = 0
        else:   
            f = '%s/%s/resting/%s_lsd_rest_raw_%s_fsa5_%s.mgz' % (surfDir, subject, subject, scan, hemi)
            if os.path.isfile(f):
                df['surf_raw_%s' % hemi].iloc[idx] = 1
            else:
                df['surf_raw_%s' % hemi].iloc[idx] = 0
            

############################# nan counts ######################################

for hemi in ['lh', 'rh']:
    df['surf_raw_%s_nan_count' % hemi] = np.nan
    for idx in df.index[(df['surf_raw_%s' % hemi] != 0) & (df['surf_raw_%s' % hemi].notnull())]:
        subject = df['subject'].iloc[idx]
        scan = df['scan'].iloc[idx]
        if scan == 'lemon':
            f1 = '%s/%s/resting/%s_lemon_rest_raw_fsa5_%s.mgz' % (surfDir, subject, subject, hemi)
            if os.path.isfile(f1):
                f2 = '%s/%s/resting/%s_lemon_nan_mask_fsa5_%s.npy' % (surfDir, subject, subject, hemi)
                if os.path.isfile(f2):
                    count = np.load(f2).sum()
                    df['surf_raw_%s_nan_count' % hemi].iloc[idx] = count
                else:
                    df['surf_raw_%s_nan_count' % hemi].iloc[idx] = 0
        else:
            f1 = '%s/%s/resting/%s_lsd_rest_raw_%s_fsa5_%s.mgz' % (surfDir, subject, subject, scan, hemi)
            if os.path.isfile(f1):
                f2 = '%s/%s/resting/%s_lsd_nan_mask_%s_fsa5_%s.npy' % (surfDir, subject, subject, scan, hemi)
                if os.path.isfile(f2):
                    count = np.load(f2).sum()
                    df['surf_raw_%s_nan_count' % hemi].iloc[idx] = count
                else:
                    df['surf_raw_%s_nan_count' % hemi].iloc[idx] = 0
              

#################### timeseries surf (interpolated) ###########################

for hemi in ['lh', 'rh']:
    df['surf_interp_%s' % hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        scan = df['scan'].iloc[idx]
        if scan == 'lemon':
            f = '%s/%s/resting/%s_lemon_rest_interp_fsa5_%s.mgz' % (surfDir, subject, subject, hemi)
            if os.path.isfile(f):
                df['surf_interp_%s' % hemi].iloc[idx] = 1
            else:
                df['surf_interp_%s' % hemi].iloc[idx] = 0
        else:
            f = '%s/%s/resting/%s_lsd_rest_interp_%s_fsa5_%s.mgz' % (surfDir, subject, subject, scan, hemi)
            if os.path.isfile(f):
                df['surf_interp_%s' % hemi].iloc[idx] = 1
            else:
                df['surf_interp_%s' % hemi].iloc[idx] = 0
            

########################### correlation matrices ##############################

for hemi in ['lh', 'rh']:
    df['corr_%s' % hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        scan = df['scan'].iloc[idx]
        if scan == 'lemon':
            f = '%s/%s/correlation_maps/%s_lemon_corr_interp_fsa5_%s.npy' % (surfDir, subject, subject, hemi)
            if os.path.isfile(f):
                df['corr_%s' % hemi].iloc[idx] = 1
            else:
                df['corr_%s' % hemi].iloc[idx] = 0
        else:
            f = '%s/%s/correlation_maps/%s_lsd_corr_interp_%s_fsa5_%s.npy' % (surfDir, subject, subject, scan, hemi)
            if os.path.isfile(f):
                df['corr_%s' % hemi].iloc[idx] = 1
            else:
                df['corr_%s' % hemi].iloc[idx] = 0
            

############################# geodesic distance ###############################

for hemi in ['lh', 'rh']:
    df['distance_%s' %hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        f = '%s/%s/distance_maps/%s_%s_geoDist_fsa5.mat' % (surfDir, subject, subject, hemi)
        if os.path.isfile(f):
            df['distance_%s' %hemi].iloc[idx] = 1
        else:
            df['distance_%s' %hemi].iloc[idx] = 0    

########################### euclidean distance ################################

for hemi in ['lh', 'rh']:
    df['distance_%s' %hemi] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        f = '%s/%s/distance_maps/%s_%s_euclDist_fsa5.npy' % (surfDir, subject, subject, hemi)
        if os.path.isfile(f):
            df['distance_%s' %hemi].iloc[idx] = 1
        else:
            df['distance_%s' %hemi].iloc[idx] = 0    


############################ qa metrics #######################################

old = ['rest1a ', 'rest1b', 'rest2a', 'rest2b', 'rest1a .1', 'rest1b.1', 'rest2a.1', 'rest2b.1', 
       'rest1a .2', 'rest1b.2', 'rest2a.2', 'rest2b.2', 'rest1a .3', 'rest1b.3', 'rest2a.3', 'rest2b.3',
       'rest1a .4', 'rest1b.4', 'rest2a.4', 'rest2b.4']
new = ['link_1a', 'link_1b', 'link_2a', 'link_2b', 'coreg_1a', 'coreg_1b', 'coreg_2a', 'coreg_2b', 
       'meanFD_1a', 'meanFD_1b', 'meanFD_2a', 'meanFD_2b', 'maxFD_1a', 'maxFD_1b', 'maxFD_2a', 'maxFD_2b',
       'tSNR_1a', 'tSNR_1b', 'tSNR_2a', 'tSNR_2b']

df_qa = pd.read_csv(lsd_qa_f, skiprows=1, converters={'subject ID':str})
df_qa = df_qa.rename(columns=dict(zip(old, new)))
df_qa[new] = df_qa[new].convert_objects(convert_numeric=True)
for metric in  ['maxFD', 'meanFD', 'coreg', 'tSNR', 'link']:
    df[metric] = np.nan
    for idx in df.index:
        subject = df['subject'].iloc[idx]
        scan = df['scan'].iloc[idx]
        if scan in ['1a', '1b', '2a', '2b']:
            try: 
                idx_qa = df_qa[df_qa['subject ID'] == subject].index[0]
                df[metric].iloc[idx] = df_qa['%s_%s' % (metric,scan)].loc[idx_qa]
            except:
                pass
del df_qa

# save
df.to_pickle(overview_tidy)

