__author__ = 'oligschlager'



import os, os.path, glob, shutil
from nipype.pipeline.engine import Node, Workflow
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
from nipype import config
from meanDist import meanDist_geo, meanDist_eucl

######################
# specfiy
######################

func = meanDist_eucl
distype = 'geo' # 'eucl'
wd_dir = '/scr/liberia1/data/distconnect/new_meanDists/wd_%s' % distype
sink_dir = '/scr/liberia1/data/distconnect/new_meanDists/results_%s' % distype

subjects_list = ['...', '...']


###############################################################################
# copying input data from afs directory to scr so that condor can be used
###############################################################################

srcDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands'
trgtDir = '/scr/kansas1/data/lsd-lemon'

for subject in subjects_list:
    for f_type in ['%s/%s/distance_maps/*eucl*', 
                   '%s/%s/correlation_maps/*lsd_corr_interp*.npy']:
    
        for f_src in glob.glob(f_type % (srcDir, subject)):
            f_trgt = os.path.join(trgtDir, os.path.basename(f_src))
            if not os.path.isfile(f_trgt):
                print f_trgt
                shutil.copy(f_src, f_trgt)



###############################################################################
# WF
###############################################################################
wf = Workflow(name='distconnect_meanDist_%s' % distype)
wf.base_dir = os.path.join(wd_dir)
nipype_cfg = dict(logging=dict(workflow_level='DEBUG'), execution={'stop_on_first_crash': False,
                                                                   'remove_unnecessary_outputs': False,
                                                                   'job_finished_timeout': 120})
config.update_config(nipype_cfg)
wf.config['execution']['crashdump_dir'] = os.path.join(wd_dir, 'crash')
ds = Node(nio.DataSink(base_directory=sink_dir), name='sink_%s' % distype)



###############################################################################
# GET DATA
###############################################################################               
subjects_infosource = Node(util.IdentityInterface(fields=['subject_id']), name='subjects_infosource')
subjects_infosource.iterables = ('subject_id', subjects_list)

run_mean_dist = Node(util.Function(input_names=['sub'],
                                   output_names=[], #'filelist'
                                   function=func), name='run_mean_dist_%s' % distype)
wf.connect(subjects_infosource, 'subject_id', run_mean_dist, 'sub')
#wf.connect(run_mean_dist, 'filelist', ds, 'mats.@m')



###############################################################################
# RUN
###############################################################################
wf.write_graph(dotfilename='mean_dist_%s' % distype, graph2use='exec', format='pdf')
wf.run(plugin='CondorDAGMan')
#wf.run(plugin='MultiProc', plugin_args={'n_procs': 10})
