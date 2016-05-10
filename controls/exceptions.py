########################################################################
#
# gantry_control_exceptions.py
#
# Exception package for python based gantry control
#
# Author: Maria Buechner
#
# History:
# 11.12.2013: started
#
########################################################################


class PythonControlsError(Exception):
    pass


class TubeInterrupt(PythonControlsError):
    """ Tube error

    """


class SerialInterrupt(PythonControlsError):
    """ Serial (connection) error

    """


class CameraInterrupt(PythonControlsError):
    """ Camera (server) error

    """


class ScanInterrupt(PythonControlsError):
    """  during DPC or tomography scan

    """


class MotorInterrupt(PythonControlsError):
    """ Motor error

    """
