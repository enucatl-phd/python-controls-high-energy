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

# Parent class
class GantryError(Exception):
    """ Parent class for all custom Gantry errors
    
        Functions:
            
            __init__(message): stores and prints error message
                
    """
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        Exception.__init__(self, '\n'+message)

# Derived classes       
class ErrorTubeInterrupt(GantryError):
    """ Tube error, inherits from GantryError
                    
    """
        
class ErrorSerialInterrupt(GantryError):
    """ Serial (connection) error, inherits from GantryError
                    
    """
        
class ErrorCameraInterrupt(GantryError):
    """ Camera (server) error, inherits from GantryError
                    
    """

class ErrorScanInterrupt(GantryError):
    """ Error during DPC or tomography scan, inherits from GantryError
                    
    """
        
class ErrorMotorInterrupt(GantryError):
    """ Motor error, inherits from GantryError
                    
    """

# Error/Warning handling
#try:
# 	#code
# 	#doing stuff
# 	#and error occurs (exception is raised)
# 	 	
#except: 
#	#handling exception (e.g. clean up, soft-stops etc.)
# 	#if necessray: reraise exception with "raise" command