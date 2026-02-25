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


### Args
`api` (pigpio handle or str 'smbus')
- pigpio handle is value returned from pigpio.pi()
- If not 'smbus' then `api` is assumed to be a valid pigpio handle (not validity checked)

`i2c_bus_num` (int 0 or 1, default 1)
- Bus 1 is the typical user I2C bus
- Bus 0 is often reserved for comm with HAT boards, but may be used as well
- `i2c_bus_num` is not validity checked


### Returns
- pi_i2c handle associated with I2C comm using the specified api and bus
    """

    def __init__(self, api, i2c_bus_num=1):
        global i2c_msg
        self.api =                  api
        self.i2c_bus_num =          i2c_bus_num
        
        sda = BUS0_I2C_SDA_GPIO  if self.i2c_bus_num == 0  else BUS1_I2C_SDA_GPIO
        scl = BUS0_I2C_SCL_GPIO  if self.i2c_bus_num == 0  else BUS1_I2C_SCL_GPIO
        self.i2c_device_handles =   {}

        if self.api == 'smbus':
            pitools_logger.debug (f"Set up <smbus> mode for i2c_bus_num <{self.i2c_bus_num}>")
            from smbus2.smbus2 import SMBus, i2c_msg
            self.smbus_handle = SMBus(self.i2c_bus_num)
            pass
        else:   # pigpio API
            pitools_logger.debug (f"Set up <pigpio> mode for i2c_bus_num <{self.i2c_bus_num}>")
            import pigpio
            self.api.set_mode(sda, pigpio.ALT0)                 # set pins to I2C mode
            self.api.set_mode(scl, pigpio.ALT0)


        # i2c_write_byte_data HTU21D


    #=====================================================================================
    #=====================================================================================
    #  i 2 c _ w r i t e _ d e v i c e 1
    #=====================================================================================
    #=====================================================================================

    def i2c_write_device (self, addr, bytes_list):
        """
## i2c_write_device (addr, bytes_list) - Write a list of bytes to the target

***pi_i2c class member function***


### Args
`addr` (int)
- i2c address of target - range 0x00 to 0x7F
- No validity checks - caller should confirm adder validity

`bytes_list` (list of bytes)
- Data to be written to the device
- Minimal data validity checking - some invalid data results in write failure
- Commonly, the first byte in the list is taken as a register address to which the following bytes are written;
however, this behavior is device type specific


### Returns
- Raises ValueError if bytes_list is not a list or is an empty list.
- On success, returns length of `bytes_list`
- On fail, raises exception
        """

        # ADC121C, MCP23008, SHT3x

        if not isinstance(bytes_list, list)  or  len(bytes_list) == 0:
            raise ValueError (f"Illegal bytes_list received: <{bytes_list}>")
        if pitools_logger.isEnabledFor(logging.DEBUG):
            pitools_logger.debug (f"Using api <{self.api}> write bus <{self.i2c_bus_num}> addr <0x{addr:0>2x}> data <{bytes_to_str(bytes_list)}>")
        if self.api == 'smbus':
            b0 = bytes_list[0]
            b1plus = bytes_list[1:]
            self.smbus_handle.write_i2c_block_data(addr, b0, b1plus)    # returns None
            return len(bytes_list)
        else:   # pigpio API
            i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
            xx = self.api.i2c_write_device(i2c_device_handle, bytes_list)
            if xx < 0:
                raise OSError (f"i2c_write_device failed - error code <{xx}>")
            return len(bytes_list)
            # i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
            # try:
            #     xx = self.api.i2c_write_device(i2c_device_handle, bytes_list)
            # except Exception as e:
            #     raise OSError (f"i2c_write_device failed (pigpio exception: {type(e).__name__}: {e})")
            # if xx < 0:
            #     raise OSError (f"i2c_write_device failed - error code <{xx}>")
            # return len(bytes_list)


    #=====================================================================================
    #=====================================================================================
    #  i 2 c _ r e a d _ d e v i c e  2
    #=====================================================================================
    #=====================================================================================
        # ADC121C, HTU21D, SHT3x

    def i2c_read_device (self, addr, read_byte_count):
        """
## i2c_read_device (addr, read_byte_count) - Read a number of bytes from the target

***pi_i2c class member function***


### Args
`addr` (int)
- i2c address of target - range 0x00 to 0x7F
- No validity checks - caller should confirm adder validity

`read_byte_count` (int)
- Number of bytes to read from the target
- No validity checking


### Returns
- On success, returns tuple (actual read count, [data])
- On failure, any exception raised by the smbus or pigpio api must be caught by the calling code
- If using pigpio.i2c_read_device(), if the returned byte count is negative this error code is passed within a raised OSError exception
        """
        if pitools_logger.isEnabledFor(logging.DEBUG):
            pitools_logger.debug (f"Using api <{self.api}> read bus <{self.i2c_bus_num}> addr <0x{addr:0>2x}> read_byte_count <{read_byte_count}>")
        if self.api == 'smbus':
            msg = i2c_msg.read(addr, read_byte_count)
            self.smbus_handle.i2c_rdwr(msg)
            return read_byte_count, list(msg)
        else:   # pigpio API
            i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
            count, data = self.api.i2c_read_device(i2c_device_handle, read_byte_count)
            if count < 0:
                raise OSError (f"i2c_read_device failed - error code <{count}>")
            return count, list(data)
            # except Exception as e:
            #     raise OSError (f"i2c_read_device failed (pigpio exception: {type(e).__name__}: {e})")
            # if count < 0:
            #     raise OSError (f"i2c_read_device failed - error code <{count}>")
            # return count, data


            # i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
            # try:
            #     count, data = self.api.i2c_read_device(i2c_device_handle, read_byte_count)
            #     # if count < 0:
            #     #     raise OSError (f"i2c_read_device failed - error code <{count}>")
            #     # return count, data
            # except Exception as e:
            #     raise OSError (f"i2c_read_device failed (pigpio exception: {type(e).__name__}: {e})")
            # if count < 0:
            #     raise OSError (f"i2c_read_device failed - error code <{count}>")
            # return count, data


    #=====================================================================================
    #=====================================================================================
    #  i2c_read_i2c_block_data 3
    #=====================================================================================
    #=====================================================================================

    # MCP23008

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


    #=====================================================================================
    #=====================================================================================
    #  i 2 c _ w r i t e _ b y t e 4
    #=====================================================================================
    #=====================================================================================

    def i2c_write_byte (self, addr, byte_value):
        """
## i2c_write_byte (addr, byte_value) - Write one byte to the target

***pi_i2c class member function***


### Args
`addr` (int)
- i2c address of target - range 0x00 to 0x7F
- No validity checks - caller should confirm adder validity

`byte_value` (int)
- Data to be written to the device
- The value is check to be an int the range of 0x00 to 0xFF


### Returns
- Raises ValueError if byte_value is not an int in the range of 0x00 to 0xFF
- On write success, returns 1 (one byte written)
- On write fail, raises exception
        """
        # HTU21D, PCA9548

        if not isinstance(byte_value, int)  or  byte_value < 0x00  or  byte_value > 0xFF:
            raise ValueError (f"Illegal byte_value received: <{byte_value}>")
        if pitools_logger.isEnabledFor(logging.DEBUG):
            pitools_logger.debug (f"Using api <{self.api}> write bus <{self.i2c_bus_num}> addr <0x{addr:0>2x}> data <{bytes_to_str(byte_value)}>")

        if self.api == 'smbus':
            rslt = self.smbus_handle.write_byte(addr, byte_value)
        else:   # pigpio API
            i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
            rslt = self.api.i2c_write_byte(i2c_device_handle, byte_value)
            if rslt < 0:
                raise OSError (f"i2c_write_device failed - error code <{rslt}>")
        return 1


        # try:
        #     if self.api == 'smbus':
        #         rslt = self.smbus_handle.write_byte(addr, byte_value)
        #     else:   # pigpio API
        #         i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
        #         rslt = self.api.i2c_write_byte(i2c_device_handle, byte_value)
        # except Exception as e:
        #     pitools_logger.warning (f"i2c_write_byte failed\n  {type(e).__name__}: {e}")
        #     return I2C_ERROR
        # return rslt



    #=====================================================================================
    #=====================================================================================
    #  i 2 c _ r e a d _ b y t e  5
    #=====================================================================================
    #=====================================================================================

    def i2c_read_byte (self, addr):
        """
## i2c_read_byte (addr) - Read one byte from the target

***pi_i2c class member function***


### Args
`addr` (int)
- i2c address of target - range 0x00 to 0x7F
- No validity checks - caller should confirm addr validity


### Returns
- On read success, returns one byte read from the target
- On read fail, raises exception
        """

        # PcA9548

        if pitools_logger.isEnabledFor(logging.DEBUG):
            pitools_logger.debug (f"Using api <{self.api}> read 1 byte from bus <{self.i2c_bus_num}> addr <0x{addr:0>2x}>")

        if self.api == 'smbus':
            byte_value = self.smbus_handle.read_byte(addr)
        else:   # pigpio API
            i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
            byte_value = self.api.i2c_read_byte(i2c_device_handle)

        # try:
        #     if self.api == 'smbus':
        #         byte_value = self.smbus_handle.read_byte(addr)
        #     else:   # pigpio API
        #         i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
        #         byte_value = self.api.i2c_read_byte(i2c_device_handle)
        # except Exception as e:
        #     pitools_logger.warning (f"i2c_read_byte failed\n  {type(e).__name__}: {e}")
        #     return I2C_ERROR

        if pitools_logger.isEnabledFor(logging.DEBUG):
            # pitools_logger.debug (f"i2c_read_byte from addr <0x{addr:0>2x}>:  <0x{byte_value:0>2x}>")
            pitools_logger.debug (f"i2c_read_byte from addr <0x{addr:0>2x}>:  <{bytes_to_str(byte_value)}>")
        return byte_value


    #=====================================================================================
    #=====================================================================================
    #  get_pigpio_i2c_device_handle
    #=====================================================================================
    #=====================================================================================

    def get_pigpio_i2c_device_handle (self, addr):     # int
        if not addr in self.i2c_device_handles:
            i2c_device_handle = self.i2c_device_handles[addr] = self.api.i2c_open(self.i2c_bus_num, addr)
            pitools_logger.debug (f"New i2c_device_handle: <{i2c_device_handle}> for addr <0x{addr:0>2x}>")
        else:
            i2c_device_handle = self.i2c_device_handles[addr]
            pitools_logger.debug (f"Got i2c_device_handle: <{i2c_device_handle}> for addr <0x{addr:0>2x}>")
        return i2c_device_handle


    #=====================================================================================
    #=====================================================================================
    #  close
    #=====================================================================================
    #=====================================================================================

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

def bytes_to_str(_bytes):
    # Expects one byte or list of bytes
    # Returns str hex representation
    # If can't convert, then return _bytes

    try:
        if isinstance(_bytes, int):
            return f"0x{_bytes:0>2x}"
        else:   # Must be list of bytes
            xx = '['
            for item in _bytes:
                xx += f" 0x{item:0>2x}"
            return xx + ' ]'
    except:
        return _bytes