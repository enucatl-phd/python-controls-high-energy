import dectris.albula
import os
import logging
import datetime
import json
import requests
import time

import controls.hdf5

logger = logging.getLogger(__name__)


class Eiger(dectris.albula.DEigerDetector):

    def __init__(self,
                 host,
                 port=80,
                 photon_energy=10000,
                 storage_path="."):

        self.host = host
        self.port = port
        self.storage_path = storage_path
        super(Eiger, self).__init__(host, port)
        self.initialize()
        self.setNImages(1)
        self.send_command("config/trigger_mode", {"value": "inte"})
        self.stream = dectris.albula.DEigerStream(host, port)
        self.stream.setEnabled(True)
        logger.debug(
            "eiger version %s returns status %s",
            self.version(),
            self.status()
        )
        logger.debug(
            "eiger stream version %s returns status %s",
            self.stream.version(),
            self.stream.enabled()
        )
        logger.debug("Set energy to %s eV", photon_energy)
        self.setPhotonEnergy(photon_energy)

    def send_command(self, path, dictionary):
        url = 'http://{0}:{1}/detector/api/{2}/{3}'.format(
                self.host,
                self.port,
                self.version(),
                path,
                )
        headers = {'Content-Type': 'application/json'}
        response = requests.put(url, json.dumps(dictionary), headers=headers)
        logger.debug("sent %s", dictionary)
        logger.debug("got response %s %s", response.status_code, response.json())
        return response.json()

    def save(self):
        _ = self.stream.pop()
        now = datetime.datetime.now()
        output_file = os.path.join(
            self.storage_path,
            "series.{0}.h5".format(now.strftime("%y%m%d.%H%M%S%f"))
        )
        logger.debug("saving eiger image to %s ...", output_file)
        with controls.hdf5.Hdf5Writer(output_file) as hdf5_writer:
            data = self.stream.pop()
            while data["type"] == "data":
                hdf5_writer.write(data["data"])
                data = self.stream.pop()
        logger.info("eiger image saved to %s", output_file)
        logger.debug(now.strftime("%H%M%S%f"))

    def setNTrigger(self, n):
        return self.send_command("config/ntrigger", {"value": n})

    def trigger(self, exposure_time=1):
        response = self.send_command("command/trigger", {"value": exposure_time})
        time.sleep(exposure_time)
        return response

    def snap(self, exposure_time=1):
        self.setNTrigger(1)
        self.arm()
        self.trigger(exposure_time)
        self.disarm()
        self.save()
