
import glob
import nibabel as nib
import numpy as np
import os
import os.path
from surfer import Brain


fsDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"
dataDir = "/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands"

for hemi in ['lh', 'rh']:
    for rest_raw_f in glob.glob('%s/*/resting/*_lsd_rest_raw_*_fsa5_%s.mgz' % (dataDir, hemi)):
        rest_interp_f = rest_raw_f.replace('_raw_', '_interp_')
        mask_f = rest_raw_f.replace('rest_raw', 'nan_mask').replace('.mgz', '')
        mask_img_f = rest_raw_f.replace('rest_raw', 'nan_mask').replace('.mgz', '.png')

        if not os.path.isfile(rest_interp_f):
            surf_img = nib.load(rest_raw_f)
            surf_data = surf_img.get_data()

            if True in np.isnan(surf_data):
                print rest_interp_f
                surf_data = surf_data.squeeze()
                surf_f = '%s/fsaverage5/surf/%s.orig' % (fsDir, hemi)
                surf_faces = nib.freesurfer.io.read_geometry(surf_f)[1]
                mask = np.zeros((10242))

                while True in np.isnan(surf_data):
                    nans = np.unique(np.where(np.isnan(surf_data))[0])
                    mask[nans] = 1
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

                brain = Brain('fsaverage5', hemi, 'pial', curv=False)
                brain.add_data(mask, mask.min(), mask.max(), colormap="spectral", alpha=0.6)
                brain.save_montage(mask_img_f, order=['lat', 'med'], orientation='h', border_size=10)
                np.save(mask_f, mask)


            surf_img.to_filename(rest_interp_f)