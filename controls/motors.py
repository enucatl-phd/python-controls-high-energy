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


# Imports
import epics
#import epicsVP
#import epicsMotor
from gantry_control_exceptions import *
from gantry_motor_definitions import *

import time

# Global variables
list_of_motors = []

# Constants
MOTORS_DISABLED = False
WAIT_FOR_FINISH = True

########################################################################
# Motor class
########################################################################

class GantryMotor():
    """ Class to define and control motors using the EPICS package
        
        variables:
            
            name: name of motor
            epics_name: Motor name in EPICS
            description: brief description
            
            
            
            
        functions:
            
            __init__(self, name, epics_name, description, init=False)
            
            
    
    """
    def __init__(self, name, epics_name, description, init=False):
        """ Initialization function, sets motor name and description and all
            other motor specific parameters
            
            Input variables:
                
                name: Motor name (necessary ???)
                epics_name: Motor name in EPICS
                description: brief description
                init: if ture, moce to initialization position
                      Default: False
                      
            Variables:
                
                Class variables:
                    
                    TODO
                    
                Instance variables:
                    
                    TODO
                
            Functions:
                
                TODO
            
        """
        global list_of_motors
        
        # Class variables
        self._motor_disabled = MOTORS_DISABLED # Init all GantryMotor instances as
                                          # false (enabled)
        self._wait_for_finish = WAIT_FOR_FINISH # wait fpr processing to complete 
                                           # before returning
        list_of_motors.append(self) # Add motor to list of all motor instances
        
        # Instance variables
        self._name = name
        self._epics_name = epics_name
        self._description = description
        
        # Set motor process variable (PV)
        self._pv = epics.PV(self._epics_name + ".VAL") # To set/get parameters
        
        # Get motor parameters (THIS DOES NOT WORK FOR THE PIEZO!!!)
        #self._val = epics.caget(self._epics_name + '.VAL') # Current PV value
        #self._hlm = epics.caget(self._epics_name + '.HLM') # High limit
        #self._llm = epics.caget(self._epics_name + '.LLM') # Low limit
        
        self._val = self._pv.get() # Current PV value
        self._hlm = self._pv.upper_ctrl_limit # High limit
        self._llm = self._pv.lower_ctrl_limit # Low limit
        
        # Move to init position?
        self._initialization_position = INITIALIZATION_POSITIONS[self._name]
        if init:
            self.reset()
        
    ########################################################################
    # Public functions
    ########################################################################
    
    def mv(self, absolute_position):
        """ Move motor to absolute position
            
            Input parameters:
                
                absolute_position: absoulte "position" value, can be um/rad/V
                
            Return parameters:
                
                none
                
        """
        if self._motor_disabled:
            raise ErrorMotorInterrupt("\n[WARNING]: Motor [{0}] is disabled"
                                       .format(self._name))
                                       
        # Check validity of absolute position
        if absolute_position > self._hlm or absolute_position < self._llm:
	   raise ErrorMotorInterrupt("\n[Error]: Moving motor [{0}] to position"
	   "[{1}] failed: position out of range.".format(self._name, position))
	                            
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
	   raise ErrorMotorInterrupt("\n[Error]: Moving motor [{0}] to position"
	   "[{1}] failed: position out of range.".format(self._name, position))
        
        # Set new position and wait (if necessary) for finish
        self._pv.put(absolute_position, self._wait_for_finish)
        
    def reset(self, ):
        """ Move motor to the initialization position
            
            Input parameters:
                
                none
                
            Return parameters:
                
                none
                
        """
        if self._initialization_position is None:
            raise ErrorMotorInterrupt('\n[ERROR]: Initialization position '
                                      'of motor {0} is "None".'
                                      .format(self._name))
        self.mv(self._initialization_position)
    
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
    def print_info(self):
        """ Print name, epics name and descritpion of motor
        
            Input parameters:
                
                none
                
            Return parameters:
                
                none
            
        """
        print("\n{0}\t\t{1}\t\t{2}\t\t{3}".format(self._name, 
               self._epics_name, self._description, self.get_current_value()))

########################################################################
# Functions
########################################################################
    
# Print Info of all motors 
def list_motors():
    """ List name, epics name and descritpion of all motors in motor list
        
        Input parameters:
                
                none
                
        Return parameters:
                
                none
                
    """
    print("\n\nMotor name\tEPICS name\t\t\tDescription\t\t\tPosition")
    print("-------------------------------------------------------"
        "-----------------------------------")
    for _motor in list_of_motors:
        _motor.print_info()

########################################################################
# Main
########################################################################

gb_trz	    = GantryMotor("GB_TRZ","X02DA-LAB-GNT1:GB_TRZ",
                          "Gantry base Z translation")
gb_roty	    = GantryMotor("GB_ROTY","X02DA-LAB-GNT1:GB_ROTY",
                          "Gantry base Y rotation")
sh_try	    = GantryMotor("SH_TRY","X02DA-LAB-GNT1:SH_TRY",
                          "Sample Holder Y translation")

g1_trz1	    = GantryMotor("G1_TRZ1","X02DA-LAB-GNT1:G1_TRZ1",
                          "G1 M1 Z translation")
g1_trz2	    = GantryMotor("G1_TRZ2","X02DA-LAB-GNT1:G1_TRZ2",
                          "G1 M2 Z translation")
g1_trz3	    = GantryMotor("G1_TRZ3","X02DA-LAB-GNT1:G1_TRZ3",
                          "G1 M3 Z translation")                             
g2_trx	    = GantryMotor("G2_TRX","X02DA-LAB-GNT1:G2_TRX",
                          "G2 Piezo X translation")
