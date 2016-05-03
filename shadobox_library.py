########################################################################
# 
# schadobox_library.py
#
# All functions to connect to SBWinServer and control framebrabber/ShadoBox
#
# Author: Maria Buechner
#
# History:
# 20.11.2013: started
#
########################################################################

# Imports
import socket
import string
import subprocess # To use linux commands to get user infos
import time
import os
import re
#from sys import stdout
import sys
from sb_command_definitions import *
from gantry_control_exceptions import *

# Constants
HOST = 'PC10005'
PORT = 12345
SOCKET_BUFFERSIZE = 256
# Directory types
RAW_DIR = 0
SNAP_DIR = 1
# Pixel Correction methods
MEAN = 0
INTERPOLATE = 1
GRADIENT = 2
PIXEL_METHODS = ['Mean', 'Interpolate', 'Gradient']

# TODO: automatically determine windrive (or fix!)
# Fix: check and add/delete on winserver!
#WINDRIVE = 'C:\\Users\\buechner_m\\Desktop\\'
WINDRIVE = 'X:\\' # Needs to be mapped to e account (e14980)

# Get user and home directory information
USER = subprocess.Popen('whoami',stdout=subprocess.PIPE).communicate()[0]
USER = USER[0:len(USER)-1]
HOME_DIRECTORY = os.path.expanduser('~')
# If not e-account, add x02da path
if not USER[0]=='e': # 'slsbl' CORRECT???
	HOME_DIRECTORY = HOME_DIRECTORY + '/slsbl/x02da/' + USER
	print("\n[WARNING]: No e-account. Current home directory: {0}"
		  .format(HOME_DIRECTORY))
		  
RAW_PATH = HOME_DIRECTORY+"/Data20/Gantry"
SNAP_PATH = HOME_DIRECTORY+"/Data20/Gantry"

########################################################################
# ShadoBox camera class
########################################################################

class SBCamera:
    """ ShadoBox camera class.
        
        Contains all necessary variables and fuctions to establish a
        connection to the windows server and send and recieve commands
        
        variables:
            
            client_socket: to communicate with windows server
            return_message: incomming and outgoing message
            return_error: return status of server
            
            camera_on: true, if camera is ready
            
            
        functions:
            
            __init__(self, host, port)
            
            connect(self): Connect to server
            disconnect(self): Disconnect from server and stop camera
            
            start(self): init/start SchadoBox/framegrabber
            stop(self): stop/close camera/framegrabber
            
            TODO: rest

    """
    def __init__(self, host=HOST, port=PORT):
        """ Initialization function of SBCamera class
            
            Sets variables to default.
            
            Input valiable:
            
                host: Host PC name of camera server
                port: port number for socket connection      
            
        """
        # Initialize variables
        self._host = host
        self._port = port
        
        self._camera_on = False # true, if camera is ready
        
        self.client_socket = 0
        self._return_message = '' # Incomming and outgoing message
        self._return_error = True # True, if server failed to execute command
                                  # and default 
        
        # Should local and status ([INFO]) messages be printed?
        self._print_info = False # Set always to False, if function is
                                 # called internally
                                
        
    
    ########################################################################
    # Server functions
    ########################################################################
    
    # Connect to windows server
    def connect(self):
        """ Creat a client socket and connect to windows server.
            
            Input parameters:
                
                none
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Check if client socket is already open
        if self.client_socket:
            self._print_info_message('\n[INFO]: Already connected to server.')
            return
            
        self._print_info_message('\n[INFO]: Connecting to server...')
            
        # Create socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to server
        self.client_socket.connect((self._host, self._port))
            
        self._recieve_return_message()
            
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]: ' 
                                        + self._return_message)
                
        self._print_info_message(' done.')
        
    # Disconnect from windows server
    def disconnect(self):
        """ Disconnect client socket from windows server.
            
            Input parameters:
                
                none
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # is there a connection to close?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[INFO]: No open connection '
                                        'to close.')
                
        self._print_info_message('\n[INFO]: Closing client connection'
                                'and camera...')
        
        # Camera still open?
        if self._camera_on:
            # Close camera
            self.stop()

        # Disconnect from server
        self.client_socket.close()
        self.client_socket = 0
            
        self._print_info_message(' done.')
    
    ########################################################################
    # Camera functions
    ########################################################################
    
    ########################################################################
    
    # Start camera
    def start(self):
        """ Start camera on windows server
            
            Open and initialize framegrabber
            
            Input parameters:
                
                none
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Connection open?
        if not self.client_socket:
            # Connect to server
            self.connect()
    
        # Is camera already open?
        if self._camera_on:
            self._print_info_message('\n[INFO]: Camera is already on.')
            return
                
        self._print_info_message('\n[INFO]: Starting camera...')
        
        # Send command
        self._send_message(CMD_START_CAMERA)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' +
                                            self._return_message)
                
        self._camera_on = True
        
        # Set default directories
        self.set_directory(RAW_PATH, RAW_DIR)
	self.set_directory(SNAP_PATH, SNAP_DIR)
        
        self._print_info_message(' done.')
            
    # Stop camera
    def stop(self):
        """ Stop camera on windows server
            
            Input parameters:
                
                none
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection '
                                        'to server. Camera could not '
                                        'be closed.')
            
        
        # Is camera already turned off?
        if not self._camera_on:
            self._print_info_message('\n[INFO]: Camera is already '
                                    'turned off.')
            return
            
        self._print_info_message('\n[INFO]: Stopping camera...')
        
        # Send command
        self._send_message(CMD_STOP_CAMERA)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        self._camera_on = False
        self._print_info_message(' done.')
          
    # Check if camera is turned on
    def is_camera_on(self):
        """Return local camera status
        
        Input parameters:
            
            none
            
        Return values:
            
            returns self._camera_on
    
        """
        return self._camera_on
        
    ########################################################################
    # Settings
    ########################################################################
         
    # Set exposure time
    def set_exposure_time(self, exposure_time):
        """ Set camera exposure time
            
            Send exposure time to windows server
            
            Input parameters:
                
                exposure time in ms (convert to us for framegrabber!)
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
            
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')

        self._print_info_message('\n[INFO]: Setting exposure time to' +
                                '{0} ms...'.format(exposure_time))
            
        # Send command
        self._send_message(CMD_SET_EXPOSURE_TIME, str(exposure_time*1000))
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        self._print_info_message(' done.')
        
    # Get exposure time
    def get_exposure_time(self):
        """ Get camera exposure time
            
            Get exposure time from windows server
            
            Input parameters:
                
                none
                
            Return values:
                
                returns 'exposure time' in ms, if succeeds
                returns -1, if error occurs
        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')

        # Send command
        self._send_message(CMD_GET_EXPOSURE_TIME)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
                
        return int(self._return_message)/1000 # if succeeds, exposure time is
                                               # return message
    
    # Set pixel clock
    def set_pixel_clock(self, pixel_clock):
        """ Set pixel clock
            
            Send pixel clock frequency to windows server
            
            Input parameters:
                
                pixel clock frequency in Hz
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')
        
        self._print_info_message('\n[INFO]: Setting pixel clock '
                                'frequency to {0} Hz...'.format(pixel_clock))
            
        # Send command
        self._send_message(CMD_SET_PIXEL_CLOCK, str(pixel_clock))
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
                
        self._print_info_message(' done.')
        
    # Get pixel clock
    def get_pixel_clock(self):
        """ Get pixel clock
            
            Get pixel clock frequency from windows server
            
            Input parameters:
                
                none
                
            Return values:
                
                returns 'pixel clock frequency', if succeeds
                returns -1, if error occurs
        
        """ 
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
            
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')
                
        # Send command
        self._send_message(CMD_GET_PIXEL_CLOCK)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
                
        return int(self._return_message) # if succeeds, pixel clock is
                                            # return message                                         
                                     
    # Set cycle time
    def set_cycle_time(self, cycle_time):
        """ Set camera cycle time
            
            Send cycle time to windows server
            
            Input parameters:
                
                cycle time in us
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
            
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')
                
        self._print_info_message('\n[INFO]: Setting cycle time to '
                                '{0} us...'.format(cycle_time))
                
        # Send command
        self._send_message(CMD_SET_CYCLE_TIME, str(cycle_time))
        # Recieve response
        self._recieve_return_message()
            
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        self._print_info_message(' done.')
        
    # Get cycle time
    def get_cycle_time(self):
        """ Get camera cycle time
            
            Get cycle time from windows server
            
            Input parameters:
                
                none
                
            Return values:
                
                returns 'cycle time', if succeeds
                returns -1, if error occurs
        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')
            
        # Send command
        self._send_message(CMD_GET_CYCLE_TIME)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        return int(self._return_message) # if succeeds, cycle time is
                                          # return message
                                         
     # Set ROI time
    def set_roi(self, number_of_rows=1024, number_of_columns=2048,
                row_offset=0, column_offset=0):
        """ Set ROI
            
            Send ROI parameters to windows server. Point of origin is at
            (0, 0) at the upper left corner of the detector.
            
            Input parameters:
                
                #rows (y_size): in pixel, >=1 and <=1024
                #columns (x_size): in pixel, >=1 and <=2048
                row offset (y_offset): in pixel, >0 and <=1024 - number_of_rows
                column offset (x_offset): in pixel, >0 and <=2048
                                                            - number_of_columns
                
                default: full field, 1024x2048 at (0, 0)
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
            
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')
            
        # Check if correct input arguments
   	if(number_of_columns<=0 or number_of_columns>2048 or 
    	   number_of_rows<=0 or number_of_rows>1024 or row_offset<0 or
    	   row_offset>1023 or column_offset<0 or column_offset>2047):
    	   raise ErrorCameraInterrupt('\n[ERROR]: Invalid ROI parameter(s).')
    	  
   	elif(number_of_columns>2048-column_offset or 
 	      number_of_rows>1024-row_offset):
   	    raise ErrorCameraInterrupt('\n[ERROR]: Image size and offset '
  	                               'not compatible.')
            
        self._print_info_message('\n[INFO]: Setting ROI to {0}x{1} at '
                                '({2}, {3})...'.format(number_of_rows, 
                                number_of_columns, column_offset, row_offset))
            
        # Send command
        # Send message like (x_size, y_size, x_offset, y_offset)
        self._send_message(CMD_SET_ROI, 
                '{0}_{1}_{2}_{3}'.format(number_of_columns, number_of_rows,
                column_offset, row_offset))
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        self._print_info_message(' done.')
        
    # Get ROI time
    def get_roi(self):
        """ Get current region of interest
            
            Get ROI from windows server
            
            Input parameters:
                
                none
                
            Return values:
                
                returns 'roi', if succeeds
                returns -1, if error occurs
        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
            
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')
                
        # Send command
        self._send_message(CMD_GET_ROI)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
        
        # Parse return  message
        roi = string.split(self._return_message, '_')
        return map(int, roi) # Converts all strings in list into integer
              
    # Set file directory
    def set_directory(self, dir_name, dir_type=RAW_DIR):
        """ Set directory path
            
            Based on dir_type, set snap shot or .raw image directory
            
            Input parameters:
                
                dir_type: 0 OR RAW_DIR: .raw (default)
                        1 OR SNAP_DIR: snap.tiff
                dir_name: valid path to directory name
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')
        
        # Check if valid directory type was entered
        
        # Check if valid path was entered
       	# Is homedir included?
       	if dir_name.find(HOME_DIRECTORY)!=-1:
       	    path = dir_name
       	# Is tilde at beginning?
       	elif dir_name[0]=='~':
            path = HOME_DIRECTORY + dir_name[1:len(dir_name)]
       	else:
            path = HOME_DIRECTORY + '/' + dir_name
       
       	# Check if path exists
       	if not self._is_dir(path):
            raise ErrorCameraInterrupt('\n[ERROR]: Directory does not exist.')
        
      
       	# Create windows path (make '/' in string '\\' (aka \), so that
       	# CreateFile() will interpret the path correctly
       	# NOTE: This needs to be undone, if path is recieved
       	path = self._path_lin2win(path)
       
       	dir_types = ('.raw', 'snap.raw')
       	self._print_info_message('\n[INFO]: Setting {0} directory to '
  	                         '{1}...'.format(dir_types[dir_type], path))
        
        # Send command
        self._send_message(CMD_SET_DIRECTORY, 
                        '{0}_{1}'.format(dir_type, path))
        # Recieve response
        self._recieve_return_message()
            
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        self._print_info_message(' done.')
        
    # Get directory
    def get_directory(self, dir_type=RAW_DIR):
        """ Get current directory path
            
            Based on dir_type, set snap shot or .raw image directory
            
            Input parameters:
                
                dir_type: 0 OR RAW_DIR: .raw (default)
                        1 OR SNAP_DIR: snap.raw
                dir_name: valid path to directory name
                
            Return values:
                
                returns directory, if succeeds
                returns '' if error occurs
        
        """   
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')
            
        dir_types = ('.raw', 'snap.raw')
        self._print_info_message('\n[INFO]: {0} directory is:'.format(
                                dir_types[dir_type]))
            
        # Send command
        self._send_message(CMD_GET_DIRECTORY, dir_type)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
        
        # Convert to linux path (if string is not empty
        if self._return_message:
            path = self._path_win2lin(self._return_message)
        else:
            # For empty string
            path = HOME_DIRECTORY

        return path

    # Set filename prefix
    def set_prefix(self, prefix):
        """ Set filename prefix
            
            Input parameters:
                
                prefix; resulting filename: prefix_NumbProjection_NumbStep
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')
        
        # Check if valid (windows) filename was entered
        if not self._is_valid_filename(prefix):
            raise ErrorCameraInterrupt('\n[ERROR]: Prefix name is not valid.\n'
                                'Valid characters are: A...Z, a...z, '
                                '0...9, _ and -')
        
   	self._print_info_message('\n[INFO]: Setting filename prefix to '
  	                         '{0}...'.format(prefix))
        
        # Send command
        self._send_message(CMD_SET_PREFIX, prefix)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        self._print_info_message(' done.')
        
    # Get prefix
    def get_prefix(self):
        """ Get current filename prefix
            
            Input parameters:
                
                none
                
            Return values:
                
                returns prefix, if succeeds
                returns '' if error occurs
        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')
        
        # Send command
        self._send_message(CMD_GET_PREFIX)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        return self._return_message
        
    ########################################################################
    # SchadoCam Imaging Library
    ########################################################################  
        
    # Set gap space setting
    def set_gap_space(self, gap_space):
        """ Set gap space setting
            
            Input parameters:
                
                gap_space; 1, if gap sapce is to be added
                           0, if no gap space is to be added
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
            
        # Covnert boolean to int (in case boolean value is entered
        gap_space = int(gap_space)
        
   	self._print_info_message('\n[INFO]: Setting gap space setting to '
  	                         '{0}...'.format(gap_space))
        
        # Send command
        self._send_message(CMD_SET_GAP_SPACE, gap_space)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        self._print_info_message(' done.')
        
    # Get gap space setting
    def get_gap_space(self):
        """ Get current gap space setting
            
            Input parameters:
                
                none
                
            Return values:
                
                returns gap space setting (0 or 1), if succeeds
        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Send command
        self._send_message(CMD_GET_GAP_SPACE)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        return self._return_message
        
    # Set offset correction setting
    def set_offset_correction(self, offset_correction):
        """ Set offset correction setting
            
            Input parameters:
                
                offset_correction; 1, if offset correction is to be done
                                   0, if offset correction is not to be done
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
            
        # Covnert boolean to int (in case boolean value is entered)
        offset_correction = int(offset_correction)
        
   	self._print_info_message('\n[INFO]: Setting offsetcorrection setting '
  	                         'to {0}...'.format(offset_correction))
        
        # Send command
        self._send_message(CMD_SET_OFFSET_CORRECTION, offset_correction)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        self._print_info_message(' done.')
        
    # Get offsetcorrection setting
    def get_offset_correction(self):
        """ Get current offset correction setting
            
            Input parameters:
                
                none
                
            Return values:
                
                returns offset correction setting (0 or 1), if succeeds
        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Send command
        self._send_message(CMD_GET_OFFSET_CORRECTION)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        return self._return_message
        
    # Set gain correction setting
    def set_gain_correction(self, gain_correction):
        """ Set gain correction setting
            
            Input parameters:
                
                gain_correction; 1, if gain correction is to be done
                                   0, if gain correction is not to be done
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
            
        # Covnert boolean to int (in case boolean value is entered)
        gain_correction = int(gain_correction)
        
   	self._print_info_message('\n[INFO]: Setting gain correction setting '
  	                         'to {0}...'.format(gain_correction))
        
        # Send command
        self._send_message(CMD_SET_GAIN_CORRECTION, gain_correction)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        self._print_info_message(' done.')
        
    # Get gain correction setting
    def get_gain_correction(self):
        """ Get current gain correction setting
            
            Input parameters:
                
                none
                
            Return values:
                
                returns gain correction setting (0 or 1), if succeeds
        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Send command
        self._send_message(CMD_GET_GAIN_CORRECTION)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        return self._return_message
        
    # Set pixel correction setting
    def set_pixel_correction(self, pixel_correction):
        """ Set pixel correction setting
            
            Input parameters:
                
                pixel_correction; 1, if pixel correction is to be done
                                   0, if pixel correction is not to be done
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
            
        # Covnert boolean to int (in case boolean value is entered)
        pixel_correction = int(pixel_correction)
        
   	self._print_info_message('\n[INFO]: Setting pixel correction setting '
  	                         'to {0}...'.format(pixel_correction))
        
        # Send command
        self._send_message(CMD_SET_PIXEL_CORRECTION, pixel_correction)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        self._print_info_message(' done.')
        
    # Get pixel correction setting
    def get_pixel_correction(self):
        """ Get current pixel correction setting
            
            Input parameters:
                
                none
                
            Return values:
                
                returns pixel correction setting (0 or 1), if succeeds
        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Send command
        self._send_message(CMD_GET_PIXEL_CORRECTION)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        return self._return_message
        
    # Set pixel correction method
    def set_pixel_method(self, pixel_method):
        """ Set pixel correction method
            
            Input parameters:
                
                pixel_method:
                    
                    SCMETHOD_MEAN:        0	simple mean of adjacent pixels
                    SCMETHOD_INTERPOLATE: 1	interpolate across line defects
                    SCMETHOD_GRADIENT:    2	interpolate along minimum 
                                                gradient
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
   	self._print_info_message('\n[INFO]: Setting pixel correction method '
  	                         'to {0}...'.format(pixel_method))
        
        # Send command
        self._send_message(CMD_SET_PIXEL_METHOD, pixel_method)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
            
        self._print_info_message(' done.')
        
    # Get pixel correction method
    def get_pixel_method(self):
        """ Get current pixel correction method
            
            Input parameters:
                
                none
                
            Return values:
                
                returns pixel correction method (0, 1 or 2), if succeeds
        
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Send command
        self._send_message(CMD_GET_PIXEL_METHOD)
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
        
        pixel_method = int(self._return_message)
        return ("{0} ({1})".format(PIXEL_METHODS[pixel_method], pixel_method))
        #return self._return_message
        
    ########################################################################
    # List all current settings
    ########################################################################
    
    def settings(self):
        """ List current settings ()except cycle time, since definition 
            not necessary...)
        
            Input parameters:
                
                none
                
            Return values:
                
                none (just print onto screen)
                
        """
        print("\nCurrent settings:"
               "\n"
               "\nExposure time:\t\t{0} ms"
               "\nROI:\t\t\t{1}"
               "\nPrefix:\t\t\t{2}"
               "\nData shot directory:\t{3}"
               "\nSnap shot directory:\t{4}"
               "\nGap space setting:\t{5} (0: do not add; 1: add)"
               "\nPixel clock:\t\t{6} Hz".format(self.get_exposure_time(),
               self.get_roi(), self.get_prefix(), self.get_directory(RAW_DIR),
               self.get_directory(SNAP_DIR), self.get_gap_space(),
               self.get_pixel_clock()))
        
    ########################################################################
    # Acquisition
    ########################################################################
        
    # Acquire snap shot
    def snap(self, exposure_time=0):
        """ Acquire and save a snap shot image
            
            Images saved as snap.tiff in snap shot folder. Set exposure time
            optional, if 0, then use current exposure time
            
            Input parameters:
                
                exposure time [ms], default: 0 (use current exposure time)
                
            Return values:
                
               raises camera exception, if error occurs

                
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection '
                                        'to server.')
        
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')
            
        self._print_info_message('\n[INFO]: Acquiring snap shot...')
            
        # Send command (convert exposur etime to us for framegrabber)
        self._send_message(CMD_SNAP, '{0}'.format(exposure_time*1000))
        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
        
        self._print_info_message(' done.')
        
        # Signal file change to linux folder system
        snap_file = self.get_directory(SNAP_DIR) + '/snap.raw'
        os.utime(snap_file, None)
        
    # Acquire single image
    def acquire(self, image_count, number_of_digits, exposure_time=0):
        """ Acquire and save a single image
            
            Images saved as .raw in data folder.
            
            Input parameters:
                
                image_count: current number of acquisition
                number_of_digits: number of digits to store image count in
                exposure_time (default = 0): if not zero, new exposure time
											 is set before aquisition
                
            Return values:
                
               raises camera exception, if error occurs

                
        """
        # Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')

	# Set new exposure time?
        if exposure_time:
		    self.set_exposure_time(exposure_time)
            
        self._print_info_message('\n[INFO]: Acquiring single image...')
        
        # Send command
        self._send_message(CMD_ACQUIRE, '{0}_{1}'.format(
                                        image_count, number_of_digits))
#        self._send_message(CMD_ACQUIRE, '{0}_{1}_{2}'.format(
#                        exposure_time, projection_number, step_number))

        # Recieve response
        self._recieve_return_message()
        
        # Print returned error message if necessary
        if self._return_error:
            raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                        self._return_message)
        
        self._print_info_message(' done.')

    # From Thomas (adapted)
    def exposure(self, cnt, digits, retry=1):
        """ Exposure function acquires one image for given settings,
            adapted from Thmoas Thuering
            
            Can be used with Thomas phase retrieval and reconstruction 
            algorithms.
            
            Input parameters:
                
                cnt: image counter, set images name with digits
                digits: number of digits for image counter in image name
                retry: number of retries for images acquisition,
                       if acquisition (communications) fails
                
            Return values:
                
               raises camera exception, if error occurs
            
        """	
	# Connection open?
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to server.')
        
        # Is camera open?
        if not self._camera_on:
            raise ErrorCameraInterrupt('\n[ERROR]: Camera not started.')
		
	#start exposure
	retry_left = retry
        while retry_left>0:
  	    sstr = str(cnt) + "." + str(digits)
	    try:
	        self._send_message(CMD_EXPOSURE,sstr)
	        
	        self._recieve_return_message()
		
		# Print returned error message if necessary
		# Now image was not acquired!
                if self._return_error:
                    raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                                self._return_message)
		
              	# If no exeptions were raise: images successfully acquired!	
	        retry_left = -1 #-1: successful exposure
		
	    except ErrorCameraInterrupt: #sending error
	        print ('\nError while sending or recieveing command... '
	               'retry exposure!')
	        if retry-retry_left >= 5:
		    print "retry exposure in 5 minutes..."
		    time.sleep(300) #wait for 5 minutes
	        elif retry-retry_left >= 3:
		    print "retry exposure in 1 minute..."
		    time.sleep(60) #wait for one minute
	        else:
		    print "retry exposure..."
				
	        #now try again
	        retry_left = retry_left-1
	        
	    except KeyboardInterrupt:
	        print "\nKeyboard interrupt, stop exposure..."
	        self._recieve_return_message()
	        # Print returned error message if necessary
                if self._return_error:
                    raise ErrorCameraInterrupt('\n[SERVER ERROR]:' + 
                                                self._return_message)
                #return
	
	#end while
		
	if retry_left==0: #give up trying, exposure failed
	    raise # raise last exception to communicate error

	
 #   def exposure(self, counter, digits, retries):
 #       """ 
 #           
 #       """
 #       global PI_client_socket
	#global PI_cameraOn
	#global srvMsgON
	#global PI_dat
	#
	##connection checking
	#if not PI_client_socket:
	#	_printMsg("ERROR: No server connection established")
	#	return _returnVal(False)
	#
	#if not PI_cameraOn:
	#	_printMsg("ERROR: Camera has not yet been started!")
	#	return _returnVal(False)
	#	
	##start exposure
	#retry_left = retry
	#while retry_left>0:
 # 	    sstr = str(cnt) + "." + str(digits)
	#    if _PISend(CMD_EXPOSURE,sstr):
	#        try:
	#	    recv = _PIReceive()
	#        except KeyboardInterrupt, e:
	#	    print "Keyboard interrupt, stop exposure..."
	#	    _PIReceive()
	#	    return _returnVal(False)
	#			
	#        if recv:
	#	    retry_left = -1 #-1: successful exposure
	#        else: #receiving error
	#	    _printRcvError(CMD_EXPOSURE,PI_dat)
	#	    if retry-retry_left >= 5:
	#	        print "retry exposure in 5 minutes..."
	#	        time.sleep(300) #wait for 5 minutes
	#	    elif retry-retry_left >= 3:
	#	        print "retry exposure in 1 minute..."
	#	        time.sleep(60) #wait for one minute
	#	    else:
	#	        print "retry exposure..."
	#			
	#	    #now try again
	#	    retry_left = retry_left-1
	#	
	#    else: #sending error
	#        print "Error while sending command"
	#        if retry-retry_left >= 5:
	#	    print "retry exposure in 5 minutes..."
	#	    time.sleep(300) #wait for 5 minutes
	#        elif retry-retry_left >= 3:
	#	    print "retry exposure in 1 minute..."
	#	    time.sleep(60) #wait for one minute
	#        else:
	#	    print "retry exposure..."
	#			
	#        #now try again
	#        retry_left = retry_left-1
	#
	##end while
	#	
	#if retry_left==0: #give up trying, exposure failed
	#    return _returnVal(False)
	#
	#_printRcvOK(CMD_EXPOSURE,PI_dat)
	#
	#return _returnVal(True)

        
    ########################################################################
    # Public utility functions
    ########################################################################
    
    # Turn on display of info messages
    def info_on(self):
        self._print_info = True
    
    # Turn off display of info messages
    def info_off(self):
        self._print_info = False
    
    ########################################################################
    # Private functions
    ########################################################################
    
    def _send_message(self, command, message=''):
        """ Send a message (or command) to server.
            
            Input parameters:
                
                Command number: Constant number corresponding to command
                Command message: string containing all necessary information
                
            Return values:
                
               raises camera exception, if error occurs

        
        """
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to '
                                        'server open.')
        
        self.client_socket.send('{0}_{1}'.format(command, message))
        
    
    def _recieve_return_message(self):
        """ Recieve return message from server.
            
            Call the function immediately after sending a command. Return 
            message will be in this format:
                "ReturnNumber_Message"
            
            Input parameters:
                
                none
                
            Return values:
                
               raises camera exception, if error occurs
        
        """
        if not self.client_socket:
            raise ErrorCameraInterrupt('\n[ERROR]: No connection to '
                                        'server open.')
        
        # Reset return error and return message
        self._return_error = True
        self._return_message = ''
        
        # Recieve message
        message = self.client_socket.recv(SOCKET_BUFFERSIZE)
        # If empty
        if message=='':
            # Set return message to print later
            self._return_message = ''
            raise ErrorCameraInterrupt('\n[ERROR]: Server response could '
                                        'not be recieved.')
        
        # Parse message into error number and message
        temp = string.split(message,'_',1)
        # Store returned message
        self._return_message = temp[1]
        # Handle returned error number
        if int(temp[0])==RETURN_OK:
            self._return_error = False
            return
        elif int(temp[0])==RETURN_ERROR:
            self._return_error = True
            return
        else:
            raise ErrorCameraInterrupt('\n[ERROR]: Invalid error status '
                                        'from server.')
    
    ########################################################################
    # Private utility functions
    ########################################################################
    
            
    # Print info message if desired
    def _print_info_message(self, msg):
        """ Print info message, if print_error is true.
            
            Input parameters:
                
                msg, string containing the message
                
            Return values:
                
                none
    
        """
        if self._print_info:
            # If msg is contains 'done.', print in same line
            if 'done.' in msg:
                stdout.write(msg)
            else:
                print msg
    
    # Check if enterd path is existing directoy
    def _is_dir(self, path):
        """ Checks whether the imput path exists
            
            Input parameters:
                
            path, string containing directory
                
            Return values:
                
                True, if path existes
                False, if path doen not exists
                
        """
        # Does path end on '/'
	if path[len(path)-1]!='/':
		path = path + '/'
	directory = os.path.dirname(path)
	if not os.path.exists(directory):
		return False
	return True

    # Convert linux path to windows (adapted from Thomas)
    def _path_lin2win(self, path):
        """ Converts linux path to windows path
            
            Input parameters:
                
            path, string containing directory
                
            Return values:
                
                True, if error occurs and path was not converted
                otherwise: converted path
                
        """
	# Does path exist?
	if not os.path.exists(os.path.dirname(path)):
	    return True
	
	# Remove linux home directory
	if path.find(HOME_DIRECTORY)==-1:
	    raise ErrorCameraInterrupt('\n[ERROR]: Trying to convert unknown path.')
	
	# Remove linux home directory
	directory = path[len(HOME_DIRECTORY)+1:len(path)]
	
	# Replace '/' with '\'
	directory = directory.replace('/','\\')
	
	# Add WINDRIVE at the beginning
	directory = WINDRIVE + directory
	return directory
	
    # Convert windows path to linux (adapted from Thomas)
    def _path_win2lin(self, path):
        """ Converts windows path to linux path
            
            Input parameters:
                
            path, string containing directory
                
            Return values:
                
                True, if error occurs and path was not converted
                otherwise: converted path
                
        """
	if path.find(WINDRIVE)==-1:
	    raise ErrorCameraInterrupt('\n[ERROR]: Trying to convert '
	                         'unknown windows directoy.')
	
	# Remove WINDRIVE
	directory = path[len(WINDRIVE):len(path)]	
	
	# Replace '\' with '/'
	directory = directory.replace('\\','/')
	
	#add home directory
	directory = HOME_DIRECTORY + '/' + directory
	
	return directory
	
    # Check if prefix name (filename) does contain any invald characters
    def _is_valid_filename(self, name):
        """ Checks whether the imput (prefix) name is valid
            
            Valid characters are:
                A...Z, a...z, 0...9, _ and -
            
            Input parameters:
                
            name, string containing name
                
            Return values:
                
                True, name is valid
                False, if name is not valid
            
        """
        # Valid characters are:
        #   A...Z, a...z, 0...9, _ and -
        if not re.findall(r'[^A-Za-z0-9_\-]', name):
            return True # no invalid characters were returned
            
        return False


########################################################################
# Main
########################################################################

sb = SBCamera()
