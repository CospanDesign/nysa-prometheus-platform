#! /usr/bin/python

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
import signal
import socket
import threading
import select
import re

from defines import *
#from pyudev.pyqt4 import MonitorObserver

import usb.core
import usb.util

from array import array as Array

sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir))

from usb_device import USBDeviceError
from usb_device import USBDevice


SLEEP_COUNT = 2

def enum(*sequential, **named):
  enums = dict(zip(sequential, range(len(sequential))), **named)
  return type('Enum', (), enums)

class PrometheusUSBError(Exception):
    def __init__(self, data):
        if type(data) is str:
            super (PrometheusUSBError, self).__init__(data)
        if type(data) is usb.core.USBError:
            err = ""
            if data.errno == 110:
                err = "Device timed out"
            elif (data.errno == 6) or (data.errno == 16):
                err = "Device is disconnected"
            else:
                err = "Unknown error number: %d" % str(err)

class PrometheusUSBWarning(Exception):
    pass

class PrometheusUSB(object):
    """
    Class to handle communication between the processor and host computer
    """

    def __init__(self, debug = False):
        super (PrometheusUSB, self).__init__()
        self.debug = debug
        self.usb_lock = threading.Lock()
        self.dev = None
        #One Second
        self.timeout = 1000

    def is_attached(self):
        if self.is_prometheus_attached() or self.is_boot_attached():
            return True
        return False

    def is_boot_attached(self):
        return usb.core.find(idVendor = CYPRESS_VID, idProduct=BOOT_PID) is not None

    def is_prometheus_attached(self):
        return usb.core.find(idVendor = CYPRESS_VID, idProduct=PROMETHEUS_PID) is not None

    def connect_to_prometheus(self):
        if self.dev is not None:
            if self.dev.manufacture == CYPRESS_VID and self.dev.idProduct == PROMETHEUS_PID:
                return
            self.disconnect()
        self.dev = usb.core.find(idVendor = CYPRESS_VID, idProduct=PROMETHEUS_PID)
        if self.dev is None:
            raise PrometheusUSBError("Prometheus USB Not Found!")
        if self.dev:
            if self.debug: print "connected to promtheus"

    def connect_to_boot(self):
        if self.dev is not None:
            if self.dev.idVendor == CYPRESS_VID and self.dev.idProduct == BOOT_PID:
                return
            self.disconnect()

        self.dev = usb.core.find(idVendor = CYPRESS_VID, idProduct=BOOT_PID)
        if self.dev:
            if self.debug: print "connected to boot device"

    def _is_boot_connected(self):
        if self.dev is None:
            return False
        if self.dev.idVendor == CYPRESS_VID and self.dev.idProduct == BOOT_PID:
            return True
        return False

    def _is_prometheus_connected(self):
        if self.dev is None:
            return False
        if self.dev.idVendor == CYPRESS_VID and self.dev.idProduct == PROMETHEUS_PID:
            return True
        return False

    def _write_mcu_config(self, address, data = Array('B')):
        if self._is_boot_connected():
            raise PrometheusUSBError("MCU is in boot state, cannot set configuration data")
        with self.usb_lock:
            try:
                self.dev.ctrl_transfer(
                    bmRequestType   =   0x40,
                    bRequest        =   address,
                    wValue          =   0x00,
                    wIndex          =   0x00,
                    data_or_wLength =   data,
                    timeout         =   self.timeout)
            except usb.core.USBError, err:
                raise PrometheusUSBError(err)

    def _read_mcu_config(self, address, length = 1):
        data = None
        with self.usb_lock:
            try:
                data = self.dev.ctrl_transfer(
                    bmRequestType   =   0xC0, #Read
                    bRequest        =   address,
                    wValue          =   0x00,
                    wIndex          =   0x00,
                    data_or_wLength =   length,
                    timeout         =   self.timeout)
            except usb.core.USBError, err:
                raise PrometheusUSBError(err)

    def disconnect(self):
        if self.dev is not None:
            usb.util.dispose_resources(self.dev)
            self.dev = None

    def reset_to_boot_mode(self):
        if self.is_prometheus_attached():
            self.connect_to_prometheus()
            self._write_mcu_config(CMD_RESET_TO_BOOTMODE)
        self.disconnect()

    def program_fpga(self, filepath):
        if not self.is_prometheus_attached():
            raise PrometheusUSBError("Prometheus is not attached")
        self.connect_to_prometheus()

        f = open(filepath, 'r')
        buf = Array('B')
        buf.fromstring(f.read())
        f.close()

        max_size = 512
        length = len(buf)
        flength = float(length)
        length_buf = Array('B', [0, 0, 0, 0])
        length_buf[3] = (length >> 24)  & 0xFF
        length_buf[2] = (length >> 16)  & 0xFF
        length_buf[1] = (length >> 8)   & 0xFF
        length_buf[0] = (length)        & 0xFF
        if self.debug: print "FPGA Image size: 0x%08X (%d)" % (length, length)
        self._write_mcu_config(CMD_ENTER_FPGA_CONFIG_MODE, length_buf.tostring())
        if self.debug: print "Wait for a moment..."
        time.sleep(0.1)
        count = 0
        while len(buf) > max_size:
            block = buf[:max_size]
            try:
                self.dev.write(0x02, block, timeout = self.timeout)
            except usb.core.USBError, err:
                raise PrometheusUSBError(err)
            if self.debug: sys.stdout.write("\r%%% 3.1f" % (100 * count / flength))
            if self.debug: sys.stdout.flush()


            buf = buf[max_size:]
            count += max_size

        if len(buf) > 0:
            try:
                self.dev.write(0x02, buf, timeout = self.timeout)
            except usb.core.USBError, err:
                raise PrometheusUSBError(err)

        if self.debug: sys.stdout.write("\r%%% 3.1f" % (100 * count / flength))
        if self.debug: sys.stdout.flush()
        if self.debug: print ""

    def program_mcu(self, filepath):
        if self.is_attached():
            if self.is_prometheus_attached():
                if self.debug: print "Prometheus attached, issuing reset to boot command..."
                self.reset_to_boot_mode()
                print "Was in FX3 Mode, change to boot mode..."
                time.sleep(2)
        self.connect_to_boot()
        if not self._is_boot_connected():
            d = usb.core.show_devices()
            raise PrometheusUSBError("BUG: pyusb doesn't re-enumerate very well so re-run this script to program MCU")
        f = open(filepath, 'r')
        buf = Array('B')
        buf.fromstring(f.read())
        f.close()

        pos = 0
        cyp_id = "%c%c" % (buf[0], buf[1])
        image_cntrl = buf[2]
        image_type = buf[3]
        length = float(len(buf[4:]))
        pos = 4
        checksum = 0
        program_entry = 0x00
        if cyp_id != "CY": raise PrometheusUSBError("Image File does not start with Cypress ID: 'CY': %s" % str(buf[0:1]))
        if image_cntrl & 0x01 != 0: raise PrometheusUSBError("Image Control Byte bit 0 != 1, this file is not an executable")
        if image_type != 0xB0: raise PrometheusUSBError("Not a normal FW Binary with Checksum")

        while True:
            size = (buf[pos + 3] << 24) + (buf[pos + 2] << 16) + (buf[pos + 1] << 8) + buf[pos]
            pos += 4
            address = (buf[pos + 3] << 24) + (buf[pos + 2] << 16) + (buf[pos + 1] << 8) + buf[pos]
            pos += 4

            if size > 0:
                data = buf[pos: (pos + size * 4)]
                self._write_program_data(address, data)
                for i in range(0, (size * 4), 4):
                    checksum += ((data[i + 3] << 24) + (data[i + 2] << 16) + (data[i + 1] << 8) + (data[i]))
                    checksum = checksum & 0xFFFFFFFF
                pos += (size * 4)
            else:
                program_entry = address
                break


            if self.debug: sys.stdout.write("\r%%% 3.1f" % (100 * pos / length))
            if self.debug: sys.stdout.flush()


        if self.debug: print ""
        read_checksum = (buf[pos + 3] << 24) + (buf[pos + 2] << 16) + (buf[pos + 1] << 8) + buf[pos]
        if read_checksum != checksum:
            raise PrometheusUSBError("Checksum from file != Checksum from Data: 0x%X != 0x%X" % (read_checksum, checksum))
        time.sleep(1)
        if self.debug: print "Sending Reset"
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
        self.disconnect()

    def _write_program_data(self, address, data):
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

            #if self.debug: print "Writing: %d bytes to address: 0x%X" % (len(buf), address)
            try:
                write_len = self.dev.ctrl_transfer(
                    bmRequestType   = 0x40,                     #VRequest, to device, endpoint
                    bRequest        = 0xA0,                     #Vendor Spcific write command
                    wValue          = 0x0000FFFF & address,     #Addr Low 16-bit value
                    wIndex          = address >> 16,            #Addr High 16-bit value
                    data_or_wLength = buf.tostring(),           #Data
                    timeout         = 1000)                     #Timeout 1 second
            except usb.core.USBError, err:
                raise PrometheusUSBError("Error while programming MCU: %s" % str(err))

            #Check if there was an error in the transfer
            if write_len != len(buf):
                raise PrometheusUSBError("Write Size != Length of buffer: %d != %d" % (write_len, len(buf)))

            #Update the index
            index += write_len
            address += write_len

            #Check if we wrote all the data out
            if index >= len(data):
                #We're done
                #if self.debug: print "Sent: %d bytes to address %d" % (len(data), start_address)
                break

    def set_comm_mode(self):
        pass

'''
    def set_comm_mode(self):
        if self.prometheus_fx3.is_attached():
            self.prometheus_fx3.set_fpga_comm_mode()

    def host_to_device_comm(self, text):
        if self.prometheus_fx3:
            self.prometheus_fx3.host_to_device_comm(text)

    def device_to_host_comm(self, name, level, text):
        self.device_to_host_comm_cb(name, level, text)

    #Prometheus USB Functions
    def prometheus_read_config(self, address = CMD_INTERNAL_CONFIG, length = 1):
        return self.prometheus_fx3.read_mcu_config(address, length)

    def prometheus_write_config(self, address = CMD_INTERNAL_CONFIG, data = []):
        self.prometheus_fx3.write_mcu_config(address, data)

    def prometheus_start_debug(self):
        self.prometheus_fx3.write_mcu_config(address = CMD_START_DEBUG, data = [0])
        self.prometheus_fx3.start_read_logger_listener()

    def prometheus_set_reg_en_to_output(self):
        self.prometheus_fx3.write_mcu_config(address = CMD_USB_SET_REG_EN_TO_OUT, data = [0])

    def enable_regulator(self, enable):
        if enable:
            self.prometheus_fx3.write_mcu_config(address = CMD_USB_ENABLE_REGULATOR, data = [0])
        else:
            self.prometheus_fx3.write_mcu_config(address = CMD_USB_DISABLE_REGULATOR, data = [0])

    def prometheus_ping(self):
        self.prometheus_fx3.ping()

    def prometheus_write(self, data = [0]):
        address = 0
        self.prometheus_fx3.write(address, data)

    def prometheus_read(self, length):
        address = 0
        self.prometheus_fx3.read(address, length)

    def enable_fpga_reset(self, enable):
        gpios = self.read_gpios()

    def read_gpios(self):
        return self.prometheus_fx3.read_gpios()

    def write_gpios(self, gpios):
        self.prometheus_fx3.write_gpios(gpios)

    #Shutdown Server
    def shutdown(self):
        if self.cypress_fx3_dev is not None:
            self.cypress_fx3_dev.reset()
            self.cypress_fx3_dev = None
        if self.prometheus_fx3:
            self.prometheus_fx3.shutdown()

'''
