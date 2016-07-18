# Copyright (C) 2013 Dectris Ltd.

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

#
#  \file      pilatus.py
#  \details
#  \author    Volker Pilipp
#  \author    Contact: support@dectris.com
#  \version   2.2
#  \date      07/01/2014
#  \copyright See General Terms and Conditions (GTC) on http://www.dectris.com
#
#


import itertools
import os
import os.path
import re
import shutil
import socket
import subprocess
import sys
import time
import threading
import numpy

import dectris.albula as albula
from delegator import DDelegator

try:
    from dectris.spluegen_ext.pilatus import DPilatus as PilatusExtended
    print "Found extension module 'dectris.spluegen_ext.pilatus'"
except:
    PilatusExtended = None



class DPilatus(DDelegator):
    """Class DPilatus provides an interface to camserver. You should not need to use this class explicitely, because the
    interface may change in the future. Use class DCamera instead.

    Extending class DPilatus:
        Add module dectris.spluegen_ext.pilatus containing class DPilatus. The __init__ method of the extension class
        DPilatus must read:
            __init__(self, pilatus, socket, detectorPath, clientPath)
        where pilatus is an instance of class DPilatus, which may be used to call DPilatus methods from the extension module.
        socket is an open socket to camserver and detectorPath and clientPath are defined analogous to
        this __init__ method.
        All further methods of the extension class DPilatus are callable from DCamera after DCamera.open() has been called.
    """



    def __init__(self, host = "localhost", port = None, detectorPath = None, clientPath = None):
        """
        Create DPilatus object.
        If DPilatus is neither run locally on a detector computer nor on a PPU,
        detectorPath and clientPath must point to a storage device both detector and client computer
        can access, where the former parameter must be the path on the detector computer, the latter
        the path on the client computer.

        Args:

           host: String or list of strings. In the latter case open() tries to connect to the listed hosts.
           port: Port number
           detectorPath: Path on the detector computer to a storage device both detector computer and client computer have in common.
           clientPath: Path on the client computer to a storage device both detector computer and client computer have in common.

        """
        super(DPilatus,self).__init__()
        self.__host = host
        if port is None:
            self.__port = 41234
        else:
            self.__port = port
        self.__detectorPath = detectorPath
        self.__clientPath = clientPath
        self.__socketBufferSize = 1024

        self.__isLocal = False
        self.__isPPU = False
        self.__abort = False
        self.__abortCondition =  threading.Condition()
        
    def detector(self):
        return "PILATUS"
        
        


    def open(self, timeout = 5 ):
        """
        Open connection to camserver.

        Args:
            timeout: Timeout in seconds

        Returns:

            True if connection was established successfully else False.
        """
        if type(self.__host) == str:
            self.__openSocket(self.__host, timeout)
        elif type(self.__host) == list:

            # put localhost IPs to the front, i.e. try localhost first
            if 'localhost' in self.__host:
                self.__host.remove('localhost')
                self.__host.insert(0,'127.0.0.1')
            if '127.0.0.1' in self.__host:
                self.__host.remove('127.0.0.1')
                self.__host.insert(0,'127.0.0.1')

            for h in self.__host:
                self.__openSocket(h)
                if not self.__socket is None:
                    self.__host = h
                    break

        if not self.__socket:
            return False
        self.__socket.sendall("prog b*_m*_chsel 0xffff\n")
        answer = self.__socket.recv(self.__socketBufferSize)
        self.__socket.settimeout(None)

        with open('/dev/null','w') as devNull:
            if self.__host in ['localhost','127.0.0.1']:
                self.__isLocal = True
            elif ( None in [self.__detectorPath,self.__clientPath] and 
                   self.__host.startswith('10.10.') and 
                   subprocess.call(['/etc/init.d/furka','status'],stdout = devNull) == 0 ):
                self.__isPPU = True

        if None in [self.__detectorPath,self.__clientPath]:
            if self.__isLocal:
                self.__detectorPath = '/dev/shm'
                self.__clientPath = self.__detectorPath
            elif self.__isPPU:
                self.__detectorPath = '/ramdisk'
                self.__clientPath = self.__detectorPath
        if None in [self.__detectorPath,self.__clientPath]:
            raise albula.DRuntimeException('Computer is neither detector computer nor PPU. Both detectorPath and clientPath must be set explicitely in __init__()')

        if self.__isPPU:
            self.__maxSearchDepth = 2
        else:
            self.__maxSearchDepth = 0

        if not PilatusExtended is None:       
            self.setDelegated(PilatusExtended(self, self.__socket, self.__detectorPath, self.__clientPath))



        return True

    def close(self ):
        """
        Close connection to camserver
        """
        if self.__socket:
            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
            self.__socket = None
        return
        
    def abort(self):
        with self.__abortCondition:
            try:
                self.__socket.sendall("k")
                self.__socketRecv(timeout = 0.1) # set timeout because 'k' may or may not return an answer
                self.__socketRecv(timeout = 0.1) # set timeout because 'k' may or may not return an answer
                self.__socketRecv(timeout = 10) # eventually read final answer from exposure, ...
            except:
                pass
            self.__abort = True;
            self.__abortCondition.notify()
        return

    def exposeCallback(self, callback, exptime = 1, nimages = 1, expperiod = None, mode = None, timeout = -1):
        """Expose a single image or a series of images and run callback(img) on every image img.

        Args:

            exptime: Exposure time in seconds.
            nimages: Number of images to expose. If nimage > 1 expperiod should be set to a value different form None
            expperiod: Time in seconds between two successive exposures (nimage > 1 otherwise no effect).
                       Default is exptime + deadtime if set to None
            mode: Trigger mode. Possible modes:
                  * expo: internal exposure (Default)
                  * extt: external trigger
                  * extm: external multi trigger
                  * exte: external enable
            timeout: Timeout for an external trigger (time before the trigger has to arrive, otherwise the command is interrupted)

        """
        with self.__abortCondition:
            self.__abort = False
            if not self.__socket:
                return
            self.__socket.sendall("imgmode x\n")
            answer = self.__socket.recv(self.__socketBufferSize)
            self.__socket.sendall("nimages {0}\n".format(nimages))
            answer = self.__socket.recv(self.__socketBufferSize)
            self.__socket.sendall("expt={0}\n".format(exptime)) 
            answer = self.__socket.recv(self.__socketBufferSize)
            if nimages > 1:
                if expperiod is None:
                    _expperiod = exptime + self.readoutTime()*0.001
                else:
                    _expperiod = float(expperiod)
                self.__socket.sendall("expperiod {0}\n".format(_expperiod))
                answer = self.__socket.recv(self.__socketBufferSize)
    
            self.__socket.sendall("imgpath {0}\n".format(self.__detectorPath))
            answer = self.__socket.recv(self.__socketBufferSize)

            fileName = 'dectrisAlbula{0}'.format(time.strftime('%H%M%S'))
    
            modeDict = {
                'expo': 'Exposure',
                'extt': 'ExtTrigger',
                'extm': 'ExtMTrigger',
                'exte': 'ExtEnable'
                }
            if mode is None:
                mode = "expo"
            self.__socket.sendall("{0} {1}\n".format(modeDict[mode], fileName + '.tif'))
            self.__socketRecv(timeout = None)


        returnList = []
        for i in range(nimages):
            if nimages == 1:
                seriesId = "{0}.tif".format(fileName)
            else:
                seriesId = "{0}_{1:0>5}.tif".format(fileName,i)
            try:
                if timeout < 0:
                    timeout = 86400 # 24 hours!
                img = self.__readImage(seriesId, timeout = timeout * 1000)
            except albula.DRuntimeException as e:
                if str(e) == "Timeout":
                    self.abort()
                    return None
                elif str(e) == "Aborted":
                    return None
                else:
                    raise e
            callback(img)

        self.__socketRecv(timeout = None) # Read final answer from exposure, ...



    def expose(self,exptime = 1, nimages = 1, expperiod = None, mode="expo", timeout = -1):
        """Expose a single image or a series of images.

        Args:

            exptime: Exposure time in seconds.
            nimages: Number of images to expose. If nimage > 1 expperiod should be set to a value different form None
            expperiod: Time in seconds between two successive exposures (nimage > 1 otherwise no effect). 
                       Default is exptime + deadtime if set to None
            mode: Trigger mode. Possible modes:
                  * expo: internal exposure
                  * extt: external trigger
                  * extm: external multi trigger
                  * exte: external enable
            timeout: Timeout for an external trigger (time before the trigger has to arrive, otherwise the command is interrupted)
    
            Returns:

                List of taken DImageInt objects. None if timed out.
        """

        returnList = []
        def callback(img):
            returnList.append(img)

        self.exposeCallback(callback,exptime,nimages,expperiod,mode,timeout)
        return returnList


    def setEnergy(self, energy, threshold=None, applyFlatfield = True, applyMask = True, gain = None):
        """
         Args:
                energy: the beam energy in eV
                threshold: the detector threshold in eV, default is half of the beam energy
                applyFlatfield: If True (False) flatfield corrections are (not) applied to successive images
                applyMask: If True (False) bad pixel mask is (not) added to successive images
                gain: For old detectors only
        """
             
        if gain is None:
            gain = 'midg'
        if threshold is None:
            threshold = energy/2.
        self.__socket.sendall('setth energy {0} {1} {2}\n'.format(energy,gain,threshold))
        answer = self.__socket.recv(self.__socketBufferSize)
        if not applyFlatfield:
            self.__socket.sendall('LdFlatField 0\n')
            answer = self.__socket.recv(self.__socketBufferSize)
        if not applyMask:
            self.__socket.sendall('LdBadPixMap 0\n')
            answer = self.__socket.recv(self.__socketBufferSize)
    

    def readSensors(self):
        """
        Reads back the temperature and humidity values from the detector.
        Returns:
            dictionary
        """
        pass

    def readoutTime(self):
        self.__socket.sendall("readouttime\n")
        answer = self.__socket.recv(self.__socketBufferSize)
        # print "DEBUG: readoutTime:  ", answer
        m = re.search(r" Detector readout time \[ms\]: ([0-9.]+)[\x1815]",answer)
        return float(m.group(1))

    def sendCommand(self, command):
        """Send a command to camserver

        Args:

            command: command to send (as string)

        Return:

            Answer of camserver

        """
        if (not self.__socket):
            return
        self.__socket.sendall(command)
        answer = self.__socketRecv()
        return answer

    def rbd(self):
        """Take an rbd image. All pixels get the value 1000

        Returns:

            dectris.albula.DImage
        """

        if (not self.__socket):
            return

        self.__socket.sendall("imgmode p\n")
        answer = self.__socket.recv(self.__socketBufferSize)

        self.__socket.sendall("imgpath {0}\n".format(self.__detectorPath))
        answer = self.__socket.recv(self.__socketBufferSize)

        self.__socket.sendall("fillpix {0}\n".format('0x9d367'))
        answer = self.__socket.recv(self.__socketBufferSize)

        time.sleep(0.5)

        fileName = 'dectrisAlbula{0}.tif'.format(time.strftime('%H%M%S'))
        self.__socket.sendall("imgonly {0}\n".format(fileName))
        answer = self.__socket.recv(self.__socketBufferSize)

        return self.__readImage(fileName, readModules = False)



    def calibration(self, numberOfPulses, rect = None):
        """Take an calibration image

        Args:

            numberOfPulses: Number of pulses
            rect: DRect object. This argument is only for consistency with DEiger and is ignored.

        Returns:

            dectris.albula.DImage
        """

        if (not self.__socket):
            return

        if (not self.__socket):
            return
        self.__socket.sendall("imgmode p\n")
        answer = self.__socket.recv(self.__socketBufferSize)

        self.__socket.sendall("imgpath {0}\n".format(self.__detectorPath))
        answer = self.__socket.recv(self.__socketBufferSize)

        self.__socket.sendall("calibrate {0}\n".format(int(numberOfPulses)))
        answer = self.__socket.recv(self.__socketBufferSize)

        time.sleep(0.5)

        fileName = 'dectrisAlbula{0}.tif'.format(time.strftime('%H%M%S'))
        self.__socket.sendall("imgonly {0}\n".format(fileName))
        answer = self.__socket.recv(self.__socketBufferSize)

        return self.__readImage(fileName, readModules = False)


    def selfTest(self, display = False):
        """ Run a self test on the detector.
        
        Args:
          display: If True show test results in a viewer window
        
        Returns:
        Tuple (result, List) where result is an integer coding the 
        test result ( 0 = success, 1 = failure)
        and List is a list of the test images.
        """
    
        result = 0
        imgList = []
                        
        pixelMask = self.__maskInterchip(self.expose(exptime = 0.1)[0], interchip = 3)
        print "Running RBD test"
        imgRbd, nRbdOutside = self.__rbdTest(pixelMask)
        imgList.append(imgRbd)
        if nRbdOutside > 0:
            sys.stderr.write("RBD test failed: Found {0} pixels differing from the expected value\n".format(nRbdOutside))
            result |= 1
        else:
            print "RBD test passed"
            
        print "Running calibration test"
        imgCalibration, nCalibrationOutside = self.__calibrationTest(pixelMask)
        imgList.append(imgCalibration)
        if nCalibrationOutside > 0:
            sys.stderr.write("Calibration test failed: Found {0} pixels differing from the expected value\n".format(nCalibrationOutside))
            result |= 2
        else:
            print "Calibration test passed"
            
        if display:
            imgRbd.optionalData().set_pixel_mask(pixelMask)
            imgCalibration.optionalData().set_pixel_mask(pixelMask)

            mainFrame = albula.openMainFrame()
            mainFrame.synchronizeViewport(False)
            mainFrame.synchronizeContrast(False)


            s = mainFrame.openSubFrame()
            s.loadImage(imgRbd)
            s.hideToolButtons()
            s.setColorMode("RB")
            rbdValue = 1000
            s.setContrast(rbdValue+1,rbdValue-1)  
            s.setTitle("RBD   value = {0}".format(1000))

            try:           
                s = mainFrame.openSubFrame()
            except a.NoObject:
                mainFrame = a.openMainFrame()
                s = mainFrame.openSubFrame()

            s.loadImage(imgCalibration)
            s.hideToolButtons()
            s.setColorMode("RB")
            s.setContrast(1,-1) 
            s.setTitle("calibration   number of pulses = {0}".format(1))

            mainFrame.waitForClose() 
            
            
        return (result,imgList)

    def liveview(self,exptime = 1, nimages = 1, expperiod = None, subframe = None):
        """
        Expose a series of images and display in viewer window.

        Args:

            exptime: Exposure time in seconds.
            nimages: Number of images to expose. If nimage > 1 expperiod should be set to a value different form None
            expperiod: Time in seconds between two successive exposures (nimage > 1 otherwise no effect).
                       Default is exptime + deadtime if set to None
            subframe: DSubFrame
        """

        frames = [subframe]
        lastImage = [None]

        tStart = [time.time()]
        def tElapsed():
            return 1000*(time.time() - tStart[0])

        def callback(img):
            if tElapsed() > 200 or lastImage[0] is None:
                if frames[0] is None:
                    m,s = albula.display(img)
                    frames[0] = s
                else:
                    frames[0].loadImage(img)
                lastImage[0] = None
                tStart[0] = time.time()
            else:
                lastImage[0] = img

        self.exposeCallback(callback,exptime,nimages,expperiod,mode = "expo",timeout = -1)

        if not lastImage[0] is None:
            frames[0].loadImage(lastImage[0])

        return frames[0]

    def updateBadpix(self):
        """
        If run locally on a camserver computer, compute new and update bad pixel mask.
        Returns:
            New DImage containing the bad pixel mask.
        """

        img = self.expose(exptime = 0.1)[0]
        width = img.width()
        height = img.height()
        bitmask = self.__maskInterchip(img,interchip = 4) # bits = [gap,defective,interchip,undefined,...,undefined]
        bitmaskInv =  bitmask.createMask(0,0,inverse = True).data()
        hotpixelMask = ( img.createMask(-1,1).data() &  bitmaskInv ) * 2
        nHotpixels = numpy.count_nonzero(hotpixelMask)
        calibration, nBadpixels = self.__calibrationTest(bitmask)
        print "# bad pixels (calibration): {0}".format(nBadpixels)
        print "# hot pixels: {0}".format(nHotpixels)
        if nBadpixels > 0 or nHotpixels > 0:
            calibrationMask = ( numpy.array( calibration.data() != 0 , dtype = 'int32') & bitmaskInv ) * 2
            newMask = bitmask.data() | calibrationMask | hotpixelMask

            # mask interchip pixels
            interchipMask = bitmask.data() & 4
            interchipPixels = interchipMask.nonzero()
            for y,x in zip(interchipPixels[0],interchipPixels[1]):
                if y+1 < height and x+1 < width and interchipMask[y,x+1] != 0  and interchipMask[y+1,x] != 0: # cross point of 4 chips
                    #
                    # if any of the 4 neighbour real pixels of
                    # a cross point virtual pixel is defective the virtual pixel is defective as well
                    #
                    #                 |                      |
                    #      ----------------------------------------------
                    #                 | defective (virtual)  | defective (real)
                    #      ==============================================
                    #                 | defective (virtual)  | defective (virtual)
                    #      ==============================================
                    #                 |                      |
                    #
                    if (2 & (newMask[y-1,x-1] | newMask[y-1,x+1] | newMask[y+1,x-1] | newMask[y+1,x+1])) != 0:
                        newMask[y,x] = 2
                elif x+1 < width and x > 1 and interchipMask[y,x+1] == 0 and (2 & (newMask[y,x-1] | newMask[y,x+1])) != 0:
                    newMask[y,x] = 2
                elif y+1 < height and y > 1 and  interchipMask[y+1,x] == 0 and (2 & (newMask[y-1,x] | newMask[y+1,x])) != 0:
                    newMask[y,x] = 2


            gapMask = (newMask & 1) != 0
            defectiveMask = (newMask & 2) != 0
            newMask.fill(0)
            newMask[defectiveMask | gapMask] = 1

            newMask = albula.DImage(newMask, dataType = "int32")

            if self.__isLocal:
                print "Warning: replacing badpix_mask.tif by new bad pixel mask"
                badPixPath = '/home/det/p2_det/config/calibration/Mask/'
                if not os.path.exists(badPixPath):
                    sys.stderr("Error: {0} does not exist".format(badPixPath))
                    sys.stderr.flush()
                    return newMask
                pathToOld = os.path.join(badPixPath,'badpix_mask.tif')
                backup = 'badpix_mask_until{0}.tif'.format(time.strftime('%d%m%y'))
                # personal comment: the guy who defined the order day, month, year is an idiot
                pathToBackup = os.path.join(badPixPath,backup)
                if os.path.exists(pathToOld):
                    print "Renaming {0} to {1}".format(pathToOld,pathToBackup)
                    shutil.copyfile(pathToOld,pathToBackup)
                    readmePath = os.path.join(badPixPath,'README')
                    if not os.path.exists(readmePath):
                        with open(readmePath,'w') as f:
                            f.write("  Mask File{0}# bad pixels\n\n".format(' '*(10 + len('badpix_mask_untilDDMMYY.tif')-len('Mask File'))))
                    with open(readmePath,'a') as f:
                        img = albula.readImage(pathToBackup)
                        below, nBadPixels, above = img.numberOfPixelsInInterval(1,1)
                        f.write("  {0}{1}{2}\n".format(backup,' '*10,nBadPixels))
                print "Writing bad pixel mask to {0}".format(pathToOld)
                albula.DImageWriter.write(newMask,pathToOld)
                    


            return newMask
        else:
            print "No new bad or hot pixels where detected"
            return self.__maskInterchip(img,interchip = 0)

    def __openSocket(self, host, timeout):
        self.__socket = None
        for addrFam, socketType, proto, canonName, socketAddr in socket.getaddrinfo(host, self.__port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            try:
                self.__socket = socket.socket(addrFam, socketType, proto)
            except socket.error, msg:
                self.__socket = None
                continue
            try:
                self.__socket.settimeout(0.1)
                self.__socket.connect(socketAddr)
                timeWaited = 0
                while True:
                    self.__socket.sendall("imgmode x\n")
                    answer = self.__socket.recv(self.__socketBufferSize)
                    if (answer.find("access denied")>=0):
                        if timeWaited < timeout:
                            timeWaited += 1
                            time.sleep(1)
                        else:
                            self.__socket.close()
                            self.__socket = None
                            return None
                    else:
                        break
            except socket.error, msg:
                self.__socket.close()
                self.__socket = None
                continue
            break

    def __readImage(self, fileName, timeout = 5000):
        """Try reading image from fileName in self.__clientPath and subdirectories up to maximum depth (self.__maxSearchDepth)
        Remove fileName afterwards
        Params:
            fileName: name of file
            readModules: read modules into NeXus header
            timeout: Timeout in ms
        Returns:
            DImageInt
        Raises:
            dectris.albula.DRuntimeException if timeout
        """


        tbegin = time.time()
        def timeRemain():
            return timeout - 1000*(time.time() - tbegin)

        condition = threading.Condition()
        img = []
        pathToFile = []
        finish = [False]
        def finished():
            with condition:
                return finish[0]
        def readImage(path):
            while not finished() and timeRemain() > 0:
                try:
                    imgPrivate = albula.readImage(path, timeout = 10)
                except albula.DTimeoutException:
                    continue
                else:
                    condition.acquire()
                    if not finish[0]:
                        img.append(imgPrivate)
                        pathToFile.append(path)
                        finish[0] = True
                        condition.notify()
                    condition.release()

        subDirs = [[self.__clientPath]]
        for i in range(0,self.__maxSearchDepth):
            subDirs.append([ os.path.join(d0,d1)  for d0 in subDirs[-1] for d1 in os.listdir(d0) if os.path.isdir(os.path.join(d0,d1))])
        subDirs = list(itertools.chain(*subDirs))

        threads = [ threading.Thread(target = readImage, args = [os.path.join(d,fileName)]) for d in subDirs ]
        for t in threads:
            t.start()

        def aborted():
            with self.__abortCondition:
                return self.__abort
        with condition:
            while timeRemain() > 0:
                if aborted():
                    #print "Operation aborted"
                    raise albula.DRuntimeException("Aborted")
                elif finish[0]:
                    self.__clientPath = os.path.dirname(pathToFile[0])
                    #print "Found {0} in {1} after {2} ms".format(fileName,self.__clientPath,int(timeout-timeRemain()))
                    os.remove(pathToFile[0])
                    self.__maxSearchDepth = 0
                    return img[0]
                else:
                    condition.wait(timeRemain()*0.001)
            if not finish[0]:
                #print "Waiting for {0} timed out after {1} ms".format(fileName,timeout-timeRemain())
                raise albula.DRuntimeException("Timeout")
                
        #while not self.__abort and not finish[0] and timeRemain() > 0:
            #condition.wait(timeRemain()*0.001)
        #if not finish[0]:
            #print "Waiting for {0} timed out after {1} ms".format(fileName,timeout-timeRemain())
            #ret = None
        #else:
            #self.__clientPath = os.path.dirname(pathToFile[0])
            #print "Found {0} in {1} after {2} ms".format(fileName,self.__clientPath,int(timeout-timeRemain()))
            #os.remove(pathToFile[0])
            #self.__maxSearchDepth = 0
            #ret = img[0]
        #condition.release()
        #if ret is None:
            #raise albula.DRuntimeException("Timeout Error")
        #return ret

    def __socketRecv(self, timeout = None):
        self.__socket.settimeout(timeout)
        try:
            answer = self.__socket.recv(self.__socketBufferSize)
        except socket.timeout:
            answer = None
        except Exception as e:
            answer = None
            self.__socket.settimeout(None)
            raise e
        self.__socket.settimeout(None)
        return answer


    def __maskInterchip(self, img, interchip):
        """mask out interchip pixels
        Params:
           img: DImage with optionalData() set
           interchip: pixel value set to interchip pixels
        Returns:
           DImage
        """
        modules = img.optionalData().modules()
        mask = img.optionalData().pixel_mask()
        maskInterChip = albula.DImage(mask,0)
        for m in modules:
            modWidth = m.geometry().width()
            modHeight = m.geometry().height()
            for c in range(m.numberOfChips()):
                rAbs = m.absoluteChipGeometry(c)
                rRel = m.chip(c)
                if rRel.right() < modWidth:
                    maskInterChip[rAbs.right(), rAbs.top():rAbs.bottom()] = 1  
                if rRel.bottom() < modHeight:
                    maskInterChip[rAbs.left():rAbs.right(), rAbs.bottom()] = 1
                if rRel.right() < modWidth and rRel.bottom() < modHeight:  
                    maskInterChip[rAbs.right(), rAbs.bottom()] = interchip
        maskFill = mask.createMask(0,0,inverse = False) + maskInterChip.createMask(0,0,inverse=True)
        maskReturn = albula.DImage(mask,0)
        maskReturn.fill(interchip, mask = maskFill)
        maskReturn += mask
        return maskReturn


    def __rbdTest(self, mask):
        """
        Set all pixel values to 1000 and read them back. 
        Params:
            camera: DCamera object
            mask: mask with interchip pixels masked out
        Returns:
            (DImageInt, # pixels different from 1000)
        """
        
        rbdValue = 1000
        
        imgRbd = self.rbd()
    
        below, inside, above = imgRbd.numberOfPixelsInInterval(rbdValue,rbdValue,None,mask)
        return (imgRbd,below+above)
        
    def __calibrationTest(self,mask):
        """
        Take a series of 10 images (IMG_i) with 1 pulse. Check the following 
        condition:
           \Pi_{i=0}^{9} (IMG_i - 1)_{m,n} MASK_{inv}_{m,n} = 0 (1)
        for all 0 <= m < width and 0 <= n < height.
        MASK_{inv} is the inverse mask i.e. 0 for masked pixels and 1 else. Condition (1) 
        asserts no cosmic events lead to a false positive result. 
        Params:
            camera: DCamera object
            mask: mask with interchip pixels masked out
        Returns:
            (DImageInt, # pixels different from 1)
        """
        
        numberOfPulses = 1
        imgCalibrationList = [ self.calibration(numberOfPulses) for i in range(10) ]
        
        maskInverse = mask.createMask(0,0,True)
        imgMult = albula.DImage(imgCalibrationList[0],1)
        for img in imgCalibrationList:
            imgMult *= (img - numberOfPulses) * maskInverse
        below, inside, above = imgMult.numberOfPixelsInInterval(0,0,None,mask)
        return (imgMult,below+above)
    


