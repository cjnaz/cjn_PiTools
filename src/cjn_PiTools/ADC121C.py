#!/usr/bin/env python3
"""ADC121C* library for Raspberry Pi
"""
#==========================================================
#
#  Chris Nelson, Copyright 2026
#
#==========================================================

import time
import logging

CONVERSION_RSLT_REG_PTR =   0x00
CONFIG_REG_PTR =            0x02
I2C_ERROR =                 -256
ADC121_ADDRS =              [0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59]


adc121c_logger = logging.getLogger('cjn_PiTools.ADC121C')
# adc121c_logger.setLevel(logging.WARNING)             # Set default logging level for this module

# I2C operation
# The first data byte of every write operation is stored in the address pointer register.
# This value selects the register that the following data bytes will be written to or read from.
# Write a register send sequence:
#   1) ADC address, write Address Pointer Register byte, write 1 or 2 bytes of target register data (same sequence)
# Read a register send sequence:
#   If the (address) pointer is preset correctly, a read operation can occur without writing the address pointer register.
#   1) ADC address, write Address Pointer Register byte
#   2) ADC address, read 1 or 2 byte register data

class ADC121C:

    def __init__(self, device_name, device_addr, pi_i2c_bus_handle, Vref, ntrys=2, retry_wait=0):
        self.device_name =          device_name
        self.device_addr =          device_addr
        self.pi_i2c_bus_handle =    pi_i2c_bus_handle
        self.Vref =                 Vref
        self.ntrys =                ntrys
        self.retry_wait =           retry_wait

        if self.device_addr not in ADC121_ADDRS:
            raise ValueError (f"ADC121 device address must be in range of 0x50 to 0x59.  Received <0x{device_addr:0>2x}>")

        ADC121C.initialize(self)        # Use base class implementation when this class is inherited

        api = 'smbus'  if self.pi_i2c_bus_handle.api == 'smbus'  else 'pigpio'
        adc121c_logger.debug (f"<{self.device_name}> New ADC121C device defined at addr <0x{self.device_addr:0>2x}> using api <{api}> on i2c bus <{self.pi_i2c_bus_handle.i2c_bus_num}>")


    def initialize(self):
        try:
            # All disabled:  Auto conversion mode, Alert Hold, Alert Flag, Alert Pin
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [CONFIG_REG_PTR, 0b00000000])
            # Set read register to the Conversion Result register.  self.read() assumes this.
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [CONVERSION_RSLT_REG_PTR])
        except:
            adc121c_logger.debug (f"Initialize of <{self.device_name}> failed")
            return I2C_ERROR
        adc121c_logger.debug (f"Initialize of <{self.device_name}> success")
        return 0


    def read(self):
        for trynum in range(self.ntrys):
            try:
                (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 2)
                rslt = (((data[0] & 0x0f) << 8) | (data[1] & 0xff)) / 4096 * self.Vref
                adc121c_logger.debug (f"Conversion result <{self.device_name}>:  (0x{data[0]:0>2x} 0x{data[1]:0>2x}) = {rslt:5.3f} V")
                return rslt
            except:
                adc121c_logger.debug (f"Read  try# {trynum} FAILED <{self.device_name}>")
            if trynum < self.ntrys - 1:
                time.sleep(self.retry_wait)
            else:
                adc121c_logger.warning (f"Read  FAILED <{self.device_name}>")
                return I2C_ERROR

