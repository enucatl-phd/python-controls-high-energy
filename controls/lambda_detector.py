import PyTango
import datetime
import time
import subprocess
import logging
import os

logger = logging.getLogger(__name__)

class Lambda(object):
    """
    """
    def __init__(self,
                 host="hasmlmbd01",
                 port=10000,
                 photon_energy=10000,
                 storage_path="."):

            self.host = host
            self.storage_path = storage_path
            device_name = "//{0}:{1}/demo/lambda/01".format(host, port)
            self.device = PyTango.DeviceProxy(device_name)
            logger.debug(
                'State of detector after init is: {}'.format(
                    self.device.state()))
            self.device.FrameNumbers = 1
            self.device.FileStartNum = 1
            self.device.EnergyThreshold = photon_energy
            self.device.SaveFilePath = "/localdata/psi/"

    def trigger(self, exposure_time=1):
        now = datetime.datetime.now()
        self.device.FilePrefix = "snap_{0}".format(now.strftime("%H%M%S%f"))
        self.device.FileStartNum = 0
        self.device.ShutterTime = exposure_time * 1e3
        self.device.command_inout("StartAcq") # start
        time.sleep(exposure_time) # wait
        logger.debug("writing file %s", self.device.FilePrefix)
        cnt = 0
        done = False
        while not done and cnt < 100:
            time.sleep(0.1)
            cnt +=1
            if self.device.state() == PyTango._PyTango.DevState.ON:
                done = True
                logger.info('... done.')
                if cnt >= 100:
                    raise Exception("Detector timeout - acquisition failed")
        return True

    def setNTrigger(self, intervals):
        pass

    def setFrameTime(self, exposure_time):
        pass

    def setCountTime(self, exposure_time):
        pass

    def countTime(self):
        pass

    def frameTime(self):
        pass

    def arm(self):
        pass

    def disarm(self):
        pass

    def snap(self, exposure_time=1):
        self.trigger(exposure_time)
        self.save()

    def save(self):
        now = datetime.datetime.now()
        folder_name = os.path.join(
            self.storage_path,
            now.strftime("%H%M%S%f"))
        subprocess.check_call(
            "ssh e14980@x02da-gws-1 'mkdir {0}'".format(folder_name),
            shell=True)
        subprocess.check_call("scp {0}/*.nxs e14980@x02da-gws-1:{1}".format(
            self.device.SaveFilePath,
            folder_name), shell=True)
        subprocess.check_call("rm {0}/*.nxs".format(
            self.device.SaveFilePath), shell=True)
        logger.info("images saved to %s", folder_name)
