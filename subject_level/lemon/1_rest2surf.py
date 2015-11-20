# -*- coding: utf-8 -*-

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
from nipype.interfaces.freesurfer import SampleToSurface

preprocDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/probands"
freesurferDir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer"
workingDir = "/scr/liberia1/data/lemon/surface/rest2surf/vol2surf_workingDir"
sinkDir = "/scr/liberia1/data/lemon/surface/rest2surf"


subjects = ['03820', '08747', '13081', '13753', '21923', '22872', '23197', '23269', 
            '23302', '23305', '23353', '23426', '23428', '23429', '23464', '23514', 
            '23574', '23576', '23602', '23629', '23649', '23650', '23651', '23668', 
            '23688', '23689', '23697', '23700', '23705', '23708', '23713', '23734', 
            '23741', '23780', '23850', '23860', '23861', '23884', '23886', '23946', 
            '23947', '23948', '23960', '23963', '23965', '23983', '23985', '24002', 
            '24010', '24024', '24050', '24057', '24061', '24102', '24134', '24246', 
            '24247', '24275', '24444', '24445', '24587', '24614', '24691', '24700', 
            '24703', '24707', '24715', '24719', '24720', '24730', '24731', '24732', 
            '24756', '24757', '24759', '24766', '24772', '24773', '24774', '24790', 
            '24843', '24844', '24877', '24899', '24915', '24944', '24945', '25019', 
            '25036', '25081', '25171', '25177', '25188', '25192', '25194', '25195', 
            '25197', '25199', '25200', '25201', '25260', '25264', '25274', '25283', 
            '25326', '25524', '25552', '26436', '26449', '26489', '26526', '26571', 
            '26589', '26591', '26617', '26619', '26626', '26635', '26642', '26674', 
            '26687', '26719', '26723', '26724', '26728', '26753', '26782', '26789', 
            '26793', '26801', '26802', '26803', '26804', '26805', '26806', '26820', 
            '26839', '26841', '26842', '26843', '26844', '26854', '26856', '26857', 
            '26858', '26926', '26980', '27109', '27110', '27111', '27112', '27134', 
            '27174', '27325', '27345', '27346', '27353', '27354', '27360', '27361', 
            '27372', '27428', '27565', '27566', '27611', '27612', '27614', '27616', 
            '27619', '27622', '27683', '27696', '27722', '27774', '27833', '27834', 
            '27864', '27868', '27880', '27892', '27910', '27937', '27951', '27954', 
            '27963', '27968', '27969', '27990']


'''workflow'''
if __name__ == '__main__':
    wf = pe.Workflow(name="map_to_surface")
    wf.base_dir = workingDir
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"

    infosource = pe.Node(util.IdentityInterface(fields=['subject_id', 'hemi']), name="infosource")
    infosource.iterables = [('subject_id', subjects),
                            ('hemi', ['lh', 'rh'])]


    selectfiles_templates = {'resting_lemon': '{subject_id}/preprocessed/lemon_resting/rest_preprocessed.nii.gz'}
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
                       name='vol2surf_lemon')

    def gen_out_file(subject_id, hemi):
        return "%s_lemon_rest_raw_fsa5_%s.mgz" % (subject_id, hemi)
    output_name = pe.Node(util.Function(input_names=['subject_id', 'hemi'],
                                        output_names=['name'],
                                        function=gen_out_file),
                          name="output_name")

    datasink = pe.Node(nio.DataSink(parameterization=False, base_directory=sinkDir), name='sinker')

    wf.connect([(infosource, selectfiles, [('subject_id', 'subject_id')]),
                (infosource, output_name, [('subject_id', 'subject_id')]),
                (infosource, output_name, [('hemi', 'hemi')]),
                (infosource, vol2surf, [('subject_id', 'subject_id')]),
                (infosource, vol2surf, [('hemi', 'hemi')]),
                (selectfiles, vol2surf, [('resting_lemon', 'source_file')]),
                (output_name, vol2surf, [('name', 'out_file')]),
                (vol2surf, datasink, [('out_file', 'LEMON_rest_surf')])
                ])
    wf.write_graph(dotfilename='wf_rest2surf.dot', graph2use='colored', format='pdf', simple_form=True)
    wf.run(plugin='MultiProc', plugin_args={'n_procs' : 5})
    #wf.run()