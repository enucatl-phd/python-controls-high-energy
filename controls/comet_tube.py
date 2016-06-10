from __future__ import print_function
import logging
import serial

logger = logging.getLogger(__name__)


def send_string(serial, string):
    message = "{0}{1}{2}".format(
        chr(2),
        string,
        chr(13)
    ).encode()
    logger.debug("sending to serial %s: %s\n", serial.name, message)
    serial.write(message)
    return " ".join(serial.readline().decode().split()[1:])


class CometTube(object):
    def __init__(self, serial_port="/dev/ttyS0", baudrate=9600, timeout=1):
        super(CometTube, self).__init__()
        self.serial = serial.Serial(
            serial_port,
            baudrate=baudrate,
            timeout=timeout
        )

    @property
    def error_code(self):
        error = send_string(self.serial, "E")
        error_code = send_string(self.serial, "A")
        return error + " " + error_code

    @property
    def current(self):
        return send_string(self.serial, "IS")

    @current.setter
    def current(self, value):
        return send_string(
            self.serial, "I{0:.0f}".format(value * 100)
        )

    @property
    def voltage(self):
        return send_string(self.serial, "US")

    @voltage.setter
    def voltage(self, value):
        return send_string(
            self.serial, "U{0:.0f}".format(value * 10)
        )

    @property
    def focus(self):
        return send_string(self.serial, "F")

    def set_small_focus(self):
        return send_string(self.serial, "F1")

    def set_large_focus(self):
        return send_string(self.serial, "F0")

    def on(self):
        return send_string(self.serial, "ON")

    def off(self):
        return send_string(self.serial, "OF")


if __name__ == '__main__':
    tube = CometTube()
    logging.basicConfig(level=logging.DEBUG)
    logger.debug("current error code %s", tube.error_code)
    logger.debug("voltage %s", tube.voltage)
    logger.debug("current %s", tube.current)
    # print("focus", tube.focus)
    # print("set voltage to 120")
    # tube.voltage = 120
    # print("voltage", tube.voltage)
    # print("set voltage to 160")
    # tube.voltage = 160
    # print("voltage", tube.voltage)
    # print("set current to 5")
    # tube.current = 5
    # print("current", tube.current)
    # print("set current to 10")
    # tube.current = 10
    # print("current", tube.current)
    # tube.set_small_focus()
    # print(tube.focus)
    # tube.set_large_focus()
    # print(tube.focus)
