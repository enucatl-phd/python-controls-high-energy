import socket
import datetime
import os
import logging
import tempfile
import glob
import shutil
import subprocess

import dectris.albula

logger = logging.getLogger(__name__)


REMOTE_IMAGE_PATH = "/home/det/python-controls-high-energy"
SOCKET_BUFFER_SIZE = 1024


class DPilatusDetector(object):
    "Use the same interface as the DEigerDetector class from dectris.albula"

    def __init__(self, host="129.129.99.81", port=41234):
        super(DPilatusDetector, self).__init__()
        self.host = host
        self.port = port

    def initialize(self, timeout=5):
        """
        Open connection to camserver.

        Args:
            timeout: Timeout in seconds

        Returns:

            True if connection was established successfully else False.
        """

        self.__openSocket(self.host, timeout)
        if not self.__socket:
            return False
        self.__socket.sendall("prog b*_m*_chsel 0xffff\n")
        answer = self.__socket.recv(SOCKET_BUFFER_SIZE)
        logger.debug(answer)
        self.__socket.settimeout(None)
        # unload flat field
        self.__socket.sendall('LdFlatField 0\n')
        answer = self.__socket.recv(SOCKET_BUFFER_SIZE)
        logger.debug(answer)
        # set remote image path
        self.__socket.sendall("imgpath {0}\n".format(REMOTE_IMAGE_PATH))
        answer = self.__socket.recv(SOCKET_BUFFER_SIZE)
        logger.debug(answer)
        return True

    def close(self):
        """
        Close connection to camserver
        """
        if self.__socket:
            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
            self.__socket = None
        return
        
    def abort(self):
        try:
            self.__socket.sendall("k")
            self.__socketRecv(timeout = 0.1) # set timeout because 'k' may or may not return an answer
            self.__socketRecv(timeout = 0.1) # set timeout because 'k' may or may not return an answer
            self.__socketRecv(timeout = 10) # eventually read final answer from exposure, ...
        except:
            pass
        self.__abort = True;
        return self.__abort

    def setPhotonEnergy(self, photon_energy):
        self.__socket.sendall("SetThreshold {0}\n".format(photon_energy))
        answer = self.__socket.recv(SOCKET_BUFFER_SIZE)
        return answer

    def photonEnergy(self):
        self.__socket.sendall("SetThreshold\n")
        answer = self.__socket.recv(SOCKET_BUFFER_SIZE)
        return answer

    def setCountTime(self, exposure_time):
        self.__socket.sendall("Exptime {0}\n".format(exposure_time))
        answer = self.__socket.recv(SOCKET_BUFFER_SIZE)
        return answer

    def countTime(self):
        self.__socket.sendall("Exptime\n")
        answer = self.__socket.recv(SOCKET_BUFFER_SIZE)
        return answer

    setFrameTime = setCountTime

    frameTime = countTime

    def setNImages(self, n):
        # dont want to take more than one image with the pilatus trigger now
        pass

    def nImages(self):
        return 1

    def version(self):
        self.__socket.sendall("version\n")
        answer = self.__socket.recv(SOCKET_BUFFER_SIZE)
        return answer

    def status(self):
        self.__socket.sendall("status\n")
        answer = self.__socket.recv(SOCKET_BUFFER_SIZE)
        return answer

    isError = status

    def trigger(self):
        now = datetime.datetime.now().strftime("%y%m%d.%H%M%S%f")
        fileName = 'dectrisAlbula.{0}.cbf'.format(now)
        logger.debug("exposing for %s", fileName)
        self.__socket.sendall("expo {0}\n".format(fileName))
        answer = self.__socketRecv(SOCKET_BUFFER_SIZE)
        logger.debug(answer)
        answer = self.__socketRecv(SOCKET_BUFFER_SIZE)
        logger.debug(answer)

    def arm(self):
        pass

    def disarm(self):
        pass

    def __openSocket(self, host, timeout):
        self.__socket = None
        for addrFam, socketType, proto, canonName, socketAddr in socket.getaddrinfo(host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            try:
                self.__socket = socket.socket(addrFam, socketType, proto)
            except socket.error as msg:
                logger.error("socket connection failed %s", msg)
                self.__socket = None
                continue
            try:
                self.__socket.connect(socketAddr)
                timeWaited = 0
                while True:
                    self.__socket.sendall("imgmode x\n")
                    answer = self.__socket.recv(SOCKET_BUFFER_SIZE)
                    if (answer.find("access denied")>=0):
                        if timeWaited < timeout:
                            timeWaited += 1
                            time.sleep(1)
                        else:
                            self.__socket.close()
                            self.__socket = None
                            return None
                    else:
                        break
            except socket.error as msg:
                logger.error("socket connection failed %s", msg)
                self.__socket.close()
                self.__socket = None
                continue
            break

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


class Pilatus(DPilatusDetector):

    def __init__(self,
                 host="129.129.99.81",
                 port=41234,
                 photon_energy=10000,
                 storage_path="."):

        self.storage_path = storage_path
        super(Pilatus, self).__init__(host, port)
        self.initialize()
        logger.debug(
            "pilatus camserver version %s",
            self.version()
        )
        logger.debug(self.status())
        answer = self.setPhotonEnergy(photon_energy)
        logger.debug("Set energy %s", answer)

    def save(self):
        now = datetime.datetime.now().strftime("%y%m%d.%H%M%S%f")
        output_file = os.path.join(
            self.storage_path,
            "series.{0}.h5".format(now)
        )
        logger.debug("saving pilatus image to %s ...", output_file)
        tempdir = tempfile.mkdtemp()
        try:
            logger.debug("created temporary directory %s", tempdir)
            copy_command = "scp det@{0}:{1}/*.cbf {2}".format(
                self.host,
                REMOTE_IMAGE_PATH,
                tempdir) 
            logger.debug(copy_command)
            copied = subprocess.check_output(copy_command, shell=True)
            logger.debug(copied)
            removed = subprocess.check_output(
                "ssh det@{0} 'rm {1}/*.cbf'".format(
                    self.host,
                    REMOTE_IMAGE_PATH,
                    ), shell=True)
            logger.debug(removed)
            copied_files = glob.glob("{0}/*.cbf".format(tempdir))
            with dectris.albula.DHdf5Writer(output_file, 0) as hdf5_writer:
                for input_file in copied_files:
                    data = dectris.albula.readImage(input_file)
                    hdf5_writer.write(data)
            logger.info("pilatus image saved to %s", output_file)
        finally:
            shutil.rmtree(tempdir)

    def snap(self, exposure_time=1):
        self.setNImages(1)
        self.setCountTime(exposure_time)
        self.trigger()
        self.save()
