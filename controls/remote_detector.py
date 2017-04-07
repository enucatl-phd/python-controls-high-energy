import zmq
import subprocess
import logging
import os

logger = logging.getLogger(__name__)


class RemoteDetector(object):

    delegated_methods = [
        "setThresholds",
        "arm",
        "disarm",
        "trigger",
        "setNTrigger",
        "setExposureParameters",
    ]

    def __init__(
            self,
            host,
            port=5555,
            photon_energy=[10000, 40000],
            storage_path="."):
        super(RemoteDetector, self).__init__()
        self.host = host
        self.port = port
        self.storage_path = storage_path
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.LINGER, 10000)
        self.socket.setsockopt(zmq.RCVTIMEO, 10000)
        self.socket.connect("tcp://{0}:{1}".format(
            host, port))
        logger.debug("test message...")
        # test that the connection works
        try:
            message = self.send_command("echo", "test")
        except zmq.error.Again as e:
            logger.error(
                "could not connect to server, please run remote_detector_server.py on the remote machine")
            raise e
        self.socket.setsockopt(zmq.LINGER, -1)
        self.socket.setsockopt(zmq.RCVTIMEO, -1)
        for method_name in self.delegated_methods:
            self.add_delegated_method(method_name)
        self.setThresholds(photon_energy)

    def add_delegated_method(self, method_name):
        def method(self, *args, **kwargs):
            return self.send_command(method_name, *args, **kwargs)
        method.__name__ = method_name
        setattr(self.__class__, method_name, method)

    def send_command(self, method, *args, **kwargs):
        dictionary = {
            "method": method,
            "args": args,
            "kwargs": kwargs,
        }
        logger.debug("sending %s", dictionary)
        self.socket.send_pyobj(dictionary)
        message = self.socket.recv_pyobj()
        logger.debug("got response %s", message)
        return message

    def save(self):
        remote_file_name = self.send_command("save")["value"]
        logger.debug("remote file name %s", remote_file_name)
        subprocess.check_call("scp det@{0}:{1} {2}".format(
            self.host,
            remote_file_name,
            self.storage_path
        ), shell=True)
        logger.debug("saved file %s",
            os.path.join(self.storage_path,
                         os.path.basename(remote_file_name)))
        logger.debug("%s", remote_file_name.split(".")[-2])
        subprocess.check_call("ssh det@{0} 'rm {1}'".format(
            self.host,
            remote_file_name), shell=True)

    def snap(self, exposure_time=1):
        self.setNTrigger(1)
        self.setExposureParameters(exposure_time)
        self.arm()
        self.trigger(exposure_time)
        self.disarm()
        self.save()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    detector = RemoteDetector("129.129.99.119")
    logger.debug("created")
    message = detector.send_command("echo", "test")
    logger.debug("received echo %s", message)
    detector.snap()
