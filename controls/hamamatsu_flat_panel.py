import socket
import datetime
import os
import logging
import tempfile
import glob
import shutil
import subprocess
import time

import controls.hdf5

logger = logging.getLogger(__name__)


SOCKET_BUFFER_SIZE = 256
REMOTE_IMAGE_PATH = "X:\\Data20\\FPD\\Matteo\\"
# Let sever return a "OK" and display it.
_CMD_ECHO       = "10"
# Set the exposure time
_CMD_EXPTIME    = "11"
# Snap an image
_CMD_SNAP       = "12"
# Set the image path
_CMD_IMAGEPATH  = "13"
# Init the FPD
_CMD_START      = "14"
# Stop the FPD
_CMD_STOP       = "15"
# Create the data directory
_CMD_CREATDIR   = "16"
# Get the exposure time_FPD_lastErrorMsg
_CMD_GETEXPTIME = "17"
# Cancel current snap
_CMD_CANCELSNAP = "18"
# Set ROI
_CMD_SETROI     = "19"
# Get ROI
_CMD_GETROI     = "20"
# Set Trigger mode
_CMD_SETTRIGGER = "21"
# Get Trigger mode
_CMD_GETTRIGGER = "22"
# Expousre, for continous acquisition.
_CMD_EXPOSURE   = "23"
# Camera status
_CMD_STATUS     = "24"
# The cmds belfore is to optimize the untilization of exposure on the Mammo tube
# Pre phase stepping
_CMD_PREPS	= "25"
# Post phase stepping
_CMD_POSTPS	= "26"
# Step
_CMD_STEP	= "27"

class HamamatsuFlatPanel(object):
    "Detector interface for Zhentian's camera server on mpc1777"

    def __init__(self, host="mpc1777", port=44444, photon_energy=1,
                 storage_path="."):
        super(HamamatsuFlatPanel, self).__init__()
        self.host = host
        self.port = port
        self.storage_path = storage_path
        self.initialize()

    def initialize(self, timeout=5):
        """
        Open connection to camserver.

        Args:
            timeout: Timeout in seconds

        Returns:

            True if connection was established successfully else False.
        """

        self.__openSocket(timeout)
        if not self.__socket:
            return False
        logger.debug("initializing detector")
        self.__send_command(_CMD_STOP, "")
        self.__send_command(_CMD_START, "")
        self.setExposureParameters(1)
        self.setROI(600, 1200, 1600, 1800)
        self.setPaths()
        logger.debug("detector initialized")
        return True

    def close(self):
        """
        Close connection to camserver
        """
        self.__send_command(_CMD_STOP, "")
        if self.__socket:
            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
            self.__socket = None
        return

    def __del__(self):
        self.close()
        
    def trigger(self, exposure_time=1):
        now = datetime.datetime.now().strftime("%y%m%d.%H%M%S%f")
        fileName = REMOTE_IMAGE_PATH + 'snap.{0}.tif'.format(now)
        self.setExposureParameters(exposure_time)
        self.__send_command(_CMD_SNAP, fileName)

    def arm(self):
        pass

    def disarm(self):
        pass

    def setNTrigger(self, n):
        pass

    def __openSocket(self, timeout):
        self.__socket = None
        try:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__socket.setblocking(1)
            self.__socket.connect((self.host, self.port))
        except socket.error as msg:
            logger.error("socket connection failed %s", msg)
            self.__socket.close()
            self.__socket = None


    def __socketRecv(self, timeout=None):
        self.__socket.settimeout(timeout)
        try:
            answer = self.__socket.recv(SOCKET_BUFFER_SIZE)
        except socket.timeout:
            answer = None
        except Exception as e:
            answer = None
            self.__socket.settimeout(None)
            raise e
        self.__socket.settimeout(None)
        return answer

    def __send_command(self, command, parameters):
        payload = command + "_" + parameters
        logger.debug("sending command %s", payload)
        self.__socket.send(payload)
        answer = self.__socketRecv()
        logger.debug("received answer %s", answer)
        return answer

    def setExposureParameters(self, exposure_time=1):
        return self.__send_command(_CMD_EXPTIME, str(float(exposure_time)))

    def setROI(self, x1, y1, x2, y2):
        roi = ",".join([str(x) for x in [x1, y1, x2, y2]])
        return self.__send_command(_CMD_SETROI, roi)

    def setPaths(self):
        self.__send_command(_CMD_IMAGEPATH, REMOTE_IMAGE_PATH)

    def save(self):
        root = "/afs/psi.ch/user/a/abis_m/slsbl/x02da/e13510/Data20/FPD/Matteo"
        now = datetime.datetime.now()
        folder = now.strftime("%y%m%d.%H%M%S%f")
        output_folder = os.path.join(
            root, folder
        )
        logger.debug("saving hamamatsu images to %s ...", output_folder)
        os.makedirs(output_folder)
        move_command = "mv {0}/*.tif {1}".format(
            root, output_folder)
        logger.debug(move_command)
        moved = subprocess.check_output(move_command, shell=True)
        logger.debug(moved)
        remove_command = "rm {0}/ct*.tif".format(output_folder)
        logger.debug(remove_command)
        removed = subprocess.check_output(remove_command, shell=True)
        logger.debug(removed)

    def snap(self, exposure_time=1):
        self.trigger(exposure_time)
        self.save()
