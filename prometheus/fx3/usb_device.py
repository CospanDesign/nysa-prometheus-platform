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


import usb
import threading
from defines import CMD_RESET_TO_BOOTMODE


class USBDeviceListenThread(threading.Thread):
    """
    Launch off a thread that periodically reads the USB device at the given
    Configuraiton, interface, and endpoint.

    A timeout is put in place. If there is new data available the callback will
    be called with the new data.

    I'm not sure if the user can write while a read is going on??? Check this
    out
    """
    def __init__(self,
                 dev,
                 server,
                 configuration = 0,
                 interface = 0,
                 endpoint = 0,
                 length = 1024,
                 timeout = 100,
                 callback = None):

        super(ListenThread, self).__init__()
        self.dev = dev
        self.server = server
        self.configuration = 0
        self.interface = 0
        self.endpoint = 0
        self.timeout = timeout
        self.length = length
        self.callback = callback
        self.listeners = []
        self.ready = True


        #Set all this stuff up here so that any failures will be in the main
        #thread
        self.dev.set_configuration(self.configuration)
        self.dev.set_alt_setting(self.interface)

    def run(self):
        while self.ready:
            data = self.dev.read(self.interface, self.endpoint, self.length, self.timeout)
            if len (data) is not 0:
                self.callback(data)

    def kill(self):
        self.ready = False

class USBDeviceError (Exception):
    pass

class USBDevice (object):

    def __init__(self, name, vid, pid):
        super (USBDevice, self).__init__()
        self.vid = vid
        self.pid = pid
        self.name = name
        self.dev = None

        self.timer = None
        self.timeout = .5
        self.listeners = []

        self.usb_lock = threading.Lock()

    def reset_to_boot(self):
        """
        Send a Cypress Specific 'Reset to default command to put the USB back
        into a programmable configuration with vendor ID/Product ID

        04B4:00BC

        Args:
            Nothing

        Returns:
            Nothing

        Raises:
            USBDeviceError:
                -Device is not even connected
            USBError
                -Underlying USB Error
        """
        if self.dev is None:
            raise USBDeviceError("Device is None")
        try:
            self.dev.ctrl_transfer(
                bmRequestType = 0x40,   #VRequest, To the devce, Endpoint
                bRequest      = CMD_RESET_TO_BOOTMODE,   #Reset
                wValue        = 0x00,
                wIndex        = 0x00,
                timeout       = 1000)   #Timeout    = 1 second
            self.release()
        except usb.core.USBError, err:
            if err.errno == 110:
                raise USBDeviceError("110 Errror")
                return
            if err.errno == 5:
                raise USBDeviceError("Error 5: Device was disconnected")
            if err.errno == 16:
                raise USBDeviceError("Error 16: Device was disconnected")
            else:
                raise USBDeviceError("Unknown USB Error: %s" % str(err))

    def get_device_info(self):
        """
        Returns a string representation of the USB Configuration
        """
        num_configs = self.dev.bNumConfigurations
        print "Number of Configurations: %d" % num_configs

    def get_vid(self):
        return self.vid

    def get_pid(self):
        return self.pid

    def on_release(self):
        pass

    def release(self):
        """
        Deterministically release any reference to this device, if the reference
        is already released then just return

        Args:
            Nothing

        Returns:
            Nothing

        Raises:
            Nothing
        """
        if self.dev is None:
            return

        usb.util.dispose_resources(self.dev)
        self.dev = None
        #usb.util.release_interface(self.dev)
        self.on_release()
        self.remove_all_listeners()

    def on_connect(self):
        pass

    def connect(self):
        """
        Attempt to connect to the device specified by devices vendor and
        product id is the vendor id or the product id is 0 then raise an
        exception.

        If the device is not found an error is raised to the user

        Args:
            Nothing

        Returns:
            Nothing

        Raises:
            USBDeviceError:
                -Vendor ID or Product ID is 0
                -Device was not found
            USBError
                -Underlying USB Error
        """
        if self.vid == 0x0000 or self.pid == 0x0000:
            raise USBDeviceError("VID and or PID must not be 0: %04X:%04X" % (self.vid, self.pid))

        self.dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)

        if self.dev is None:
            raise USBDeviceError("USB Device: %04X:%04X is not connected" % (self.vid, self.pid))
        self.on_connect()

    def set_timeout(self, timeout):
        self.timeout = timeout

    def add_listener(self, callback):
        print "Add a listener"
        if callback not in self.listeners:
            print "Adding %s to listener list" % str(callback)
            self.listeners.append(callback)

        if self.timer is None:
            print "Timer Thread not running, starting timer thread"
            self.timer = threading.Timer(self.timeout, self.listen_callback)
            self.timer.start()

    def remove_all_listeners(self):
        self.listeners = []
        if self.timer is not None:
            self.timer.cancel()

    def remove_listener(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def shutdown(self):
        self.remove_all_listeners()

    def listen_callback(self):
        #print "timer callback"
        if len(self.listeners) == 0:
            if isinstance(self.timer, threading.Timer):
                self.timer.cancel()
            self.timer = None
            return

        for callback in self.listeners:
            with self.usb_lock:
                callback()

        if len(self.listeners) > 0:
        #    #This is ugly but I'm not sure how to do this outside of pyside
            self.timer = threading.Timer(self.timeout, self.listen_callback)
            self.timer.start()




