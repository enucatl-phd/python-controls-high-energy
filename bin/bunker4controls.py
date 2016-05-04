########################################################################
# 
# gantry_control_init.py
#
# Initialize all needed packages and modules
#
# Author: Maria Buechner
#
# History:
# 20.11.2013: started
#
########################################################################

# Imports
import threading
import time
import IPython

# Imports need to be done like this, to only import the module once,
# even if it is imported again in another module!

# Camera control
from shadobox_library import *

# Tube control
from tube_library import *

# Gantry Motors
# from gantry_motors import *

# Gantry DPC functions
from gantry_DPC_functions import *


#########################################################################
# Functions
#########################################################################

def quit():
    """ Shutsdown all open devices gracefully
        
        Input parameters:
            
            none
            
        return parameters:
            
            none
            
    """
    # Close camera (and disconnect from sever
    if sb.is_camera_on():
        sb.stop()
    elif sb.client_socket: # if camera off, but still connected to server
        sb.disconnect()
    # Shutdown serial connection, if tube is connected
    if tube.is_connected():
        tube.stop()
        
    # TODO: motors?
    
    # Reminder message (display for 3 secs)
    print('\n\n\n'
    '-----------------------------------------------------------------------'
    '\n\n'
    '                        DETECTOR/TUBE TURNED OFF?'
    '\n\n'
    '-----------------------------------------------------------------------')
    time.sleep(3)
    
    # Exit interactive interpreter
    exit()
    

#########################################################################
# Main
#########################################################################
    
# Display introduction?

IPython.embed()
