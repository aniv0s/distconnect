# -*- coding: utf-8 -*-


def euclDist(subject):

    import numpy as np
    import nibabel.freesurfer.io as fs
    from scipy.spatial import distance_matrix
    
    fsDir = '/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer'
    surfDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands'
    
    for hemi in ['lh', 'rh']:
        
        # fsaverage5 coords on sphere
        fsa5_sphere_coords = fs.read_geometry('%s/fsaverage5/surf/%s.sphere' % (fsDir, hemi))[0]
        cort = fs.read_label('%s/fsaverage5/label/%s.cortex.label' % (fsDir, hemi))
     
        # get corresponding nodes on subject sphere (find coords of high-dim subject surface closest to fsa5 nodes in sphere space)
        subj_sphere_coords = fs.read_geometry('%s/%s/surf/%s.sphere' % (fsDir, subject, hemi))[0]
        subj_indices = []
        for node in cort:
            dist2all = np.squeeze(distance_matrix(np.expand_dims(fsa5_sphere_coords[node], axis=0), subj_sphere_coords))
            subj_indices.append(list(dist2all).index(min(dist2all)))
        
        # pair-wise euclidean distance between included nodes on subject surface (midline)
        subj_surf_coords_pial = fs.read_geometry('%s/%s/surf/%s.pial' % (fsDir, subject, hemi))[0]
        subj_surf_coords_wm = fs.read_geometry('%s/%s/surf/%s.smoothwm' % (fsDir, subject, hemi))[0]
        subj_surf_coords = (subj_surf_coords_pial + subj_surf_coords_wm) / 2.
        
        euclDist = np.zeros((10242,10242))
        euclDist[np.ix_(cort, cort)] = distance_matrix(subj_surf_coords[subj_indices,:],subj_surf_coords[subj_indices,:])
        np.save('%s/%s/distance_maps/%s_%s_euclDist_fsa5' % (surfDir, subject, subject, hemi), euclDist)
            
