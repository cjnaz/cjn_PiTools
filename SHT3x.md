# SHT3x Temperature/RH sensor library for Raspberry Pi

Skip to [API documentation](#links)

This module provides a clean and complete API for SHT3x series of temperature/RH sensors, including SHT30, SHT31, and SHT35.

Supports:
- Reading single-shot mode temperature and RH values using either I2C bus clock stretching mode or non-clock stretching mode (your code is responsible for measurement delays)
- Enabling all Periodic Data Acquisition Modes (including ART) and data read back
- Read and decode, and clear the status register
- Control of the on-die heater
- Configuring and read back of the alert registers
- Asserting a soft_reset
- Both smbus and pigpio (local and remote) interfaces/APIs

Tested on Python 3.9.2

Do read the [fine datasheet](https://sensirion.com/media/documents/213E6A3B/63A5A569/Datasheet_SHT3x_DIS.pdf) and the [AlertMode application note](https://sensirion.com/media/documents/40D749F7/65D61534/HT_AN_AlertMode.pdf).


<br>

## Using the API

Example code:
```
#!/usr/bin/env python3
# SHT3x_README_ex.py available in the docs directory in the github repo

import logging
from cjn_PiTools.shared import pi_i2c
from cjn_PiTools.SHT3x  import SHT3x

logging.basicConfig()
logging.getLogger('cjn_PiTools.SHT3x').setLevel(logging.DEBUG)

i2c_bus_handle =    pi_i2c('smbus')
my_sht3x =          SHT3x('My_SHT3x', 0x44, i2c_bus_handle)

temp, rh = my_sht3x.single_shot()
logging.warning (f"Current temperature for sensor {my_sht3x.device_name}:  " + \
                 f"{temp:7.3f} C,  RH:  {rh:7.3f} %")
               

# Clean up
i2c_bus_handle.close()
```

And running it:
```
$ ./SHT3x_README_ex.py 
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> ***** soft_reset()
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> Status reg:  0x0000
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> New SHT3x device defined at addr <0x44> using api <smbus> on i2c bus <1>
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> ***** single_shot()
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> ***** fetch_data()
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> Temp/RH raw data:
  temp data returned bytes: 0x64 0x7f 0x81,  calc CRC: <0x81>
  RH   data returned bytes: 0x6d 0x8e 0xf1,  calc CRC: <0xf1>
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> Calculated temp (C):      23.7
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> Calculated RH:            42.8
WARNING:root:Current temperature for sensor My_SHT3x:   23.700 C,  RH:   42.795 %
```

<br>

## Enabling debug logging

To enabled debug logging from this module's classes/functions, add this to your tool script code:

     logging.getLogger('cjn_PiTools.SHT3x').setLevel(logging.DEBUG)




<a id="links"></a>
         
<br>

---

# Links to classes, methods, and functions

- [SHT3x](#SHT3x)
- [soft_reset](#soft_reset)
- [single_shot](#single_shot)
- [start_periodic_DA](#start_periodic_DA)
- [start_ART](#start_ART)
- [stop_periodic_DA](#stop_periodic_DA)
- [fetch_data](#fetch_data)
- [read_status_reg](#read_status_reg)
- [clear_status_reg](#clear_status_reg)
- [heater_enable](#heater_enable)
- [heater_disable](#heater_disable)
- [read_alert_reg](#read_alert_reg)
- [write_alert_reg](#write_alert_reg)



<br/>

<a id="SHT3x"></a>

---

# Class SHT3x (device_name, device_addr, pi_i2c_bus_handle, do_reset) - SHT3x Temperature/RH sensor library for Raspberry Pi

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


### Class instance variables - as passed in at instantiation
- `device_name` (str)
- `device_addr` (int)


### Returns
- Handle to the SHT3x instance on success
- Raises ValueError if args checks fail
- Raises RuntimeError if the device fails soft reset


### Behaviors and rules
- Per the datasheet, "After sending a command to the sensor a minimal waiting time of 1ms is needed before another command
can be received by the sensor." Normally, the time between consecutive API calls takes >1ms, so no padding seems necessary.
- Debug logging may be enabled in the tool script code by setting this module's logging level:

        logging.getLogger('cjn_PiTools.SHT3x').setLevel(logging.DEBUG)

<br/>

<a id="soft_reset"></a>

---

# soft_reset (reset_wait=1.5) - Issue a soft_reset

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

<br/>

<a id="single_shot"></a>

---

# single_shot (tempunits='C', repeatability='High', reading_wait=-1, fetch_data=True) - Issue a single shot temperature/RH measurement and read back the results

***SHT3x class member function***

NOTE that this is a blocking operation for the duration of the internal temperature measurement conversion or 
`reading_wait` time.

The _trigger mode_ is the combination of the `repeatability` setting and the `reading_wait` setting (whether clock 
stretching mode is enabled or not)


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

<br/>

<a id="start_periodic_DA"></a>

---

# start_periodic_DA (repeatability='High', mps=2) - Start Periodic Data Acquisition Mode

***SHT3x class member function***


### Args
`repeatability` (str, default 'High')
- Select repeatability setting 'High', 'Medium', or 'Low' per datasheet, with corresponding measurement time differences

mps (int or float, default 2)
- Measurements per second.
- Allowed values are 0.5, 1, 2, 4, and 10


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
- Raises ValueError if `repeatability` is invalid


### Behaviors and rules
- Status bit 0x0020 indicates Periodic / free running measurement mode is active (undocumented)
- Status bit 0x0040 indicates new measurement data is available (undocumented)
- Attempting to fetch data more frequently than new data is available results in 
`fetch_data()` returning (I2C_ERROR, I2C_ERROR) and debug logging will show:
  - smbus api:  OSError: [Errno 121] Remote I/O error
  - pigpio api: OSError: i2c_read_device failed - error code <-83>

<br/>

<a id="start_ART"></a>

---

# start_ART () - Start Periodic Data Acquisition Mode using Accelerated Response Time

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

<br/>

<a id="stop_periodic_DA"></a>

---

# stop_periodic_DA () - Stop Periodic Data Acquisition Mode, including ART mode

***SHT3x class member function***


### Returns
- 0 on success
- I2C_ERROR on I2C IO error

<br/>

<a id="fetch_data"></a>

---

# fetch_data (tempunits='C', send_fetch=True, force_CRC_fail=False) - Fetch temperature and RH data from the device

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

<br/>

<a id="read_status_reg"></a>

---

# read_status_reg (quiet=False, force_CRC_fail=False) - Read and return the status register

***SHT3x class member function***


### Args
`quiet` (bool, default False)
- Set True by SHT3x class internal calls for debugging logging

`force_CRC_fail` (bool, default False)
- Used for validation


### Returns
- 2-byte status register value on success
- I2C_ERROR on I2C IO error
- CRC_ERROR on fetched data CRC mismatch


### Behaviors and rules
- If `quiet=False` and module debug logging is enabled the status register bits are decoded and logged
- Status register bit 4 (reset detected) does not seem to be set by a soft_reset(), contrary to the datasheet.

<br/>

<a id="clear_status_reg"></a>

---

# clear_status_reg () - Clear the status register

***SHT3x class member function***


### Returns
- 0 on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- `clear_status_reg()` clears only the alert status bits 15, 11, and 10, and bit 4 (System reset detected).
Other bits, including undocumented bits, are not cleared.

<br/>

<a id="heater_enable"></a>

---

# heater_enable () - Turn the heater on

***SHT3x class member function***


### Returns
- 0 on success
- I2C_ERROR on I2C IO error

<br/>

<a id="heater_disable"></a>

---

# heater_disable () - Turn the heater off

***SHT3x class member function***


### Returns
- 0 on success
- I2C_ERROR on I2C IO error

<br/>

<a id="read_alert_reg"></a>

---

# read_alert_reg (reg_select, tempunits='C', force_CRC_fail=False) - Fetch temperature and RH alert values from selected register

***SHT3x class member function***


### Args
'reg_select' (str)
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

<br/>

<a id="write_alert_reg"></a>

---

# write_alert_reg (reg_select, temp, rh, tempunits='C', force_CRC_fail=False) - Write temperature and RH alert values to selected register

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
- Raises ValueError if `reg_select` or `tempunits` is invalid, or temp or rh is out of range


### Behaviors and rules
- A CRC error on the write data to the alert registers causes a stuck I2C bus error, requiring a power cycle to recover.
