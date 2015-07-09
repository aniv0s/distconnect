__author__ = 'oligschlager'

import nibabel as nib
import numpy as np
import os as os
import pandas as pd

'''directories'''
inputDir_point = "/scr/liberia1/data/lsd/surface/rest2surf_point02"
inputDir_average = "/scr/liberia1/data/lsd/surface/testing/LSD_rest2surf_0208"


subjects = [name for name in os.listdir('/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/probands/')
            if os.path.isdir('/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/probands/%s' %name)]


idx = []
nan_count_point = []
nan_count_average = []
nan_count_diff = []


for sub in subjects:
    for scan in ['1a', '1b', '2a', '2b']:
        for hemi in ['lh', 'rh']:

                funcFile_point = '%s/%s_lsd_rest%s_preprocessed_fsaverage5_%s.mgz' \
                                 % (inputDir_point, sub, scan, hemi)
                funcFile_average = '%s/lsd_rest%s_%s_preprocessed_fsaverage5_%s.mgz' \
                                   % (inputDir_average, scan, sub, hemi)

                if os.path.exists(funcFile_point) & os.path.exists(funcFile_average):

                    surf_average = nib.load(funcFile_average).get_data().squeeze().transpose()
                    if True in np.isnan(surf_average):
                        count_average = len(np.squeeze(np.where(np.isnan(surf_average[0]))))
                        del surf_average
                        surf_point = nib.load(funcFile_point).get_data().squeeze().transpose()
                        count_point = len(np.squeeze(np.where(np.isnan(surf_point[0]))))
                        del surf_point

                        idx.append('%s_%s_%s' %(sub, scan, hemi))
                        nan_count_point.append(count_point)
                        nan_count_average.append(count_average)
                        nan_count_diff.append(count_average-count_point)


df = pd.DataFrame(index=idx, data={'nan_count_point': nan_count_point, 'nan_count_average': nan_count_average, 'diff_average-point': nan_count_diff})
#df.sort(columns='nan_count_average', ascending=False).to_csv('/scr/liberia1/data/lsd/surface/nan_counts_sorted.txt', sep='\t')
