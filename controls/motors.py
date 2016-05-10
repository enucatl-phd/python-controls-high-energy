########################################################################
#
# gantry_motors.py
#
# Motor class for the DPC gantry setup using EPICS package
#
# Author: Maria Buechner
#
# History:
# 25.02.2014: started
#
########################################################################


import epics
import controls.exceptions


class Motor():
    """ Class to define and control motors using the EPICS package
    """
    def __init__(
            self,
            name,
            epics_name,
            description,
            init=False,
            disabled=False,
            wait_for_finish=True):
        """ Initialization function, sets motor name and description and all
            other motor specific parameters

            Input variables:

                name: Motor name
                epics_name: Motor name in EPICS
                description: brief description
                description: brief description
                init: if true, move to initialization position
                      (default: False)
                disabled: set the motor as disabled (default: False)
                wait_for_finish: wait for the motor finish movement
                before returning (default: True)

        """

        # Class variables
        # Init all Motor instances as false (enabled)
        self._motor_disabled = disabled
        # wait for processing to complete before returning
        self._wait_for_finish = wait_for_finish

        # Instance variables
        self._name = name
        self._epics_name = epics_name
        self._description = description

        # Set motor process variable (PV)
        self._pv = epics.PV(self._epics_name + ".VAL")  # To set/get parameters

        self._val = self._pv.get()  # Current PV value
        self._hlm = self._pv.upper_ctrl_limit  # High limit
        self._llm = self._pv.lower_ctrl_limit  # Low limit

    def mv(self, absolute_position):
        """ Move motor to absolute position

            Input parameters:

                absolute_position: absoulte "position" value, can be um/rad/V

            Return parameters:

                none

        """
        if self._motor_disabled:
            raise ErrorMotorInterrupt(
                "\n[WARNING]: Motor [{0}] is disabled".format(self._name)
            )

        # Check validity of absolute position
        if absolute_position > self._hlm or absolute_position < self._llm:
            raise ErrorMotorInterrupt(
                "\n[Error]: Moving motor [{0}] to position\
                [{1}] failed: position out of range.".format(
                    self._name, position))

        # Set new position and wait (if necessary) for finish
        self._pv.put(absolute_position, self._wait_for_finish)

    def mvr(self, relative_position):
        """ Move motor to relative position

            I.e. if current position is 40um, and mvr(20), move to 60um

            Input parameters:

                realtive_position: relative "position" value, can be um/rad/V

            Return parameters:

                none

        """
        if self._motor_disabled:
            raise ErrorMotorInterrupt("\n[WARNING]: Motor [{0}] is disabled"
                                      .format(self._name))

        # Calculate absolute position
        absolute_position = self.get_current_value() + relative_position
        # Check validity of absolute position
        if absolute_position > self._hlm or absolute_position < self._llm:
            raise ErrorMotorInterrupt(
                "\n[Error]: Moving motor [{0}] to position\
                [{1}] failed: position out of range.".format(
                    self._name, position))

        # Set new position and wait (if necessary) for finish
        self._pv.put(absolute_position, self._wait_for_finish)

    # Get current value of motor PV (position)
    def get_current_value(self):
        """ Update motor PV value (position) and return it

            Input parameters:

                none

            Return parameters:

                self._val (current)

        """
        self._val = epics.caget(self._epics_name + '.VAL')
        return self._val

    # Get high/low limits
    def get_high_limit(self):
        """ Return the motors high limit value

            Input parameters:

                none

            Return parameters:

                self._hlm

        """
        return self._hlm

    def get_low_limit(self):
        """ Return the motors low limit value

            Input parameters:

                none

            Return parameters:

                self._llm

        """
        return self._llm

    # Print Info of single motor
    def __str__(self):
        """ Print name, epics name and descritpion of motor
        """
        return "\n{0}\t\t{1}\t\t{2}\t\t{3}".format(
            self._name,
            self._epics_name,
            self._description,
            self.get_current_value())
