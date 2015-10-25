__author__ = 'oligschlager'



import os
from nipype.pipeline.engine import Node, Workflow, MapNode, JoinNode
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import nipype.interfaces.io as nio
from nipype import config
import pandas as pd
from meanDist import meanDist

wd_dir = '/scr/liberia1/data/distconnect/new_meanDists/wd'
ds_dir = '/scr/liberia1/data/distconnect/new_meanDists/results'





######################
# WF
######################
wf = Workflow(name='distconnect_meanDist')
wf.base_dir = os.path.join(wd_dir)
nipype_cfg = dict(logging=dict(workflow_level='DEBUG'), execution={'stop_on_first_crash': False,
                                                                   'remove_unnecessary_outputs': False,
                                                                   'job_finished_timeout': 120})
config.update_config(nipype_cfg)
wf.config['execution']['crashdump_dir'] = os.path.join(wd_dir, 'crash')

ds = Node(nio.DataSink(base_directory=ds_dir), name='ds')



######################
# GET DATA
######################
# SUBJECTS ITERATOR

baseDir = "/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands"
subjects_list = [sub for sub in os.listdir(baseDir) if os.path.isdir(os.path.join(baseDir, sub))]

subjects_infosource = Node(util.IdentityInterface(fields=['subject_id']), name='subjects_infosource')
subjects_infosource.iterables = ('subject_id', subjects_list)

run_mean_dist = Node(util.Function(input_names=['sub'],
                                   output_names=[], #'filelist'
                                   function=meanDist), name='run_mean_dist')
wf.connect(subjects_infosource, 'subject_id', run_mean_dist, 'sub')
#wf.connect(run_mean_dist, 'filelist', ds, 'mats.@m')



######################
# RUN
######################
wf.write_graph(dotfilename='mean_dist', graph2use='exec', format='pdf')

#
#import warnings

#with warnings.catch_warnings():
    #warnings.simplefilter("ignore")

wf.run(plugin='MultiProc', plugin_args={'n_procs': 5})
#wf.run(plugin='CondorDAGMan')

