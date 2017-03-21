import zmq
import subprocess
import logging

logger = logging.getLogger(__name__)


class Titlis(object):

    delegated_methods = [
        "setThresholds",
        "arm",
        "disarm",
        "trigger",
        "setNTrigger",
    ]

    def __init__(
            self,
            host,
            port=5555,
            photon_energy=[10000, 40000],
            storage_path="."):
        super(Titlis, self).__init__()
        self.host = host
        self.port = port
        self.storage_path = storage_path
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        subprocess.check_call(
            "ssh det@{0} 'python ~/python-controls-high-energy/controls/titlis_server.py &'".format(
            host), shell=True)
        self.socket.connect("tcp://{0}:{1}".format(
            host, port))
        self.add_delegated_methods()
        self.setThresholds(photon_energy)

    def add_delegated_methods(self):
        for method_name in self.delegated_methods:
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
        logger.debug("sending dict %s", dictionary)
        self.socket.send_pyobj(dictionary)
        message = self.socket.recv_pyobj()
        logger.debug("got response %s", message)
        return message


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(dir(Titlis))
    detector = Titlis("129.129.99.119")
    message = detector.send_command("echo", "test")
    print(message)
    detector.send_command("__exit__")
