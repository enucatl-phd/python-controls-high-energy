import dectris.prototype.PrototypeControl
import os
import time
import numpy as np
import datetime
import zmq
import logging
import glob
import h5py
from libtiff import TIFF

logger = logging.getLogger(__name__)


class RemoteDetectorServer(object):

    """zmq REP server to remotely control the remoteDetector detector."""

    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")
        file_name_template = "series_id_{series_id:05d}_threshold_{threshold}_image_{image_id:06d}.tif"
        self.number_of_thresholds = 2

        # # Detector Calibration File
        calibration_path = "/home/det/calibrations/calibration-T0804_75-01_20170522_14h02m20"

        # Detector Configuration File
        configuration_file = "/home/det/configuration/titlis-75um_2halfmodules.py"

        # Create Spluegen Camera Object
        self.detector = dectris.prototype.PrototypeControl(
            receive_ip="10.0.10.1",
            detector_ip="10.0.10.50",
            configuration=configuration_file
        )
        self.detector.configure_file_output(
            image_destination_path="/data/PSI_data",
            file_name_template=file_name_template)
        self.detector.load_calibration(calibration_path=calibration_path)

    def trigger(self, exposure_time=1):
        self.detector.acquire_images(
            count_time=exposure_time,
            number_of_images=1,
            number_of_triggers=1,
            trigger_mode="ints")

    def loop(self):
        while True:
            message = self.socket.recv_pyobj()
            method_name = message["method"]
            if method_name == "__exit__":
                self.socket.send_pyobj({
                    "status": 200,
                    "value": "received __exit__ command, stopping server"})
                break
            args = message["args"]
            kwargs = message["kwargs"]
            logger.debug("received %s", method_name)
            logger.debug("args %s", args)
            logger.debug("kwargs %s", kwargs)
            try:
                value = getattr(self, method_name)(*args, **kwargs)
                self.socket.send_pyobj({
                    "status": 200,
                    "value": value})
            except Exception as e:
                self.socket.send_pyobj({
                    "status": 500,
                    "value": e.message})

    def echo(self, value):
        return value

    def set_energy_and_thresholds(self, energy, thresholds):
        return self.detector.set_energy_and_thresholds(
            80000, # fudge useless value
            thresholds=thresholds,
            number_of_thresholds=2)

    def save(self):
        for _ in range(self.n_trigger):
            self.image_builder.waitImageIsSaved()
        logger.debug("image saved")
        now = datetime.datetime.now().strftime("%y%m%d.%H%M%S%f"))
        output_file_name = os.path.join(
            self.image_destination_path,
            now + ".h5")
        output_file = h5py.File(output_file_name)
        groups = ["th_0", "th_1"]
        for group_name in groups:
            group = output_file.require_group("/entry/data/{0}".format(group_name))
            group_files = sorted(glob.glob(
                os.path.join(
                    self.image_destination_path,
                    "*{0}*.tif".format(group_name))))
            for i, group_file in enumerate(group_files):
                logger.debug("trying to read %s", group_file)
                tif = TIFF.open(group_file, mode="r")
                dataset = tif.read_image()
                group.create_dataset(
                    "data_{0:06d}".format(i + 1),
                    data=dataset)
                os.remove(group_file)
        output_file.close()
        logger.debug("created %s file", output_file_name)
        return os.path.abspath(output_file_name)



if __name__ == "__main__":
    import logging.config
    import controls.log_config
    import click

    @click.command()
    @click.option("-v", "--verbose", count=True)
    def main(verbose):
        logging.config.dictConfig(controls.log_config.get_dict(verbose))
        logger.debug("starting server")
        server = RemoteDetectorServer()
        logger.debug("starting loop")
        server.loop()

    main()
