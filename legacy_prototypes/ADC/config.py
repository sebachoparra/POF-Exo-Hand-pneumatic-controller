# /*****************************************************************************
# * | File        :	  config.py
# * | Author      :   Waveshare team
# * | Function    :   Hardware underlying interface
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2020-12-12
# * | Info        :   
# ******************************************************************************/
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


#! /usr/bin/python3
import os
import sys
import time
import spidev
import gpiozero

class RaspberryPi:
    # Pin definition
    RST_PIN     = 13
    CS_PIN      = 26
    DRDY_PIN    = 19

    def __init__(self):
        # SPI device, bus = 0, device = 0
        self.SPI = spidev.SpiDev(0, 0)

        self.outputpins = {
            self.RST_PIN: gpiozero.OutputDevice(self.RST_PIN),
            self.CS_PIN: gpiozero.OutputDevice(self.CS_PIN)
        }

        self.inputpins = {
            self.DRDY_PIN: gpiozero.InputDevice(self.DRDY_PIN, pull_up = True)
        }

    def digital_write(self, pin, value):
        if pin in self.outputpins:
            if value:
                self.outputpins[pin].on()  # Enciende el pin
            else:
                self.outputpins[pin].off()  # Apaga el pin

    def digital_read(self, pin):
        if pin in self.inputpins:
            return self.inputpins[pin].is_active

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.writebytes(data)
        
    def spi_readbytes(self, reg):
        return self.SPI.readbytes(reg)
        
    def module_init(self):
        self.SPI.max_speed_hz = 2000000
        self.SPI.mode = 0b01
        return 0;

    def module_exit(self):
        self.SPI.close()
        self.outputpins[self.RST_PIN].off()  # Apagar el pin RST
        self.outputpins[self.CS_PIN].off()   # Apagar el pin CS
        
hostname = os.popen("uname -n").read().strip()

implementation = RaspberryPi()

for func in [x for x in dir(implementation) if not x.startswith('_')]:
    setattr(sys.modules[__name__], func, getattr(implementation, func))
