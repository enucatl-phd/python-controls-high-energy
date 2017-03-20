import dectris
import dectris.spluegen
import dectris.albula
import os
import numpy
import pickle
import sys
import time
import zmq
import logging

logger = logging.getLogger(__name__)


class TitlisServer(object):

    """zmq REP server to remotely control the titlis detector."""

    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")
        self.file_name_template = "titlis_ev_{event_id}_seq_{sequence_id}_th_{threshold_id}_im_{image_id}"
        file_name_template_suffix = "tif"

        # # Detector Calibration File
        calibration_path = "/home/det/calibration/calibration-T0804_75-01_20170314_14h29m22/"

        # Detector Configuration File
        self.configuration_file = "/etc/dectris/titlis-75um_500k-MatH.py"

        # Create Spluegen Camera Object
        self.camera = dectris.spluegen.DCamera(
            "10.0.10.50",
            configuration_file=configuration_file
        )
        self.setNTrigger(1)
        self.camera.open()
        self.camera.setNumberOfThresholds(number_of_thresholds)
        self.camera.setCalibrationPath(calibration_path)

        # Fetch the Detector and Logger Objects
        self.detector = camera.getDetectorObject()
        self.image_builder = camera._image_builder
        self.image_builder._file_name_template = file_name_template
        self.image_builder._file_name_suffix = "tif"

    def setNTrigger(self, n):
        self.n_trigger = n
        # Set the Detector Image Series Parameter(s)
        self.detector.setImageSeriesParameters(
            series_id=1,
            number_of_triggers=n,
            number_of_images=1,
            number_of_thresholds=2)
        # Set the Image Destination and the File Name Template
        basepath = "/data/slow_acquisition/"
        self.image_destination_path = os.path.join(
            basepath,
            time.strftime("%y%m%d_%H%M%S"))
        if not os.path.exists(self.image_destination_path):
            os.makedirs(self.image_destination_path)
        self.image_builder.setSaveDirectory(self.image_destination_path)
        return n

    def trigger(self, exposure_time=1):
        self.detector.setExposureParameters(
            count_time=exposure_time,
            image_period=1.01 * exposure_time,
            sequence_period=1.02 * exposure_time,
            frame_count_time=1.01 * exposure_time)
        self.detector.sendSoftwareTriggerPulse()
        time.sleep(exposure_time)
        saved = self.image_builder.waitImageIsSaved()
        return saved

    def loop(self):
        while True:
            message = self.socket.recv_pyobj()
            method_name = message["method"]
            kwargs = message["kwargs"]
            print(method_name)
            print(kwargs)
            try:
                value = getattr(self, method_name)(**kwargs)
                self.socket.send_pyobj({
                    "status": 200,
                    "value": value})
            except Exception as e:
                self.socket.send_pyobj({
                    "status": 500,
                    "value": e.message})

    def echo(self, value):
        return value

    def arm(self):
        value = self.detector.arm("ints")
        time.sleep(1)
        return value

    def disarm(self):
        return self.detector.disarmSeries()

    def setTresholds(thresholds):
        assert len(thresholds) == 2
        return self.camera.setEnergyForReal(
            80000, # fudge useless value
            threshold=thresholds[0],
            threshold2=thresholds[1])


if __name__ == "__main__":
    server = TitlisServer()
    server.loop()
