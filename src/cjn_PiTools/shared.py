#!/usr/bin/env python3
"""Shared functions library for cjn_PiTools
"""

#==========================================================
#
#  Chris Nelson, Copyright 2026
# TODO
#   SHT3x doc, check alignment to datasheet names
#   HDU21D driver, tests
#   Retry loop
#   
#==========================================================

import importlib.metadata
__version__ = importlib.metadata.version(__package__ or __name__)

import math
import logging
# from pathlib import Path


# Configs / Constants
BUS0_I2C_SDA_GPIO = 0
BUS0_I2C_SCL_GPIO = 1
BUS1_I2C_SDA_GPIO = 2
BUS1_I2C_SCL_GPIO = 3

I2C_ERROR =         -256

logging.getLogger('cjn_PiTools').setLevel(logging.WARNING)  # Set default log level for all cjn_PiTools modules
pitools_logger = logging.getLogger('cjn_PiTools.shared')


#=====================================================================================
#=====================================================================================
#  C l a s s   pi_i2c
#=====================================================================================
#=====================================================================================

class pi_i2c:
    """
## Class pi_i2c - Support both smbus and pigpio APIs for I2C

device_name, pio_handle, i2c_handle
        pio_handle is from pigpio.pi()
        i2c_handle is from pio.i2c_open()


i2c_write_device ( i2c_handle, list of bytes )
i2c_write_byte(self.i2c_device, READ_USER_REG)
i2c_write_byte_data(self.i2c_device, WRITE_USER_REG, value)

i2c_read_device(self.i2c_device, num bytes to read)
    returns count, data
i2c_read_byte(self.resource_i2c_handle)
    return byte
i2c_read_i2c_block_data (handle, reg, count)
    returns count, data

-------------------------
### Parameters
`driver_mode` ('GPIO' or pigpio handle)
- As listed in /sys/bus/w1/devices/, eg '28-0b228004203c'

`device_name` (str, default 'DS18B20')
- User friendly name for the sensor

### Class variables

`device_id` (str)
- device_id from sensor instantiation

`device_name` (str, default 'DS18B20')
- device_name from sensor instantiation

`sensor_path` (Path)
- full pathlib path to the sensor directory

`bus_master_path` (Path)
- full pathlib path the w1 bus master for the sensor

Returns
    Return valid data on success
    Raise exceptions on failure

    The caller must have call these within a try - except block

    """
    def __init__(self, api, i2c_bus_num=1):
        global i2c_msg
        self.api =              api         # 'smbus' or a a pigpio.pi() handle
        self.i2c_bus_num =          i2c_bus_num     # int 0, 1, ...  default 1
        
        sda = BUS0_I2C_SDA_GPIO  if self.i2c_bus_num == 0  else BUS1_I2C_SDA_GPIO
        scl = BUS0_I2C_SCL_GPIO  if self.i2c_bus_num == 0  else BUS1_I2C_SCL_GPIO
        # self.device_name =      device_name           # TODO bus name
        self.i2c_device_handles =      {}

        if self.api == 'smbus':
            pitools_logger.debug (f"Set up <smbus> mode for i2c_bus_num <{self.i2c_bus_num}>")
            # import smbus2 as smbus
            from smbus2.smbus2 import SMBus, i2c_msg
            self.smbus_handle = SMBus(self.i2c_bus_num)                              # TODO implement i2c_lock??
            pass
        else:   # pigpio API
            pitools_logger.debug (f"Set up <pigpio> mode for i2c_bus_num <{self.i2c_bus_num}>")
            import pigpio
            self.api.set_mode(sda, pigpio.ALT0)                             # set pins to I2C mode
            self.api.set_mode(scl, pigpio.ALT0)


    def i2c_write_device (self, addr, bytes_list):
        if self.api == 'smbus':
            b0 = bytes_list[0]
            b1plus = bytes_list[1:]
            self.smbus_handle.write_i2c_block_data(addr, b0, b1plus)
            return len(bytes_list)
        else:   # pigpio API
            i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
            try:
                xx = self.api.i2c_write_device(i2c_device_handle, bytes_list)
            except Exception as e:
                raise OSError (f"i2c_write_device failed (pigpio exception: {type(e).__name__}: {e})")
            if xx < 0:
                raise OSError (f"i2c_write_device failed - error code <{xx}>")
            return xx


    def i2c_read_device (self, addr, read_byte_count):
        if self.api == 'smbus':
            msg = i2c_msg.read(addr, read_byte_count)
            self.smbus_handle.i2c_rdwr(msg)
            return read_byte_count, list(msg)
        else:   # pigpio API
            i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
            try:
                count, data = self.api.i2c_read_device(i2c_device_handle, read_byte_count)
                # if count < 0:
                #     raise OSError (f"i2c_read_device failed - error code <{count}>")
                # return count, data
            except Exception as e:
                raise OSError (f"i2c_read_device failed (pigpio exception: {type(e).__name__}: {e})")
            if count < 0:
                raise OSError (f"i2c_read_device failed - error code <{count}>")
            return count, data


    def i2c_read_i2c_block_data (self, addr, reg, read_byte_count):
        if self.api == 'smbus':
            msg = i2c_msg.read(addr, read_byte_count)
            self.smbus_handle.i2c_rdwr(msg)
            return read_byte_count, list(msg)
        else:   # pigpio API
            i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
            try:
                count, data = self.api.i2c_read_i2c_block_data(i2c_device_handle, reg, read_byte_count)
                # if count < 0:
                #     raise OSError (f"i2c_read_device failed - error code <{count}>")
                # return count, data
            except Exception as e:
                raise OSError (f"i2c_read_i2c_block_data failed (pigpio exception: {type(e).__name__}: {e})")
            if count < 0:
                raise OSError (f"i2c_read_i2c_block_data failed - error code <{count}>")
            return count, data


    def i2c_write_byte (self, addr, byte_value):
        try:
            if self.api == 'smbus':
                self.smbus_handle.write_byte(addr, byte_value)
            else:   # pigpio API
                i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
                self.api.i2c_write_byte(i2c_device_handle, byte_value)
        except Exception as e:
            pitools_logger.warning (f"i2c_write_byte failed\n  {type(e).__name__}: {e}")
            return I2C_ERROR
        return 0

        pitools_logger.debug (f"i2c_write_byte to addr <0x{addr:0>2x}>:  <0x{byte_value:0>2x}>")


    def i2c_read_byte (self, addr):
        try:
            if self.api == 'smbus':
                byte_value = self.smbus_handle.read_byte(addr)
            else:   # pigpio API
                i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
                byte_value = self.api.i2c_read_byte(i2c_device_handle)
        except Exception as e:
            pitools_logger.warning (f"i2c_read_byte failed\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        pitools_logger.debug (f"i2c_read_byte from addr <0x{addr:0>2x}>:  <0x{byte_value:0>2x}>")
        return byte_value


    def get_pigpio_i2c_device_handle (self, addr):     # int
        if not addr in self.i2c_device_handles:
            i2c_device_handle = self.i2c_device_handles[addr] = self.api.i2c_open(self.i2c_bus_num, addr)
            pitools_logger.debug (f"New i2c_device_handle: <{i2c_device_handle}> for addr <0x{addr:0>2x}>")
        else:
            i2c_device_handle = self.i2c_device_handles[addr]
            pitools_logger.debug (f"Got i2c_device_handle: <{i2c_device_handle}> for addr <0x{addr:0>2x}>")
        return i2c_device_handle


    def close(self):
        # pigpio handle owned/closed outside of this module
        if self.api == 'smbus':
            pitools_logger.debug (f"smbus_handle closed")
            self.smbus_handle.close()
        else:   # pigpio API
            for addr in self.i2c_device_handles:
                i2c_device_handle = self.i2c_device_handles[addr]
                pitools_logger.debug (f"Closing i2c_device_handle <{i2c_device_handle}>")
                self.api.i2c_close(i2c_device_handle)

    # def close_smbus(self):
    #     self.smbus_handle.close()


def CtoF(tempC):
    return tempC*1.8 +32.0


def FtoC(tempF):
    return (tempF -32.0) / 1.8


def calculate_dew_point(T_c, RH):
    # Magnus formula constants
    a = 17.62
    b = 243.12

    # Calculate gamma
    gamma = (a * T_c) / (b + T_c) + math.log(RH / 100.0)

    # Calculate dew point in Celsius
    dew_point_c = (b * gamma) / (a - gamma)
    return dew_point_c
