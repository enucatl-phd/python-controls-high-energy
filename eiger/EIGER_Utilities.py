

#imports
import sys
sys.path.insert(0,"/sls/X02DA/data/e13510/Data20/ALBULA3/dectris/albula/3.0/python/dectris/albula")
from wrapper import DImageSeries
import time
import ConfigParser
import epics
import thread
import matplotlib.pyplot as plt
import scipy.io as sio
import numpy as np
import requests,json
import os.path
sys.path.append("/sls/X02DA/data/e13510/Data20/dectris/python/dectris/albula/")
from eigerclient import DEigerClient

#Motor interface
print "Load FPD Motor definitions..."
from FPD_Motors import *


class EIGER:

    def __init__(self):
        "Initialize EIGER"
        config = ConfigParser.ConfigParser()
        config.read('EIGER_parameters.ini')
        sections = config.sections()
        if len(sections) == 0:
            print "[ERROR] Initial file is corrupted. Fix it first!"
            return
        else:
            params = sections[0]
            self.IP = config.get(params, 'IP')
            self.storagePath = config.get(params, 'storagePath')
            self.photonEnergy = int(config.get(params, 'photonEnergy'))
            self.threshold = int(config.get(params, 'thresholdEnergy'))
	

    def convert_to_mat(self, file_id):
        "Convert EIGER hdf5 file to matlab file."
	# ALBULA 3.0 version	
	h5cont = DImageSeries(self.storagePath + "//series_" + str(file_id) + "_master.h5")
	dataset = h5cont[h5cont.first()].data()
	for i in range(h5cont.first(), h5cont.first() + h5cont.size()-1):
		img = h5cont[i+1]
		dat = img.data()
		dataset = np.concatenate((dataset, dat))
	sio.savemat(self.storagePath + "//dat_" + str(file_id) + ".mat", {'img': dataset})
	

