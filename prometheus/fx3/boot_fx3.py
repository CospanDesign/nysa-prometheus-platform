# -*- coding: UTF-8 -*-

#Distributed under the MIT licesnse.
#Copyright (c) 2013 Dave McCoy (dave.mccoy@cospandesign.com)

#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import sys
import os
import time
from array import array as Array
import usb.core
import usb.util

from usb_device import USBDeviceError
from usb_device import USBDevice


sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir))

from defines import CYPRESS_VID
from defines import FX3_PID


class BootFX3Error(Exception):
    pass

class BootFX3(USBDevice):
    def __init__(self):
        super(BootFX3, self).__init__()
        self.dev = None
        self.vid = CYPRESS_VID
        self.pid = FX3_PID

    def download(self, buf):
        """
        Download code to the FX3

        Arg:
            (Array Unsigned Bytes) An Array of unsigned bytes from the input
            file

        Returns:
            Nothing

        Raises:
            BootFX3Error with a description of the error
        """
        pos = 0
        cyp_id = "%c%c" % (buf[0], buf[1])
        image_cntrl = buf[2]
        image_type = buf[3]
        pos = 4
        checksum = 0
        program_entry = 0x00


        print "cyp id: %s" % cyp_id
        if cyp_id != "CY":
            raise BootFX3Error("Image file does not start with Cypress ID: %s" % cpy_id)
        print "Image Control: 0x%X" % image_cntrl
        if image_cntrl & 0x01 != 0:
            raise BootFX3Error("Image Control Byte bit 0 != 1, thie file does not contain executable code")
        print "Image Type: 0x%X" % image_type
        if image_type != 0xB0:
            raise BootFX3Error("Not a normal FW Binary with Checksum")

        while True:
            size = (buf[pos + 3] << 24) + (buf[pos + 2] << 16) + (buf[pos + 1] << 8) + buf[pos]
            pos += 4
            address = (buf[pos + 3] << 24) + (buf[pos + 2] << 16) + (buf[pos + 1] << 8) + buf[pos]
            pos += 4

            if size > 0:
                #print "size: 0x%X" % size
                #print "address: 0x%X" % address
                data = buf[pos: (pos + size * 4)]
                self.write_program_data(address, data)
                for i in range(0, (size * 4), 4):
                    checksum += ((data[i + 3] << 24) + (data[i + 2] << 16) + (data[i + 1] << 8) + (data[i]))
                    checksum = checksum & 0xFFFFFFFF
                pos += (size * 4)
            else:
                #print "Starting address: 0x%X" % address
                program_entry = address
                break


        read_checksum = (buf[pos + 3] << 24) + (buf[pos + 2] << 16) + (buf[pos + 1] << 8) + buf[pos]
        #print "Checksum from file: 0x%X" % read_checksum
        #print "Checksum from calculation: 0x%X" % checksum
        if read_checksum != checksum:
            raise BootFX3Error("Checksum from file != Checksum from Data: 0x%X != 0x%X" % (read_checksum, checksum))

        time.sleep(1)
        
        #Set the program entry point
        print "Sending Reset"
        try:
            write_len = self.dev.ctrl_transfer(
                    bmRequestType = 0x40,                 #VRequest, To the devce, Endpoint
                    bRequest = 0xA0,                      #Vendor Specific
                    wValue = program_entry & 0x0000FFFF,  #Entry point of the program
                    wIndex = program_entry >> 16,
                    #data_or_wLength = 0,                  #No Data
                    timeout = 1000)                       #Timeout = 1 second
        except usb.core.USBError, err:
            pass

    def write_program_data(self, address, data):
        print "Write data to the device"
        start_address = address
        buf = Array('B', [])

        index = 0
        #Size is maximum of 4096
        finished = False
        write_len = 0
        while True:
            if len(data[index:]) > 4096:
                buf = data[index: index+ 4096]
            else:
                buf = data[index:]

            print "Writing: %d bytes to address: 0x%X" % (len(buf), address)
            try:
                write_len = self.dev.ctrl_transfer(
                    bmRequestType = 0x40,            #VRequest, to device, endpoint
                    bRequest = 0xA0,                 #Vendor Spcific write command
                    wValue = 0x0000FFFF & address,   #Addr Low 16-bit value
                    wIndex = address >> 16,          #Addr High 16-bit value
                    data_or_wLength = buf.tostring(),              #Data
                    timeout = 1000)                                #Timeout 1 second
            except usb.core.USBError, err:
                pass

            #Check if there was an error in the transfer
            if write_len != len(buf):
                raise BootFX3Error("Write Size != Length of buffer")

            #Update the index
            index += write_len
            address += write_len

            #Check if we wrote all the data out
            if index >= len(data):
                #We're done
                print "Sent: %d bytes to address %d" % (len(data), start_address)
                break

    def reset_to_boot(self):
        print "Do not reset the board when it is already in boot mode"
        pass
