import dectris.albula
import os
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
        self.initialize()
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

    def save(self):
        config = self.stream.pop()
        output_file = os.path.join(
            self.storage_path,
            "series_{0}.h5".format(config["series"])
        )
        logger.debug("saving eiger image to %s ...", output_file)
        with dectris.albula.DHdf5Writer(output_file, 0, config["config"]) as hdf5_writer:
            data = self.stream.pop()
            while data["type"] == "data":
                hdf5_writer.write(data["data"])
                data = self.stream.pop()
        logger.info("eiger image saved to %s", output_file)

    def snap(self, exposure_time=1):
        self.setNImages(1)
        self.setFrameTime(exposure_time + 0.000020)
        self.setCountTime(exposure_time)
        self.arm()
        self.trigger()
        self.disarm()
        self.save()
