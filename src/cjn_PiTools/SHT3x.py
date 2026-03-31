#!/usr/bin/env python3
"""SHT3x Temperature/RH sensor library for Raspberry Pi
"""
#==========================================================
#
#  Chris Nelson, Copyright 2023-2026
#   
#==========================================================

import time
import logging
from crc import Calculator, Configuration

from .shared import I2C_ERROR, CRC_ERROR, CtoF, FtoC, CtoK, KtoC


# Configs / Constants
TOOLNAME = 'SHT3x'

SHT3x_ADDRS =               [0x44, 0x45]
SOFT_RESET =                [0x30, 0xa2]
FETCH_DATA =                [0xe0, 0x00]
ART =                       [0x2b, 0x32]
READ_STATUS_REGISTER =      [0xf3, 0x2d]
CLEAR_STATUS_REGISTER =     [0x30, 0x41]
HEATER_ENABLE =             [0x30, 0x6d]
HEATER_DISABLE =            [0x30, 0x66]
BREAK =                     [0x30, 0x93]
SINGLE_SHOT_MODES = {
            "High_CS":      [0x2c, 0x06],
            "Medium_CS":    [0x2c, 0x0d],
            "Low_CS":       [0x2c, 0x10],
            "High_noCS":    [0x24, 0x00],
            "Medium_noCS":  [0x24, 0x0b],
            "Low_noCS":     [0x24, 0x16]  }
PERIODIC_DA_MODES = {
            'High_0.5':     [0x20, 0x32],
            'Medium_0.5':   [0x20, 0x24],
            'Low_0.5':      [0x20, 0x2f],
            'High_1':       [0x21, 0x30],
            'Medium_1':     [0x21, 0x26],
            'Low_1':        [0x21, 0x2d],
            'High_2':       [0x22, 0x36],
            'Medium_2':     [0x22, 0x20],
            'Low_2':        [0x22, 0x2b],
            'High_4':       [0x23, 0x34],
            'Medium_4':     [0x23, 0x22],
            'Low_4':        [0x23, 0x29],
            'High_10':      [0x27, 0x37],
            'Medium_10':    [0x27, 0x21],
            'Low_10':       [0x27, 0x2a]  }
READ_ALERT_MODES = {
            'High_Set':     [0xe1, 0x1f],
            'High_Clear':   [0xe1, 0x14],
            'Low_Clear':    [0xe1, 0x09],
            'Low_Set':      [0xe1, 0x02]  }
WRITE_ALERT_MODES = {
            'High_Set':     [0x61, 0x1d],
            'High_Clear':   [0x61, 0x16],
            'Low_Clear':    [0x61, 0x0b],
            'Low_Set':      [0x61, 0x00]  }

MIN_READING_WAIT =  0.001                   # Minimal waiting time in single shot mode between meas trigger and fetch
RESET_WAIT =        0.0015                  # Soft reset spec wait is 1.5ms


crc_calc_config = Configuration(
    width=8,
    polynomial=0x31,
    init_value=0xFF,
    final_xor_value=0x00,
    reverse_input=False,
    reverse_output=False)
crc_calc = Calculator(crc_calc_config)


sht3x_logger = logging.getLogger('cjn_PiTools.SHT3x')


class SHT3x:
    """
## Class SHT3x (device_name, device_addr, pi_i2c_bus_handle, do_reset=True) - SHT3x Temperature/RH sensor library for Raspberry Pi

Create a SHT3x family device instance

### Args
`device_name` (str)
- User defined name for this instance, e.g., 'My_SHT3x'

`device_addr` (int)
- I2C bus address for this instance, e.g., 0x44 or 0x45

`pi_i2c_bus_handle` (cjn_PiTools.shared.pi_i2c instance)
- Get a `pi_i2c` instance handle in the tools script code and pass it to this device instantiation

`do_reset` (bool, default True)
- If True, call `soft_reset()` and `clear_status_reg()` as part of instantiation
- If the device is not accessible at the time of instantiation then set `do_reset=False` and reset the device when available


### Class instance variables - as passed in at instantiation
- `device_name` (str)
- `device_addr` (int)


### Returns
- Handle to the SHT3x instance on success
- Raises ValueError if args checks fail
- Raises RuntimeError if the device fails soft reset or clearing the status register


### Behaviors and rules
- Per the datasheet, "After sending a command to the sensor a minimal waiting time of 1ms is needed before another command
can be received by the sensor." Normally, the time between consecutive API calls takes >1ms, so no padding seems necessary.
- Debug logging may be enabled in the tool script code by setting this module's logging level:

        logging.getLogger('cjn_PiTools.SHT3x').setLevel(logging.DEBUG)
"""

    def __init__(self, device_name, device_addr, pi_i2c_bus_handle, do_reset=True):
        self.device_name =          device_name
        self.device_addr =          device_addr
        self.pi_i2c_bus_handle =    pi_i2c_bus_handle

        if not isinstance(self.device_name, str):
            raise ValueError (f"SHT3x device_name must be a str.  Received <{device_name}>")

        if self.device_addr not in SHT3x_ADDRS:
            raise ValueError (f"<{self.device_name}> SHT3x device address must be 0x44 or 0x45.  Received <0x{device_addr:0>2x}>")

        if do_reset:
            if self.soft_reset() == I2C_ERROR:
                raise RuntimeError (f"<{self.device_name}> soft_reset() during instantiation failed")

            if self.clear_status_reg() == I2C_ERROR:
                raise RuntimeError (f"<{self.device_name}> clear_status_reg() during instantiation failed")

        api = 'smbus'  if self.pi_i2c_bus_handle.api == 'smbus'  else 'pigpio'
        sht3x_logger.debug (f"<{self.device_name}> New SHT3x device defined at addr <0x{self.device_addr:0>2x}> using api <{api}> on i2c bus <{self.pi_i2c_bus_handle.i2c_bus_num}>")


    #=====================================================================================
    #=====================================================================================
    #  s o f t _ r e s e t
    #=====================================================================================
    #=====================================================================================

    def soft_reset(self, reset_wait=RESET_WAIT):
        """
## soft_reset (reset_wait=0.0015) - Issue a soft_reset

***SHT3x class member function***


### Args
`reset_wait` (float, default 1.5ms)
- The spec time is 1.5ms


### Returns
- 0 on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- The reset time is blocking to the calling code
- A soft_reset() does NOT clear the status register
- A soft_reset() DOES reset the alert High/Low Set/Clear registers to their defaults
- From the datasheet:  "This triggers the sensor to reset its system controller and reloads calibration data from the memory.
It is worth noting that the sensor reloads calibration data prior to every measurement by default."  Note that a soft_reset 
cannot be applied if the system controller (I2C interface) is stuck - a power cycle is required if your device version does not
have a reset pin.
"""

        sht3x_logger.debug (f"<{self.device_name}> ***** soft_reset()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, SOFT_RESET)
            time.sleep (reset_wait)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


    #=====================================================================================
    #=====================================================================================
    #  s i n g l e _ s h o t
    #=====================================================================================
    #=====================================================================================

    def single_shot(self, tempunits='C', repeatability='High', reading_wait=-1, fetch_data=True):
        """
## single_shot (tempunits='C', repeatability='High', reading_wait=-1, fetch_data=True) - Issue a single shot temperature/RH measurement and read back the results

***SHT3x class member function***


### Args
`tempunits` (str, default 'C', case-independent)
- Must be 'C', 'F' or 'K'

`repeatability` (str, default 'High')
- Select repeatability setting 'High', 'Medium', or 'Low' per datasheet, with corresponding measurement time differences

`reading_wait` (int or float, default -1)
- If = -1 then use clock stretch mode (device indicates when data is available by releasing TCK)
- If >= 0 then use non-clock-stretch mode and use `reading_wait` value between triggering the single shot 
measurement and fetching the data (if `fetch_data` = True)
- The worst case maximum measurement durations are High repeatability 15.5ms, Medium 6.5ms, and Low 4.5ms. 
See the datasheet.

`fetch_data` (bool, default True)
- If True, the temperature and RH data is read back after the measurement is triggered
- If False, the measurement is triggered but the data is not read back.  A separate call to `fetch_data()` may be used to 
read back the measurement results.


### Returns
- If `fetch_data` = True, return (Temperature, RH) tuple on success
- If `fetch_data` = False, return (0, 0) tuple on success
- (I2C_ERROR, I2C_ERROR) tuple on I2C IO error
- (CRC_ERROR, CRC_ERROR) tuple on fetched data CRC mismatch
- Raises ValueError on invalid args


### Behaviors and rules
- The single shot measurement trigger and fetching the temperature/rh results may be separated by setting `reading_wait = 0`
(no delay after the trigger) and `fetch_data = False`.  Follow this single shot trigger call with a later call to 
`fetch_data()` to get the results.  Consider the minimum measurement time rules before calling `fetch_data()`.
- The entire measurement sequence (trigger single shot, any `reading_wait` or clock stretch time, and the `fetch_data()` call) 
is blocking to the calling code.
- If the devices is still busy doing the measurement when `fetch_data()` is called (`reading_wait` too short) then 
(I2C_ERROR, I2C_ERROR) is returned and debug logging will show:
  - smbus api:  OSError: [Errno 121] Remote I/O error
  - pigpio api: OSError: i2c_read_device failed - error code <-83>
"""

        if not isinstance(reading_wait, (int, float))  or  not (reading_wait == -1  or  reading_wait >= 0.0):
            raise ValueError (f"<{self.device_name}> Invalid reading_wait value - expecting -1 or >= 0.0 - received <{reading_wait}>")

        mode = '_CS'  if reading_wait == -1  else '_noCS'
        try:
            bytes_code = SINGLE_SHOT_MODES[repeatability + mode]
        except:
            raise ValueError (f"<{self.device_name}> Invalid Single Shot mode selection - received repeatability <{repeatability}>")

        sht3x_logger.debug (f"<{self.device_name}> ***** single_shot()  <{repeatability}{mode}>")

        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, bytes_code)
            if reading_wait == -1:
                time.sleep(MIN_READING_WAIT)
            else:
                time.sleep(reading_wait)
            if fetch_data:
                return self.fetch_data(tempunits, send_fetch=False)
            else:
                return 0, 0
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR, I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  s t a r t _ p e r i o d i c _ D A
    #=====================================================================================
    #=====================================================================================

    def start_periodic_DA (self, repeatability='High', mps=2):
        """
## start_periodic_DA (repeatability='High', mps=2) - Start Periodic Data Acquisition Mode

***SHT3x class member function***


### Args
`repeatability` (str, default 'High')
- Select repeatability setting 'High', 'Medium', or 'Low' per datasheet, with corresponding measurement time differences

`mps` (int or float, default 2)
- Measurements per second.
- Allowed values are 0.5, 1, 2, 4, and 10


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
- Raises ValueError if `repeatability` or `mps` is invalid


### Behaviors and rules
- Status bit 0x0020 indicates Periodic / free running measurement mode is active (undocumented)
- Status bit 0x0040 indicates new measurement data is available (undocumented)
- Attempting to fetch data more frequently than new data is available (based on the `mps` setting) results in 
`fetch_data()` returning (I2C_ERROR, I2C_ERROR) and debug logging will show:
  - smbus api:  OSError: [Errno 121] Remote I/O error
  - pigpio api: OSError: i2c_read_device failed - error code <-83>
"""

        sht3x_logger.debug (f"<{self.device_name}> ***** start_periodic_DA()")
        try:
            bytes_code = PERIODIC_DA_MODES[repeatability + '_' + str(mps)]
        except:
            raise ValueError (f"<{self.device_name}> Invalid Periodic Data Acquisition mode selection - received repeatability <{repeatability}>, mps: <{mps}>")

        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, bytes_code)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


    #=====================================================================================
    #=====================================================================================
    #  s t a r t _ A R T
    #=====================================================================================
    #=====================================================================================

    def start_ART (self):
        """
## start_ART () - Start Periodic Data Acquisition Mode using Accelerated Response Time

***SHT3x class member function***


### Returns
- 0 on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- New measurement data is available at 4 measurements per second (250ms)
- Status bit 0x0020 indicates Periodic / free running measurement mode is active (undocumented)
- Status bit 0x0040 indicates new measurement data is available (undocumented)
- Attempting to fetch data more frequently than new data is available results in 
`fetch_data()` returning (I2C_ERROR, I2C_ERROR) and debug logging will show:
  - smbus api:  OSError: [Errno 121] Remote I/O error
  - pigpio api: OSError: i2c_read_device failed - error code <-83>
"""

        sht3x_logger.debug (f"<{self.device_name}> ***** start_ART()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, ART)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


    #=====================================================================================
    #=====================================================================================
    #  s t o p _ p e r i o d i c _ D A
    #=====================================================================================
    #=====================================================================================

    def stop_periodic_DA (self):
        """
## stop_periodic_DA () - Stop Periodic Data Acquisition Mode, including ART mode

***SHT3x class member function***


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
"""

        sht3x_logger.debug (f"<{self.device_name}> ***** stop_periodic_DA()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, BREAK)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


    #=====================================================================================
    #=====================================================================================
    #  f e t c h _ d a t a
    #=====================================================================================
    #=====================================================================================

    def fetch_data(self, tempunits='C', send_fetch=True, force_CRC_fail=False):
        """
## fetch_data (tempunits='C', send_fetch=True, force_CRC_fail=False) - Fetch temperature and RH data from the device

***SHT3x class member function***


### Args
`tempunits` (str, default 'C', case-independent)
- Must be 'C', 'F' or 'K'

`send_fetch` (bool, default True)
- If True, the fetch data instruction will be sent to the device
- `single_shot()` calls `fetch_data()` with `send_fetch=False` since the device is ready to be read 
after the single shot measurement trigger has completed.
- When using a Periodic Data Acquisition Mode call `fetch_data()` with `send_fetch=True` (default)

`force_CRC_fail` (bool, default False)
- Used for validation


### Returns
- (Temperature, RH) tuple on success
- (I2C_ERROR, I2C_ERROR) tuple on I2C IO error
- (CRC_ERROR, CRC_ERROR) tuple on fetched data CRC mismatch
- Raises ValueError if `tempunits` is invalid


### Behaviors and rules
- Status bit 0x0040 indicates new measurement data is available (undocumented)
- Attempting to fetch data when no new data is available results in 
`fetch_data()` returning (I2C_ERROR, I2C_ERROR) and debug logging will show:
  - smbus api:  OSError: [Errno 121] Remote I/O error
  - pigpio api: OSError: i2c_read_device failed - error code <-83>
"""

        sht3x_logger.debug (f"<{self.device_name}> ***** fetch_data()")
        try:
            if send_fetch:
                self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, FETCH_DATA)

            (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 6)

        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR, I2C_ERROR
        
        if count != 6:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR - error code <{count}>")
            return I2C_ERROR, I2C_ERROR

        if force_CRC_fail:
            data[2] = data[5] = 0x00

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            xx =  f"<{self.device_name}> Temp/RH raw data:\n"
            xx += f"  temp data returned bytes: 0x{data[0]:0>2x} 0x{data[1]:0>2x} 0x{data[2]:0>2x},  calc CRC: <0x{crc_calc.checksum(bytes([data[0], data[1]])):0>2x}>\n"
            xx += f"  RH   data returned bytes: 0x{data[3]:0>2x} 0x{data[4]:0>2x} 0x{data[5]:0>2x},  calc CRC: <0x{crc_calc.checksum(bytes([data[3], data[4]])):0>2x}>"
            sht3x_logger.debug (xx)

        # Process temp data
        if crc_calc.checksum(bytes([data[0], data[1]])) != data[2]:
            sht3x_logger.debug (f"<{self.device_name}> temp data CRC error")
            temp_rslt = CRC_ERROR
        else:
            rawtemp = ((data[0] <<8) | data[1]) & 0xFFFF
            temp_rslt = _decode_temp (rawtemp)
            _tempunits = tempunits.lower()
            if _tempunits not in ['c', 'f', 'k']:
                raise ValueError (F"<{self.device_name}> tempunits must be 'C', 'F', or 'K' - received <{tempunits}>")

            if _tempunits == 'f':
                temp_rslt = CtoF(temp_rslt)
            elif _tempunits == 'k':
                temp_rslt = CtoK(temp_rslt)

        sht3x_logger.debug (f"<{self.device_name}> Calculated temp ({tempunits}):     {temp_rslt:>5.1f}")

        # Process RH data
        if crc_calc.checksum(bytes([data[3], data[4]])) != data[5]:
            sht3x_logger.debug (f"<{self.device_name}> RH data CRC error")
            RH_rslt = CRC_ERROR
        else:
            rawRH = ((data[3] <<8) | data[4]) & 0xFFFF
            RH_rslt = _decode_rh(rawRH)

        sht3x_logger.debug (f"<{self.device_name}> Calculated RH:           {RH_rslt:>5.1f}")

        return temp_rslt, RH_rslt


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ s t a t u s _ r e g
    #=====================================================================================
    #=====================================================================================

    def read_status_reg(self, quiet=False, force_CRC_fail=False):
        """
## read_status_reg (quiet=False, force_CRC_fail=False) - Read and return the status register

***SHT3x class member function***


### Args
`quiet` (bool, default False)
- Set True by SHT3x class internal calls for debug logging

`force_CRC_fail` (bool, default False)
- Used for validation


### Returns
- 2-byte status register value (16-bit int) on success
- I2C_ERROR on I2C IO error
- CRC_ERROR on fetched data CRC mismatch


### Behaviors and rules
- If `quiet=False` and module debug logging is enabled the status register bits are decoded and logged
- Status register bit 4 (reset detected) does not seem to be set by a soft_reset(), contrary to the datasheet.
"""

        if not quiet:
            sht3x_logger.debug (f"<{self.device_name}> ***** read_status_reg()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, READ_STATUS_REGISTER)
            (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 3)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if count != 3:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR - error code <{count}>")
            return I2C_ERROR

        if force_CRC_fail:
            data[2] = 0x00

        if not quiet:
            sht3x_logger.debug (f"<{self.device_name}> status reg raw data: 0x{data[0]:0>2x} 0x{data[1]:0>2x} 0x{data[2]:0>2x},  calc CRC: <0x{crc_calc.checksum(bytes([data[0], data[1]])):0>2x}>")

        if crc_calc.checksum(bytes([data[0], data[1]])) != data[2]:
            sht3x_logger.debug (f"<{self.device_name}> status register data CRC error")
            return CRC_ERROR
        
        reg_value = ((data[0] <<8) | data[1]) & 0xFFFF
        if not quiet:
            if reg_value & 0x8000:
                sht3x_logger.info ("  At least one pending alert")
            if reg_value & 0x4000:
                sht3x_logger.info ("  Reserved (undocumented)")
            if reg_value & 0x2000:
                sht3x_logger.info ("  Heater ON")
            if reg_value & 0x1000:
                sht3x_logger.info ("  Reserved (undocumented)")
            if reg_value & 0x0800:
                sht3x_logger.info ("  RH tracking alert")
            if reg_value & 0x0400:
                sht3x_logger.info ("  T  tracking alert")
            if reg_value & 0x0200:
                sht3x_logger.info ("  Reserved (undocumented)")
            if reg_value & 0x0100:
                sht3x_logger.info ("  Reserved (undocumented)")
            if reg_value & 0x0080:
                sht3x_logger.info ("  New data available - stale data overwritten? (undocumented)")
            if reg_value & 0x0040:
                sht3x_logger.info ("  New data available? (undocumented)")
            if reg_value & 0x0020:
                sht3x_logger.info ("  PeriodicDA running? (undocumented)")
            if reg_value & 0x0010:
                sht3x_logger.info ("  System reset detected")
            if reg_value & 0x0008:
                sht3x_logger.info ("  Reserved (undocumented)")
            if reg_value & 0x0004:
                sht3x_logger.info ("  Reserved (undocumented)")
            if reg_value & 0x0002:
                sht3x_logger.info ("  Last command not processed")
            if reg_value & 0x0001:
                sht3x_logger.info ("  Checksum of last write transfer failed")

        return reg_value


    #=====================================================================================
    #=====================================================================================
    #  c l e a r _ s t a t u s _ r e g
    #=====================================================================================
    #=====================================================================================

    def clear_status_reg(self):
        """
## clear_status_reg () - Clear the status register

***SHT3x class member function***


### Returns
- 0 on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- `clear_status_reg()` clears only the alert status bits 15, 11, and 10, and bit 4 (System reset detected).
Other bits, including undocumented bits, are not cleared.
"""

        sht3x_logger.debug (f"<{self.device_name}> ***** clear_status_reg()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, CLEAR_STATUS_REGISTER)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


    #=====================================================================================
    #=====================================================================================
    #  h e a t e r _ e n a b l e
    #=====================================================================================
    #=====================================================================================

    def heater_enable(self):
        """
## heater_enable () - Turn the heater on

***SHT3x class member function***


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
"""

        sht3x_logger.debug (f"<{self.device_name}> ***** heater_enable()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, HEATER_ENABLE)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


    #=====================================================================================
    #=====================================================================================
    #  h e a t e r _ d i s a b l e
    #=====================================================================================
    #=====================================================================================

    def heater_disable(self):
        """
## heater_disable () - Turn the heater off

***SHT3x class member function***


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
"""

        sht3x_logger.debug (f"<{self.device_name}> ***** heater_disable()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, HEATER_DISABLE)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ a l e r t _ r e g
    #=====================================================================================
    #=====================================================================================

    def read_alert_reg(self, reg_select, tempunits='C', force_CRC_fail=False):
        """
## read_alert_reg (reg_select, tempunits='C', force_CRC_fail=False) - Fetch temperature and RH alert values from selected register

***SHT3x class member function***


### Args
`reg_select` (str)
- One of 'High_Set', 'High_Clear', 'Low_Clear', or 'Low_Set'

`tempunits` (str, default 'C', case-independent)
- Must be 'C', 'F' or 'K'

`force_CRC_fail` (bool, default False)
- Used for validation


### Returns
- (Temperature, RH) tuple on success
- (I2C_ERROR, I2C_ERROR) tuple on I2C IO error
- (CRC_ERROR, CRC_ERROR) tuple on fetched data CRC mismatch
- Raises ValueError if `reg_select` or `tempunits` is invalid
"""

        try:
            reg_code = READ_ALERT_MODES[reg_select]
        except:
            raise ValueError (f"<{self.device_name}> Invalid Alert Register selection - received <{reg_select}>")
        sht3x_logger.debug (f"<{self.device_name}> ***** read_alert_reg() <{reg_select}>")

        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, reg_code)
            (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 3)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR, I2C_ERROR

        if count != 3:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR - error code <{count}>")
            return I2C_ERROR, I2C_ERROR

        if force_CRC_fail:
            data[2] = 0x00
        if crc_calc.checksum(bytes([data[0], data[1]])) != data[2]:
            sht3x_logger.debug (f"<{self.device_name}> Alert register <{reg_select}> data CRC error")
            return CRC_ERROR, CRC_ERROR
        
        temp, rh = self._decode_alert_word (data[0] <<8 | data[1], tempunits)
        sht3x_logger.debug (f"<{self.device_name}> <{reg_select}> temp: <{temp:5.1f}{tempunits}>, rh: <{rh:5.1f}%>")

        return temp, rh


    #=====================================================================================
    #=====================================================================================
    #  w r i t e _ a l e r t _ r e g
    #=====================================================================================
    #=====================================================================================

    def write_alert_reg(self, reg_select, temp, rh, tempunits='C', force_CRC_fail=False):
        """
## write_alert_reg (reg_select, temp, rh, tempunits='C', force_CRC_fail=False) - Write temperature and RH alert values to selected register

***SHT3x class member function***


### Args
`reg_select` (str)
- One of 'High_Set', 'High_Clear', 'Low_Clear', or 'Low_Set'

`temp` (int or float)
- Temperature value in `tempunits`
- Must be in range of -40C to 125C

`rh` (int or float)
- Relative humidity value in %
- Must be in range of 0% to 100%

`tempunits` (str, default 'C', case-independent)
- Must be 'C', 'F' or 'K'

`force_CRC_fail` (bool, default False)
- Used for validation


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
- Raises ValueError if `reg_select` or `tempunits` are invalid, or `temp` or `rh` are out of range


### Behaviors and rules
- A CRC error on the write data to the alert registers causes a stuck I2C bus, requiring a power cycle to recover.
"""

        try:
            reg_code = WRITE_ALERT_MODES[reg_select]
        except:
            raise ValueError (f"<{self.device_name}> Invalid Alert Register selection - received <{reg_select}>")

        if tempunits.lower() == 'c':
            tempC = temp
        elif tempunits.lower() == 'f':
            tempC = FtoC(tempC)
        elif tempunits.lower() == 'k':
            tempC = KtoC(tempC)
        else:
            raise ValueError (F"<{self.device_name}> tempunits must be 'C', 'F', or 'K' - received <{tempunits}>")

        if tempC < -40.0  or  tempC > 125.0:
            raise ValueError (f"<{self.device_name}> Invalid temperature value - Expecting -40C <= temp value <= 125C - received <{tempC}C>")

        if rh < 0.0  or  rh > 100.0:
            raise ValueError (f"Invalid RH value - Expecting 0.0 <= rh value <= 100.0 - received <{rh}>")

        tempbits =  _encode_temp(tempC) >> 7
        rhbits =    _encode_rh(rh) & 0xfe00
        regbits = rhbits | tempbits
        sht3x_logger.debug (f"<{self.device_name}> ***** write_alert_reg() <{reg_select}>: <{self._decode_alert_word(regbits, tempunits)}>")
        MSB = regbits >> 8
        LSB = regbits & 0xff
        regCRC = crc_calc.checksum(bytes([MSB, LSB]))  if not force_CRC_fail  else 0x00

        payload = reg_code
        payload.append(MSB)
        payload.append(LSB)
        payload.append(regCRC)

        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, payload)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        return 0

    #---------------------------------------------------------------------
    def _decode_alert_word (self, word, tempunits):
        # Upper 7 bits are the RH value MSBs
        # Lower 9 bits are the Temp value MSBs
        # Returns tuple (temp (in C or F), rh)

        tempbits = (word & 0x01ff) << 7
        temp = _decode_temp(tempbits)

        _tempunits = tempunits.lower()
        if _tempunits not in ['c', 'f', 'k']:
            raise ValueError (F"<{self.device_name}> tempunits must be 'C', 'F', or 'K' - received <{tempunits}>")

        if _tempunits == 'f':
            temp = CtoF(temp)
        elif _tempunits == 'k':
            temp = CtoK(temp)

        rh = _decode_rh (word & 0xfe00)
        return temp, rh


def _decode_temp (tempbits):     # returns tempC
    return -45.0 + (175 * tempbits / 65535)   #(2**16 -1))

def _encode_temp (tempC):
    return int((tempC + 45.0) / (175/65535))

def _decode_rh (rhbits):
    return 100.0 * rhbits / 65535

def _encode_rh (rh):
    return int(rh / 100.0 * 65535)
