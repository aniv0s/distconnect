
def meanDist(sub):
    import glob
    import os.path
    import nibabel as nib
    import numpy as np
    import h5py

    baseDir = "/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands"
    fsDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"

    #subjects = [sub for sub in os.listdir(baseDir) if os.path.isdir(os.path.join(baseDir, sub))]

    combi_dict = {'1ab': ['1a', '1b'], '2ab': ['2a', '2b'], '1ab2ab': ['1a', '1b', '2a', '2b']}

    for hemi in ['lh', 'rh']:
        cort = np.sort(nib.freesurfer.io.read_label('%s/fsaverage5/label/%s.cortex.label' % (fsDir, hemi)))

        #for sub in subjects:
        dist_f = '%s/%s/distance_maps/%s_%s_geoDist_fsa5.mat' % (baseDir, sub, sub, hemi)
        corr_f_list = glob.glob('%s/%s/correlation_maps/%s_lsd_corr_interp_*_fsa5_%s.npy' % (baseDir, sub, sub, hemi))

        if (os.path.isfile(dist_f)):
            print sub, hemi
            # normalized distance matrix
            with h5py.File(dist_f, 'r') as f:
                dist = f['dataAll'][()]
            dist_cort = dist[cort, :][:, cort]
            dist_cort_scaled = ((dist_cort - dist_cort.min()) / (dist_cort.max() - dist_cort.min())) * (1 - 0) + 0
            del dist, dist_cort

            # single correlation matrix
            for corr_f in corr_f_list:
                corr = np.load(corr_f)
                corr[np.diag_indices_from(corr)] = 0 # to leave them out in meanDist calculation
                corr_cort = corr[cort, :][:, cort]

                # meanDist
                for thr in [70, 75, 80, 85, 90, 95, 98]:
                    print thr
                    meanDist_cort = np.zeros((len(cort)))
                    meanDist = np.zeros((10242))
                    for node in range(len(cort)):
                        cutoff = np.percentile(corr_cort[node], thr)
                        dist_masked = dist_cort_scaled[node][corr_cort[node] > cutoff]
                        meanDist_cort[node] = dist_masked.mean()
                    meanDist[cort] = meanDist_cort
                    meanDist_f = corr_f.replace('/correlation_maps/',
                                                '/meanDist/').replace('corr_interp_',
                                                                    'meanDist_interp_%s_' % thr)
                    np.save(meanDist_f, meanDist)


            # averaging correlation matrices & meanDist
            if (len(corr_f_list) == 4):
                for combi in combi_dict.keys():
                    print combi

                    corr_combi = np.zeros((10242,10242))
                    for scan in combi_dict[combi]:
                        print scan
                        corr_f = '%s/%s/correlation_maps/%s_lsd_corr_interp_%s_fsa5_%s.npy' % (baseDir, sub, sub, scan, hemi)
                        corr = np.load(corr_f)
                        corr_combi = corr_combi + corr
                        del corr
                    corr_mean = corr_combi / len(combi_dict[combi])
                    del corr_combi

                    corr_mean[np.diag_indices_from(corr_mean)] = 0 # to leave them out in meanDist calculation
                    corr_mean_cort = corr_mean[cort, :][:, cort]

                    # mean distance
                    for thr in [70, 75, 80, 85, 90, 95, 98]:
                        print thr
                        meanDist_cort = np.zeros((len(cort)))
                        meanDist = np.zeros((10242))
                        for node in range(len(cort)):
                            cutoff = np.percentile(corr_mean_cort[node], thr)
                            dist_masked = dist_cort_scaled[node][corr_mean_cort[node] > cutoff]
                            meanDist_cort[node] = dist_masked.mean()
                        meanDist[cort] = meanDist_cort
                        meanDist_f = '%s/%s/meanDist/%s_lsd_meanDist_interp_%s_%s_fsa5_%s.npy' % (baseDir, sub, sub, thr, combi, hemi)
                        np.save(meanDist_f, meanDist)
