#################################################################
#
# serial_communication.py
#
# This file contains a class SerialCommunication which is a
# single thread and implements the communication with the tubes
# serial port
#
# Author:
# Celine Stoecklin (celine.stoecklin@psi.ch)
# Maria Buechner (maria.buechner@psi.ch)
#
# History:
# 15.11.2013: started
# 08.12.2013: modified (mb)
#
#################################################################

# Imports

import threading
import serial
import Queue
from time import sleep

from gantry_control_exceptions import ErrorSerialInterrupt

# Constants
#PORT = 'COM1' # Port name on Windows
PORT = '/dev/ttyS0' # Port name on linux
BAUDRATE = 38400
BUFFER_SIZE = 40 # Max. number of byte to send/read
                 # Needs to be adjusted according to larges
                 # send/receive message (usually: 1 character
                 # = 1 byte)
QUEUE_MAX_SIZE = 10
#TIMEOUT = 0.01
TIMEOUT = 0.1 # Tube hangs itself up, maybe timeout because of long cable?


RETRIES = 5 # Number of retries after failed communication
########################################################################
# Define classes
########################################################################

class SerialCommunication(threading.Thread):

    """Class for serial port communication.
       This class is in a single thread and manage the actual serial port
       communication, via two Queue objects.

       Commands send to the port are placed into the write_queue
       and the "Serial thread" writes them to the port.
       The "Serial thread" reads the received message from the port
       and places it into the read_queue.
       The message is then taken out from the read queue.

       Variables:

            deamon: thread parameter
            serial_port
            connected: connection status, true if connection is open
            port, baudrate, buffersize, timeout : serial port settings
            write_queue: FIFO
            read_queue: FIFO

    """
    def __init__(self):
        threading.Thread.__init__ (self)
        # Set thread as deamn thread, so that it is forcefully shutdown,
        # when main (or all other non-deamon threads) are exited
        self.deamon = True
        self.port = PORT
        self.baudrate = BAUDRATE
        self.buffersize = BUFFER_SIZE
        self.timeout = TIMEOUT

        self.serial_port = serial.Serial()
        self.connected = False # state of the serial port

        self.write_queue = Queue.Queue(QUEUE_MAX_SIZE)
        self.read_queue = Queue.Queue(QUEUE_MAX_SIZE)

    ##################  Serial connection functions  #########################

    def run(self):
        """
        The run() method determines the activity of the thead when it starts.
        Here the thread is active while the connection is open.
        It writes message to the serial port from the write_queue if there
        are messages to get from the write_queue.
        It reads the received messages from the serial port and puts them into
        the read_queue.
        The thread activity (run() method) terminates once the serial port is
        closed, however the thread does not stop.
        The thread is alive until the exit of the program.
        A reinitialization (__INIT__()) of the thread is necessary when the
        port is closed and opened again in the same programm.

        """
        while self.connected:
            sleep(0.2) # To stop executing while port is shut down\
                       # 0.5 seems to be working
            if not self.write_queue.empty():
                # Write and read in one function, to correlate outgoing and
                # incoming messages
                # NOTE: not necessary (or usefull) if tube class functions
                # don't do the same!
                self._write_message()
                self._read_message()
        # Call thread init function, to be able to restart the thread when
        # the port is opened
        threading.Thread.__init__ (self)

    def open_serial(self):
        """A function to start a serial connection

           A new connection will be opened with constant serial port settings,
           if there is no connection open already.

           Input parameters:

                none

        """
        # Open serial port
        if not self.serial_port.isOpen():
            print "\n[INFO]: Opening serial port..."
            self.serial_port = serial.Serial(self.port, self.baudrate,
                                             timeout = self.timeout)
            if self.serial_port.isOpen():
                print "\n[OPEN]: Serial connection at port '{0}' is open."\
                "\nSerial port details: {1}".format(self.port,self.serial_port)
                self.connected = True
            else:
                raise ErrorSerialInterrupt("\n[ERROR]: Serial connection "
                        "at port '{0}' could not be opened.".format(self.port))
                self.connected = False
        else:
            print ("\nSerial connection at port '{0}' is"
                    "already open.".format(self.port))
            self.connected = True

    def close_serial(self):
        """A function to close a serial connection

           The existing serial port connection is closed, if it is not
           already closed.

           Input parameters:

                none

        """
        # Close serial port connection
        if self.serial_port.isOpen():
            print "\n[INFO]: Closing serial port..."
            self.serial_port.close()
            if not self.serial_port.isOpen():
                print "\n[CLOSE]: Serial connection at port '{0}' is closed."\
                "\nSerial port details: {1}".format(self.port,self.serial_port)
                self.connected = False
            else:
                raise ErrorSerialInterrupt("\n[ERROR]: Serial connection "
                        "at port '{0}' could not be closed.".format(self.port))
                self.connected = True
        else:
            print ("\nSerial connection at port '{0}' is "
                    "already closed.".format(self.port))
            self.connected = False

    # Send a message through the tube
    def _write_message(self):
        """A function to write the message to the serial port ie.
           send the command to the tube.

           If a message is in the write_queue, the input message will be send
           to the serial port.
           Typical command consists of an alphanumeric string, the message msg,
           following by a carriage return CR '\r' delimiter.
           Here the carriage return is implement automatically.
           serial_port.flushInput is used to clean the input buffer content
           (message received by the serial port from the tube) before writing
           another message.
           When the xray is ON and then a shut down "XOF" command is sent,
           the tube shust down but has not enough time to send a message before
           the return message is received. That is why another XOF command is
           send in order to be sure that the xray is OFF.

           Input parameters:

                none

        """
        if self.connected:
            try:
                msg = self.write_queue.get()
                if 'XOF' in msg:
                    self.serial_port.flushInput()
                    self.serial_port.write(msg + "\r")
                    sleep(0.5)
                    self.serial_port.flushInput()
                    self.serial_port.write(msg + "\r")
                    #print "\n[SEND]: {0}.".format(msg)
                else:
                    self.serial_port.flushInput()
                    self.serial_port.write(msg + "\r")
            except Queue.Empty:
                raise ErrorSerialInterrupt("[ERROR]: Write queue empty, "
                                            "nothing to write.")
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: Cannot send message, "
                                        "no serial connection open.")

    # Receive a message
    def _read_message(self):
        """A function that reads the received message from the serial port.

           If a connection is open, an incoming message will be read from
           the port. If the message is not empty, the received message is
           put into the read_queue.
           The received message consists of an alphanumeric string
           following by a carriage return CR.

           Input parameters:

                none

        """
        if self.connected:
            #try:
            #    received_msg = self.serial_port.read(self.buffersize)
            #    received_msg = received_msg.rstrip("\r")
            #    #removed CR at the end of the received message
            #    if received_msg:
            #        # recieved message not empty
            #        self.read_queue.put(received_msg)
            #    else:
            #        raise ErrorSerialInterrupt("\n[ERROR]: No message "
            #                                    "received.")
            try:
                received_msg = self.serial_port.read(self.buffersize)
                received_msg = received_msg.rstrip("\r")
                #removed CR at the end of the received message
                if received_msg:
                    # recieved message not empty
                    self.read_queue.put(received_msg)
                else:
                    received_msg = self.serial_port.read(self.buffersize)
                    received_msg = received_msg.rstrip("\r")
                    #removed CR at the end of the received message
                    if received_msg:
                        # recieved message not empty
                        self.read_queue.put(received_msg)
                    else:
                        raise ErrorSerialInterrupt("\n[ERROR]: No message "
                                                "received.")
            #try:
            #    while retries<RETRIES:
            #        received_msg = self.serial_port.read(self.buffersize)
            #        received_msg = received_msg.rstrip("\r")
            #        #removed CR at the end of the received message
            #        if received_msg:
            #            # recieved message not empty
            #            self.read_queue.put(received_msg)
            #            break
            #        retries = retries+1
            #    # If after RETRIES af read messages still empty reply
            #    if received_msg:
            #        raise ErrorSerialInterrupt("\n[ERROR]: No message "
            #                                    "received.")                                       
            except Queue.Full:
                raise ErrorSerialInterrupt("[ERROR]: Read queue full, "
                                            "cannot store message.")
            except ErrorSerialInterrupt:
                raise # re-raises caught exception (To fix bug that program
                      # stalls after this exception (only no message recieved)
                      # But: no effect
        else:
            raise ErrorSerialInterrupt("\n[ERROR]: Cannot receive message, "
                                        "no serial connection open.")

        return received_msg

    def put_into_write_queue(self, msg):
        """
        A function that puts the input message into the write_queue.

        Typical message or command consists of an alphanumeric string,
        the message msg, following by a carriage return CR '\r' delimiter.

        Input parameter:
            
            msg is a string (without CR)

        """
        try:
            self.write_queue.put(msg)
        except Queue.Full:
            raise ErrorSerialInterrupt("[ERROR]: Write queue is full, "
                                        "message not stored.")

    def get_from_read_queue(self):
        """
        A function to get the received message from the read_queue

        Input parameter:
            
             none

        """
        try:
            return self.read_queue.get()
        except Queue.Empty:
            raise ErrorSerialInterrupt("[ERROR]: Read queue is empty, "
                                        "nothing to get.")

########################################################################

# Main function

########################################################################
