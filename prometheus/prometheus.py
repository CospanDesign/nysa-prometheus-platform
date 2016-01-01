""" prometheus

Concrete interface for Nysa on the prometheus board
"""

__author__ = 'you@example.com'

import sys
import os
import time
from array import array as Array

from nysa.cbuilder.sdb import SDBError
from nysa.host.nysa import Nysa
from nysa.host.nysa import NysaError
from nysa.host.nysa import NysaCommError

from fx3.prometheus_usb import PrometheusUSB
from fx3.prometheus_usb import USB_STATUS

class Prometheus(Nysa):

    def __init__(self, dev_dict, status = None):
        Nysa.__init__(self, status)
        self.dev_dict = dev_dict
        self.configuration = None
        self.usb_status = USB_DEVICE_NOT_CONNECTED
        self.fx3 = PrometheusUSB(self.usb_device_status_cb,
                                 self.device_to_host_comm)

    def device_to_host_comm(self, name, level, text):
        #self.status(0, "Data from: %s: %s" % (name, text0))
        self.s.Info("Callback from Device: %s, %s" % name, text)

    def usb_device_status_cb(self, status):
        #print "USB Main Callback"
        #self.status(0, "USB Device CB: %d" % status)
        if status == USB_STATUS.BOOT_FX3_CONNECTED:
            if self.usb_status != USB_DEVICE_CONNECTED:
                self.usb_status = USB_DEVICE_CONNECTED
                self.s.Info("USB Device Connected")

        elif status == USB_STATUS.DEVICE_NOT_CONNECTED:
            if self.usb_status != USB_DEVICE_NOT_CONNECTED:
                self.usb_status = USB_DEVICE_NOT_CONNECTED
                self.s.Info("USB Device Not Connected")

        elif status == USB_STATUS.FX3_PROGRAMMING_FAILED:
            if self.usb_status != USB_FAILED:
                self.usb_status = USB_FAILED
                self.s.Info("USB Failed")

        elif status == USB_STATUS.FX3_PROGRAMMING_PASSED:
            if self.usb_status != USB_PROGRAMMED:
                self.usb_status = USB_PROGRAMMED
                self.s.Info("FX3 Programmed")

        elif status == USB_STATUS.BUSY:
            if self.usb_status != USB_BUSY:
                self.usb_status = USB_BUSY
                self.s.Info("USB Busy")

        elif status == USB_STATUS.USER_APPLICATION:
            if self.usb_status != USB_USER_APPLICATION:
                self.usb_status = USB_USER_APPLICATION
                self.s.Info("User Application??")

        elif status == USB_STATUS.PROMETHEUS_FX3_CONNECTED:
            if self.usb_status != USB_USER_PROMETHEUS_FX3_CONNECTED:
                self.usb_status = USB_USER_PROMETHEUS_FX3_CONNECTED
                self.s.Info("Prometheus FX3 Connected")

    def read(self, address, length = 1, disable_auto_inc = False):
        """read

        Generic read command used to read data from a Nysa image
        
        Args:
            length (int): Number of 32 bit words to read from the FPGA
            address (int):  Address of the register/memory to read
            disable_auto_inc (bool): if true, auto increment feature will be disabled

        Returns:
            (Array of unsigned bytes): A byte array containtin the raw data
                                     returned from Nysa

        Raises:
            NysaCommError: When a failure of communication is detected
        """
        raise AssertionError("%s not implemented" % sys._getframe().f_code.co_name)

    def write(self, address, data, disable_auto_inc = False):
        """write

        Generic write command usd to write data to a Nysa image
        
        Args:
            address (int): Address of the register/memory to read
            data (array of unsigned bytes): Array of raw bytes to send to the
                                           device
            disable_auto_inc (bool): if true, auto increment feature will be disabled
        Returns:
            Nothing

        Raises:
            AssertionError: This function must be overriden by a board specific
                implementation
        """
        raise AssertionError("%s not implemented" % sys._getframe().f_code.co_name)

    def ping(self):
        """ping

        Pings the Nysa image

        Args:
          Nothing

        Returns:
          Nothing

        Raises:
          NysaCommError: When a failure of communication is detected
        """
        raise AssertionError("%s not implemented" % sys._getframe().f_code.co_name)

    def reset(self):
        """reset

        Software reset the Nysa FPGA Master, this may not actually reset the
        entire FPGA image

        Args:
          Nothing

        Returns:
          Nothing

        Raises:
          NysaCommError: A failure of communication is detected
        """
        raise AssertionError("%s not implemented" % sys._getframe().f_code.co_name)

    def is_programmed(self):
        """
        Returns True if the FPGA is programmed

        Args:
            Nothing

        Returns (Boolean):
            True: FPGA is programmed
            False: FPGA is not programmed

        Raises:
            NysaCommError: A failure of communication is detected
        """
        raise AssertionError("%s not implemented" % sys._getframe().f_code.co_name)

    def get_sdb_base_address(self):
        """
        Return the base address of the SDB (This is platform specific)

        Args:
            Nothing

        Returns:
            32-bit unsigned integer of the address where the SDB can be read

        Raises:
            Nothing
        """
        return 0x00

    def wait_for_interrupts(self, wait_time = 1):
        """wait_for_interrupts

        listen for interrupts for the specified amount of time

        Args:
          wait_time (int): the amount of time in seconds to wait for an
                           interrupt

        Returns:
          (boolean):
            True: Interrupts were detected
            False: No interrupts detected

        Raises:
            NysaCommError: A failure of communication is detected
        """
        raise AssertionError("%s not implemented" % sys._getframe().f_code.co_name)

    def register_interrupt_callback(self, index, callback):
        """ register_interrupt

        Setup the thread to call the callback when an interrupt is detected

        Args:
            index (Integer): bit position of the device
                if the device is 1, then set index = 1
            callback: a function to call when an interrupt is detected

        Returns:
            Nothing

        Raises:
            Nothing
        """
        raise AssertionError("%s not implemented" % sys._getframe().f_code.co_name)

    def unregister_interrupt_callback(self, index, callback = None):
        """ unregister_interrupt_callback

        Removes an interrupt callback from the reader thread list

        Args:
            index (Integer): bit position of the associated device
                EX: if the device that will receive callbacks is 1, index = 1
            callback: a function to remove from the callback list

        Returns:
            Nothing

        Raises:
            Nothing (This function fails quietly if ther callback is not found)
        """
        raise AssertionError("%s not implemented" % sys._getframe().f_code.co_name)

    def get_board_name(self):
        return "prometheus"

    def upload(self, filepath):
        """
        Uploads an image to a board

        Args:
            filepath (String): path to the file to upload

        Returns:
            Nothing

        Raises:
            NysaError:
                Failed to upload data
            AssertionError:
                Not Implemented
        """

        raise AssertionError("%s not implemented" % sys._getframe().f_code.co_name)

    def program (self):
        """
        Initiate an FPGA program sequence, THIS DOES NOT UPLOAD AN IMAGE, use
        upload to upload an FPGA image

        Args:
            Nothing

        Returns:
            Nothing

        Raises:
            AssertionError:
                Not Implemented
        """
        raise AssertionError("%s not implemented" % sys._getframe().f_code.co_name)

    def ioctl(self, name, arg = None):
        """
        Platform specific functions to execute on a Nysa device implementation.

        For example a board may be capable of setting an external voltage or
        reading configuration data from an EEPROM. All these extra functions
        cannot be encompused in a generic driver

        Args:
            name (String): Name of the function to execute
            args (object): A generic object that can be used to pass an
                arbitrary or multiple arbitrary variables to the device

        Returns:
            (object) an object from the underlying function

        Raises:
            NysaError:
                An implementation specific error
        """

        raise AssertionError("%s not implemented" % sys._getframe().f_code.co_name)

    def list_ioctl(self):
        """
        Return a tuple of ioctl functions and argument types and descriptions
        in the following format:
            {
                [name, description, args_type_object],
                [name, description, args_type_object]
                ...
            }

        Args:
            Nothing

        Raises:
            AssertionError:
                Not Implemented

        """
        raise AssertionError("%s not implemented" % sys._getframe().f_code.co_name)


