
import os
import subprocess
import nibabel as nib

dataDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands'
fsDir = '/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer'

subjects = [sub for sub in os.listdir(dataDir) if os.path.isdir(os.path.join(dataDir, sub))]

for hemi in ['lh', 'rh']:
    labels = nib.freesurfer.io.read_annot('%s/fsaverage5/label/lh.aparc.a2009s.annot' %fsDir)[2]

    for sub in subjects:
        subDir_label_native = '%s/%s/labels/native' % (dataDir, sub)
        subDir_label_fsa5 = '%s/%s/labels/fsa5' % (dataDir, sub)

        # transform individual annot file to individual label files
        cml_annot2label = 'mri_annotation2label --sd %s  --subject %s --hemi %s --annotation aparc.a2009s --outdir %s' % (fsDir, sub, hemi, subDir_label_native)
        subprocess.call(cml_annot2label, shell=True)

        # transform individual label files from native to fsa5 surface space
        for label in labels:
            cml_sub2fsa5 = 'mri_label2label --sd %s --srcsubject %s --srclabel %s/%s.%s.label --trgsubject fsaverage5 --trglabel %s/%s.%s_fsa5 --regmethod surface --hemi %s' % \
                           (fsDir, sub, subDir_label_native, hemi, label, subDir_label_fsa5, hemi, label, hemi)
            subprocess.call(cml_sub2fsa5, shell=True)