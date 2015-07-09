__author__ = 'oligschlager'


import numpy as np
import nibabel as nib
from surfer import Brain


def vizBrain(data, subject_id='fsaverage5', hemi='lh', surface='pial', filename='brain.png'):
    brain = Brain(subject_id, hemi, surface)
    dmin = data.min()+(data.std()/2)
    dmax = data.max()-(data.std()/2)
    brain.add_data(data, dmin, dmax, colormap="hot", alpha=0.7)
    brain.save_montage(filename, order=['lat', 'med'], orientation='h', border_size=10)


def nan_replace_interpolation(surf_data, surf_file):
    surf_faces = nib.freesurfer.io.read_geometry(surf_file)[1]
    while True in np.isnan(surf_data):
        nans = np.unique(np.where(np.isnan(surf_data))[0])
        bad = []
        good = {}
        for node in nans:
            neighbors = np.unique(surf_faces[np.where(np.in1d(surf_faces.ravel(), [node]).reshape(surf_faces.shape))[0]])
            bad_neighbors = neighbors[np.unique(np.where(np.isnan(surf_data[neighbors]))[0])]
            good_neighbors = np.setdiff1d(neighbors, bad_neighbors)
            bad.append((node, len(bad_neighbors)))
            good[node] = good_neighbors
        bad = np.array(bad).transpose()
        nodes_with_least_bad_neighbors = bad[0][bad[1] == np.min(bad[1])]
        for node in nodes_with_least_bad_neighbors:
            surf_data[node] = np.mean(surf_data[list(good[node])], axis=0)
    return np.expand_dims(np.expand_dims(surf_data, axis=1), axis=1)


def run_corr_combined(scanfile1, scanfile2, cort):
    restNorm = []
    corr_all = np.zeros((10242, 10242))
    for scan in [scanfile1, scanfile2]:
        rest = nib.load(scan).get_data().squeeze()[cort, :]
        restNorm.extend((rest.transpose() - rest.mean(axis=1)) / rest.std(axis=1))
    corr = np.corrcoef(np.array(restNorm).transpose())
    corr_all[np.ix_(cort, cort)] = corr
    return corr_all


def run_meanDist(corr_mat, dist_scaled_mat, cort, thr):
                corr_cort = corr_mat[cort, :][:, cort]
                meanDist_cort = np.zeros((len(cort)))
                meanDist_all = np.zeros((10242))
                for node in range(len(cort)):
                    cutoff = np.percentile(corr_cort[node], thr)
                    dist_masked = dist_scaled_mat[node][corr_cort[node] > cutoff]
                    meanDist_cort[node] = dist_masked.mean()
                meanDist_all[cort] = meanDist_cort
                return meanDist_all













