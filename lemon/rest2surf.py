__author__ = 'oligschlager'

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
from nipype.interfaces.freesurfer import SampleToSurface
from os import listdir
from os.path import isdir

'''
Script to resample lsd functional  time-series to surface space
----------------------------------------------------------------
picks all subjects that have a lsd rest_preprocessed.nii.gz
'''

'''directories'''
preprocDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/probands"
freesurferDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"
workingDir = "/scr/liberia1/data/lemon/vol2surf_workingDir"
sinkDir = "/scr/liberia1/data/lemon"

'''subjects'''
#subjects = ['08747']
subjects = [sub for sub in os.listdir(preprocDir) if os.path.isdir(os.path.join(preprocDir, sub))]

'''workflow'''
if __name__ == '__main__':
    wf = pe.Workflow(name="map_to_surface")
    wf.base_dir = workingDir
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"

    subjects_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subjects_infosource")
    subjects_infosource.iterables = ('subject_id', subjects)

    template_infosource = pe.Node(util.IdentityInterface(fields=['fsaverage']), name="template_infosource")
    template_infosource.iterables = ('fsaverage', ['fsaverage4', 'fsaverage5'])

    hemi_infosource = pe.Node(util.IdentityInterface(fields=['hemi']), name="hemi_infosource")
    hemi_infosource.iterables = ('hemi', ['lh', 'rh'])

    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id'],
                                          outfields=['resting_lemon']),
                          name="datagrabber")
    datagrabber.inputs.base_directory = preprocDir
    datagrabber.inputs.template = '%s/preprocessed/lemon_resting/rest_preprocessed.nii.gz'
    datagrabber.inputs.template_args['resting_lemon'] = [['subject_id']]
    datagrabber.inputs.sort_filelist = True
    datagrabber.inputs.raise_on_empty = False

    vol2surf = pe.Node(SampleToSurface(subjects_dir=freesurferDir,
                                       args='--surfreg sphere.reg',
                                       reg_header=True,
                                       cortex_mask=True,
                                       sampling_method="average",
                                       sampling_range=(0.2, 0.8, 0.1),
                                       sampling_units="frac",
                                       smooth_surf=6.0),
                       name='vol2surf_lsd')


    def gen_out_file(subject_id, hemi, fsaverage):
        return "%s_lemon_%s_%s.mgz" % (subject_id, fsaverage, hemi)
    output_name = pe.Node(util.Function(input_names=['subject_id', 'hemi', 'fsaverage'],
                                        output_names=['name'],
                                        function=gen_out_file),
                          name="output_name")

    datasink = pe.Node(nio.DataSink(parameterization=False, base_directory=sinkDir), name='sinker')

    wf.connect([(subjects_infosource, datagrabber, [('subject_id', 'subject_id')]),
                (subjects_infosource, output_name, [('subject_id', 'subject_id')]),
                (template_infosource, output_name, [('fsaverage', 'fsaverage')]),
                (hemi_infosource, output_name, [('hemi', 'hemi')]),
                (subjects_infosource, vol2surf, [('subject_id', 'subject_id')]),
                (hemi_infosource, vol2surf, [('hemi', 'hemi')]),
                (template_infosource, vol2surf, [('fsaverage', 'target_subject')]),
                (datagrabber, vol2surf, [('resting_lemon', 'source_file')]),
                (output_name, vol2surf, [('name', 'out_file')]),
                (vol2surf, datasink, [('out_file', 'lemon_rest_surf')])
                ])

    #wf.run(plugin="CondorDAGMan")
    wf.run()