# Copyright (C) 2013 Dectris Ltd.

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

#
#  \file      pilatus.py
#  \details
#  \author    Volker Pilipp
#  \author    Contact: support@dectris.com
#  \version   2.2
#  \date      07/01/2014
#  \copyright See General Terms and Conditions (GTC) on http://www.dectris.com
#
#


import socket
import datetime
import os
import logging

import dectris.albula

logger = logging.getLogger(__name__)


REMOTE_IMAGE_PATH = "/home/det/python-controls-high-energy"


class DPilatus(object):

    def __init__(self, host="129.129.99.81", port=41234):
        super(DPilatus, self).__init__()
        self.__host = host
        self.__port = port
        self.__socketBufferSize = 1024

    def initialize(self, timeout=5):
        """
        Open connection to camserver.

        Args:
            timeout: Timeout in seconds

        Returns:

            True if connection was established successfully else False.
        """

        self.__openSocket(self.__host, timeout)
        if not self.__socket:
            return False
        self.__socket.sendall("prog b*_m*_chsel 0xffff\n")
        answer = self.__socket.recv(self.__socketBufferSize)
        self.__socket.settimeout(None)
        # unload flat field
        self.__socket.sendall('LdFlatField 0\n')
        answer = self.__socket.recv(self.__socketBufferSize)
        # set remote image path
        self.__socket.sendall("imgpath {0}".format(REMOTE_IMAGE_PATH))
        answer = self.__socket.recv(self.__socketBufferSize)
        return True

    def close(self ):
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

    def setPhotonEnergy(photon_energy):
        self.__socket.sendall("SetThreshold {0}".format(photon_energy))
        answer = self.__socket.recv(self.__socketBufferSize)
        return answer

    def photonEnergy():
        self.__socket.sendall("SetThreshold")
        answer = self.__socket.recv(self.__socketBufferSize)
        return answer

    def setCountTime(exposure_time):
        self.__socket.sendall("Exptime {0}".format(exposure_time))
        answer = self.__socket.recv(self.__socketBufferSize)
        return answer

    def countTime():
        self.__socket.sendall("Exptime")
        answer = self.__socket.recv(self.__socketBufferSize)
        return answer

    setFrameTime = setCountTime

    frameTime = countTime

    def setNImages(n):
        # dont want to take more than one image with the pilatus trigger now
        pass

    def nImages():
        return 1

    def version():
        self.__socket.sendall("version")
        answer = self.__socket.recv(self.__socketBufferSize)
        return answer

    def status():
        self.__socket.sendall("status")
        answer = self.__socket.recv(self.__socketBufferSize)
        return answer

    isError = status

    def trigger():
        now = datetime.datetime.now().strftime("%y%m%d.%H%M%S%f")
        fileName = 'dectrisAlbula{0}.cbf'.format(now)
        self.__socket.sendall("expo {0}\n".format(modeDict[mode], fileName))
        self.__socketRecv(timeout=None)

    def arm():
        pass

    def disarm():
        pass

    def __openSocket(self, host, timeout):
        self.__socket = None
        for addrFam, socketType, proto, canonName, socketAddr in socket.getaddrinfo(host, self.__port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            try:
                self.__socket = socket.socket(addrFam, socketType, proto)
            except socket.error, msg:
                self.__socket = None
                continue
            try:
                self.__socket.settimeout(0.1)
                self.__socket.connect(socketAddr)
                timeWaited = 0
                while True:
                    self.__socket.sendall("imgmode x\n")
                    answer = self.__socket.recv(self.__socketBufferSize)
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
            except socket.error, msg:
                self.__socket.close()
                self.__socket = None
                continue
            break

    def __socketRecv(self, timeout = None):
        self.__socket.settimeout(timeout)
        try:
            answer = self.__socket.recv(self.__socketBufferSize)
        except socket.timeout:
            answer = None
        except Exception as e:
            answer = None
            self.__socket.settimeout(None)
            raise e
        self.__socket.settimeout(None)
        return answer


class Pilatus(DPilatus):

    def __init__(self,
                 host="129.129.99.81",
                 port=41234,
                 photon_energy=10000,
                 storage_path="."):

        self.storage_path = storage_path
        super(Pilatus, self).__init__(host, port)
        self.initialize()
        logger.debug(
            "pilatus camserver version %s returns status %s",
            self.version(),
            self.status()
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
        with dectris.albula.DHdf5Writer(output_file, 0) as hdf5_writer:
            data = self.stream.pop()
            while data["type"] == "data":
                hdf5_writer.write(data["data"])
                data = self.stream.pop()
        logger.info("pilatus image saved to %s", output_file)

    def snap(self, exposure_time=1):
        self.setNImages(1)
        self.setCountTime(exposure_time)
        self.trigger()
        self.save()
