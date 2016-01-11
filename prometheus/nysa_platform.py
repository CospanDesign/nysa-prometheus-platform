#Distributed under the MIT licesnse.
#Copyright (c) 2014 Dave McCoy (dave.mccoy@cospandesign.com)

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

"""
Prometheus Interface
"""
__author__ = 'dave.mccoy@cospandesign.com (Dave McCoy)'

import sys
import os
import glob
import json
import hashlib
from array import array as Array


from nysa.host.nysa_platform import Platform
from nysa.ibuilder.lib.xilinx_utils import find_xilinx_path
from prometheus import Prometheus

from fx3.prometheus_usb import PrometheusUSB
from fx3.prometheus_usb import USB_STATUS

MCU_BINARY_PATH = os.path.join(os.path.dirname(__file__), "board", "prometheus.img") 

class PrometheusPlatform(Platform):
    def __init__(self, status = None):
        super (PrometheusPlatform, self).__init__(status)
        self.vendor = 0x0403
        self.product = 0x8530

    def get_type(self):
        if self.status: self.status.Verbose("Returnig 'prometheus' type")
        return "prometheus"

    def scan(self):
        """
        Nysa will call this function when the user wants to scan for the
        platform specific boards

        Args:
            Nothing


        Returns:
            Dictionary of prometheus instances, where the key is the serial number
            or unique identifier of a board

        Raises:
            NysaError: An error occured when scanning for devices
        """

        self.dev_dict = {}

        self.usb_status = USB_STATUS.DEVICE_NOT_CONNECTED
        self.fx3 = PrometheusUSB(self.usb_device_status_cb,
                                 self.device_to_host_comm)

        if self.fx3.is_connected():
            print "FX3 is connected, determining if it is programmed as Prometheus..."
            if self.fx3.is_prometheus_connected():
                print "FX3 is programmed as prometheus!"
            else:
                print "Attempting to program prometheus board"
                f = open(MCU_BINARY_PATH, 'r')
                mcu_binary = Array('B')
                print "Length of mcu_binary path: %d" % len(mcu_binary)
                mcu_binary.fromstring(f.read())
                print"Binary Length: %d" % len(mcu_binary)
                f.close()
                self.fx3.program_mcu(mcu_binary)
                if self.fx3.is_prometheus_connected():
                    print "FX3 is programmed as prometheus!"
                else:
                    print "FX3 is not programmed as prometheus!"

        return self.dev_dict

    def test_build_tools(self):
        """
        Runs a test to determine if the Vendor specific build tools are present

        Args:
            Nothing

        Returns:
            Boolean:
                True: Build tools found
                False: Build tools not found

        Raises:
            NysaError: An error occured when scanning for the build tools
        """
        if find_xilinx_path() is None:
            return False
        return True

    def device_to_host_comm(self, name, level, text):
        self.status.Info("Callback from Device: %s, %s" % (name, text))

    def usb_device_status_cb(self, status):
        if status == USB_STATUS.BOOT_FX3_CONNECTED:
            self.usb_status = USB_STATUS.BOOT_FX3_CONNECTED
            self.status.Info("USB Device Connected")

        elif status == USB_STATUS.DEVICE_NOT_CONNECTED:
            self.usb_status = USB_STATUS.DEVICE_NOT_CONNECTED
            self.status.Info("USB Device Not Connected")

        elif status == USB_STATUS.FX3_PROGRAMMING_FAILED:
            self.usb_status = USB_STATUS.FX3_PROGRAMMING_FAILED
            self.status.Info("USB Failed")

        elif status == USB_STATUS.FX3_PROGRAMMING_PASSED:
            self.usb_status = USB_STATUS.FX3_PROGRAMMING_PASSED
            self.status.Info("FX3 Programmed")

        elif status == USB_STATUS.BUSY:
            self.usb_status = USB_STATUS.BUSY
            self.status.Info("USB Busy")

        elif status == USB_STATUS.USER_APPLICATION:
            self.usb_status = USB_STATUS.USER_APPLICATION
            self.status.Info("User Application??")

        elif status == USB_STATUS.PROMETHEUS_FX3_CONNECTED:
            self.usb_status = USB_STATUS.PROMETHEUS_FX3_CONNECTED
            self.status.Info("Prometheus FX3 Connected")


