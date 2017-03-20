import dectris
import dectris.spluegen
import dectris.albula
import os
import numpy
import pickle
import sys
import time
import zmq

# Image Destination

class TitlisServer(object):

    """zmq REP server to remotely control the titlis detector."""

    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")
        # basepath = "/data/slow_acquisition/"
        # self.image_destination_path = os.path.join(
            # basepath,
            # time.strftime("%y%m%d_%H%M%S"))
        # self.file_name_template = "titlis_ev_{event_id}_seq_{sequence_id}_th_{threshold_id}_im_{image_id}"
        # file_name_template_suffix = "tif"

        # # Detector Calibration File
        # use_calibration_flag = True
        # callibration_path = "/home/det/calibration/calibration-T0804_75-01_20170314_14h29m22/"

        # # Detector Configuration File
        # configuration_file = "/etc/dectris/titlis-75um_500k-MatH.py"

        # # Detector Image Series Parameter(s)
        # serie_id = 1
        # number_of_thresholds = 2
        # number_of_images = 1
        # number_of_triggers = 1
        # number_of_sequences = 1

        # # Detector Arming Parameter(s)
        # trigger_mode = "ints"

        # # Spluegen Exposure Parameter(s)
        # beam_energy = 80000
        # thresholds = photon_energy

        # # Create Spluegen Camera Object
        # camera = dectris.spluegen.DCamera(
            # "10.0.10.50",
            # configuration_file=configuration_file
        # )
        # camera.open()
        # camera.setNumberOfThresholds(number_of_thresholds)
        # if not os.path.exists(image_destination_path):
            # os.makedirs(image_destination_path)

        # if use_calibration_flag:
            # camera.setCalibrationPath(callibration_path)
            # camera.setEnergyForReal(
                # beam_energy,
                # threshold=thresholds[0],
                # threshold2=thresholds[1]
            # )

        # # Fetch the Detector and Logger Objects
        # detector = camera.getDetectorObject()
        # logger   = detector.logger

        # # Set the Detector Exposure Parametere(s)
        # detector.setExposureParameters(
            # count_time=count_time,
            # image_period=1.01 * count_time,
            # sequence_period=1.02 * count_time * number_of_images,
            # frame_count_time=1.01 * count_time)

        # # Set the Detector Image Series Parameter(s)
        # detector.setImageSeriesParameters(series_id=serie_id,
                                        # number_of_triggers=number_of_triggers,
                                        # number_of_sequences=number_of_sequences,
                                        # number_of_images=number_of_images,
                                        # number_of_thresholds=number_of_thresholds)

        # image_builder = camera._image_builder
        # # Set the Image Destination and the File Name Template
        # image_builder.setSaveDirectory(image_destination_path)
        # image_builder._file_name_template = file_name_template
        # image_builder._file_name_suffix = file_name_template_suffix

        # # Arm the Detector
        # detector.arm(trigger_mode)

        # # Wait until the detector is armed and the data receivers are started
        # time.sleep(5)

        # # Loop over all the events
        # for event in xrange(number_of_triggers):
            # logger.info("Event ["      + str(event+1)    + "/" + str(number_of_triggers)  + "]")

            # if trigger_mode == "ints":
                # # Sending software trigger
                # detector.sendSoftwareTriggerPulse()

            # elif trigger_mode == "exts":
                # pass

            # else:
                # msg = "Not supported"
                # logger.critical(msg)
                # raise ValueError(msg)

            # for img in range(number_of_images):
                # image_builder.waitImageIsSaved()
        # detector.disarmSeries()

        # camera.close()

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


if __name__ == "__main__":
    server = TitlisServer()
    server.loop()
