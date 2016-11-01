
import glob
import os.path
import nibabel as nib
import numpy as np

'''directories'''
baseDir = "/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands"
fsDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"

for hemi in ['lh', 'rh']:
    cort = np.sort(nib.freesurfer.io.read_label('%s/fsaverage5/label/%s.cortex.label' % (fsDir, hemi)))
    file_list = glob.glob('%s/*/resting/*_lsd_rest_interp_*_fsa5_%s.mgz' % (baseDir, hemi))

    for n, rest_f in enumerate(file_list):
        corr_f = rest_f.replace('resting',
                                'correlation_maps').replace('_rest_',
                                                            '_corr_').replace('.mgz', '')
        if not os.path.isfile(corr_f + '.npy'):
            print os.path.basename(corr_f)
            data = nib.load(rest_f).get_data().squeeze()
            corr_cort = np.corrcoef(data[cort])
            corr = np.zeros((len(data), len(data)))
            corr[np.ix_(cort, cort)] = corr_cort
            np.save(corr_f, corr)