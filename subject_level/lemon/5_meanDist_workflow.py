__author__ = 'oligschlager'



import os
from nipype.pipeline.engine import Node, Workflow, MapNode, JoinNode
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import nipype.interfaces.io as nio
from nipype import config
import pandas as pd
from meanDist import meanDist_geo, meanDist_eucl


######################
# specify
######################

distype = 'geo' # or 'eucl'
func = meanDist_geo

subjects_list = ['03820', '08747', '13081', '13753', '21923', '22872', '23197', 
                 '23269', '23302', '23305', '23353', '23426', '23428', '23429', 
                 '23464', '23514', '23574', '23576', '23602', '23629', '23649', 
                 '23650', '23651', '23688', '23697', '23700', '23705', '23708', 
                 '23713', '23734', '23741', '23780', '23860', '23861', '23884', 
                 '23886', '23946', '23947', '23948', '23960', '23963', '23965', 
                 '23983', '23985', '24010', '24024', '24050', '24057', '24061', 
                 '24102', '24134', '24246', '24247', '24275', '24444', '24445', 
                 '24587', '24614', '24691', '24700', '24703', '24707', '24715', 
                 '24719', '24720', '24730', '24731', '24732', '24756', '24759', 
                 '24766', '24772', '24773', '24774', '24790', '24844', '24915', 
                 '24945', '25019', '25036', '25081', '25171', '25177', '25188', 
                 '25192', '25194', '25195', '25197', '25199', '25200', '25201', 
                 '25260', '25264', '25274', '25283', '25326', '25524', '25552', 
                 '26436', '26449', '26489', '26526', '26571', '26589', '26591', 
                 '26617', '26619', '26635', '26642', '26674', '26687', '26719', 
                 '26723', '26724', '26728', '26753', '26782', '26789', '26793', 
                 '26801', '26802', '26803', '26804', '26805', '26806', '26820', 
                 '26839', '26841', '26842', '26843', '26844', '26856', '26857', 
                 '26858', '26926', '27696', '27834', '27954']



######################
# WF
######################

wd_dir = '/scr/kansas1/data/lsd-lemon/lemon_wd_meanDist_%s' % distype
ds_dir = '/scr/kansas1/data/lsd-lemon/lemon_results_meanDist_%s' % distype

wf = Workflow(name='distconnect_meanDist_%s' % distype)
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
          
subjects_infosource = Node(util.IdentityInterface(fields=['subject_id']), name='subjects_infosource')
subjects_infosource.iterables = ('subject_id', subjects_list)

run_mean_dist = Node(util.Function(input_names=['sub'],
                                   output_names=[], 
                                   function=func), name='run_mean_dist')
wf.connect(subjects_infosource, 'subject_id', run_mean_dist, 'sub')


######################
# RUN
######################

wf.write_graph(dotfilename='mean_dist_eucl', graph2use='exec', format='pdf')

#import warnings

#with warnings.catch_warnings():
    #warnings.simplefilter("ignore")

#wf.run(plugin='MultiProc', plugin_args={'n_procs': 10})
wf.run(plugin='CondorDAGMan')

