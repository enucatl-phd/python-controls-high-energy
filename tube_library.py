#################################################################
#
# tube_library.py
#
# This file contains the TubeControl class.
# It implements all the important methods needed to control 
# the tube and creates the object: tube.
#
# Author: 
# Celine Stoecklin (celine.stoecklin@psi.ch)
# Maria Buechner (maria.buechner@psi.ch)
#
#
# History:
# 15.11.2013: started
# 14.01.2014: modified (mb)
#
#################################################################

# Imports
import string
import datetime
import sys
from time import sleep
import threading

import serial_communication
from gantry_control_exceptions import *

########################################################################
# Define classes
########################################################################

class TubeControl:
    """ Class for the control of the tube. 
        This class contains all the important functions to send the
        tube commands and check the tube status.
       
        Variables:

            serial_port: object from the class serial communication
            connected : set to true if serial port is open  
            xon: variable set to true if the xray beam is on
            warmup_dictionnary: list of the different warmup patterns 

    """
    # Init function
    def __init__(self):
        self.serial_port = serial_communication.SerialCommunication()
        self._connected = False
        self.xon = False
        self.warmup_dictionnary = {'SWS 1 5': 4, 'SWS 1 4': 7, 'SWS 1 3': 10,
        'SWS 1 2': 13, 'SWS 1 1': 14, 'SWS 1 0': 15, 'SWS 0 0': 1, 
        'SWS 3 5': 10, 'SWS 3 4': 30, 'SWS 3 3': 60, 'SWS 3 2': 80,
        'SWS 3 1': 110, 'SWS 3 0': 120, 'SWS 2 5': 10,'SWS 2 4': 17, 
        'SWS 2 2': 30, 'SWS 2 3': 24, 'SWS 2 1': 35, 'SWS 2 0': 40}
        
    ########################################################################
    #  Tube communication
    ########################################################################

    def open_port(self):
        """
        A function to open the serial port and start the serial communication 
        thread if the port is open. 

           Input parameters:

                none

           Return variables:

                none                

        """
        self.serial_port.open_serial()
        # Global connection status
        self._connected = self.serial_port.connected
        if self._connected:
            #Start the communication thread
            self.serial_port.start()

    def close_port(self):
        """
        A function that closes the serial port and ends the serial 
        communication thread.  

           Input parameters:

                none 

           Return variables:
      
                none
                
        """
        self.serial_port.close_serial()
        # Global connection status
        self._connected = self.serial_port.connected

    def write_message(self, msg):
        """
            A function that writes a message to the tube via the write_queue.

            Input parameters:

                msg is a string (without CR)

            Return variables:
      
                none

        """
        self.serial_port.put_into_write_queue(msg)

    def read_message(self):
        """
            A function that reads the received message via the read_queue

            Input parameters:

                none 

            Return variables:
      
               The received message is returned. It is a string without CR.
                          
        """
        return self.serial_port.get_from_read_queue()
        
    def is_connected(self):
        """ Return serial conncetion status
            
            Input parameters:

                none 

            Return variables:
      
               self._connected
            
        """
        return self._connected
        
    ###########################################################################
    #  Tube basic command functions
    ###########################################################################

    def start(self):
        """ A function to start the tube, so that it is ready to emit Xrays

            If the serial port is not open, it opens the port or check for 
            errors.
            When the port is open, it sends the first dummy command, 
            check the battery level, check the tube status and if no
            errors occurs (STS 5 = preheat, intelock, hardware errors or 
            STS 4 = overload protection function is activated), it does
            the warming up (if not already done).
            When the status is STS 2, the tube is started and the user control
            commands are ready to be used.
                
            Input parameters:

                none 

            Return variables:
      
                none  
        """
        if not self._connected:
            self.open_port()
            
        if self._connected:
            print "\n[INFO]: Tube is starting..."
            #Send a dummy command as a first command
            self.check_power_supply()

        #Check battery level
        self.battery_status()

        #Check status
        tube_status = self.status()
            
        if self._get_status() != "STS 2":
            #If serial port connected, check why X-rays cannot be emitted.
            if self._get_status() == "STS 5":
                print ("\n[WARNING STS 5]: X-rays cannot be emitted."
                        "\nIt can be caused by preheating, hardware error "
                        "or an open interlock. Checking for the reason...")
                    
                # Is it an interlock open?
                self.interlock_status()
                # Is it an hardware error?
                self.hardware_error_check()
		# Is it preheating?
		while self._get_preheat_status() == "SPH 1":
		    self._blink_text("[WARNING SPH 1]: Preheating "
                    "in progress. Please wait for one minute.")
		if self._get_preheat_status() == "SPH 0":
                    print ("\n[SPH 0]: Preheating is completed "
			   "or not started yet.")

            #Is the overload protection function activated?
            elif self._get_status() == "STS 4":
                status()

            # Need of Warming-up?
            elif self._get_status() == "STS 0":
                print "\n[WARNING STS 0]: Awaiting warmup."
                self.warmup_start()
                while self._get_status() == "STS 1":
                    #During the warming up, print a blinking text info
                    #Get the warmup pattern number and calculate the time
                    #remaining time with the warmup dictionnary
                    step = self._get_warmup_step()
                    self._blink_text("[STS 1]: Approximate remaining "
                                    "warmup time: {0} min. Please be "
                                    "patient..."
                                    .format(self.warmup_dictionnary[step]))
                if self._get_status() == "STS 2":
                    print "\nWarmup completed!"
                else:
                    # Other problems (Interlock open, hardware errors, ...)
                    self._check_error()
        print ("\n[STS 2]: The tube is ready to emit X-rays."
                "\nEnter your command functions.")

    def stop(self):
        """ A function to close the tube

            If the serial port is open, shut down the Xrays and close the 
            serial connection.
                
            Input parameters:
    
                none 
    
            Return variables:
      
                none  
                
        """
        if self._connected:
            # Shutting down Xrays
            if self.is_on():
                self.off()
            
            #Closing serial port
            print "\n[INFO]: Closing serial connection..."
            self.close_port()
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")
                                        
    ###########################################################################
    #  Tube custom command functions for experiments
    ###########################################################################

    # X-ray emission ON and OFF
    def on(self):
        """
            A function that creates a thread to start xray emmission. 

            The function that starts the xrays is put into a thread, so that
            the while loop necessary to keep the xray on is working in 
            background (for security reason the xrays shut down after 3s if no 
            command is sent).
            Other command can then be sent to the tube or Camera during Xray 
            emission.
            If the tube is connected and the xrays are not turned on yet, 
            the xrays are starting in a thread. Otherwise it raises an 
            ErrorSerialInterrupt or respectively an ErrorTubeInterrupt.  

            Input parameters:

                none 

            Return variables:

                none  

        """
        if self._connected and not self.xon:
            # thread object is created and called the target function 
            # that starts xray
            self.xraystart_thread = threading.Thread(target=
                                                     self.thread_xray_on)
            # Set thread as deamn thread, so that it is forcefully shutdown,
            # when main (or all other non-deamn threads) are exited
            self.xraystart_thread.daemon = True
            # The thread starts here
            self.xraystart_thread.start()
        elif not self._connected:
            #Raise an error if the connection is closed
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")
        else:
            #Raise an error if the tube is already emitting Xrays
            raise ErrorTubeInterrupt("[ERROR]: Tube already emitting x-rays.")

    def thread_xray_on(self):
        """
            A function to start the X-ray emission 

            A while loop is needed to keep the xray on. For security reason the 
            xrays shut down after 3s if no command is sent.
            This function will be the thread target function since we want that 
            the while loop works in background.
            This function checks for errors when sending the XON commmand and 
            during Xray emission. 

            Input parameters:

                none 

            Return variables:

                none  

        """
        try:
            if self._connected:
                #Send the command xrays on
                self.write_message("XON")
                #Received message
                xon = self.read_message()
                if xon == "XON":
                    print "\n[XON]: Emitting x-rays."
		    sys.stdout.write(">>> ") 
                    self.xon = True
                    while self._get_status() == "STS 3":
                        # Ask for the status so that Xrays do not shut down
                        # after 3s 
                        self._get_status()
                    else:
                        # If status is not "STS 3: Xrays are being emitted"  
                        # anymore, check for errors during Xray emission.
                        self._check_error()
                else:
                    #Check for errors at command sending
                    self._check_command_error(xon)
            else:
                #Raise an error if the connection is closed
                raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                            "open.")
        except (ErrorSerialInterrupt, ErrorTubeInterrupt):
            # If xrays are turned on and an error occurs, 
            # try to shut the tube down
            # If a communication error occurs at any point, xrays will shut
            # down after 3 seconds automatically
            if self.xon:
                self.off()
            raise # re-raise exception

    def off(self):
        """ A function to stop the X-ray emission and check for errors. 

            Input parameters:

                none 

            Return variables:

                none  

        """
        if self._connected:
            #Send command xray off
            self.write_message("XOF")
            #Received response
            xof  = self.read_message()
            if xof == "XOF":
                self.xon = False
		print "\n[XOF]: X-ray emission stopped."
            else:
                #Check for errors at command sending
                self._check_command_error(xof)
        else:
            #Raise an error if the tube is already emitting Xrays
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")
    
    #def xray(self, exposure_time=0):
    def expose(self, exposure_time=0):
        """
            A function that starts the xray for a chosen exposure time 
            in a thread, shuts the xray and thread down after exposure time
            finished.
    
            The function that starts the xrays during the exposure time 
            and shutd the xrayd down is put into a thread, so that
            the while loop necessary to keep the xray on is working 
            in background (for security reason the xrays shut down after 
            3s if no command is sent).
            Other commands can then be sent to the tube or Camera during Xray
            emission.
            If the tube is connected and the xrays are not turned on yet, the
            xrays are started in a thread. Otherwise it raises an 
            ErrorSerialInterrupt or respectively an ErrorTubeInterrupt.  
            
            Input parameters:

                exposure_time is the xray exposure time in milliseconds.
                It is set by default to 0 milliseconds

            Return variables:
      
                none  

        """
        if self._connected and not self.xon:
            #Create the thread with the target function below
            self.xon_thread = threading.Thread(target=self.thread_expose,
                                               args = (exposure_time,))
            # Set thread as deamn thread, so that it is forcefully shutdown,
            # when main (or all other non-deamn threads) are exited
            self.xon_thread.daemon = True
            #Start thread
            self.xon_thread.start()
        elif not self._connected:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")
        else:
            raise ErrorTubeInterrupt("[ERROR]: Tube already emitting x-rays.")

    def thread_expose(self, exposure_time):
        """ A function to emit xrays during a defined exposure time

            If a connection is open, the xrays start. 
            While the time counter (corresponding to the difference between the 
            current time and starting time) is below the exposure time and 
            the status indicates it is emitting Xrays, it asks for the 
            tube status.
            Otherwise it will shut down within 3s for safety reason, if 
            no commands are sent.
            If the status changes during xrays exposure, errors are checked.
            When the exposure time is reached and no error occurs, the xrays 
            stop.
    
            Input parameters:

                exposure_time is the xray exposure time in milliseconds.

            Return variables:
      
                none 

        """
        try:
            if self._connected:
                #Start xrays
                self.write_message("XON")
                xon = self.read_message()
                if xon == "XON":
                    #If Xrays are starting, save the starting time of emission
                    start_time= datetime.now()
                    print "\n[XON]: X-rays emission started."
                    # In the terminal, because of the thread the three ">>> " 
                    # in python interactive mode desappear.
                    # For user convenience there are reprinted
                    sys.stdout.write(">>> ") 
                    self.xon = True
                    while self._get_status() == "STS 3" and \
                    (datetime.now() - start_time < \
                    timedelta(milliseconds=exposure_time)):
                        #Ask the tube status during exposure 
                        self._get_status()
                    if self._get_status() != "STS 3" \
		    and self.xon:
                        # If the status is not "STS 3 Xray are being emitted "
                        # anymore, and the xray was not manually stopped
			# check for errors. 
                        self._check_error()
                    elif self.xon:
                        # Stop xray when exposure time is reached
                        self.off()
			sys.stdout.write(">>> ") 
                else:
                    #Check for errors at command sending
                    self._check_command_error(xon)
            else:
                #Raise an error if the tube is already emitting Xrays
                raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                            "open.")
        except (ErrorSerialInterrupt, ErrorTubeInterrupt):
            # If xrays are turned on and an error occurs, 
            # try to shut the tube down
            # If a communication error occurs at any point, xrays will shut
            # down after 3 seconds automatically
            if self.xon:
                self.off()
            raise

    def warmup_start(self):
        """ A function to start the warmup when the status is STS 0 or STS 2.

            Input parameters:

                none 

            Return variables:
                
                none  

        """
        if self._connected:
            self.write_message("WUP")
            warmup  = self.read_message()
            if warmup ==  "WUP":
                print "\n[WUP]: The warmup started.\n"
            else:
                self._check_command_error(warmup)
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def selftest_start(self):
        """ A function to start the self-test when the status STS 2.

            Input parameters:

                none 

            Return variables:

                none  

        """
        if self._connected:
            self.write_message("TSF")
            selftest  = self.read_message()
            if selftest ==  "TSF":
                print "\n[TSF]: The self test starts."
		while self._get_status() == "STS 6":
                    # Ask for the status so that Xrays do not shut down
                    # after 3s 
                    self._get_status()
		    self._blink_text("Please wait 2 minutes.")
                if self._get_selftest_status() == "ZTE 1":
                # If status is not "STS 6:
		# Either self test complete ("ZTE 1") or
		# error occured
		    print "[INFO]: Self test completed."
		else:
                    self._check_error()
            else:
                self._check_command_error(selftest)
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def overload_reset(self):
        """ A function to reset the overload protection function when the 
            status is STS 4.
        
            Input parameters:

                none 

            Return variables:
      
                none  
        """
        if self._connected:
            self.write_message("RST")
            reset  = self.read_message()
            if reset ==  "RST":
                print "\n[RST]: The overload protection function was reset."
            else:
                self._check_command_error(reset)
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    ###########################################################################
    # Tube status information 
    ###########################################################################
    
    def status(self):
        """ A function to check the status of the tube,
            if the tube is connected.

            Input parameters:

                none 

            Return variables:
      
               The tube status is returned or raised.

        """
        if self._connected:
            #send message to the write_queue
            self.write_message("STS")
            #read message from the read_queue
            tube_status = self.read_message()
            if tube_status == "STS 5":
                return ("[WARNING STS 5]: X-rays cannot be emitted. "
                         "It can be caused by preheating, hardware error or "
                         "an open interlock.")
            elif tube_status == "STS 4":
                raise ErrorTubeInterrupt("[WARNING STS 4]: "
                    "Overload protection function is activated."
                    "\nTo restart X-ray emmission cancel the function or "
                    "'RST' overload protection function by sending the "
                    "overload_reset() function and check that a 'RST' response "
                    "is returned. Then, be sure to wait for few minutes before "
                    "turning on the X-rays again."
                    "\nAt this point, we recommend reducing the tube current "
                    "settings by about 10 percent and gradually increasing it "
                    "back to the original value after X-ray emission has "
                    "restarted."
                    "\nIf a 'STS 4' response is returned again, turn off "
                    "the power supply and then turn it back on."
                    "\nIf a 'STS 4'response is still returned even after "
                    "above operation, then the X-ray tube is probably defective. "
                    "Stop using the X-ray source and "
                    "consult the sales office.")
            elif tube_status == "STS 1":
                return "[WARNING STS 1]: Warm-up in progress. "
            elif tube_status == "STS 6":
                return "[WARNING STS 6]: Self-test in progress. "
            elif tube_status == "STS 3":
                return "[WARNING STS 3]: X-rays are (already) being emitted. "
            elif tube_status == "STS 0":
                return "[WARNING STS 0]: Awaiting warm-up. "
            elif tube_status == "STS 2":
                return "[STS 2]: Ready to emit X-rays. "
        else:
            #If the tube is not connected raise a ErrorSerialInterrupt
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")
                                        
    # Check if tube status is "STS 2", so ready to emit (AND: not emmitting!)
    def is_ready():
        """ Check if tube status is "STS 2" (tube ready to emit)
        
            E.g. if dark scan, and one needs to make sure that no x-rays are
            being emitted.
            
            Input parameters:

                none 

            Return variables:
      
                true, if ready (no emission)
                false, if something is going on...
        
        """
        #if self._connected:
        #    #send message to the write_queue
        #    self.write_message("STS")
        #    #read message from the read_queue
        #    tube_status = self.read_message()
        #    if tube_status == "STS 2":
        #        return True
        #    else:
        #        return False
        #else:
        #    #If the tube is not connected raise a ErrorSerialInterrupt
        #    raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
        #                                "open.")
        if "STS 2" in status():
            return True
        else:
            return False
                                        
    # Check if tube status is "STS 3", so emitting
    def is_on(self):
        """ Check if tube status is "STS 3" (x-rays a being emitted)
        
            E.g. before image acquisition.
            
            Input parameters:

                none 

            Return variables:
      
                true, if x-ray on
                false, if x-ray off
        
        """
        #if self._connected:
        #    #send message to the write_queue
        #    self.write_message("STS")
        #    #read message from the read_queue
        #    tube_status = self.read_message()
        #    if tube_status == "STS 3":
        #        return True
        #    else:
        #        return False
        #else:
        #    #If the tube is not connected raise a ErrorSerialInterrupt
        #    raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
        #                                "open.")
        if "STS 3" in self.status():
            return True
        else:
            return False

    def operation_status(self):
        """ A function to check the tube operation status

            Seven parameters are printed: Status "STS", output voltage "SHV",
            output current "SCU" and the remaining four parameters are zero.
            The parameters are separated by one space.
            Example: command: "SAR", response: "SAR 0-6 0-100 0-200 0 0 0 0"

            Input parameters:

                none 

            Return variables:
      
                none

        """
        if self._connected:
            self.write_message("SAR")
            operation_status = self.read_message()
	    operation_list = operation_status.split(" ")
            print ("\n[{0}]:" 
		   "\nStatus: STS {1}"
                   "\nVoltage {2} kV" 
		   "\nCurrent {3} ".format(operation_status, 
		   operation_list[1], operation_list[2], operation_list[3])
                   + u"\u00B5"+ "A")
            # u"\u00B5" is greek symbol mu
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection open.")

    def noxray_status(self):
        """ A function to check the tube status if X-rays cannot be emitted.

            Four parameters are printed: Hardware error "SER", interlock "SIN",
            preheating "SPH" and the remaining parameters are zero.
            The parameters are separated by one space.
            Example: command: "SNR", response: "SNR 0,3,4,200-209 0-1 0-1 0"
    
            Input parameters:

                none 

            Return variables:
      
                none

        """
        if self._connected:
            self.write_message("SNR")
            noxray_status = self.read_message()
	    noxray_list = noxray_status.split(" ")
            print ("\n[{0}]:"
                   "\nHardware error: SER {1}"
                   "\nInterlock: SIN {2} "
		   "\nPreheating: SPH {3}".format(noxray_status,
		    noxray_list[1], noxray_list[2], noxray_list[3]))
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")
                                        
        #Preheat status check
    def preheat_status(self):
        """ A function to check the status of the preheating.

            Input parameters:

                none 

            Return variables:

                Preheat status is returned. If the preheat is in progress 
                it raises an ErrorTubeInterrupt exception.

        """
        if self._connected:
            self.write_message("SPH")
            preheat = self.read_message()
            if preheat == "SPH 0":
                return ("\n[SPH 0]: Preheating is completed "
			"or not started yet.")
            elif preheat == "SPH 1":
                return ("\n[WARNING SPH 1]: Preheating "
                         "in progress. Please wait for one minute.")
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    #Warm-up status check
    def warmup_status(self):
        """ A function to check the status of the warm-up.

            Input parameters

                none 

            Return variables:

               warmup status is returned

        """
        if self._connected:
            self.write_message("SWE")
            warmup = self.read_message()
            if warmup == "SWE 0":
                return "\n[SWE 0]: Warmup completed."
            elif warmup == "SWE 1":
                return "\n[SWE 1]: Warmup in progress. Please wait."
            elif warmup == "SWE 2":
                return "\n[SWE 2]: Warmup does not start yet."
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def warmup_step(self):
        """ A function to check the warmup completion.

            The function prints the warmup pattern number and step number
            described in the tube instruction manual Appendix 15.A2.

            Input parameters:

                none 

            Return variables:

                none

        """
        if self._connected:
            self.write_message("SWS")
            step=self.read_message()
            if step == "SWS 0 0":
                print "\n[SWS 0 0]: No Warmup"
            else:
                print ("\n[{0}]: Warmup in progress at pattern {1} and "
                        "step {2}.".format(step, step[4], step[6]))
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    #Interlock status check
    def interlock_status(self):
        """ A function to check the status of the interlock.

            Input parameters:

                none 

            Return variables:

                returns the interlock status and raises an ErrorTubeInterrupt 
                if the interlock is open
                
        """
        if self._connected:
            self.write_message("SIN")
            interlock = self.read_message()
            if interlock == "SIN 0":
                return "\n[SIN 0]: Interlock is closed."
            elif interlock == "SIN 1":
                raise ErrorTubeInterrupt("\n[ERROR SIN 1]: Interlock circuit "
                                          "is open.")
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    # Button battery check
    def battery_status(self):
        """ A function to check the level of the button battery.

            Input parameters:

                none 

            Return variables:

                none
                
        """
        if self._connected:
            print "\n[INFO]: Checking battery level..."
            self.write_message("SBT")
            battery = self.read_message()
            if battery == "SBT 0":
                print "[SBT 0]: Battery is normal."
            elif battery == "SBT 1":
                print ("[WARNING SBT 1]: Battery is low. Refer to "
                         "paragraph 12: Replacing the button battery in "
                         "the tube instruction manual.")
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    #Self-test diagnostic
    def selftest_status(self):
        """ A function to check if the self test is completed or not.

            Input parameters:

                none 

            Return variables:

                return the selftest status

        """
        if self._connected:
            self.write_message("ZTE")
            selftest = self.read_message()
            if selftest == "ZTE 0":
                return "\n[ZTE 0]: Self test in progress."
            if selftest == "ZTE 1":
                return "\n[ZTE 1]: Self test is complete."
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")
                                        
    # Hardware error check
    def hardware_error_check(self):
        """ A function to check the hardware errors

            X rays stop if any hardware error is detected.
            SER 0 is return as long as no error occurs.

            Input parameters:

                none 

            Return variables:

                raise all the hardware errors as ErrorTubeInterrupt

        """
        if self._connected:
            self.write_message("SER")
            herror = self.read_message()
            if herror == "SER 0":
                return ("\n[SER 0]: No hardware error "
                "occured.")
            elif herror == "SER 3" or herror == "SER 4":
                raise ErrorTubeInterrupt("\n[ERROR {0}]: The X-ray source "
                "is probably defective. Turn off the power supply and " 
                "contact the sales office.".format(herror))
            elif herror == "SER 200":
                raise ErrorTubeInterrupt("\n[ERROR SER 200]: The fan is "
                "stopped. Check to see if aforeign object is cogged in the "
                "fan blades.\nThe fan might be brocken if excessive supply "
                "voltage is applied. In this case contact the sales office.")
            elif herror == "SER 201":
                raise ErrorTubeInterrupt("\n[ERROR SER 201]: Check the input "
                "supply voltage and adjust it to meet the specifications.")
            elif herror == "SER 202":
                raise ErrorTubeInterrupt("\n[ERROR SER 202]: Input voltage "
                "supply is too low. Check the input voltage and adjust it" 
                "to meet the specifications.")
            elif herror == "SER 208":
                raise ErrorTubeInterrupt("\n[ERROR SER 208]: Input voltage "
                "supply is too high. Check the input voltage and adjust it"
                "to meet the specifications.")
            elif herror == "SER 204" or herror == "SER 206" \
            or herror == "SER 207" or herror == "SER 203":
                raise ErrorTubeInterrupt("\n[ERROR {0}]: Turn off the "
                "power supply. "
                "\nWait at least one minute and turn on the power again. "
                "If the same error is returned again, the internal circuit "
                "might be defective. Immediatly turn off the power and "
                "contact the sales office".format(herror))
            elif herror == "SER 209":
                raise ErrorTubeInterrupt("\n[ERROR SER 209]: "
                                          "Temperature alarm.")
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")
    
    ###########################################################################
    # Set/Get parameters
    ###########################################################################

    def get_actual_voltage(self):
        """ A function to check the tube output voltage (between 0-100 kV). 

            Input parameters:

                none 

            Return variables:

                none
                
        """
        if self._connected:
            self.write_message("SHV")
            voltage = self.read_message()
            return ("\n[{0}]:Tube output voltage = {1} kV."
                    .format(voltage, voltage[4:]))
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def get_voltage(self):
        """ A function to check the set tube voltage (between 0-100 kV).

            Input parameters:

                none 

            Return variables:

                none

        """
        if self._connected:
            self.write_message("SPV")
            preset_voltage = self.read_message()
            return ("\n[{0}]: Preset tube voltage = {1} kV."
                    .format(preset_voltage, preset_voltage[4:]))
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")
                                        
    #Tube set/get commands
    def set_voltage(self, voltage):
        """ A function to set the tube voltage

            If a connection is open, the tube voltage is set through the parameter
            voltage. The command send to the tube is "HIV voltage".
            If an error occurs in the command or the parameter it will be raised.

            Input parameters:

                voltage is number between 0 to 100 (kV)

            Return variables:

                none  

        """
        if self._connected:
            self.write_message("HIV {0}".format(voltage))
            hiv  = self.read_message()
            if hiv ==  "HIV {0}".format(voltage):
                print ("\n[{0}]: Tube voltage set at {1} kV"
                        .format(hiv, hiv[4:]))
            else:
               self._check_command_error(hiv)
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def get_actual_current(self):
        """ A function to check the tube output current (between 0-200 microA).

            Input parameters:

                none 

            Return variables:

                none

        """
        if self._connected:
            self.write_message("SCU")
            current = self.read_message()
            return ("\n[{0}]: Tube output current = {1} "
                    .format(current, current[4:]) + u"\u00B5" + "A") 
                    # u"\u00B5" is greek symbol mu
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def get_current(self):
        """ A function to check the set tube current (between 0-200 microA).

            Input parameters:

                none 

            Return variables:

                none

        """
        if self._connected:
            self.write_message("SPC")
            preset_current = self.read_message()
            return ("\n[{0}]: Preset tube current = {1} "
                    .format(preset_current, preset_current[4:])
                    + u"\u03BC" + "A") 
                    # u"\u00B5" is greek symbol mu
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def set_current(self, current):
        """ A function to set the tube current

            If a connection is open, the current is set through the parameter
            current. The command send to the tube is "CUR current".
            If an error occurs in the command or the parameter it will be raised.
            
            Input parameters:

                current is a number between 0 to 200 (microA)

            Return variables:

                none  

        """
        if self._connected:
            self.write_message("CUR {0}".format(current))
            cur  = self.read_message()
            if cur ==  "CUR {0}".format(current):
                print ("\n[{0}]: Tube current set at {1} "
                        .format(cur, cur[4:]) + u"\u00B5"+ "A")
            else:
                self._check_command_error(cur)
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    ###########################################################################
    # Utility functions
    ###########################################################################

    def selftest_results(self):
        """ A function to check the detailed results of the self test.

            Input parameters:

                none 

            Return variables:

                none

        """
        if self._connected:
            self.write_message("ZTR")
            res = self.read_message()
            print ("\n[{0}]: Self-test detailed results:"
                   "\nCathode level (5:good - 1:deteriorated): {1}"
                   "\nMaximum value of input voltage (0.00V to 99.9V): {2} V"
                   "\nMinimum value of input power voltage (0.00 V to 99.9 V): {3} V"
                   "\nAverage value of input power voltage (0.00V to 99.9 V): {4} V"
                   "\nControl circuit 1 (0:normal - 1:abnormal): {5}"
                   "\nControl circuit 2 (0:normal - 1:abnormal): {6}"
                   "\nHigh voltage block (0:normal - 1:abnormal): {7}"
                   .format(res, res[4], res[6:10], res[11:15], res[16:20], 
                   res[21], res[23], res[25]))
            ## For linux but not windows: u"\u2103" = the symbol degre celcius
            #print("PC board temperature 1 (00 to 99 " + u"\u2103" + " ): "
            #    + res[27:29] + u"\u2103")
            #print("PC board temperature 2 (00 to 99 " + u"\u2103" + " ): "
            #    + res[30:32] + u"\u2103")
            ## For windows:
            print("PC board temperature 1 (00 to 99 " + u"\xb0" + "C ): "
            + res[27:29] + " " + u"\xb0" + "C")
            print("PC board temperature 2 (00 to 99 " + u"\xb0" + "C ): "
            + res[30:32] + " " + u"\xb0" + "C")
            # u\"xb0" is the symbol degree for windows
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def check_power_supply(self):
        """ This function send a dummy command "bla" as a first command after 
            serial connection open.

            A 'ERR 0 NOC' is returned in response to a command that is first sent
            after power-on. This is to check the connection.
            So as the first command, a dummy command "bla" is send.
            This function works also if the power was already on because sending
            a dummy command will be consider as a incorrect command and the answer to
            an incorrect command is 'ERR 0 NOC'.
            If 'ERR 0 NOC' is not returned, it raised an ErrorTubeInterrupt,
            the powersupply is probably not on.
                    
            Input parameters:

                none 

            Return variables:

                none  

        """
        if self._connected:
             self.write_message("bla")
             first_response = self.read_message()
             if first_response != "ERR 0 NOC":
                raise ErrorTubeInterrupt("\n[ERROR] Check if the power supply is on.")
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    # time check
    def poweron_time(self):
        """ A function to ckeck the accumulate time in hours that the tube 
            has been turned on.
         
            Input parameters:

                none 

            Return variables:

                none

        """
        if self._connected:
            self.write_message("STM")
            poweron = self.read_message()
            print ("\n[{0}]: Power-on time = {1} h."
                    .format(poweron, poweron[4:]))
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def emission_time(self):
        """ A function to ckeck the accumulate time in hours that the X-rays 
            have been emitted during operation and warmup

            Input parameters:

                none 

            Return variables:

                none

        """
        if self._connected:
            self.write_message("SXT")
            emission = self.read_message()
            print ("\n[{0}]: Xrays emission time = {1} h."
                    .format(emission, emission[4:]))
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    

    # Model check
    def model_name(self):
        """ A function to ckeck Xray source model name.

            Input parameters:

                none 

            Return variables:

                none

        """
        if self._connected:
            self.write_message("TYP")
            model = self.read_message()
            print ("\n[{0}]: Model name = {1}.".format(model, model[4:]))
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")
                                        
    ###########################################################################
    # List all current settings
    ###########################################################################
    
    def settings(self):
        """ List current settings
        
            Input parameters:
                
                none
                
            Return values:
                
                none (just print onto screen)
                
        """
        voltage = string.split(self.get_actual_voltage(), "= ")[1]
        current = string.split(self.get_actual_current(), "= ")[1]
        print voltage
        print current
        print self.status()
        print("\nCurrent settings:"
               "\n"
               "\nVoltage:\t{0}"
               "\nCurrent:\t{1}"
               "\nTube status:\t{2}".format(voltage,
               current, self.status()))

###############################################################################
#  Private functions
###############################################################################

    def _get_status(self):
        """ A function which return the status of the tube.

            It raises an error if the serial connection is closed
    
            Input parameters:

                none

            Return variables:
      
                tube_status 

        """
        if self._connected:
            self.write_message("STS")
            return self.read_message()
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def _get_preheat_status(self):
        """ A function which return the status of the preheating

            Input parameters:

                none

            Return variables:
       
                preheat
          
        """
        if self._connected:
            self.write_message("SPH")
            return self.read_message()
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")


    def _get_warmup_status(self):
        """ A function which return the status of the warmup

            Input parameters:

                none

            Return variables:
       
                warmup
          
        """
        if self._connected:
            self.write_message("SWE")
            return self.read_message()
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def _get_interlock_status(self):
        """ A function which return the status of the interlock

            Input parameters:

                none

            Return variables:
       
                interlock
          
        """
        if self._connected:
            self.write_message("SIN")
            return self.read_message()
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def _get_battery_status(self):
        """ A function to check the level of the button battery

        """
        if self._connected:
            self.write_message("SBT")
            return self.read_message()
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def _get_warmup_step(self):
        """ A function which return the progress of the warmup by indicating 
            the current warmup pattern

            Input parameters:

                none

            Return variables:
       
                step represents the warmup step or pattern
          
        """
        if self._connected:
            self.write_message("SWS")
            step=self.read_message()
            return step
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")


    def _get_hardware_error_check(self):
        """ A function which return the type of hardware errors

            Input parameters:

                none

            Return variables:
       
                herror representing the type of hardware errors
          
        """
        if self._connected:
            self.write_message("SER")
            return self.read_message()
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")
					
    def _get_selftest_status(self):
        """ A function which return the self test status

                Input parameters:

            none

                Return variables:
       
            status
          
        """
        if self._connected:
            self.write_message("ZTE")
            return self.read_message()
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: No serial connection "
                                        "open.")

    def _check_command_error(self,response):
        """ A function that checks for errors when a command is sent to the 
            serial port
        
            5 kind of command errors can occur: (*** = basic command: 
            XON, XOF, ...)
            [ERR 10 ***] = Status error (Not ready to receive command).
                        The cause of this error depend of the sent command.
                        That's why different cases are distinguished depending 
                        on the command.
                        Refer to the first table at the end of the manual
            [ERROR 20 ***] = Parameter error (Parameter value outside 
                             allowable range)
            [ERROR 30 ***] = Maximum usable value exceded (Exceed the range 
                             set by CMV and CMC).
            [ERROR 40 ***] = Wattage error (Wattage outside the 
                             allowable range)
            [ERROR ERR 0 NOC]: Incorrect command received
            
            The functions that check for errors inside this functions
            raise an ErrorTubeInterrupt in case of an error. 
            This error is then reraised in the higher level functions 
            that sends the command such as set_voltage(), 
            thread_xray_on(), ...   
    
            Input parameters:

                response corresponds to the receiving message from the tube
                get after sending a command

            Return variables:
       
            n    one

        """
        # response[7:] corresponds to the basic command string that can be sent 
        #(XON, XOF, WUP, ...) 
        if response == "ERR 10 {0}".format(response[7:]): 
            print "\n[ERROR ERR 10 {0}]:".format(response[7:])
            if "XON" in response:
                # if an ERROR 10 occurs by sending XON it can be  
                #because of hardware error, interlock open, preheat status.
                if self._get_hardware_error_check() != "SER 0":
                    self.hardware_error_check()
                if self._get_preheat_status() == "SPH 1":
                    self.preheat_status()
                if self._get_interlock_status() == "SIN 1":
                    self.interlock_status()
                else:
                    # It can also be because of the overload protection 
                    # function (STS 4), self test (STS 6), warmup (STS 0), 
                    # xray which are already emitted (STS 3)
                    raise ErrorTubeInterrupt(self.status())
            elif "WUP" in response:
                # if an ERROR 10 occurs by sending warming up it can be 
                #because of hardware error, interlock open, preheat status.
                if self._get_hardware_error_check() != "SER 0":
                    self.hardware_error_check()
                if self._get_preheat_status() == "SPH 1":
                    self.preheat_status()
                if self._get_interlock_status() == "SIN 1":
                    self.interlock_status()
                else:
                    # It can also be because of the overload protection 
                    # function (STS 4), self test (STS 6), xray on (STS 3), 
                    # warmup which already started (STS 3)
                    raise ErrorTubeInterrupt(self.status())
            elif "TSF" in response:
                if self._get_status() != "STS 2":
                    raise ErrorTubeInterrupt("Wrong Status. Self test can "
                    "only be performed when the status is ready to emit Xrays "
                    "[STS 2].")
            elif "RST" in response:
                if self._get_status() != "STS 4":
                    raise ErrorTubeInterrupt("Wrong Status. Overload "
                    "protection reset command can only be sent when the "
                    "overload protection function is activated [STS 4].")
            else:
                #In other case such as XOF, HIV, CUR (but "normally" for 
                #these command no ERR 10 occurs, see first table of 
                #the manual)
                raise ErrorTubeInterrupt("\nNot ready to send the command {0}"
                            "or command already sent".format(response[7:]))

        elif response == "ERR 20 {0}".format(response[7:]):
            # Only for command with parameter ie. HIV (set_voltage()) and 
            # CUR (set_current())
            raise ErrorTubeInterrupt("\n[ERROR ERR 20 {0}]: Parameter error "
            "(Parameter value is outside the allowable range. "
            .format(response[7:]))
        elif response == "ERR 30 {0}".format(response[7:]):
            raise ErrorTubeInterrupt("\n[ERROR ERR 30 {0}]: Maximum usable "
            "value exceded (Exceed the range set by CMV and CMC)."
            .format(response[7:]))
        elif response == "ERR 40 {0}".format(response[7:]):
            raise ErrorTubeInterrupt("\n[ERROR ERR 40 {0}]: Wattage error "
            "(Wattage was outside the allowable range)."
            .format(response[7:]))
        elif response == "ERR 0 NOC":
            raise ErrorTubeInterrupt("\n[ERROR ERR 0 NOC]: Incorrect command"
            "was received.")


    def _check_error(self):
        """ A function that checks for errors during warmup and Xray emission
        
            It search for STS 5 status : Hardware error, preheat and interlock 
            open and for the STS 4 status: overload protection function 
            activated.
            The functions that check for hardware error, intelock, preheat 
            and STS 4 raise an ErrorTubeInterrupt in case of an error. 
            This error is then reraised in the higher level functions such as:
            start(), thread_xray_on(), thread_xray_on().   
            
            Input parameters:

                none

            Return variables:
       
                none

        """
        if self._get_status() == "STS 5":
            if self._get_hardware_error_check() != "SER 0":
                self.hardware_error_check()
            if self._get_preheat_status() == "SPH 1":
                self.preheat_status()
            if self._get_interlock_status() == "SIN 1":
                self.interlock_status()
        elif self._get_status() == "STS 4":
            self.status()



    def _blink_text(self, text):
        """ A function to made the output text in the console blinking.

            Input parameter:

            text is a string (here text must be a two lines string)

        """
        #sys.stdout.write(text + "\x1b[A" + "\r" ) 
        ## "\x1b[A" sends the cursor at the end of the first line
        ## The CR sends the cursor at the begining of the first line
        ## This is in order to overwrite the text afterwards
        #sys.stdout.flush()  # flush output to not see the cursor move
        #sleep(1)  # wait to see the blinking, to fast otherwise
        #textlist=text.split("\n")  #split the two lines of the text in a list
        #sys.stdout.write("".ljust(len(textlist[0]))+ "\n" + 
        #"".ljust(len(textlist[1])) +"\x1b[A"+"\r")
        ## replace the text by 2 lines of space with the same size as the  
        ## text writen on each line to overwrite the text and do the blinking
        #sys.stdout.flush()
        #sleep(1)  # wait to see the blinking, to fast otherwise

        # One line
        print("\r" + text),
        sys.stdout.flush()  # flush output to not see the cursor move
        sleep(1)  # wait to see the blinking, to fast otherwise
        print("\r" + "".ljust(len(text))),
        sys.stdout.flush()  # flush output to not see the cursor move
        sleep(1)  # wait to see the blinking, to fast otherwise


########################################################################
# Main function
########################################################################

tube = TubeControl()
