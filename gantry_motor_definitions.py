### CURRENTLY DISPENSABLE ###

########################################################################
# 
# gantry_motor_definitions.py
#
# Motor definitions for the DPC gantry setup
#
# Author: Maria Buechner
#
# History:
# 25.02.2014: started
#
########################################################################

# Imports
#from gantry_motors import *

# Constants

# Initialization/Start positions (NOT DONE/SET CORRECTLY YET!!!)
GB_TRZ_INIT	= None
GB_ROTY_INIT    = None
SH_TRY_INIT     = None

G1_TRZ1_INIT	= None
G1_TRZ2_INIT	= None
G1_TRZ3_INIT	= None

G2_TRX_INIT     = None

INITIALIZATION_POSITIONS = {"GB_TRZ":GB_TRZ_INIT, "GB_ROTY":GB_ROTY_INIT, 
                            "SH_TRY":SH_TRY_INIT, "G1_TRZ1":G1_TRZ1_INIT, 
                            "G1_TRZ2":G1_TRZ2_INIT, "G1_TRZ3":G1_TRZ3_INIT, 
                            "G2_TRX":G2_TRX_INIT, }