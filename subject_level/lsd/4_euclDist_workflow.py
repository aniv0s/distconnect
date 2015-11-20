# -*- coding: utf-8 -*-

import os
from nipype.pipeline.engine import Node, Workflow
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
from nipype import config
from euclDist import euclDist

wd_dir = '/scr/liberia1/data/distconnect/euclDist/wd'
ds_dir = '/scr/liberia1/data/distconnect/euclDist/results'



######################
# WF
######################
wf = Workflow(name='distconnect_euclDist')
wf.base_dir = os.path.join(wd_dir)
nipype_cfg = dict(logging=dict(workflow_level='DEBUG'), execution={'stop_on_first_crash': False,
                                                                   'remove_unnecessary_outputs': False,                                                                   'job_finished_timeout': 120})
config.update_config(nipype_cfg)
wf.config['execution']['crashdump_dir'] = os.path.join(wd_dir, 'crash')

ds = Node(nio.DataSink(base_directory=ds_dir), name='ds')


######################
# SUBJECTS ITERATOR

baseDir = "/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands"
subjects = [sub for sub in os.listdir(baseDir) if os.path.isdir(os.path.join(baseDir, sub))]

subjects_infosource = Node(util.IdentityInterface(fields=['subject_id']), name='subjects_infosource')
subjects_infosource.iterables = ('subject_id', subjects)

run_euclDist = Node(util.Function(input_names=['subject'],
                                   output_names=[], #'filelist'
                                   function=euclDist), name='run_euclDist')
wf.connect(subjects_infosource, 'subject_id', run_euclDist, 'subject')
#wf.connect(run_euclDist, 'filelist', ds, 'mats.@m')



######################
# RUN
######################
wf.write_graph(dotfilename='euclDist', graph2use='exec', format='pdf')

#
#import warnings

#with warnings.catch_warnings():
    #warnings.simplefilter("ignore")

wf.run(plugin='MultiProc', plugin_args={'n_procs': 8})
#wf.run(plugin='CondorDAGMan')

