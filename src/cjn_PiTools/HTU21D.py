#!/usr/bin/env python3
"""
HTU21D Temperature/RH sensor library for Raspberry Pi
"""
#==========================================================
#
#  Chris Nelson, Copyright 2022-2026
#   
#==========================================================

import time
import logging
from .shared import I2C_ERROR, CRC_ERROR, CtoF, CtoK

HTU21D_ADDR =                   0x40

TRIGGER_TEMP_MEASURE_HOLD =     0xE3
TRIGGER_RH_MEASURE_HOLD =       0xE5
TRIGGER_TEMP_MEASURE_NOHOLD =   0xF3
TRIGGER_RH_MEASURE_NOHOLD =     0xF5
READ_USER_REG =                 0xE7
WRITE_USER_REG =                0xE6
SOFT_RESET =                    0xFE
RESET_WAIT =                    0.015                    # Soft reset spec wait is 15ms

OPEN_CIRCUIT_ERROR_CODE =       0x0000
OPEN_CIRCUIT_ERROR =            -254
CLOSED_CIRCUIT_ERROR_CODE =     0xFFFF
CLOSED_CIRCUIT_ERROR =          -253

htu21d_logger = logging.getLogger('cjn_PiTools.HTU21D')


#=====================================================================================
#=====================================================================================
#  C l a s s   H T U 2 1 D
#=====================================================================================
#=====================================================================================

class HTU21D:
    """
## Class HTU21D (device_name, pi_i2c_bus_handle, do_reset=True) - HTU21D library for Raspberry Pi

Create an HTU21D device instance

### Args
`device_name` (str)
- User defined name for this instance, e.g., 'My_HTU21D'

`pi_i2c_bus_handle` (cjn_PiTools.shared.pi_i2c instance)
- Get a `pi_i2c` instance handle in the tools script code and pass it to this device instantiation

`do_reset` (bool, default True)
- If True, issue a soft reset as part of instantiation
- Set to False if the device is not available at instantiation time, and reset the device before reading values


### Class instance variables - as passed in at instantiation
- `device_name` (str)
- `device_addr` (int 0x40 - fixed value for this sensor model)


### Returns
- Handle to the HTU21D instance on success
- Raises ValueError if args checks fail
- Raises RuntimeError if the device fails soft reset


### Behaviors and rules
- Debug logging may be enabled in the tool script code by setting this module's logging level:

        logging.getLogger('cjn_PiTools.HTU21D').setLevel(logging.DEBUG)
"""
    def __init__(self, device_name, pi_i2c_bus_handle, do_reset=True):
        self.device_name =          device_name
        self.device_addr =          HTU21D_ADDR
        self.pi_i2c_bus_handle =    pi_i2c_bus_handle

        if not isinstance(self.device_name, str):
            raise ValueError (f"HTU21D device_name must be a str.  Received <{device_name}>")

        if not isinstance(do_reset, bool):
            raise ValueError (f"<{self.device_name}> do_reset must be a bool.  Received <{do_reset}>")


        if do_reset:
            if self.soft_reset() == I2C_ERROR:
                raise RuntimeError (f"<{self.device_name}> soft_reset during instantiation failed")

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
- A soft reset sets the resolution code to 0b00 (Temperature 14-bits, RH 12-bits), On-chip heater disabled (0), 
and OTP reload disabled (1).
- This is a blocking operation for the spec 15ms.
- The datasheet implies that `soft_reset()` does not clear the heater enable bit in the user register: "with the exception
of the heater bit in the user register".  Test 4b demonstrates that the heater enable bit is cleared by soft reset.
"""
        htu21d_logger.debug (f"<{self.device_name}> ***** soft_reset()")
        try:
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, SOFT_RESET)
            time.sleep (RESET_WAIT)
            return 0
        except Exception as e:
            htu21d_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ u s e r _ r e g
    #=====================================================================================
    #=====================================================================================

    def read_user_reg(self, quiet=False):
        """
## read_user_reg () - Return the content of the user register

***HTU21D class member function***

The user register is the configuration and status register


### Returns
- User register content for successful operation
- I2C_ERROR on I2C IO error


### Behaviors and rules
- If debug logging is enabled the register content is decoded and logged
"""
        if not quiet:
            htu21d_logger.debug (f"<{self.device_name}> ***** read_user_reg()")
        try:
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, READ_USER_REG)
            (count, byte1) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 1)
            user_reg_value = byte1[0]
        except Exception as e:
            htu21d_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if count != 1:
            htu21d_logger.debug (f"<{self.device_name}> read_user_reg failed - bad byte count returned: <{count}")
            return I2C_ERROR
        htu21d_logger.debug (f"<{self.device_name}> user_reg raw data:  0x{byte1[0]:0>2x}")

        if not quiet:
            measurement_resolution_code = (user_reg_value & 0b10000000) >> 6 | (user_reg_value & 0b00000001)
            desc = {0b00: 'RH 12 bits, Temp 14 bits',
                    0b01: 'RH  8 bits, Temp 12 bits',
                    0b10: 'RH 10 bits, Temp 13 bits',
                    0b11: 'RH 11 bits, Temp 11 bits'}[measurement_resolution_code]
            
            htu21d_logger.info (f"  Measurement resolution: <0b{measurement_resolution_code:0>2b} - {desc}>")
            htu21d_logger.info (f"  End of Battery:         <{(user_reg_value & 0b01000000) >> 6}>")
            htu21d_logger.info (f"  On-chip heater enabled: <{(user_reg_value & 0b00000100) >> 2}>")
            htu21d_logger.info (f"  OTP reload disabled:    <{(user_reg_value & 0b00000010) >> 1}>")

        return user_reg_value


    #=====================================================================================
    #=====================================================================================
    #  w r i t e _ u s e r _ r e g
    #=====================================================================================
    #=====================================================================================

    def write_user_reg(self, resolution=None, heater_enable=None, OTP_reload_disable=None):
        """
## write_user_reg (resolution=None, heater_enable=None, OTP_reload_disable=None) - Set fields in the user register

***HTU21D class member function***

Writeable fields in the user register are changed to specified values, leaving other fields unchanged.


### Args
`resolution` (int, default None)
- If int, sets the *Measurement resolution* field to the given value.  The value must be in 
range 0b00 to 0b11.
- If None, the measurement resolution is unchanged
- The default resolution settings from `soft_reset()` is 0b00: temperature 14-bits, RH 12-bits

`heater_enable` (int, default None)
- If int, sets the *Enable on-chip heater* field to the given value.  The value must be 0 or 1.
- If None, the heater enable field is unchanged
- The default heater enable setting from `soft_reset()` is 0: heater disabled.  See note on `soft_reset()`.

`OTP_reload_disable` (int, default None)
- If int, sets the *Disable OTP reload* field to the given value.  The value must be 0 or 1.
- If None, the Disable OTP reload field is unchanged
- The default OTP reload disable setting from `soft_reset()` is 1: OTP reload disabled

### Returns
- 0 for successful operation
- I2C_ERROR on I2C IO error
- Raises ValueError on illegal input values


### Behaviors and rules
- The current value of the user register is read and overlaid with specified new values.  User register fields
for Non-specified values remain unchanged.
"""
        htu21d_logger.debug (f"<{self.device_name}> ***** write_user_reg()")

        new_user_reg_value = self.read_user_reg(quiet=True)
        if new_user_reg_value == I2C_ERROR:
            return I2C_ERROR
        
        if resolution is not None:
            if resolution not in [0b00, 0b01, 0b10, 0b11]:
                raise ValueError (f"<{self.device_name}> resolution value must be in range 0 to 3 - received <{resolution}>")
            new_user_reg_value = new_user_reg_value & 0b01111110 | ((resolution & 0b10) << 6 | (resolution & 0b01))

        if heater_enable is not None:
            if heater_enable not in [0b0, 0b1]:
                raise ValueError (f"<{self.device_name}> heater_enable value must be in range 0 or 1 - received <{heater_enable}>")
            new_user_reg_value = new_user_reg_value & 0b11111011 | heater_enable << 2

        if OTP_reload_disable is not None:
            if OTP_reload_disable not in [0b0, 0b1]:
                raise ValueError (f"<{self.device_name}> OTP_reload_disable value must be in range 0 or 1 - received <{OTP_reload_disable}>")
            new_user_reg_value = new_user_reg_value & 0b11111101 | OTP_reload_disable << 1

        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, [WRITE_USER_REG, new_user_reg_value])
        except Exception as e:
            htu21d_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR
        return 0


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ t e m p e r a t u r e
    #=====================================================================================
    #=====================================================================================

    def read_temperature(self, tempunits='C'):
        """
## read_temperature (tempunits='C') - Trigger a hold mode temperature measurement and return the measured temperature

***HTU21D class member function***

NOTE that this is a blocking operation for the duration of the internal temperature measurement conversion.

Calls `fetch_temperature()` after triggering the hold mode temperature measurement.  See `fetch_temperature()` for
Args, Returns, and Behaviors info.  
"""
        htu21d_logger.debug (f"<{self.device_name}> ***** read_temperature()")
        try:
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, TRIGGER_TEMP_MEASURE_HOLD)
        except Exception as e:
            htu21d_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        return self.fetch_temperature(tempunits)


    #=====================================================================================
    #=====================================================================================
    #  t r i g g e r _ t e m p e r a t u r e _ n o h o l d
    #=====================================================================================
    #=====================================================================================

    def trigger_temperature_nohold(self):
        """
## trigger_temperature_nohold () - Trigger measurement in no-hold mode

***HTU21D class member function***

Issue a no-hold mode temperature measurement.  The tool script code normally will follow up with a separate call to 
`fetch_temperature()`.


### Returns
- 0 on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- Uses the no-hold temperature measurement trigger.  Tool script code must separately call `fetch_temperature()` to
obtain the measured result after an appropriate delay. See the datasheet for measurement times based on the resolution settings.
- If the measurement is still in progress then I2C_ERROR is returned, and `fetch_temperature()` should be called again later.
"""
        htu21d_logger.debug (f"<{self.device_name}> ***** trigger_temperature_nohold()")
        try:
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, TRIGGER_TEMP_MEASURE_NOHOLD)
            return 0
        except Exception as e:
            htu21d_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  f e t c h _ t e m p e r a t u r e
    #=====================================================================================
    #=====================================================================================

    def fetch_temperature(self, tempunits='C'):
        """
## fetch_temperature (tempunits='C') - Retrieve measured temperature

***HTU21D class member function***


### Args
`tempunits` (str, default 'C', case-independent)
- Must be 'C', 'F' or 'K'


### Returns
- Temperature value in specified `tempunits` on success
- I2C_ERROR on I2C IO error
- CRC_ERROR on CRC mismatch
- OPEN_CIRCUIT_ERROR or CLOSED_CIRCUIT_ERROR is returned on device error
- Raises ValueError if `tempunits` is invalid


### Behaviors and rules
- When called from `read_temperature()` the HTU21D will assert SCK=0 until the internal measurement sequence is complete
then release SCK, then fetching the measurement data proceeds in this code.  No I2C_ERROR normally occurs. 
This sequence is the standard I2C bus clock stretching mode.
- When called by the tool script code after calling `trigger_temperature_nohold()`, if the measurement is still in progress
then the HTU21D will assert NACK during the read attempt by this code, which is returned to the tool script as an I2C_ERROR.
The tool script should then retry the `fetch_temperature()` call again after an appropriate wait time for the measurement 
sequence to complete.  See the datasheet for measurement times based on the resolution settings.
- The return data is checked for the "open circuit" code (0x0000), and OPEN_CIRCUIT_ERROR is returned.  The "closed circuit"
code 0xFFFF returns CLOSED_CIRCUIT_ERROR.  These names should be imported from this module, if needed in the tool script code.
"""
        htu21d_logger.debug (f"<{self.device_name}> ***** fetch_temperature()")
        try:
            (count, bytes3) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 3)
        except Exception as e:
            htu21d_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR
        htu21d_logger.debug (f"<{self.device_name}>  Raw bytes:  0x{bytes3[0]:0>2x} 0x{bytes3[1]:0>2x} 0x{bytes3[2]:0>2x}")

        if not self.crc8_check(bytes3):
            htu21d_logger.debug (f"<{self.device_name}> CRC error")
            return CRC_ERROR

        return_code = ((bytes3[0] <<8) | bytes3[1])

        if return_code == OPEN_CIRCUIT_ERROR_CODE:
            return OPEN_CIRCUIT_ERROR
        if return_code == CLOSED_CIRCUIT_ERROR_CODE:
            return CLOSED_CIRCUIT_ERROR

        # Apply datasheet formula:  TempC = -46.85 + (175.72 * <sensor data> / 2^16
        temp = -46.85 + (175.72 * (return_code & 0xFFFC) / 2**16)      # Mask lower two Status Bits

        _tempunits = tempunits.lower()
        if _tempunits not in ['c', 'f', 'k']:
            raise ValueError (F"<{self.device_name}> tempunits must be 'C', 'F', or 'K' - received <{tempunits}>")

        if _tempunits == 'f':
            temp = CtoF(temp)
        elif _tempunits == 'k':
            temp = CtoK(temp)

        htu21d_logger.debug (f"<{self.device_name}> - Temperature:    ({tempunits}):  <{temp}>")
        return temp


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ R H
    #=====================================================================================
    #=====================================================================================

    def read_RH(self):
        """
## read_RH () - Trigger a hold mode relative humidity measurement and return the measured RH

***HTU21D class member function***

NOTE that this is a blocking operation for the duration of the internal RH measurement conversion.

Calls `fetch_RH()` after triggering the hold mode RH measurement.  See `fetch_RH()` for
Args, Returns, and Behaviors info.
"""
        htu21d_logger.debug (f"<{self.device_name}> ***** read_RH()")
        try:
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, TRIGGER_RH_MEASURE_HOLD)
        except Exception as e:
            htu21d_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        return self.fetch_RH()


    #=====================================================================================
    #=====================================================================================
    #  t r i g g e r _ R H _ n o h o l d
    #=====================================================================================
    #=====================================================================================

    def trigger_RH_nohold(self):
        """
## trigger_RH_nohold () - Trigger measurement in no-hold mode

***HTU21D class member function***

Issue a no-hold mode RH measurement.  The tool script code normally will follow up with a separate call to `fetch_RH()`.


### Returns
- 0 on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- Uses the no-hold RH measurement trigger.  Tool script code must separately call `fetch_RH()` to
obtain the measured result after an appropriate delay. See the datasheet for measurement times based on the resolution settings.
- If the measurement is still in progress then I2C_ERROR is returned, and `fetch_RH()` should be called again later.
"""
        htu21d_logger.debug (f"<{self.device_name}> ***** trigger_RH_nohold()")
        try:
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, TRIGGER_RH_MEASURE_NOHOLD)
            return 0
        except Exception as e:
            htu21d_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  f e t c h _ R H
    #=====================================================================================
    #=====================================================================================

    def fetch_RH(self):
        """
## fetch_RH () - Retrieve measured relative humidity

***HTU21D class member function***


### Returns
- RH value on success
- I2C_ERROR on I2C IO error
- CRC_ERROR on CRC mismatch
- OPEN_CIRCUIT_ERROR or CLOSED_CIRCUIT_ERROR is returned on device error


### Behaviors and rules
- When called from `read_RH()` the HTU21D will assert SCK=0 until the internal measurement sequence is complete
then release SCK, then fetching the measurement data proceeds in this code.  No I2C_ERROR normally occurs. 
This sequence is the standard I2C bus clock stretching mode.
- When called by the tool script code after calling `trigger_RH_nohold()`, if the measurement is still in progress
then the HTU21D will assert NACK during the read attempt by this code, which is returned to the tool script as an I2C_ERROR.
The tool script should then retry the `fetch_RH()` call again after an appropriate wait time for the measurement 
sequence to complete.  See the datasheet for measurement times based on the resolution settings.
- The return data is checked for the "open circuit" code (0x0000), and OPEN_CIRCUIT_ERROR is returned.  The "closed circuit"
code 0xFFFF returns CLOSED_CIRCUIT_ERROR.  These names should be imported from this module, if needed in the tool script code.
"""
        htu21d_logger.debug (f"<{self.device_name}> ***** fetch_RH()")
        try:
            (count, bytes3) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 3)
        except Exception as e:
            htu21d_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR
        htu21d_logger.debug (f"<{self.device_name}>  Raw bytes:  0x{bytes3[0]:0>2x} 0x{bytes3[1]:0>2x} 0x{bytes3[2]:0>2x}")

        if not self.crc8_check(bytes3):
            htu21d_logger.debug (f"<{self.device_name}> CRC error")
            return CRC_ERROR

        return_code = ((bytes3[0] <<8) | bytes3[1])

        if return_code == OPEN_CIRCUIT_ERROR_CODE:
            return OPEN_CIRCUIT_ERROR
        if return_code == CLOSED_CIRCUIT_ERROR_CODE:
            return CLOSED_CIRCUIT_ERROR

        # Apply datasheet formula:  RH = -6 + 125 * <sensor data> / 2^16
        RH = -6.0 + (125 * (return_code & 0xFFFC) / 2**16)      # Mask lower two Status Bits
        htu21d_logger.debug (f"<{self.device_name}> - RH:                   <{RH}>")
        return RH




    #=====================================================================================
    #=====================================================================================
    #  c r c 8 _ c h e c k
    #=====================================================================================
    #=====================================================================================

    def crc8_check(self, value):
       """Calculate the CRC8 for the data received
       
       The CRC of value[0] and value[1] is calculated and compared to value[2]
       
       Args
       `value` (list of 3 bytes)
       - value[0] is the measured temperature/RH MSB, and value[1] is the LSB
       - value[2] is the CRC value read from the device


       Returns
       - True if value[0] and value[1] calculated CRC equals value[2], else False
    
       """
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
