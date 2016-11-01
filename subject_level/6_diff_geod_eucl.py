# -*- coding: utf-8 -*-
"""
Created on Wed Apr 27 10:19:53 2016

@author: oligschlager
"""


import os, glob
import numpy as np

dataDir = '/afs/cbs.mpg.de/projects/mar005_lsd-lemon-surf/probands' 
subjects = [sub for sub in os.listdir(dataDir) if os.path.isdir(os.path.join(dataDir, sub))]

def run_difference(subject):
    
    for geo_file in glob.glob('%s/%s/meanDist/%s_lsd_meanDist_geo_interp*.npy' % (dataDir, subject, subject)):
        eucl_file = geo_file.replace('geo', 'eucl')
        diff_file = geo_file.replace('geo', 'diff')
        if os.path.isfile(eucl_file):
            
            geo_data = np.load(geo_file)
            eucl_data = np.load(eucl_file)
            diff_data = geo_data - eucl_data
            np.save(diff_file, diff_data)
            


for n, subject in enumerate(subjects):
    print '%s / %s' % (n+1, len(subjects))
    run_difference(subject)


          

