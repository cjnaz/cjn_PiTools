#!/usr/bin/env python3
"""
HTU21D library for Raspberry Pi
"""
#==========================================================
#
#  Chris Nelson, Copyright 2022-2026
#   
#==========================================================

import time
import logging
from .shared import I2C_ERROR, CRC_ERROR, CtoF, CtoK
# from cjnfuncs.core import set_toolname, logging, setuplogging, set_logging_level

# HTU21D_ADDR =                   [0x40]
HTU21D_ADDR =                   0x40

TRIGGER_TEMP_MEASURE_HOLD =     0xE3
TRIGGER_RH_MEASURE_HOLD =       0xE5
# TRIGGER_TEMP_MEASURE_NOHOLD =   0xF3
# TRIGGER_RH_MEASURE_NOHOLD =     0xF5
READ_USER_REG =                 0xE7
WRITE_USER_REG =                0xE6
SOFT_RESET =                    0xFE
READING_WAIT =                  0.050                    # Temp and RH readings take up to 50ms
RESET_WAIT =                    0.015                    # Soft reset spec wait is 15ms

htu21d_logger = logging.getLogger('cjn_PiTools.HTU21D')


#=====================================================================================
#=====================================================================================
#  C l a s s   H T U 2 1 D
#=====================================================================================
#=====================================================================================

class HTU21D:
    """
## Class HTU21D (device_name, pi_i2c_bus_handle) - HTU21D library for Raspberry Pi

Create an HTU21D device instance

### Args
`device_name` (str)
- User defined name for this instance, e.g., 'My_HTU21D'
- Not validated as valid string

`pi_i2c_bus_handle` (cjn_PiTools.shared.pi_i2c instance)
- Get a `pi_i2c` instance handle in the tools script code and pass it to this device instantiation


### Class instance variables - as passed in at instantiation
- `device_name` (str)
- 'device_addr' (int 0x40 - fixed value for this sensor model)


### Behaviors and rules
- Only hold-based trigger temp/rh measurement methods are implemented.  Readings are blocking operations.
- Debug logging may be enabled in the tool script code by setting this module's logging level:

        logging.getLogger('cjn_PiTools.HTU21D').setLevel(logging.DEBUG)
"""
    def __init__(self, device_name, pi_i2c_bus_handle):
        self.device_name =          device_name
        self.device_addr =          HTU21D_ADDR
        self.pi_i2c_bus_handle =    pi_i2c_bus_handle

        api = 'smbus'  if self.pi_i2c_bus_handle.api == 'smbus'  else 'pigpio'
        htu21d_logger.debug (f"<{self.device_name}> New HTU21D device defined at addr <0x{self.device_addr:0>2x}> using api <{api}> on i2c bus <{self.pi_i2c_bus_handle.i2c_bus_num}>")


    #=====================================================================================
    #=====================================================================================
    #  s o f t _ r e s e t
    #=====================================================================================
    #=====================================================================================

    def soft_reset(self):
        """
## soft_reset () - Execute a soft reset

***HTU21D class member function***

Issue a soft reset and wait 15ms (blocking) for completion

### Returns
- 0 for successful operation
- I2C_ERROR on I2C IO error


### Behaviors and rules
- This is a blocking operation for the spec 15ms.
"""
        htu21d_logger.debug (f"<{self.device_name}> ***** soft_reset()")
        try:
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, SOFT_RESET)
            time.sleep (RESET_WAIT)
            return 0
        except Exception as e:
            htu21d_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR


    def read_user_reg(self):
        """Read the user register byte
        Returns UserReg value, or
            -256 for an I2C error
        """
        try:
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, READ_USER_REG)
            (count, byteArray) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 1) # vacuum up those bytes
        except:
            htu21d_logger.debug (f"HTU21D read_user_reg failed.")
            return -256
        if count != 1:
            htu21d_logger.debug (f"HTU21D read_user_reg failed - bad byte count returned.")
            return -256
        htu21d_logger.debug (f"HTU21D read_user_reg:  0x{byteArray[0]:0>2x}")

        return byteArray[0]


    def write_user_reg(self, value):
        """Write the user register byte
        Returns
            0 for successful operation
            -256 for an I2C error
        """
        try:
            self.pi_i2c_bus_handle.i2c_write_byte_data(self.device_addr, WRITE_USER_REG, value)
        except:
            htu21d_logger.debug (f"HTU21D write_user_reg failed.")
            return -256
        htu21d_logger.debug (f"HTU21D write_user_reg: 0x{value:0>2x}")
        return 0


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ t e m p _ d a t a
    #=====================================================================================
    #=====================================================================================

    def read_temp_data(self, tempunits='C'):
        """
## read_temp_data () - Trigger measurement and retrieve temperature

***HTU21D class member function***

Issue a hold-mode temperature measurement.

### Args
`tempunits` (str, default 'C', case-independent)
- Must be 'C', 'F' or 'K', else ValueError is raised


### Returns
- Temperature value in specified tempunits on success
- I2C_ERROR on I2C IO error
- CRC_ERROR on CRC mismatch
- Raises ValueError if tempunits is invalid


### Behaviors and rules
- Uses the hold-mode transaction, so the I2C bus is held/blocked until the completion of the temperature measurement.
See the datasheet for the temperature measurement times based on the configured resolution.  The default 14-bit mode
specifies a maximum of 50ms. 
"""

        htu21d_logger.debug (f"<{self.device_name}> ***** read_temp_data()")
        try:
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, TRIGGER_TEMP_MEASURE_HOLD)
            # time.sleep(READING_WAIT)
            (count, bytes3) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 3)
        except Exception as e:
            htu21d_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR
        htu21d_logger.debug (f"<{self.device_name}>  Raw bytes:  0x{bytes3[0]:0>2x} 0x{bytes3[1]:0>2x} 0x{bytes3[2]:0>2x}")

        if not self.crc8_check(bytes3):
            htu21d_logger.debug ("<{self.device_name}> CRC error")
            return CRC_ERROR

        msB = bytes3[0]
        lsB = bytes3[1]
        rawtemp = ((msB <<8) | lsB) & 0xFFFC  # Lower two bits of LSB are status bits - ignored

        # Apply datasheet formula:  TempC = -46.85 + (175.72 * <sensor data> / 2^16
        temp = -46.85 + (175.72 * rawtemp / 2**16)

        _tempunits = tempunits.lower()
        if _tempunits not in ['c', 'f', 'k']:
            raise ValueError (F"<{self.device_name}> tempunits must be 'C', 'F', or 'K' - received <{tempunits}>")

        if _tempunits == 'f':
            temp = CtoF(temp)
        elif _tempunits == 'k':
            temp = CtoK(temp)

        htu21d_logger.debug (f"<{self.device_name}>  Calculated temp: ({tempunits}):  <{temp}>")
        return temp


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ R H _ d a t a
    #=====================================================================================
    #=====================================================================================

    def read_RH_data(self):
        """
## read_RH_data () - Trigger measurement and retrieve relative humidity

***HTU21D class member function***

Issue a hold-mode RH measurement.


### Returns
- RH value on success
- I2C_ERROR on I2C IO error
- CRC_ERROR on CRC mismatch


### Behaviors and rules
- Uses the hold-mode transaction, so the I2C bus is held/blocked until the completion of the RH measurement.
See the datasheet for the RH measurement times based on the configured resolution.  The default 12-bit mode
specifies a maximum of 16ms. 
"""

        htu21d_logger.debug (f"<{self.device_name}> ***** read_RH_data()")
        try:
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, TRIGGER_RH_MEASURE_HOLD)
            # time.sleep(READING_WAIT)
            (count, bytes3) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 3)
        except Exception as e:
            htu21d_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR
        htu21d_logger.debug (f"<{self.device_name}>  Raw bytes:  0x{bytes3[0]:0>2x} 0x{bytes3[1]:0>2x} 0x{bytes3[2]:0>2x}")

        if not self.crc8_check(bytes3):
            htu21d_logger.debug ("<{self.device_name}> CRC error")
            return CRC_ERROR

        msB = bytes3[0]
        lsB = bytes3[1]
        rawRH = ((msB <<8) | lsB) & 0xFFFC  # Lower two bits of LSB are status bits - ignored

        # Apply datasheet formula:  RH = -6 + 125 * <sensor data> / 2^16
        RH = -6.0 + (125 * rawRH / 2**16)
        htu21d_logger.debug (f"<{self.device_name}>  Calculated RH:         <{RH}>")
        return RH



    def crc8_check(self, value):
       """Calculate the CRC8 for the data received"""
       if len(value) != 3:
            return False

       # Ported from Sparkfun Arduino HTU21D Library:   https://github.com/sparkfun/HTU21D_Breakout
       remainder = ( ( value[0] << 8 ) + value[1] ) << 8
       remainder |= value[2]

       # POLYNOMIAL = 0x0131 = x^8 + x^5 + x^4 + 1
       # divisor = 0x988000 is the 0x0131 polynomial shifted to farthest left of three bytes
       divisor = 0x988000

       for i in range(0, 16):
           if( remainder & 1 << (23 - i) ):
               remainder ^= divisor

           divisor = divisor >> 1

       if remainder == 0:
           return True
       else:
           return False
