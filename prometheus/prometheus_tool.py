#! /usr/bin/env python

# Copyright (c) 2015 Dave McCoy (dave.mccoy@cospandesign.com)
#
# Nysa is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# any later version.
#
# Nysa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Nysa; If not, see <http://www.gnu.org/licenses/>.


import sys
import os
import argparse

from array import array as Array

#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

NAME = os.path.basename(os.path.realpath(__file__))

DESCRIPTION = "\n" \
              "\n" \
              "usage: %s [options]\n" % NAME

EPILOG = "\n" \
         "\n" \
         "Examples:\n" \
         "\tSomething\n" \
         "\n"

MCU_BINARY_PATH = os.path.join(os.path.dirname(__file__), "board", "prometheus.img")
FPGA_BINARY_PATH = os.path.join(os.path.dirname(__file__), "board", "top.bit")

from fx3.prometheus_usb import PrometheusUSB

class PrometheusManager(object):
    def __init__(self, mcu_binary_path, fpga_binary_path):
        self.mcu_binary_path = mcu_binary_path
        self.fpga_binary_path = fpga_binary_path
        self.fx3 = PrometheusUSB()

    def check_connection(self):
        if self.fx3.is_attached():
            print "FX3 is connected, determining if it is programmed as Prometheus..."
            if self.fx3.is_prometheus_attached():
                print "FX3 is programmed as prometheus!"
            else:
                print "FX3 is not programmed as prometheus!"

    def reset_to_boot(self):
        self.fx3.vendor_reset()

    def program_mcu(self, path):
        f = open(path, 'r')
        mcu_binary = Array('B')
        mcu_binary.fromstring(f.read())
        f.close()
        self.fx3 = PrometheusUSB(self.usb_device_status_cb,
                                 self.device_to_host_comm)

        self.fx3.program_mcu(mcu_binary)

    def program_fpga(self, path):
        f = open(path, 'r')
        fpga_binary = Array('B')
        fpga_binary.fromstring(f.read())
        f.close()
        self.fx3.program_fpga(fpga_binary)

    def set_comm_mode(self):
        self.fx3.set_comm_mode()

    def is_comm_mode(self):
        print "In comm mode: %s" % str(self.fx3.prometheus_read_config())

    def is_boot_mode(self):
        if self.fx3.is_attached():
            if self.fx3.is_prometheus_attached():
                return False
            else:
                return True
        return False

    def read_gpios(self):
        return self.fx3.read_gpios()

    def write_gpios(self, gpios):
        self.fx3.write_gpios(gpios)

def main(argv):
    #Parse out the commandline arguments
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=DESCRIPTION,
        epilog=EPILOG
    )

    parser.add_argument("--reset",
                        action="store_true",
                        help="Enable Debug Messages")

    parser.add_argument("--fpga",
                        nargs='?',
                        help="Program FPGA with specified image")

    parser.add_argument("--mcuimage",
                        nargs='?',
                        help="Program MCU with specified image")

    parser.add_argument("-d", "--debug",
                        action="store_true",
                        help="Enable Debug Messages")

    parser.add_argument("--write",
                        action="store_true",
                        help="Write Test")
                        
    parser.add_argument("--gpios",
                        nargs='*',
                        default=[0],
                        help="Read/Write GPIOs")

    args = parser.parse_args()
    mcu_path = MCU_BINARY_PATH
    fpga_path = FPGA_BINARY_PATH

    if args.mcuimage is not None:
        mcu_path = args.mcuimage
        if args.debug: print "User Specified a custom MCU Path: %s" % mcu_path

    if args.fpga is not None:
        fpga_path = args.fpga
        if args.debug: print "User Specified a custom FPGA Path: %s" % fpga_path

    mcu_path = os.path.abspath(mcu_path)
    fpga_path = os.path.abspath(fpga_path)

    if not os.path.exists(mcu_path):
        print "MCU path does not exist: %s" % mcu_path
        sys.exit(1)

    if not os.path.exists(fpga_path):
        print "FPGA path does not exist: %s" % fpga_path
        sys.exit(1)


    #pm = PrometheusManager(mcu_path, fpga_path)
    #pm.check_connection()
    prometheus = PrometheusUSB(args.debug)

    if args.debug:
        print "Is Connected:            %s" % str(prometheus.is_attached())
        print "Is Boot Connected:       %s" % str(prometheus.is_boot_attached())
        print "Is Prometheus Connected: %s" % str(prometheus.is_prometheus_attached())

    if not prometheus.is_attached():
        print "Neither Prometheus or Boot device is attached!"
        sys.exit(1)

    if args.reset:
        if args.debug: print "Reset to Boot Mode"
        prometheus.reset_to_boot_mode()
        sys.exit(0)

    if args.mcuimage is not None:
        prometheus.program_mcu(mcu_path)

    if args.fpga is not None:
        prometheus.program_fpga(args.fpga)

    sys.exit(0)

    '''
    if len(args.gpios) == 0:
        print "GPIOs with no input specified!"
        v = pm.read_gpios()
        print "GPIOS: 0x%02X" % pm.read_gpios()
        sys.exit(0)
    elif args.gpios[0] != 0:
        gpios = int(args.gpios[0], 16)
        print "User specified: 0x%02X" % gpios
        pm.write_gpios(gpios)
        sys.exit(0)

    '''

if __name__ == "__main__":
    main(sys.argv)


