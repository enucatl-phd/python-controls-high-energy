#
# EIGER_Client_v3.py
# Python Client of the EIGER detector with Albula v 3.0.0
#
#
# Author: Zhentian Wang
#
#
# History:
# 01.06.2015: first release
#
#################################################################

import time
import ConfigParser
import epics
import scipy.io as sio
import numpy as np
import os.path
import logging

import dectris.albula
import controls.exceptions

logger = logging.getLogger(__name__)


class Eiger:

    def __init__(self, config_file):
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        sections = config.sections()
        if len(sections) == 0:
            raise controls.exceptions.EigerError(
                "Config file {0} is corrupted".format(config_file)
            )
        else:
            params = sections[0]
            self.IP = config.get(params, 'IP')
            self.storagePath = config.get(params, 'storagePath')
            self.photonEnergy = int(config.get(params, 'photonEnergy'))
            self.threshold = int(config.get(params, 'thresholdEnergy'))

        self.client = DEigerClient(host=self.IP)
        logger.debug("Initialize the EIGER")
        self.client.sendDetectorCommand("initialize")
        self.client.setDetectorConfig("auto_summation", 1)
        # for multiple trigger, set this value more than 1
        self.client.setDetectorConfig("ntrigger", 100)
        logger.debug("Set energy to %s eV", self.photonEnergy)
        self.client.setDetectorConfig("photon_energy", self.photonEnergy)
        logger.debug("Set threshold to %s eV", self.threshold)
        self.client.setDetectorConfig("threshold_energy", self.threshold)

    def config(self, photon_energy, threshold):
        "Re-config the energy and the threshold"
        print "Re-initialize the EIGER"
        self.client.sendDetectorCommand("initialize")
        self.client.setDetectorConfig("auto_summation", 1)
        # for multiple trigger, set this value more than 1
        self.client.setDetectorConfig("ntrigger", 100)
        logger.debug("Set energy to %s eV", self.photon_energy)
        self.client.setDetectorConfig("photon_energy", photon_energy)
        logger.debug("Set threshold to %s eV", threshold)
        self.client.setDetectorConfig("threshold_energy", threshold)

    def snap(self, exposure_time):
        # Do not use the internal flat field caliberation data
        self.client.setDetectorConfig("flatfield_correction_applied", 0)
        # Only take one image
        self.client.setDetectorConfig("nimages", 1)
        self.client.setDetectorConfig("trigger_mode", "ints")
        self.client.setDetectorConfig("frame_time", exposure_time + 0.000020)
        self.client.setDetectorConfig("count_time", exposure_time)

        # Arm the detector
        retVal = self.client.sendDetectorCommand("arm")
        if "sequence id" not in retVal:
            raise controls.exceptions.EigerError(
                "EIGER controll hang and got probably reinitialized"
            )
        sq_id = retVal['sequence id']
        logger.debug("sequence id: %s", sq_id)
        self.client.sendDetectorCommand("trigger")
        time.sleep(0.2)  # add to avoid troubles
        self.client.sendDetectorCommand("disarm")
        logger.debug("Image recorded.")

    def save(self):
        "Save all the files from the image server to local storage"
        matching = self.client.fileWriterFiles()
        for fn in matching:
            self.client.fileWriterSave(fn, self.storagePath)

    def delete(self):
        "Delete all files on the server side."
        matching = self.client.fileWriterFiles()
        [self.client.fileWriterFiles(i, method='DELETE') for i in matching]

    def convert_to_mat(self, file_id):
        "Convert EIGER hdf5 file to matlab file."
        h5cont = dectris.albula.DImageSeries(
            self.storagePath + "//series_" + str(file_id) + "_master.h5")
        dataset = h5cont[h5cont.first()].data()
        for i in range(h5cont.first(), h5cont.first() + h5cont.size()-1):
            img = h5cont[i+1]
            dat = img.data()
            dataset = np.concatenate((dataset, dat))
        sio.savemat(
            self.storagePath +
            "//dat_" +
            str(file_id) +
            ".mat", {'img': dataset})
