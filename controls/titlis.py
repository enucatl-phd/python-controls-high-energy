import zmq
import subprocess


class Titlis(object):

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
            "ssh det@{0} 'python ~/python-controls-high-energy/controls/titlis-server.py'".format(
            host))
        self.socket.connect("tcp://{0}:{1}".format(
            host, port))

    def send_command(self, method, kwargs):
        dictionary = {
            "method": method,
            "kwargs": kwargs
        }
        self.socket.send_pyobj(dictionary)
        message = self.socket.recv_pyobj()
        logger.debug("got response %s", message)
        return message
