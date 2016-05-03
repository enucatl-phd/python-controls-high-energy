########################################################################
# 
# gantry_DPC_functions.py
#
# Partially COPIED (and adjusted) from Thomas, to use for testing
#
# Implements DPC functionality for the cDPC setup, which includes
# visibility scans, radiographic scans, tomographic scans, ...
#
# Author: Thomas Thuering
#
# History:
# 11.01.2011: first release
# 10.12.2013: modiefied (maria.buechner@psi.ch)
#
########################################################################

# Imports
from sys import stdout
# Imports need to be done like this, to only import the module once,
# even if it is imported again in another module!
from shadobox_library import *
from tube_library import *
# from gantry_motors import *
from gantry_control_exceptions import *

#import epics
import math
import time
#import gantry_tomoparams # incorporate into log file writing (?)
    
#from utils import * # customize...

# Constants

# Set-up
SOURCE_TO_G1 = 440 # [mm]
G1_TO_G2 = 44 # [mm]
DETECTOR_LINE_DISTANCE = 50 # [um]
# Phase stepping (scanning through sample)
MIN_PHASE_STEPS = 5
REFERENCE_SCANS = 5
DARK_SCANS = 5
# Motor positions
GB_ROTY_START_POSITION = 0 # [rad]
GB_ROTY_END_POSITION = math.pi # [rad]


## Is tube still on?
#        if not tube.is_ready():
#            raise ErrorScanInterrupt('\n[ERROR]: Tube active.')

########################################################################
# DPCFunctions class
########################################################################

class DPCFunctions:
    """ DPC functions class.
        
        Contains all necessary variables and fuctions to use gantry motors,
        shadobox camera and tube to acquire images and do (3D) scans etc.
        
        Input valiable:
            
            none
        
        variables:
            
            
            
        functions:

            __init__()
            dpc_image()
            radiography() (add dark scans and flat fields)

    """
    def __init__(self, source_to_G1=SOURCE_TO_G1, G1_to_G2=G1_TO_G2, 
                 detector_line_distance=DETECTOR_LINE_DISTANCE):
        """ Initialization function to set set-up parameters
            
            Input parameters:
                
                source_to_G1: distance from source to G1 [mm]
                G1_to_G2: distance G1 to G2 [mm]
                detector_line_distance: distance between 2 detector lines [um]
                
                
                
            Return values:
                
                none
        
        """
        self.source_to_G1 = source_to_G1
        self.G1_to_G2 = G1_to_G2
        self.detector_line_distance = detector_line_distance
        
        
        
    ###########################################################################
    # Public functions
    ###########################################################################

    def image_series(self, name, number_images, waiting_time, exposure_time=0):
        """ bla bla
        """
        # Is camera ready?
        if not sb.is_camera_on():
            raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
        
        # Set prefix
        if name:
            sb.set_prefix(name)
        
        # Set exposure time if necessary
        if exposure_time:
            sb.set_exposure_time(exposure_time)

	for image in range(0,number_images):
            sb.acquire(image, 4)
            time.sleep(waiting_time)
    
    def acquire_ps_series(self, start_position, name, step_width, 
                            number_proje, wait=0):
        sb.set_prefix(name)
        
        gb_roty.mv(start_position)
        print("go to start position")
        if wait:
            time.sleep(wait)
            
        for current_step in range(0, number_steps):
            
            sb.acquire(current_step, 4)
            
            gb_roty.mvr(step_width)
            if wait:
                time.sleep(wait)
            print("acquire image for step: {0}"
                .format(current_step))
    
    def acquire_series(self, start_position, name, step_width, 
                        number_steps, wait=0):
        sb.set_prefix(name)
        
        gb_roty.mv(start_position)
        print("go to start position")
        if wait:
            time.sleep(wait)
            
        for current_step in range(0, number_steps):
            
            sb.acquire(current_step, 4)
            
            gb_roty.mvr(step_width)
            if wait:
                time.sleep(wait)
            print("acquire image for step: {0}"
                .format(current_step))
        
    def acquire_image(self, motor_name, start_position, name, distance, wait=0):
        if motor_name == 'TRY':
            sh_try.mv(start_position)
            print("go to start position")
            
            sb.set_prefix(name)
            print("acquire image at start position")
            sb.acquire(0, 4)
            
            sh_try.mvr(distance)
            print("acquire image at end position")
            sb.acquire(1, 4)
            
        elif motor_name == 'TRZ':
            gb_trz.mv(start_position)
            print("go to start position")
            
            sb.set_prefix(name)
            print("acquire image at start position")
            sb.acquire(0, 4)
            
            gb_trz.mvr(distance)
            print("acquire image at end position")
            sb.acquire(1, 4)
            
        elif motor_name == 'ROTY':
            gb_roty.mv(start_position)
            print("go to start position")
            if wait:
                time.sleep(wait)
            
            sb.set_prefix(name)
            print("acquire image at start position")
            sb.acquire(0, 4)
            
            #gb_roty.mvr(self._degree_to_rad(distance))
            gb_roty.mvr(distance)
            if wait:
                time.sleep(wait)
            print("acquire image at end position. Step: {0}"
                .format(self._rad_to_degree(distance)))
            sb.acquire(1, 4)
        else:
            raise ErrorScanInterrupt("Incorrect motor selected!")
    
    # DPC image acquisition
    def projection_multiple_refs(self, sample_start_position, projection_name='', 
                   number_phase_steps=MIN_PHASE_STEPS, distance_between_lines=1,
                   step_size=0, number_dark_current=DARK_SCANS, 
                   number_reference_scan=REFERENCE_SCANS, 
                   exposure_time=0):
        """ Acquire DPC projection.
        
            NOTE: Here, sample is smaller than detector hight!
        
            If necessary, the exposure time can be set. Otherwise current
            setting will be used.
            
            Input parameters:
                
                sample_start_position: Start position of SH_TRY motor
                projection_name: image name (default='') -> use current
                number_phase_steps (default=MIN_PHASE_STEPS)
                distance_between_lines (deafult=1): gap between lines [in lines]
                step_size (deault=0): [um], Sample step size, if 0: calculate
                                      needs to be smaller than distance 
                                      between two detector lines (D)
                                      step_size = D*l/(l+d)
                                      with
                                      l: source to G1 distance
                                      d: G1 to G2 distance
                number_dark_current (default: 5): Number of acquired dark 
                                                  current scans
                number_reference_scans (default: 5): Number of acquired
                                                     reference scans
                exposure_time (default=0): if zero or not entered
                                           -> use current setting
                                           
            Return values:
                
                none
        
        """
        # Is camera ready?
        if not sb.is_camera_on():
            raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
        
        # Tube connected (serial communication open)?
        if not tube.is_connected():
            raise ErrorScanInterrupt('\n[ERROR]: Tube not started.')
        
        ## Is x-ray on?
        #if not tube.is_on():
        #    raise ErrorScanInterrupt('\n[ERROR]: X-ray turned off. Please'
        #                              'turn on x-ray and start again.')
        
        # Set prefix
        if projection_name:
            sb.set_prefix(projection_name)
        
        # Set exposure time if necessary
        if exposure_time:
            sb.set_exposure_time(exposure_time)
            
        # Init
        
        #Step size
        if not step_size:
            step_size = self.detector_line_distance*distance_between_lines \
                             *self.source_to_G1 \
                             / (self.source_to_G1 + self.G1_to_G2)
        print("\n[INFO]: Step size is: {0} um".format(step_size))
        
        #number_acquisition_points = number_phase_steps + 1
        #number_digits = int(math.log(number_acquisition_points,10)) + 1
        # Get the number of digits necessary to save all images to be acquired
	number_digits = int(math.log(number_phase_steps,10)) + 1
	number_digits = max(number_digits,4)
	image_count = 0
	
	# Get dark current
	print("\n[INFO]: Acquiring {0} dark current scans.".
	       format(number_dark_current))
	if tube.is_on():
	   tube.off()
	   time.sleep(4)
	
	for i in range(0, number_dark_current):
	    sb.acquire(image_count, number_digits)
            image_count = image_count + 1
            print("\nDark current scan number {0} done.".format(image_count))
	
        # Get reference scans
        print("\n[INFO]: Acquiring {0} reference scans.".
	       format(number_reference_scan))
	  
	tube.on()
        time.sleep(4)
        
        print("\n[INFO]: Moving sample to start position...")
        sh_try.mv(sample_start_position)
	
	for i in range(0, number_reference_scan):
	    # Pretent to move sample, to account for vibrations caused by
            # motor movement
	    for j in range(0, number_phase_steps):
                sb.acquire(image_count, number_digits)
                image_count = image_count + 1
                print("\nReference scan number {0}.{1} done.".
                      format(i+1,j+1))
                # Move sample one step width
                #mv(SHTRY, sample_start_position + image_count*self.step_size)
                sh_try.mvr(step_size)
            print("\n[INFO]: Moving sample to start position...")
            sh_try.mv(sample_start_position)
        
        # Stop emmission to place sample
        tube.off()
        time.sleep(2)
        a = raw_input("\n[INFO]: Place sample and secure door!"
                      "\nPress any key to continue...")
        
        # Get object scans
        
        # Move sampte to start position
        print("\n[INFO]: Moving sample to start position...")
        sh_try.mv(sample_start_position)
        print("done.")
        
        print("\n[INFO]: Acquiring {0} object phase steps.".
	       format(number_phase_steps))
        
        tube.on()
        time.sleep(4)
        
        for i in range(0, number_phase_steps): # or number_acquisition_points
            sb.acquire(image_count, number_digits)
            image_count = image_count + 1
            print("\nPhase step number {0} done.".
                   format(i+1))
            # Move sample one step width
            #mv(SHTRY, sample_start_position + image_count*self.step_size)
            sh_try.mvr(step_size)
            #time.sleep(4)
        
        tube.off()
        
        # Move sampte to start position
        print("\n[INFO]: Moving sample to start position...")
        sh_try.mv(sample_start_position)
        
    # DPC image acquisition
    def projection(self, sample_start_position, projection_name='', 
                   number_phase_steps=MIN_PHASE_STEPS, 
                   distance_between_lines=1, step_size=0, 
                   number_dark_current=DARK_SCANS, 
                   number_reference_scan=REFERENCE_SCANS, 
                   exposure_time=0):
        """ Acquire DPC projection.
        
            NOTE: Here, sample is smaller than detector hight!
        
            If necessary, the exposure time can be set. Otherwise current
            setting will be used.
            
            Input parameters:
                
                sample_start_position: Start position of SH_TRY motor
                projection_name: image name (default='') -> use current
                number_phase_steps (default=MIN_PHASE_STEPS)
                distance_between_lines (deafult=1): gap in lines between lines
                step_size (deault=0): [um], Sample step size, if 0: calculate
                                      needs to be smaller than distance 
                                      between two detector lines (D)
                                      step_size = D*l/(l+d)
                                      with
                                      l: source to G1 distance
                                      d: G1 to G2 distance
                number_dark_current (default: 5): Number of acquired dark 
                                                  current scans
                number_reference_scans (default: 5): Number of acquired
                                                     reference scans
                exposure_time (default=0): if zero or not entered
                                           -> use current setting
                                           
            Return values:
                
                none
        
        """
        # Is camera ready?
        if not sb.is_camera_on():
            raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
        
        # Tube connected (serial communication open)?
        if not tube.is_connected():
            raise ErrorScanInterrupt('\n[ERROR]: Tube not started.')
        
        ## Is x-ray on?
        #if not tube.is_on():
        #    raise ErrorScanInterrupt('\n[ERROR]: X-ray turned off. Please'
        #                              'turn on x-ray and start again.')
        
        # Set prefix
        if projection_name:
            sb.set_prefix(projection_name)
        
        # Set exposure time if necessary
        if exposure_time:
            sb.set_exposure_time(exposure_time)
            
        # Init
        
        #Step size
        if not step_size:
            step_size = self.detector_line_distance*distance_between_lines \
                             *self.source_to_G1 \
                             / (self.source_to_G1 + self.G1_to_G2)
        print("\n[INFO]: Step size is: {0} um".format(step_size))
        
        #number_acquisition_points = number_phase_steps + 1
        #number_digits = int(math.log(number_acquisition_points,10)) + 1
        # Get the number of digits necessary to save all images to be acquired
	number_digits = int(math.log(number_phase_steps,10)) + 1
	number_digits = max(number_digits,4)
	image_count = 0
	
	# Get dark current
	print("\n[INFO]: Acquiring {0} dark current scans.".
	       format(number_dark_current))
	if tube.is_on():
	   tube.off()
	   time.sleep(2)
	
	for i in range(0, number_dark_current):
	    sb.acquire(image_count, number_digits)
            image_count = image_count + 1
            print("\nDark current scan number {0} done.".format(image_count))
	
        # Get reference scans
        print("\n[INFO]: Acquiring {0} reference scans.".
	       format(number_reference_scan))
	  
	tube.on()
        time.sleep(4)
	
	for i in range(0, number_reference_scan):
            sb.acquire(image_count, number_digits)
            image_count = image_count + 1
            print("\nReference scan number {0} done.".
                   format(image_count-number_dark_current))
            # No sample movement necessary, as flat scans gan be used to create
            # phase stepping series bu copying and rearranging the lines!
        
        # Stop emmission to place sample
        tube.off()
        time.sleep(2)
        a = raw_input("\n[INFO]: Place sample and secure door!"
                      "\nPress any key to continue...")
        
        # Get object scans
        
        # Move sampte to start position
        print("\n[INFO]: Moving sample to start position...")
        sh_try.mv(sample_start_position)
        print("done.")
        
        print("\n[INFO]: Acquiring {0} object phase steps.".
	       format(number_phase_steps))
        
        tube.on()
        time.sleep(4)
        
        for i in range(0, number_phase_steps): # or number_acquisition_points
            sb.acquire(image_count, number_digits)
            image_count = image_count + 1
            print("\nPhase step number {0} done.".
                   format(image_count-number_dark_current- \
                          number_reference_scan))
            # Move sample one step width
            #mv(SHTRY, sample_start_position + image_count*self.step_size)
            sh_try.mvr(step_size)
            #time.sleep(4)
        
        tube.off()
        
        print("\n[INFO]: Moving sample to start position...")
        sh_try.mv(sample_start_position)
    
 #   # DPC image acquisition
 #   def projection(self, sample_start_position, sample_out_position, 
 #                  projection_name='', number_phase_steps=MIN_PHASE_STEPS, 
 #                  number_dark_current=DARK_SCANS, 
 #                  number_dark_current=REFERENCE_SCANS, 
 #                  exposure_time=0):
 #       """ Acquire DPC projection.
 #       
 #           NOTE: Here, sample is smaller than detector hight!
 #       
 #           If necessary, the exposure time can be set. Otherwise current
 #           setting will be used.
 #           
 #           Input parameters:
 #               
 #               sample_start_position: Start position of SH_TRY motor
 #               sample_out_position: Position to acquire reference scans,
 #                                    sample is out of view
 #               projection_name: image name (default='') -> use current
 #               number_phase_steps (default=MIN_PHASE_STEPS)
 #               number_dark_current (default: 5): Number of acquired dark 
 #                                                 current scans
 #               number_reference_scans (default: 5): Number of acquired
 #                                                    reference scans
 #               exposure_time (default=0): if zero or not entered
 #                                          -> use current setting
 #                                          
 #           Return values:
 #               
 #               none
 #       
 #       """
 #       # Is camera ready?
 #       if not sb.is_camera_on():
 #           raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
 #       
 #       # Tube connected (serial communication open)?
 #       if not tube.is_connected():
 #           raise ErrorScanInterrupt('\n[ERROR]: Tube not started.')
 #       
 #       # Is x-ray on?
 #       if not tube.is_on():
 #           raise ErrorScanInterrupt('\n[ERROR]: X-ray turned off. Please'
 #                                     'turn on x-ray and start again.')
 #       
 #       # Set prefix
 #       if not projection_name:
 #           sb.set_prefix(projection_name)
 #       
 #       # Set exposure time if necessary
 #       if exposure_time:
 #           sb.set_exposure_time(exposure_time)
 #           
 #       # Init
 #       #number_acquisition_points = number_phase_steps + 1
 #       #number_digits = int(math.log(number_acquisition_points,10)) + 1
 #       # Get the number of digits necessary to save all images to be acquired
	#number_digits = int(math.log(number_phase_steps,10)) + 1
	#number_digits = max(number_digits,4)
	#image_count = 0
	#
	## Move sample out to acquire reference scans and dark current scans
	#sh_try.mv(sample_out_position)
	#
	## Get dark current
	#print("\n[INFO]: Acquiring {0} dark current scans.".
	#       format(number_dark_current))
	#tube.off()
	#time.sleep(0.1)
	#
	#for i in range(0, number_dark_current):
	#    sb.acquire(image_count, number_digits)
 #           image_count = image_count + 1
 #           print("\nDark current scan number {0} done.".format(image_count))
 #       tube.on()
 #       time.sleep(4)
	#
 #       # Get reference scans
 #       print("\n[INFO]: Acquiring {0} reference scans.".
	#       format(number_flat_scans))
	#
	#for i in range(0, number_flat_scans):
 #           sb.acquire(image_count, number_digits)
 #           image_count = image_count + 1
 #           print("\nReference scan number {0} done.".
 #                  format(image_count-number_dark_current))
 #           # No sample movement necessary, as flat scans gan be used to create
 #           # phase stepping series bu copying and rearranging the lines!
 #       
 #       # Get object scans
 #       print("\n[INFO]: Acquiring {0} object phase steps.".
	#       format(number_phase_steps))
 #       
 #       # Move sampte to start position
 #       sh_try.mv(sample_start_position)
 #       
 #       for i in range(0, number_phase_steps): # or number_acquisition_points
 #           sb.acquire(image_count, number_digits)
 #           image_count = image_count + 1
 #           print("\nPhase step number {0} done.".
 #                  format(image_count-number_dark_current-number_flat_scans))
 #           # Move sample one step width
 #           #mv(SHTRY, sample_start_position + image_count*self.step_size)
 #           sh_try.mvr(self.step_size)
 #           
    
    # DPC tomography acquisition
    def tomography(self, projection_name, sample_start_position,
                    sample_step_width, number_projections,
                    gantry_start_position=GB_ROTY_START_POSITION,
                    gantry_end_position=GB_ROTY_END_POSITION,
                    number_dark_current=DARK_SCANS,
                    number_phase_steps=MIN_PHASE_STEPS, exposure_time=0):
        """ 
        
        """
        # Is camera ready?
        if not sb.is_camera_on():
            raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
        
        # Tube connected (serial communication open)?
        if not tube.is_connected():
            raise ErrorScanInterrupt('\n[ERROR]: Tube not started.')
        
        # Is x-ray on?
        if not tube.is_on():
            raise ErrorScanInterrupt('\n[ERROR]: X-ray turned off. Please'
                                      'turn on x-ray and start again.')
        
    
        # Set prefix
        sb.set_prefix(projection_name)
        
        # Set exposure time if necessary
        if exposure_time:
            sb.set_exposure_time(exposure_time)
        
        
        # Init CT Scan
        #number_acquisition_points = number_phase_steps + 1
        #number_digits = int(math.log(number_acquisition_points,10)) + 1
        # Get the number of digits necessary to save all images to be acquired
        number_acquisitions = number_phase_steps*number_projections
	number_digits = int(math.log(number_acquisitions, 10)) + 1
	number_digits = max(number_digits,4)
	
	# Get gantry rotations steps for single projections
	gantry_rotation_step = (gantry_end_position - gantry_start_position) \
	                       / (number_projections - 1)
	
	image_count = 0  
	
	# Acquire dark current scans
        print("\n[INFO]: Acquiring {0} dark current scans.".
	       format(number_dark_current))
	if tube.is_on():
	   tube.off()
	   time.sleep(2)
	
	for i in range(0, number_dark_current):
	    sb.acquire(image_count, number_digits)
            image_count = image_count + 1
	
        # Get sample scans
        print("\n[INFO]: Acquiring {0} sample scans.".
	       format(number_projections))
	  
	tube.on()
        time.sleep(5)
                 
        
        # Acquire tomography scan                                          
        try:
            # Move gantry to start position
            gb_roty.mv(gantry_start_position)
            
            # Iterate through number of projections
            # range(0, N) -> 0, 1, ..., (N-1)
            for ii in range(0, number_projections):
                # For each projection scan through sample to get
                # phase stepping curve
                
                print('\n[INFO]: Scanning projection number {0}'.format(ii))
                
                # Move sample to start position
                sh_try.mv(sample_start_position)
                
                # Iterate through phase steps
                for jj in range(0, number_phase_steps):
                    sb.acquire(image_count, number_digits)
                    image_count = image_count + 1
                    # Move sample one step width
                    sh_try.mvr(sample_step_width)
                    
                # After full scan move gantry to next projection position
                gb_roty.mvr(gantry_rotation_step)
                
        except KeyboardInterrupt:
            # Should images acquired so far be deleted?
            answer = raw_input('\n[INFO]: Scan interrupted.'
                               ' Delete acquired files? [Y/n]: ')
            if answer == 'Y':
                # call function (which send command) to delete files
                # via WinServer
                print('\n[WARNING]: Files NOT deleted, function not '
                        'implemented yet...')
            elif answer == 'n':
                raise ErrorScanInterrupt('\n[ERROR]: Scan interrupted.'
                                          '\n[INFO]: Files not deleted, '
                                          'scan aborted.')
            else:
                raise ErrorScanInterrupt('\n[ERROR]: Scan interrupted.'
                                          '\n[WARNING]: Invalid input. Files '
                                          'not deleted, scan aborted.')
        #tube.off()
        
    def temperature_series(self, scanname,sleep_time, repeats, 
                            number_dark_current=DARK_SCANS, exposure_time=1000):
        # Is camera ready?
        if not sb.is_camera_on():
            raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
        
        # Tube connected (serial communication open)?
        if not tube.is_connected():
            raise ErrorScanInterrupt('\n[ERROR]: Tube not started.')
        
        # Set exposure time if necessary
        if exposure_time:
            sb.set_exposure_time(exposure_time)
        
	image_count = 0
	number_digits = 5
	
        # Dark scans
        # Acquire dark current scans
        print("\n[INFO]: Acquiring {0} dark current scans.".
	       format(number_dark_current))
	if tube.is_on():
	   tube.off()
	   time.sleep(4)
	   
	# Set prefix   
	sb.set_prefix(scanname)
	
	for i in range(0, number_dark_current):
	    sb.acquire(image_count, number_digits)
            image_count = image_count + 1
        
        
        # Flat fields
        
        tube.on()
        time.sleep(4)
        
        while True:
            for ii in range(0,repeats):
                sb.acquire(image_count, 5)
                image_count = image_count + 1
            time.sleep(sleep_time)
            
    def temperature_series_delay(self, scanname,sleep_time, repeats, 
                            warmup_time, cooling_time=0,
                            number_dark_current=DARK_SCANS, exposure_time=10000):
        ## Is camera ready?
        #if not sb.is_camera_on():
        #    raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
        
        ## Tube connected (serial communication open)?
        #if not tube.is_connected():
        #    raise ErrorScanInterrupt('\n[ERROR]: Tube not started.')
        
        # Set exposure time if necessary
        if exposure_time:
            sb.set_exposure_time(exposure_time)
        
	image_count = 0
	number_digits = 5
	
	# Wait for warm up time, then do warm up
	current_time = time.localtime()
	while not (current_time.tm_hour == warmup_time):
	    current_time = time.localtime()
	    print tube.status()
	    time.sleep(300)
	##Start warmup
 #       tube.start()
        ## Wait
        #time.sleep(cooling_time*60*60)
        
        # Set prefix
        sb.set_prefix(scanname)
	
        # Dark scans
        # Acquire dark current scans
        print("\n[INFO]: Acquiring {0} dark current scans.".
	       format(number_dark_current))
	if tube.is_on():
	   tube.off()
	   time.sleep(5)
	
	for i in range(0, number_dark_current):
	    sb.acquire(image_count, number_digits)
            image_count = image_count + 1
        
        # Flat fields
        
        tube.on()
        time.sleep(4)
        
        while True:
            for ii in range(0,repeats):
                sb.acquire(image_count, 5)
                image_count = image_count + 1
            time.sleep(sleep_time)
            

 #   # DPC tomography acquisition
 #   def tomography(self, projection_name, sample_start_position,
 #                   number_projections,
 #                   gantry_start_position=GB_ROTY_START_POSITION,
 #                   gantry_end_position=GB_ROTY_END_POSITION,
 #                   number_phase_steps=MIN_PHASE_STEPS, exposure_time=0):
 #       """ 
 #       
 #       """
 #       # Is camera ready?
 #       if not sb.is_camera_on():
 #           raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
 #       
 #       # Tube connected (serial communication open)?
 #       if not tube.is_connected():
 #           raise ErrorScanInterrupt('\n[ERROR]: Tube not started.')
 #       
 #       # Is x-ray on?
 #       if not tube.is_on():
 #           raise ErrorScanInterrupt('\n[ERROR]: X-ray turned off. Please'
 #                                     'turn on x-ray and start again.')
 #       
 #   
 #       # Set prefix
 #       sb.set_prefix(projection_name)
 #       
 #       # Set exposure time if necessary
 #       if exposure_time:
 #           sb.set_exposure_time(exposure_time)
 #                   
 #       # Init
 #       #number_acquisition_points = number_phase_steps + 1
 #       #number_digits = int(math.log(number_acquisition_points,10)) + 1
 #       # Get the number of digits necessary to save all images to be acquired
 #       number_acquisitions = number_phase_steps*number_projections
	#number_digits = int(math.log(number_acquisitions, 10)) + 1
	#number_digits = max(number_digits,4)
	#
	## Get gantry rotations steps for single projections
	#gantry_rotation_step = (gantry_end_position - gantry_start_position) \
	#                       / (number_projections - 1)
	#
	#image_count = 0           
 #       
 #       # Acquire tomography scan                                          
 #       try:
 #           # Move gantry to start position
 #           #mv(GBROTY, gantry_start_position)
 #           
 #           # Iterate through number of projections
 #           # range(0, N) -> 0, 1, ..., (N-1)
 #           for ii in range(0, number_projections):
 #               # For each projection scan through sample to get
 #               # phase stepping curve
 #               
 #               # Move sample to start position
 #               #mv(SHTRY, sample_start_position)
 #               
 #               # Iterate through phase steps
 #               for jj in range(0, number_phase_steps):
 #                   sb.acquire(image_count, number_digits)
 #                   image_count = image_count + 1
 #                   # Move sample one step width
 #                   #mv(SHTRY, sample_start_position + (jj+1)*self.step_size)
 #                   
 #               # After full scan move gantry to next projection position
 #               #mv(GBROTY, gantry_start_position + (ii+1)*gantry_rotation_step)
 #               
 #       except KeyboardInterrupt:
 #           # Should images acquired so far be deleted?
 #           answer = raw_input('\n[INFO]: Scan interrupted.'
 #                              ' Delete acquired files? [Y/n]: ')
 #           if answer == 'Y':
 #               # call function (which send command) to delete files
 #               # via WinServer
 #               pass
 #           elif answer == 'n':
 #               raise ErrorScanInterrupt('\n[ERROR]: Scan interrupted.'
 #                                         '\n[INFO]: Files not deleted, '
 #                                         'scan aborted.')
 #           else:
 #               raise ErrorScanInterrupt('\n[ERROR]: Scan interrupted.'
 #                                         '\n[WARNING]: Invalid input. Files '
 #                                         'not deleted, scan aborted.')











#    #################
#    # cDPC functions (Thomas)
#    #################
#    
#    def darkscan(self,scanname,ndarks,exptime):
#   	#camera settings
#        if not sb.is_camera_on():
#            raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
#            
#        # X-ray on?
#        #TODO
#
#       	sb.set_prefix(scanname)
#       	sb.set_exposure_time(exptime)
#       
#       	# init scan
#       	digits = int(math.log(ndarks,10)) + 1
#       	digits = max(digits,4)
#       	#setMotOutput(0) #no motor output messages
#       	retry = 5 #number of retries for exposure
#       
#       	#start scan
#       	for i in range(0,ndarks-1):
#      	     sb.acquire(i,digits)
#      	
#       	#setMotOutput(1)
#
#    
#    def visscan(self,scanname,start,end,nsteps,exptime):
#        #camera settings
#        if not sb.is_camera_on():
#            raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
#            
#        # X-ray on?
#        #TODO
#       	sb.set_prefix(scanname)
#       	sb.set_exposure_time(exptime)
#   
#   	# init scan
#   	npoints = nsteps+1
#       	dstep = (end-start)/nsteps
#       	digits = int(math.log(npoints,10)) + 1
#       	digits = max(digits,4)
#       	#setMotOutput(0) #no motor output messages
#       	retry = 5 #number of retries for exposure
#       	# Move sample to start position
#       	#mv(G2_PZ,start)
#      		
#      		
#       	#dark images
#       	ndarks = 5
#       	#PIEnableShuttering(0)
#       	tube.stop()
#       	
#       	
#       	print "Dark image acquisition..."
#       	for i in range(0,ndarks):
#       	    print str(i) + ": dark image"
#       	    PIExposure(i,digits,retry)
#       	#PIEnableShuttering(1)
#       	
#       	#start scan
#       	print "\nImage acquisition..."
#       	for i in range(0,npoints):
#            xpos = start+i*dstep
#            mv(G2_PZ,xpos)
#            print str(i) + ": xpos = " + str(xpos)
#            sb.acquire(i+ndarks,digits,retry)
#      		
#      		
#       	#setMotOutput(1)
#  	    	
#    #TODO   !!! 	
#   	    
#    def dpc_radiography(self,scanname,start,end,nsteps,exptime,samin,samout):
#   	
#   	#further params
#   	ndarks = 5
#   	nflats = 1
#   	repeats = 1
#   	retry = 5 #number of retries for exposure
#   	
#   	#camera settings
#   	if not PIIsCamON():
#  		print "Error: Camera is off"
#  		return
#  		
#   	PISetPrefix(scanname)
#   	PISetExp(exptime)
#   	
#   	# init scan
#   	npoints = nsteps+1
#   	dstep = (end-start)/nsteps
#   	digits = int(math.log(npoints,10)) + 1
#   	digits = max(digits,4)
#   	setMotOutput(0) #no motor output messages
#   	cnt = 0 #image count
#   	
#   	
#   	#dark images (old)
#   	#tmp = raw_input("Dark image acquisition. Turn off tube and press Enter to start...")
#   	#for i in range(0,ndarks):
#   	#	print str(i) + ": dark image"
#   	#	for ii in range(0,repeats):
#   	#		PIExposure(cnt,digits,retry)
#   	#		cnt = cnt+1
#  		
#   	#dark images
#   	PIEnableShuttering(0)
#   	print "Dark image acquisition..."
#   	for i in range(0,ndarks):
#  		print str(i) + ": dark image"
#  		for ii in range(0,repeats):
# 			PIExposure(cnt,digits,retry)
# 			cnt = cnt+1
#   	PIEnableShuttering(1)
#   	
#   	#flat images
#   	#tmp = raw_input("\nFlat image acquisition. Turn on tube and press Enter to start...")
#   	print "\nFlat image acquisition..."
#   	print "move sample out."
#   	mv(SAM_TRX,samout)
#   	
#   	print "start scan."
#   	for i in range(0,nflats):
#  		print "flat Nr. " + str(i+1)
#  		mv(G2_PZ,start)
#  		for ii in range(0,npoints):
# 			xpos = start+ii*dstep
# 			mv(G2_PZ,xpos)
# 			print str(ii) + ": xpos = " + str(xpos)
# 			#PIExposure(ndarks+i*npoints+ii,digits,retry)
# 			for iii in range(0,repeats):
#    				PIExposure(cnt,digits,retry)
#    				cnt = cnt+1
#   	
#   	
#   	#object images
#   	print "\nObject image acquisition."
#   	print("move sample in.")
#   	mv(SAM_TRX,samin)
#   	
#   	print "start scan."
#   	mv(G2_PZ,start)
#   	for i in range(0,npoints):
#  		xpos = start+i*dstep
#  		mv(G2_PZ,xpos)
#  		print str(i) + ": xpos = " + str(xpos)
#  		#PIExposure(ndarks+nflats*npoints+i,digits,retry)
#  		for ii in range(0,repeats):
# 			PIExposure(cnt,digits,retry)
# 			cnt = cnt+1
#  		
#   	setMotOutput(1)
#   	
#    
#    
#    
#    def dpc_radiography_rep(self,scanname,start,end,nsteps,exptime,samin,samout,nrep):
#   	
#   	#further params
#   	ndarks = 5
#   	nflats = 1
#   	repeats = 1
#   	retry = 5 #number of retries for exposure
#   	
#   	#camera settings
#   	if not PIIsCamON():
#  		print "Error: Camera is off"
#  		return
#  		
#   	PISetPrefix(scanname)
#   	PISetExp(exptime)
#   	
#   	# init scan
#   	npoints = nsteps+1
#   	dstep = (end-start)/nsteps
#   	digits = int(math.log(npoints,10)) + 1
#   	digits = max(digits,4)
#   	setMotOutput(0) #no motor output messages
#   	cnt = 0 #image count
#  		
#   	#dark images
#   	PIEnableShuttering(0)
#   	print "Dark image acquisition..."
#   	for i in range(0,ndarks):
#  		print str(i) + ": dark image"
#  		for ii in range(0,repeats):
# 			PIExposure(cnt,digits,retry)
# 			cnt = cnt+1
#   	PIEnableShuttering(1)
#   	
#   	#flat images
#   	print "\nFlat image acquisition..."
#   	print "move sample out."
#   	mv(SAM_TRX,samout)
#   	
#   	print "start scan."
#   	for i in range(0,nflats):
#  		print "flat Nr. " + str(i+1)
#  		mv(G2_PZ,start)
#  		for ii in range(0,npoints):
# 			xpos = start+ii*dstep
# 			mv(G2_PZ,xpos)
# 			print str(ii) + ": xpos = " + str(xpos)
# 			#PIExposure(ndarks+i*npoints+ii,digits)
# 			for iii in range(0,repeats):
#    				PIExposure(cnt,digits,retry)
#    				cnt = cnt+1
#   	
#   	#object images
#   	print "\nObject image acquisition."
#   	print("move sample in.")
#   	mv(SAM_TRX,samin)
#   	
#   	print "start scan."
#   	mv(G2_PZ,start)
#   	for j in range(0,nrep):
#  		print "Repetition scan No. " + str(j+1)
#  		for i in range(0,npoints):
# 			xpos = start+i*dstep
# 			mv(G2_PZ,xpos)
# 			print str(i) + ": xpos = " + str(xpos)
# 			#PIExposure(ndarks+nflats*npoints+i,digits,retry)
# 			for ii in range(0,repeats):
#    				PIExposure(cnt,digits,retry)
#    				cnt = cnt+1
#  		
#   	setMotOutput(1)
#   	
#   	
#    #####################
#    ### Tomographic scan
#    #####################
#    
#    #DPC tomoscan
#    def dpc_tomoscan(self):
#   	
#   	#load parameters
#   	reload(cDPC_tomoparams)
#   	scanname	= cDPC_tomoparams.scanname
#   	start		= cDPC_tomoparams.start
#   	end			= cDPC_tomoparams.end
#   	nsteps		= cDPC_tomoparams.nsteps
#   	exptime		= cDPC_tomoparams.exptime
#   	samin		= cDPC_tomoparams.samin
#   	samout		= cDPC_tomoparams.samout
#   	nproj		= cDPC_tomoparams.nproj
#   	scan360deg	= cDPC_tomoparams.scan360deg
#   	ndarks		= cDPC_tomoparams.ndarks
#   	nflats		= cDPC_tomoparams.nflats
#   	multiflats	= cDPC_tomoparams.multiflats
#   	postflat	= cDPC_tomoparams.postflat
#   	binning		= cDPC_tomoparams.binning
#   	repeats		= cDPC_tomoparams.repeats
#   	restart		= cDPC_tomoparams.restart
#   	restartfrom	= cDPC_tomoparams.restartfrom
#   	restartto	= cDPC_tomoparams.restartto
#   	retry 		= 10 #number of retries for exposure
#   	
#   	#camera settings
#   	if not PIIsCamON():
#  		print "Error: Camera is off"
#  		return
#  		
#   	PISetPrefix(scanname)
#   	PISetExp(exptime)
#   	PISetBin(binning)
#   	
#   	
#   	
#   	# init scan
#   	dstep = (end-start)/nsteps #step size of analyzer grating
#   	digits = int(math.log(repeats*(ndarks+nflats*multiflats*nsteps+nproj*nsteps),10)) + 1
#   	digits = max(digits,4)
#   	setMotOutput(0) #no motor output messages
#   	
#   	if scan360deg:
#  		proj = frange(0.0,360.0,360.0/nproj) #projection vector
#  		flatVec = frange(0.0,360.0,360.0/nflats) #vector for flat image acquisition
#   	else:
#  		proj = frange(0.0,180.0,180.0/nproj)
#  		flatVec = frange(0.0,180.0,180.0/nflats)
#    
#   	if restart:
#  		startproj = restartfrom
#  		endproj = restartto
#  		flatCnt = int(math.floor(float(restartfrom)/(nproj/nflats)))
#  		print "\nRestarting scan at projection " + str(proj[startproj]) + " degrees.\n"
#   	else:
#  		startproj = 0
#  		endproj = nproj
#  		flatCnt = 0
#  		
#   	if postflat:
#  		postflat = 1
#   	else:
#  		postflat = 0
#  		
#   	if repeats==0:
#  		repeats = 1
#    
#    
#   	
#   	#dark images
#   	if not restart:
#  		PIEnableShuttering(0)
#  		print "Dark image acquisition..."
#  		for i in range(0,ndarks):
# 			print str(i) + ": dark image"
# 			for irep in range(0,repeats):
#    				filenum = i*repeats+irep
#    				if not PIExposure(filenum,digits,retry):
#   					print "Exit scan!"
#   					return
#   					
#   	
#  		PIEnableShuttering(1)
#   	
#   	
#   	#flat/object images
#   	print "\nFlat/object image acquisition..."
#   	flattime = 0
#   	projtime = 0
#   	starttime = time.time()
#   	mv(G2_PZ,start)
#   	
#   	for iproj in range(startproj,endproj):
#  		
#  		cProj = proj[iproj] #current projection angle
#  		
#  		#time calculation
#  		if projtime and flattime:
# 			runtime = time.time() - starttime
# 			timeleft = (nflats+postflat-flatCnt)*flattime + (nproj-iproj)*projtime
# 			print "Runtime: " + str(int(runtime/3600.0)) + " h, " + str(int((runtime/60.0)%60)) + " min"
# 			print "Time left: " + str(int(timeleft/3600.0)) + " h, " + str(int((timeleft/60.0)%60)) + " min"
#  		
#    				
#  		#check if flat needs to be acquired
#  		#(+0.000000001 is because of rounding problem in python)
#  		if flatCnt < nflats:
# 			if cProj+0.000000001>=flatVec[flatCnt]:
#    				print "\nFlat image acquisition No. " + str(flatCnt+1)
#    				timestamp = time.time()
#    				print("move sample out.")
#    				mv(SAM_TRX,samout)
#    				
#    				for iflat in range(0,multiflats):
#   					print "\nFlat image " + str(flatCnt+1) + "." + str(iflat+1)
#   					mv(G2_PZ,start)
#   					for ii in range(0,nsteps):
#  						xpos = start+ii*dstep
#  						mv(G2_PZ,xpos)
#  						print str(ii) + ": xpos = " + str(xpos)
#  						filenum = ndarks + flatCnt*multiflats*nsteps + iflat*nsteps + ii;
#  						filenum = repeats*filenum
#  						for irep in range(0,repeats):
# 							filenum_rep = filenum + irep
# 							if not PIExposure(filenum_rep,digits,retry):
#    								print "Exit scan!"
#    								return
# 							
#    				print("move sample in.")
#    				mv(SAM_TRX,samin)
#    				flatCnt = flatCnt+1
#    				flattime = time.time() - timestamp
# 			
#  		#object acquisition
#  		print "\nProjection No. " + str(iproj+1) + ", angle = " + str(cProj) + " [deg]"
#  		timestamp = time.time()
#  		mv(SAM_ROTY,cProj)
#  		mv(SAM_TRX,samin)
#  		mv(G2_PZ,start)
#  		for ii in range(0,nsteps):
# 			xpos = start+ii*dstep
# 			mv(G2_PZ,xpos)
# 			print str(ii) + ": xpos = " + str(xpos)
# 			filenum = ndarks + (nflats+postflat)*multiflats*nsteps + iproj*nsteps + ii
# 			filenum = repeats*filenum
# 			for irep in range(0,repeats):
#    				filenum_rep = filenum + irep
#    				if not PIExposure(filenum_rep,digits,retry):
#   					print "Exit scan!"
#   					return
#   					
#  		projtime = time.time() - timestamp
#    
#    
#   	if postflat:
#  		print "\nFlat image acquisition No. " + str(flatCnt+1)
#  		print("move sample out.")
#  		mv(SAM_TRX,samout)
#  		
#  		for iflat in range(0,multiflats):
# 			print "\nFlat image " + str(flatCnt+1) + "." + str(iflat+1)
# 			mv(G2_PZ,start)
# 			for ii in range(0,nsteps):
#    				xpos = start+ii*dstep
#    				mv(G2_PZ,xpos)
#    				print str(ii) + ": xpos = " + str(xpos)
#    				filenum = ndarks + nflats*multiflats*nsteps + iflat*nsteps + ii
#    				filenum = repeats*filenum
#    				for irep in range(0,repeats):
#   					filenum_rep = filenum + irep
#   					if not PIExposure(filenum_rep,digits,retry):
#  						print "Exit scan!"
#  						return
# 			
# 			
#   	setMotOutput(1)
#   	print("Tomographic scan has finished.")
#  		
#   	
#  		
#    
#    
#    #absorption tomoscan
#    def abs_tomoscan(self):
#   	
#   	#load parameters
#   	reload(cDPC_tomoparams)
#   	scanname	= cDPC_tomoparams.scanname
#   	exptime		= cDPC_tomoparams.exptime
#   	samin		= cDPC_tomoparams.samin
#   	samout		= cDPC_tomoparams.samout
#   	nproj		= cDPC_tomoparams.nproj
#   	scan360deg	= cDPC_tomoparams.scan360deg
#   	ndarks		= cDPC_tomoparams.ndarks
#   	nflats		= cDPC_tomoparams.nflats
#   	postflat	= cDPC_tomoparams.postflat
#   	binning		= cDPC_tomoparams.binning
#   	restart		= cDPC_tomoparams.restart
#   	restartfrom	= cDPC_tomoparams.restartfrom
#   	restartto	= cDPC_tomoparams.restartto
#   	retry 		= 10 #number of retries for exposure
#   	
#   	#camera settings
#   	if not PIIsCamON():
#  		print "Error: Camera is off"
#  		return
#  		
#   	PISetPrefix(scanname)
#   	PISetExp(exptime)
#   	PISetBin(binning)
#   	
#   	
#   	# init scan
#   	digits = int(math.log(ndarks+nflats+nproj,10)) + 1
#   	digits = max(digits,4)
#   	setMotOutput(0) #no motor output messages
#   	
#   	if scan360deg:
#  		proj = frange(0.0,360.0,360.0/nproj) #projection vector
#  		flatVec = frange(0.0,360.0,360.0/nflats) #vector for flat image acquisition
#   	else:
#  		proj = frange(0.0,180.0,180.0/nproj)
#  		flatVec = frange(0.0,180.0,180.0/nflats)
#    
#   	if restart:
#  		startproj = restartfrom
#  		endproj = restartto
#  		print "Restarting scan at projection " + str(proj[startproj]) + " degrees."
#   	else:
#  		startproj = 0
#  		endproj = nproj
#  		flatCnt = 0
#  		
#   	if postflat:
#  		postflat = 1
#   	else:
#  		postflat = 0
#  		
#   	#dark images
#   	if not restart:
#  		PIEnableShuttering(0)
#  		print "Dark image acquisition..."
#  		for i in range(0,ndarks):
# 			print str(i) + ": dark image"
# 			PIExposure(i,digits,retry)
#   	
#  		PIEnableShuttering(1)
#   	
#   	
#   	#pre-flat acquisition
#   	if not restart:
#  		print "\nPre-flat image acquisition..."
#  		print("move sample out.")
#  		mv(SAM_TRX,samout)
#  		for iflat in range(0,nflats):
# 			print str(iflat) + ": flat image"
# 			PIExposure(ndarks + iflat,digits,retry)		
#  		print("move sample in.")
#  		mv(SAM_TRX,samin)
#  		
#  		
#   	#object images
#   	print "\nObject image acquisition..."
#   	projtime = 0
#   	starttime = time.time()
#   	
#   	for iproj in range(startproj,endproj):
#  		
#  		cProj = proj[iproj] #current projection angle
#  		
#  		#time calculation
#  		if projtime:
# 			runtime = time.time() - starttime
# 			timeleft = (nproj-1-iproj)*projtime
# 			print "Runtime: " + str(int(runtime/3600.0)) + " h, " + str(int((runtime/60.0)%60)) + " min"
# 			print "Time left: " + str(int(timeleft/3600.0)) + " h, " + str(int((timeleft/60.0)%60)) + " min"
#  		
# 			
#  		#object acquisition
#  		print "\nProjection No. " + str(iproj+1) + ", angle = " + str(cProj) + " [deg]"
#  		timestamp = time.time()
#  		mv(SAM_ROTY,cProj)
#  		PIExposure(ndarks + nflats + postflat*nflats + iproj,digits,retry)
#  		projtime = time.time() - timestamp
#    
#   	
#   	if postflat:
#  		print "\nPost-flat image acquisition..."
#  		print("move sample out.")
#  		mv(SAM_TRX,samout)
#  		for iflat in range(0,nflats):
# 			print str(iflat) + ": flat image"
# 			PIExposure(ndarks + nflats + iflat,digits,retry)		
#    
#  		
#   	setMotOutput(1)
#   	print("Tomographic scan has finished.")
#   	
#   	
#    
#    
#    #absorption tomoscan (old)
#    def abs_tomoscan_old(self):
#   	
#   	#load parameters
#   	reload(cDPC_tomoparams)
#   	scanname	= cDPC_tomoparams.scanname
#   	exptime		= cDPC_tomoparams.exptime
#   	samin		= cDPC_tomoparams.samin
#   	samout		= cDPC_tomoparams.samout
#   	nproj		= cDPC_tomoparams.nproj
#   	scan360deg	= cDPC_tomoparams.scan360deg
#   	ndarks		= cDPC_tomoparams.ndarks
#   	nflats		= cDPC_tomoparams.nflats
#   	postflat	= cDPC_tomoparams.postflat
#   	binning		= cDPC_tomoparams.binning
#   	restart		= cDPC_tomoparams.restart
#   	restartfrom	= cDPC_tomoparams.restartfrom
#   	restartto	= cDPC_tomoparams.restartto
#   	retry 		= 10 #number of retries for exposure
#   	
#   	#camera settings
#   	if not PIIsCamON():
#  		print "Error: Camera is off"
#  		return
#  		
#   	PISetPrefix(scanname)
#   	PISetExp(exptime)
#   	PISetBin(binning)
#   	
#   	
#   	# init scan
#   	digits = int(math.log(ndarks+nflats+nproj,10)) + 1
#   	digits = max(digits,4)
#   	setMotOutput(0) #no motor output messages
#   	
#   	if scan360deg:
#  		proj = frange(0.0,360.0,360.0/nproj) #projection vector
#  		flatVec = frange(0.0,360.0,360.0/nflats) #vector for flat image acquisition
#   	else:
#  		proj = frange(0.0,180.0,180.0/nproj)
#  		flatVec = frange(0.0,180.0,180.0/nflats)
#    
#   	# find start and end indeces of projections
#   	if restart:
#  		startproj = restartfrom
#  		endproj = restartto
#  		flatCnt = int(math.ceil(float(restartfrom)/(nproj/nflats)))
#   	else:
#  		startproj = 0
#  		endproj = nproj
#  		flatCnt = 0
#    
#   	#dark images
#   	if not restart:
#  		PIEnableShuttering(0)
#  		print "Dark image acquisition..."
#  		for i in range(0,ndarks):
# 			print str(i) + ": dark image"
# 			PIExposure(i,digits,retry)
#   	
#  		PIEnableShuttering(1)
#   	
#   	
#   	#flat/object images
#   	print "\nFlat/object image acquisition..."
#   	flattime = 0
#   	projtime = 0
#   	starttime = time.time()
#   	
#   	for iproj in range(startproj,endproj):
#  		
#  		cProj = proj[iproj] #current projection angle
#  		
#  		#time calculation
#  		if projtime and flattime:
# 			runtime = time.time() - starttime
# 			timeleft = (nflats-1-flatCnt)*flattime + (nproj-1-iproj)*projtime
# 			print "Runtime: " + str(int(runtime/3600.0)) + " h, " + str(int((runtime/60.0)%60)) + " min"
# 			print "Time left: " + str(int(timeleft/3600.0)) + " h, " + str(int((timeleft/60.0)%60)) + " min"
#  		
#    				
#  		#check if flat needs to be acquired
#  		if flatCnt < nflats:
# 			if cProj>=flatVec[flatCnt]:
#    				print "\nFlat image acquisition No. " + str(flatCnt+1)
#    				timestamp = time.time()
#    				print("move sample out.")
#    				mv(SAM_TRX,samout)
#    				PIExposure(ndarks + flatCnt,digits,retry)		
#    				print("move sample in.")
#    				mv(SAM_TRX,samin)
#    				flatCnt = flatCnt+1
#    				flattime = time.time() - timestamp
# 			
#  		#object acquisition
#  		print "\nProjection No. " + str(iproj+1) + ", angle = " + str(cProj) + " [deg]"
#  		timestamp = time.time()
#  		mv(SAM_ROTY,cProj)
#  		mv(SAM_TRX,samin)
#  		PIExposure(ndarks + nflats + iproj,digits,retry)
#  		projtime = time.time() - timestamp
#    
#   	
#   	if postflat:
#  		print "\nFlat image acquisition No. " + str(flatCnt+1)
#  		print("move sample out.")
#  		mv(SAM_TRX,samout)
#  		PIExposure(ndarks + flatCnt,digits,retry)		
#  		
#   	setMotOutput(1)
#   	print("Tomographic scan has finished.")




######################### OLD ###########################################


#########################################################################
## DPCFunctions class
#########################################################################
#
#class DPCFunctions:
#    """ DPC functions class.
#        
#        Contains all necessary variables and fuctions to use gantry motors,
#        shadobox camera and tube to acuire images and do (3D) scans etc.
#        
#        Input valiable:
#            
#            none
#        
#        variables:
#            
#            
#            
#        functions:
#            
#            __init__(self)
#            
#            # Scans
#            darkfield_scan(exposure_time, n_dark_scans=5, prefix_dark_scans
#                                                          ='darkfield')
#            
#            # Utility functions
#            info_on(self)
#            info_off(self)
#            _print_info_message(self, msg)
#
#
#    """
#    
#    def __init__(self):
#        """ Initialization function of DPCFunctions
#            
#            Sets variable to default.        
#            
#        """ 
#        # Set (default) status of error, info and return messages
#        
#        # Should local and status ([INFO]) messages be printed?
#        self.print_info = False # Set always to False, if function is
#                                # called internally
#      
#   
#    ########################################################################
#    # Public functions
#    ######################################################################## 
#    
#    ########################################################################
#    # Darkfield and visibility scans
#    ########################################################################
#    
#    def dark_scan(exposure_time, n_dark_scans=NUMBER_DARK_SCANS, 
#                        dark_prefix='darkcurrent'):
#        """ Acquire and save dark current scans
#        
#            Input parameters:
#                
#                exposure_time: in ms       
#                n_dark_scans: Number of dark current scans, default is 
#                              NUMBER_DARK_SCANS   
#                dark_prefix: default is 'darkcurrent'
#            
#            Return values:
#                
#                none
#                raises exception, if error occurs
#        
#        """
#        try:
#
#            if not sb.is_camera_on():
#                raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
#                
#            # Is x-ray off?
#            #TODO
#                
#            if n_dark_scan<=0:
#                raise ErrorScanInterrupt('\n[ERROR]: Invalid number '
#                                          'of dark current scans.')
#                
#            self._print_info_message('\n[INFO]: Starting dark current scans...')
#            
#            # Set camera parameters
#            sb.set_prefix(dark_prefix)
#            
#            # Disable motors ?
#            #TODO
#            
#            #Add retries??? (to acquire...)
#            
#            # Start scan
#            for ii in range(0, n_dark_scans-1):
#                sb.acquire(ii, 0, exposure_time) # 0 phase steps
#
#                
#            # Enable motors ?
#            #TODO
#            
#            self._print_info_message(' done.')
#        
#        except (ErrorCameraInterrupt, ErrorScanInterrupt) as e:
#            # Reraise error, so that next level will be notified as well
#            # if error was raised inside lower level function
#            raise
#    
#    def flat_scan(exposure_time, n_flat_scans=NUMBER_FLAT_IMAGES, 
#                   n_phase_steps = MIN_PHASE_STEPS, flat_prefix='flatfield'):
#        """ Acquire and save flat images
#        
#            Input parameters:
#                
#                exposure_time: in ms       
#                n_flat_scans: Number of flat image scans, default is
#                              NUMBER_FLAT_IMAGES   
#                flat_prefix: default is 'flatfield'
#            
#            Return values:
#                
#                none
#                raises exception, if error occurs
#        
#        """
#        try:
#
#            if not sb.is_camera_on():
#                raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
#                
#            # Is x-ray on?
#            #TODO
#                
#            if n_flat_scan<=0:
#                raise ErrorScanInterrupt('\n[ERROR]: Invalid number '
#                                          'of flat image scans.')
#                                          
#            if n_phase_steps<MIN_PHASE_STEPS:
#                raise ErrorScanInterrupt('\n[ERROR]: Number of phase '
#                                          'steps too small.')
#
#                
#            self._print_info_message('\n[INFO]: Starting flat image scans...')
#            
#            # Set scan parameters
#            n_phase_step_points = n_phase_steps + 1 # add one additional
#                                                    # phase step
#            step_increment = (stop_position-start_position)/n_phase_steps
#                                                    # Step size of sample
#            #Add retries??? (to acquire...)
#            
#            # Set camera parameters
#            sb.set_prefix(flat_prefix)
#            
#            # Start scan
#            for ii in range(0, n_flat_scans-1):
#                # Move motor (sample) to start position
#                #TODO
#                #move(motor_name, position)
#            
#                # Start flat image scan
#                for kk in range(0, n_phase_step_points):
#                    sample_position = start_position + kk*step_increment
#                    #move(motor_name, sample_position)
#                    sb.acquire(ii, kk, exposure_time) # 0 phase steps
#            
#            self._print_info_message(' done.')
#        
#        except (ErrorCameraInterrupt, ErrorScanInterrupt) as e:
#            # Reraise error, so that next level will be notified as well
#            # if error was raised inside lower level function
#            raise
#        
#    def visibility_scan(exposure_time, start_position, stop_position,
#                        n_phase_steps=MIN_PHASE_STEPS, 
#                        visibility_prefix='visibility'):
#        """ Acquire and save a visibility scan
#        
#            Input parameters:
#                
#                exposure_time: in ms
#                start_position: of sample
#                stop_position: of sample
#                n_phase_steps: Number of phase steps, 
#                               default is MIN_PHASE_STEPS   
#                visibility_prefix: default is 'visibility'
#            
#            Return values:
#                
#                none
#                raises exception, if error occurs
#        
#        """
#        try:
#            if not sb.is_camera_on():
#                raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
#                
#            # X-ray on?
#            #TODO
#                
#            # Check motor range
#            #TODO
#                
#            if n_phase_steps<MIN_PHASE_STEPS:
#                raise ErrorScanInterrupt('\n[ERROR]: Number of phase '
#                                          'steps too small.')
#                
#            self._print_info_message('\n[INFO]: Starting visibility scan...')
#    
#            # Set scan parameters
#            n_phase_step_points = n_phase_steps + 1 # add one additional
#                                                    # phase step
#            step_increment = (stop_position-start_position)/n_phase_steps
#                                                    # Step size of sample
#            #Add retries??? (to acquire...)
#            
#            # Get dark current images (default 5)
#            # Turn off xray
#            tube.stop_xray()
#            # Acquire dark current scan
#            self.dark_scan(exposure_time)
#            # Turn on xray
#            tube.start_xray()
#            
#            # Move motor (sample) to start position
#            #TODO
#            #move(motor_name, position)
#            
#            # Set camera parameters
#            sb.set_prefix(visibility_prefix)
#            
#            # Start visibility scan
#            for ii in range(0, n_phase_step_points):
#                sample_position = start_position + ii*step_increment
#                #move(motor_name, sample_position)
#                sb.acquire()
#            
#            self._print_info_message(' done.')
#
#        except (ErrorTubeInterrupt, ErrorCameraInterrupt,
#                 ErrorScanInterrupt) as e:
#            # Reraise error, so that next level will be notified as well
#            # if error was raised inside lower level function
#            raise        
#    
#    ########################################################################
#    # Radiographs
#    ########################################################################
#    
#    def dpc_radiography(exposure_time, start_position, stop_position,
#                        n_phase_steps=MIN_PHASE_STEPS, 
#                        radiography_prefix='radiagraphy'):
#        """ Acquire and save a DPC radiography scan
#        
#            Input parameters:
#                
#                exposure_time: in ms
#                start_position: of sample
#                stop_position: of sample
#                n_phase_steps: Number of phase steps, 
#                               default is MIN_PHASE_STEPS   
#                radiography_prefix: default is 'radiagraphy'
#            
#            Return values:
#                
#                none
#                raises exception, if error occurs
#        
#        """
#        try:
#            if not sb.is_camera_on():
#                raise ErrorScanInterrupt('\n[ERROR]: Camera not started.')
#                
#            # X-ray on?
#            #TODO
#                
#            # Check motor range
#            #TODO
#                
#            if n_phase_steps<MIN_PHASE_STEPS:
#                raise ErrorScanInterrupt('\n[ERROR]: Number of phase '
#                                          'steps too small.')
#                
#            self._print_info_message('\n[INFO]: Starting radiography scan...')
#    
#            # Set scan parameters
#            n_phase_step_points = n_phase_steps + 1 # add one additional
#                                                    # phase step
#            step_increment = (stop_position-start_position)/n_phase_steps
#                                                    # Step size of sample
#            #Add retries??? (to acquire...)
#            
#            # Get dark current images (default 5)
#            # Turn off xray
#            tube.stop_xray()
#            # Acquire dark current scan
#            self.dark_scan(exposure_time)
#            # Turn on xray
#            tube.start_xray()
#            
#            # Get flat images (default 1)
#            self.flat_scan(exposure_time)
#            
#            # Move motor (sample) to start position
#            #TODO
#            #move(motor_name, position)
#            
#            # Set camera parameters
#            sb.set_prefix(radiography_prefix)
#            
#            # Start visibility scan
#            for ii in range(0, n_phase_step_points):
#                sample_position = start_position + ii*step_increment
#                #move(motor_name, sample_position)
#                sb.acquire()
#            
#            self._print_info_message(' done.')
#
#        except (ErrorTubeInterrupt, ErrorCameraInterrupt,
#                 ErrorScanInterrupt) as e:
#            # Reraise error, so that next level will be notified as well
#            # if error was raised inside lower level function
#            raise         
#        
#    ########################################################################
#    # Tomographs
#    ########################################################################
#    
#    
#    
#    
#    
#    ########################################################################
#    # Public utility functions
#    ########################################################################
#    
#    # Turn on display of info messages
#    def info_on(self):
#        self.print_info = True
#    
#    # Turn off display of info messages
#    def info_off(self):
#        self.print_info = False
#
#    
    ########################################################################
    # Private functions
    ########################################################################
    
    ########################################################################
    # Private utility functions
    ########################################################################
            
    def _degree_to_rad(self, degree):
        """ Convert degree to radians
            
            Input parameters:
                
                degree [mdeg]
                
            Return values:
                
                degree in rad [mrad]
    
        """
        return math.pi*degree/180
    
    def _rad_to_degree(self, radians):
        """ Convert degree to radians
            
            Input parameters:
                
                radians [mrad]
                
            Return values:
                
                radians in degree [mdeg]
    
        """
        return 180*radians/math.pi



########################################################################
# Main
########################################################################

dpc = DPCFunctions()
