#!/usr/bin/env python3
"""Shared functions library for cjn_PiTools
"""

#==========================================================
#
#  Chris Nelson, Copyright 2026
#
#==========================================================

import importlib.metadata
__version__ = importlib.metadata.version(__package__ or __name__)

import math
import logging

# Configs / Constants
BUS0_I2C_SDA_GPIO = 0
BUS0_I2C_SCL_GPIO = 1
BUS1_I2C_SDA_GPIO = 2
BUS1_I2C_SCL_GPIO = 3

I2C_ERROR =         -256
CRC_ERROR =         -255

logging.getLogger('cjn_PiTools').setLevel(logging.WARNING)  # Set default log level for all cjn_PiTools modules
shared_logger = logging.getLogger('cjn_PiTools.shared')


#=====================================================================================
#=====================================================================================
#  C l a s s   p i _ i 2 c
#=====================================================================================
#=====================================================================================

class pi_i2c:
    """
## Class pi_i2c (api, i2c_bus_num=1) - Get a pi_i2c handle for the specified I2C bus and api

Supports both smbus and pigpio I2C APIs


### Args
`api` (pigpio handle or str 'smbus')
- A pigpio handle is returned from `pigpio.pi()`
- If not 'smbus' then `api` is assumed to be a valid pigpio handle (not validity checked)

`i2c_bus_num` (int 0 or 1, default 1)
- Bus 1 is the typical user I2C bus
- Bus 0 is often reserved for comm with HAT boards, but may be used as well
- `i2c_bus_num` is not validity checked


### Returns
- pi_i2c handle for I2C communication using the specified api and bus
    """

    def __init__(self, api, i2c_bus_num=1):
        global i2c_msg
        self.api =                  api
        self.i2c_bus_num =          i2c_bus_num
        
        sda = BUS0_I2C_SDA_GPIO  if self.i2c_bus_num == 0  else BUS1_I2C_SDA_GPIO
        scl = BUS0_I2C_SCL_GPIO  if self.i2c_bus_num == 0  else BUS1_I2C_SCL_GPIO
        self.i2c_device_handles =   {}

        if self.api == 'smbus':
            shared_logger.debug (f"Set up <smbus> mode for i2c_bus_num <{self.i2c_bus_num}>")
            from smbus2.smbus2 import SMBus, i2c_msg
            self.smbus_handle = SMBus(self.i2c_bus_num)
            pass
        else:   # pigpio API
            shared_logger.debug (f"Set up <pigpio> mode for i2c_bus_num <{self.i2c_bus_num}>")
            import pigpio
            self.api.set_mode(sda, pigpio.ALT0)                 # set pins to I2C mode
            self.api.set_mode(scl, pigpio.ALT0)


    #=====================================================================================
    #=====================================================================================
    #  i 2 c _ w r i t e _ d e v i c e
    #=====================================================================================
    #=====================================================================================

    def i2c_write_device (self, addr, bytes_list):
        """
## i2c_write_device (addr, bytes_list) - Write a list of bytes to the target device

***pi_i2c class member function***


### Args
`addr` (int)
- i2c address of target device - range 0x00 to 0x7F
- No validity checks - the caller should confirm address validity

`bytes_list` (list of bytes)
- Data to be written to the target device, e.g., `[0x05, 0xFF]`
- Minimal data validity checking - some invalid data results in write failure


### Returns
- On success, returns number of bytes written (length of `bytes_list`)
- Raises ValueError if `bytes_list` is not a list or is an empty list.
- On fail, raises exception (actually raised by underlying `api` call, e.g., I2C IO error, or invalid data in `bytes_list`)


### Behaviors and rules
- Commonly, the first byte in the `bytes_list` is taken as a register address to which the following bytes are written. 
  Note that this behavior is device-type specific.  The contents of `bytes_list` will simply be sent out after 
  the device at `addr` has been addressed for writing.
- Uses pigpio i2c_write_device() and smbus write_i2c_block_data()
        """

        if not isinstance(bytes_list, list)  or  len(bytes_list) == 0:
            raise ValueError (f"Illegal bytes_list received: <{bytes_list}>")
        if shared_logger.isEnabledFor(logging.DEBUG):
            shared_logger.debug (f"Using api <{self.api}> write bus <{self.i2c_bus_num}> addr <0x{addr:0>2x}> data <{_bytes_to_str(bytes_list)}>")
        if self.api == 'smbus':
            b0 = bytes_list[0]
            b1plus = bytes_list[1:]
            self.smbus_handle.write_i2c_block_data(addr, b0, b1plus)    # returns None
            return len(bytes_list)
        else:   # pigpio API
            i2c_device_handle = self._get_pigpio_i2c_device_handle(addr)
            xx = self.api.i2c_write_device(i2c_device_handle, bytes_list)
            if xx < 0:
                raise OSError (f"i2c_write_device failed - error code <{xx}>")
            return len(bytes_list)


    #=====================================================================================
    #=====================================================================================
    #  i 2 c _ r e a d _ d e v i c e
    #=====================================================================================
    #=====================================================================================

    def i2c_read_device (self, addr, read_byte_count):
        """
## i2c_read_device (addr, read_byte_count) - Read a number of bytes from the target device

***pi_i2c class member function***


### Args
`addr` (int)
- i2c address of target device - range 0x00 to 0x7F
- No validity checks - caller should confirm address validity

`read_byte_count` (int)
- Number of bytes to read from the target device
- No validity checking


### Returns
- On success, returns tuple (actual read count, [data]), e.g., `(3, [0x01, 0x02, 0x03])`
- On fail, raises exception (actually raised by underlying `api` call, e.g., I2C IO error, OSError, etc.).
- If using the pigpio api, if the returned byte count is negative this error code is passed within a raised OSError exception.


### Behaviors and rules
- Uses pigpio i2c_read_device() and smbus i2c_msg.read() / i2c_rdwr
        """

        if shared_logger.isEnabledFor(logging.DEBUG):
            shared_logger.debug (f"Using api <{self.api}> read bus <{self.i2c_bus_num}> addr <0x{addr:0>2x}> read_byte_count <{read_byte_count}>")
        if self.api == 'smbus':
            msg = i2c_msg.read(addr, read_byte_count)
            self.smbus_handle.i2c_rdwr(msg)
            return read_byte_count, list(msg)
        else:   # pigpio API
            i2c_device_handle = self._get_pigpio_i2c_device_handle(addr)
            count, data = self.api.i2c_read_device(i2c_device_handle, read_byte_count)
            if count < 0:
                raise OSError (f"i2c_read_device failed - error code <{count}>")
            return count, list(data)


    #=====================================================================================
    #=====================================================================================
    #  i 2 c _ w r i t e _ b y t e
    #=====================================================================================
    #=====================================================================================

    def i2c_write_byte (self, addr, byte_value):
        """
## i2c_write_byte (addr, byte_value) - Write one byte to the target device

***pi_i2c class member function***


### Args
`addr` (int)
- i2c address of target device - range 0x00 to 0x7F
- No validity checks - caller should confirm address validity

`byte_value` (int)
- Data to be written to the target device, e.g., `0x55`
- The value is check to be an int in the range of 0x00 to 0xFF


### Returns
- On success, returns 1 (meaning one byte written)
- Raises ValueError if `byte_value` is not an int in the range of 0x00 to 0xFF
- On fail, raises exception (actually raised by underlying `api` call, e.g., I2C IO error, OSError, etc.).


### Behaviors and rules
- Uses pigpio i2c_write_byte() and smbus write_byte()
        """

        if not isinstance(byte_value, int)  or  byte_value < 0x00  or  byte_value > 0xFF:
            raise ValueError (f"Illegal byte_value received: <{byte_value}>")
        if shared_logger.isEnabledFor(logging.DEBUG):
            shared_logger.debug (f"Using api <{self.api}> write bus <{self.i2c_bus_num}> addr <0x{addr:0>2x}> data <{_bytes_to_str(byte_value)}>")

        if self.api == 'smbus':
            rslt = self.smbus_handle.write_byte(addr, byte_value)
        else:   # pigpio API
            i2c_device_handle = self._get_pigpio_i2c_device_handle(addr)
            rslt = self.api.i2c_write_byte(i2c_device_handle, byte_value)
            if rslt < 0:
                raise OSError (f"i2c_write_device failed - error code <{rslt}>")
        return 1


    #=====================================================================================
    #=====================================================================================
    #  i 2 c _ r e a d _ b y t e
    #=====================================================================================
    #=====================================================================================

    def i2c_read_byte (self, addr):
        """
## i2c_read_byte (addr) - Read one byte from the target device

***pi_i2c class member function***


### Args
`addr` (int)
- i2c address of target device - range 0x00 to 0x7F
- No validity checks - caller should confirm address validity


### Returns
- On success, returns one byte read from the target device, e.g., `0xAA`
- On fail, raises exception (actually raised by underlying `api` call, e.g., I2C IO error, OSError, etc.).


### Behaviors and rules
- Uses pigpio i2c_read_byte() and smbus read_byte()
        """

        if shared_logger.isEnabledFor(logging.DEBUG):
            shared_logger.debug (f"Using api <{self.api}> read 1 byte from bus <{self.i2c_bus_num}> addr <0x{addr:0>2x}>")

        if self.api == 'smbus':
            byte_value = self.smbus_handle.read_byte(addr)
        else:   # pigpio API
            i2c_device_handle = self._get_pigpio_i2c_device_handle(addr)
            byte_value = self.api.i2c_read_byte(i2c_device_handle)

        if shared_logger.isEnabledFor(logging.DEBUG):
            shared_logger.debug (f"i2c_read_byte from addr <0x{addr:0>2x}>:  <{_bytes_to_str(byte_value)}>")
        return byte_value


    #=====================================================================================
    #=====================================================================================
    #  c l o s e
    #=====================================================================================
    #=====================================================================================

    def close(self):
        """
## close () - Close all connections associated with this pi_i2c handle

***pi_i2c class member function***


### Returns
- Returns 0


### Behaviors and rules
- If using pigpio, the pigpio handle (`pio = pigpio.pi()` in the above example) is owned by and must be stopped in the tool script code.
The pi_i2c.close() method only closes the allocated i2c device handles within the pigpio connection.
        """

        if self.api == 'smbus':
            shared_logger.debug (f"smbus_handle closed")
            self.smbus_handle.close()
        else:   # pigpio API
            for addr in self.i2c_device_handles:
                i2c_device_handle = self.i2c_device_handles[addr]
                shared_logger.debug (f"Closing i2c_device_handle <{i2c_device_handle}>")
                self.api.i2c_close(i2c_device_handle)
        return 0


    #=====================================================================================
    #=====================================================================================
    #  _ g e t _ p i g p i o _ i 2 c _ d e v i c e _ h a n d l e
    #=====================================================================================
    #=====================================================================================

    # Private method

    def _get_pigpio_i2c_device_handle (self, addr):
        """_get_pigpio_i2c_device_handle manages the allocation and reuse of pigpio i2c device handles
        """
        if not addr in self.i2c_device_handles:
            i2c_device_handle = self.i2c_device_handles[addr] = self.api.i2c_open(self.i2c_bus_num, addr)
            shared_logger.debug (f"New i2c_device_handle: <{i2c_device_handle}> for addr <0x{addr:0>2x}>")
        else:
            i2c_device_handle = self.i2c_device_handles[addr]
            shared_logger.debug (f"Got i2c_device_handle: <{i2c_device_handle}> for addr <0x{addr:0>2x}>")
        return i2c_device_handle


#=====================================================================================
#=====================================================================================
#  T e m p e r a t u r e   c o n v e r s i o n
#=====================================================================================
#=====================================================================================

def CtoF(tempC):
    """
## CtoF (tempC) - Convert temperature value in Celsius to Fahrenheit

### Arg
`tempC` (float)
- Temperature value in Celsius
- Value not validated

### Returns
- Returns float temperature value in Fahrenheit
    """
    return tempC*1.8 +32.0


def FtoC(tempF):
    """
## FtoC (tempF) - Convert temperature value in Fahrenheit to Celsius

### Arg
`tempF` (float)
- Temperature value in Fahrenheit
- Value not validated

### Returns
- Returns float temperature value in Celsius
    """
    return (tempF -32.0) / 1.8


def CtoK(tempC):
    """
## CtoK (tempC) - Convert temperature value in Celsius to Kelvin

### Arg
`tempC` (float)
- Temperature value in Celsius
- Value not validated

### Returns
- Returns float temperature value in Kelvin
    """
    return tempC + 273.15


def KtoC(tempK):
    """
## KtoC (tempK) - Convert temperature value in Kelvin to Celsius

### Arg
`tempK` (float)
- Temperature value in Kelvin
- Value not validated

### Returns
- Returns float temperature value in Celsius
    """
    return tempK - 273.15


def calculate_dew_point(tempC, RH):
    """
## calculate_dew_point (tempC, RH) - Calculate the dew point given tempC and relative humidity

Uses the Mangus formula - [Wikipedia](https://en.wikipedia.org/wiki/Dew_point)

### Arg
`tempC` (float)
- Temperature value in Celsius
- Value not validated

RH (float)
- Relative humidity in percent
- Value not validated

### Returns
- Returns dew point temperature value in Celsius.  Pass the returned temperature thru CtoF() if the dew
point in Fahrenheit is needed, e.g., `dp_f = CtoF(calculate_dew_point(22.6, 31.2))`
    """
    # Magnus formula constants
    a = 17.62
    b = 243.12

    # Calculate gamma
    gamma = (a * tempC) / (b + tempC) + math.log(RH / 100.0)

    # Calculate dew point in Celsius
    dew_point_c = (b * gamma) / (a - gamma)
    return dew_point_c


#=====================================================================================
#=====================================================================================
#  P r i v a t e   f u n c t i o n s
#=====================================================================================
#=====================================================================================

def _bytes_to_str(_bytes):
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
    

# Remnant
    #=====================================================================================
    #=====================================================================================
    #  i2c_read_i2c_block_data
    #=====================================================================================
    #=====================================================================================

    # def i2c_read_i2c_block_data (self, addr, reg, read_byte_count):
    #     if self.api == 'smbus':
    #         msg = i2c_msg.read(addr, read_byte_count)
    #         self.smbus_handle.i2c_rdwr(msg)
    #         return read_byte_count, list(msg)
    #     else:   # pigpio API
    #         i2c_device_handle = self.get_pigpio_i2c_device_handle(addr)
    #         try:
    #             count, data = self.api.i2c_read_i2c_block_data(i2c_device_handle, reg, read_byte_count)
    #             # if count < 0:
    #             #     raise OSError (f"i2c_read_device failed - error code <{count}>")
    #             # return count, data
    #         except Exception as e:
    #             raise OSError (f"i2c_read_i2c_block_data failed (pigpio exception: {type(e).__name__}: {e})")
    #         if count < 0:
    #             raise OSError (f"i2c_read_i2c_block_data failed - error code <{count}>")
    #         return count, data


