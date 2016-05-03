########################################################################
# 
# sb_command_definitions.py
#
# Definitions of all ShadoBox commands that can be send to and 
# interpreted by the SBWinServer
#
# Author: Maria Buechner
#
# History:
# 20.11.2013: started
#
########################################################################

# Commands

# Return status
RETURN_OK = 10 # No error occured
RETURN_ERROR = 11 # Error occured

# General
CMD_ECHO = 20 # Echo incoming command
CMD_CLOSE = 21 # Close client socket and thread, and shut down WinServer

# Camera specific

CMD_START_CAMERA = 30 # Open and initialize framegrabber
CMD_STOP_CAMERA = 31 # Close framegrabber
CMD_IS_CAMERA_ON = 32 # Check if framegrabber is operational

CMD_SET_EXPOSURE_TIME = 40
CMD_GET_EXPOSURE_TIME = 41
CMD_SET_PIXEL_CLOCK = 42 # Set internal clock in [Hz], must match 
                         # cameras clock (SB 2048: 6e6)
CMD_GET_PIXEL_CLOCK = 43
CMD_SET_CYCLE_TIME = 44 # Set frequency of image acqusition (in [us],
                        # e.g. 1e6 -> 1 image per second)
CMD_GET_CYCLE_TIME = 45
CMD_SET_ROI = 46 # Set ROI for image processing and storage
                 # (NOTE: framegrabber always acquires the maximum image)
CMD_GET_ROI = 47
CMD_SET_PREFIX = 48
CMD_GET_PREFIX = 49

CMD_SET_DIRECTORY = 50 # Set directory for .raw and snap shot files
CMD_GET_DIRECTORY = 51

CMD_SNAP = 60 # Acquire snap shot
CMD_ACQUIRE = 61 # Acquire singel image, for specific number of 
                 # projection and step
                 
CMD_EXPOSURE = 71 # Acquire singel image, copied (and modified to use
                  # with ShadoBox) from Thomas Thuering
                  
CMD_SET_GAP_SPACE = 80 # Set whether a gap space is to be added while 
                       # deinterlacing using the ShadoCam Imaging
                       # Library
CMD_GET_GAP_SPACE = 81 # Get current gap space setting
CMD_SET_OFFSET_CORRECTION = 82 # Turn correction on/off
CMD_GET_OFFSET_CORRECTION = 83 # Get setting
CMD_SET_GAIN_CORRECTION = 84
CMD_GET_GAIN_CORRECTION = 85
CMD_SET_PIXEL_CORRECTION = 86
CMD_GET_PIXEL_CORRECTION = 87
CMD_SET_PIXEL_METHOD = 88 # Choose correction method for pixel correction
CMD_GET_PIXEL_METHOD = 89


########################################################################
# NOTE: Command string styles:
########################################################################
# 
# set exposure tim3, pixel clock, cycle time:
#     
#     CMDNumber_Value, e.g. 40_2000
# 
# set ROI:
#     
#     CMDNumber_XSize_YSize_XOffset_YOffset, e.g. 46_500_600_20_20
# 
# set directory:
#     
#     CMDNumber_DirType_DirName, e.g. 50_1_c://User/Desktop
# 
# set prefix:
#     
#     CMDNumber_Prefix, e.g. 48_tomography
#
# snap shot:
#     
#     CMDNumber_ExposureTime(optional), e.g. 60_2000 [ms]
# 
#     or 60_0 if no exposure time was entered
#
# acquire image:
#     
#     CMDNumber_ExposureTime(optional)_NumbProj_NumbStep,
# 
#     e.g. 61_2000_20_5 [ms] or 61_0_20_5 if no exposure time was entered
#