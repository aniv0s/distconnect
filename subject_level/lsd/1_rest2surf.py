# -*- coding: utf-8 -*-

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
from nipype.interfaces.freesurfer import SampleToSurface

preprocDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/probands"
freesurferDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"
workingDir = "/scr/liberia1/data/lsd/surface/rest2surf/vol2surf_workingDir"
sinkDir = "/scr/liberia1/data/lsd/surface/rest2surf"

subjects = ['26693', '27773', '27895', '28036', '28098']


'''workflow'''
if __name__ == '__main__':
    wf = pe.Workflow(name="map_to_surface")
    wf.base_dir = workingDir
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"

    infosource = pe.Node(util.IdentityInterface(fields=['subject_id', 'scan', 'hemi']), name="infosource")
    infosource.iterables = [('subject_id', subjects),
                            ('scan', ['1a', '1b', '2a', '2b']),
                            ('hemi', ['lh', 'rh'])]


    selectfiles_templates = {'resting_lsd': '{subject_id}/preprocessed/lsd_resting/rest{scan}/rest_preprocessed.nii.gz'}


    selectfiles = pe.Node(nio.SelectFiles(selectfiles_templates,
                                       base_directory=preprocDir),
                       name="selectfiles")
    
    


    vol2surf = pe.Node(SampleToSurface(subjects_dir=freesurferDir,
                                       target_subject='fsaverage5',
                                       args='--surfreg sphere.reg',
                                       reg_header=True,
                                       cortex_mask=True,
                                       sampling_method="average",
                                       sampling_range=(0.2, 0.8, 0.1),
                                       sampling_units="frac",
                                       smooth_surf=6.0),
                       name='vol2surf_lsd')

    def gen_out_file(subject_id, scan, hemi):
        return "%s_lsd_rest_raw_%s_fsa5_%s.mgz" % (subject_id, scan, hemi)
    output_name = pe.Node(util.Function(input_names=['subject_id', 'scan', 'hemi'],
                                        output_names=['name'],
                                        function=gen_out_file),
                          name="output_name")

    datasink = pe.Node(nio.DataSink(parameterization=False, base_directory=sinkDir), name='sinker')

    wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id')]),
                (infosource, selectfiles, [('scan', 'scan')]),
                (infosource, output_name, [('subject_id', 'subject_id')]),
                (infosource, output_name, [('scan', 'scan')]),
                (infosource, output_name, [('hemi', 'hemi')]),
                (infosource, vol2surf, [('subject_id', 'subject_id')]),
                (infosource, vol2surf, [('hemi', 'hemi')]),
                (selectfiles, vol2surf, [('resting_lsd', 'source_file')]),
                (output_name, vol2surf, [('name', 'out_file')]),
                (vol2surf, datasink, [('out_file', 'LSD_rest_surf')])
                ])
    wf.write_graph(dotfilename='wf_rest2surf.dot', graph2use='colored', format='pdf', simple_form=True)
    wf.run(plugin='MultiProc', plugin_args={'n_procs' : 5})
    #wf.run()