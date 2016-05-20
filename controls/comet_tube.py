import serial

def send_string(serial, string):
    message = "{0}{1}{2}".format(
        chr(2),
        string,
        chr(13)
    )
    serial.write(message.encode())
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
            self.serial, "I{0:.2f}".format(value)
        )

    @property
    def voltage(self):
        return send_string(self.serial, "US")

    @voltage.setter
    def voltage(self, value):
        return send_string(
            self.serial, "U{0:.1f}".format(value)
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
