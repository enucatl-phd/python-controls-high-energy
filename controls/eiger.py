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

import dectris.albula

import scipy.io as sio
import logging

logger = logging.getLogger(__name__)


class Eiger(dectris.albula.DEigerDetector):

    def __init__(self,
                 host,
                 port=80,
                 photon_energy=35000,
                 storage_path="."):

        self.storage_path = storage_path
        super(Eiger, self).__init__(host, port)
        self.stream = dectris.albula.DEigerStream(host, port)
        self.stream.setEnabled(True)
        self.initialize()
        logger.debug("Set energy to %s eV", self.photon_energy)
        self.setPhotonEnergy(photon_energy)
        self.setNImages(1)
        logger.debug(
            "eiger version %s returns status %s",
            self.version(),
            self.status()
        )

    def snap(self, exposure_time):
        self.setFrameTime(exposure_time + 0.000020)
        self.setCountTime(exposure_time)
        self.arm()
        self.trigger()
        self.disarm()
        image, series_id, sequence_id = self.stream.pop()
        logger.debug(
            "Image recorded. %s %s %s",
            image,
            series_id,
            sequence_id
        )
