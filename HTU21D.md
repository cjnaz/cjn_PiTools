# HTU21D Temperature/RH sensor library for Raspberry Pi

Skip to [API documentation](#links)

This module provides a clean and complete API for HTU21D temperature/RH sensor.

Supports:
- Reading temperature and RH values using either I2C bus hold mode (aka clock stretching) or no-hold mode
- Writing and reading the User Register (aka the config/status register)
- Asserting a soft_reset
- Both smbus and pigpio (local and remote) interfaces/APIs

Tested on Python 3.9.2

Do read the [fine datasheet](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=HPC199_6&DocType=Data%20Sheet&DocLang=English&DocFormat=pdf&PartCntxt=CAT-HSC0004).


<br>

## Using the API

Example code:
```
#!/usr/bin/env python3
# HTU21D_README_ex.py available in the docs directory in the github repo

import logging
from cjn_PiTools.shared import pi_i2c
from cjn_PiTools.HTU21D import HTU21D

logging.basicConfig()
logging.getLogger('cjn_PiTools.HTU21D').setLevel(logging.DEBUG)

i2c_bus_handle = pi_i2c('smbus')
htu21d =         HTU21D('My_HTU21D', i2c_bus_handle)

logging.warning (f"Current temperature for sensor {htu21d.device_name}:  " + \
                 f"{htu21d.read_temperature(tempunits='F'):7.3f} F,  " + \
                 f"RH:  {htu21d.read_RH():7.3f} %")

# Clean up
i2c_bus_handle.close()
```

And running it:
```
$ ./HTU21D_README_ex.py 
DEBUG:cjn_PiTools.HTU21D:<My_HTU21D> ***** soft_reset()
DEBUG:cjn_PiTools.HTU21D:<My_HTU21D> New HTU21D device defined at addr <0x40> using api <smbus> on i2c bus <1>
DEBUG:cjn_PiTools.HTU21D:<My_HTU21D> ***** read_temperature()
DEBUG:cjn_PiTools.HTU21D:<My_HTU21D> ***** fetch_temperature()
DEBUG:cjn_PiTools.HTU21D:<My_HTU21D>  Raw bytes:  0x69 0x88 0x55
DEBUG:cjn_PiTools.HTU21D:<My_HTU21D> - Temperature:    (F):  <78.05715722656248>
DEBUG:cjn_PiTools.HTU21D:<My_HTU21D> ***** read_RH()
DEBUG:cjn_PiTools.HTU21D:<My_HTU21D> ***** fetch_RH()
DEBUG:cjn_PiTools.HTU21D:<My_HTU21D>  Raw bytes:  0x59 0xce 0x7c
DEBUG:cjn_PiTools.HTU21D:<My_HTU21D> - RH:                   <37.84613037109375>
WARNING:root:Current temperature for sensor My_HTU21D:   78.057 F,  RH:   37.846 %
```

<br>

## Enabling debug logging

To enabled debug logging from this module's classes/functions, add this to your tool script code:

     logging.getLogger('cjn_PiTools.DS18B20').setLevel(logging.DEBUG)




<a id="links"></a>
         
<br>

---

# Links to classes, methods, and functions

- [HTU21D](#HTU21D)
- [soft_reset](#soft_reset)
- [read_user_reg](#read_user_reg)
- [write_user_reg](#write_user_reg)
- [read_temperature](#read_temperature)
- [trigger_temperature_nohold](#trigger_temperature_nohold)
- [fetch_temperature](#fetch_temperature)
- [read_RH](#read_RH)
- [trigger_RH_nohold](#trigger_RH_nohold)
- [fetch_RH](#fetch_RH)



<br/>

<a id="HTU21D"></a>

---

# Class HTU21D (device_name, pi_i2c_bus_handle) - HTU21D library for Raspberry Pi

Create an HTU21D device instance

### Args
`device_name` (str)
- User defined name for this instance, e.g., 'My_HTU21D'
- Not validated as valid string

`pi_i2c_bus_handle` (cjn_PiTools.shared.pi_i2c instance)
- Get a `pi_i2c` instance handle in the tools script code and pass it to this device instantiation

`do_soft_reset` (bool, default True)
- If True, issue a soft reset as part of instantiation


### Class instance variables - as passed in at instantiation
- `device_name` (str)
- `device_addr` (int 0x40 - fixed value for this sensor model)


### Returns
- Handle to the HTU21D instance on success
- Raises RuntimeError if the device fails soft reset


### Behaviors and rules
- A `soft_reset()` is applied as part of instantiation
- Debug logging may be enabled in the tool script code by setting this module's logging level:

        logging.getLogger('cjn_PiTools.HTU21D').setLevel(logging.DEBUG)

<br/>

<a id="soft_reset"></a>

---

# soft_reset () - Execute a soft reset

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

<br/>

<a id="read_user_reg"></a>

---

# read_user_reg () - Return the content of the user register

***HTU21D class member function***

The user register is the configuration and status register


### Returns
- User register content for successful operation
- I2C_ERROR on I2C IO error


### Behaviors and rules
- If debug logging is enabled the register content is decoded and logged

<br/>

<a id="write_user_reg"></a>

---

# write_user_reg (resolution=None, heater_enable=None, OTP_reload_disable=None) - Set fields in the user register

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

<br/>

<a id="read_temperature"></a>

---

# read_temperature (tempunits='C') - Trigger a hold mode temperature measurement and return the measured temperature

***HTU21D class member function***

NOTE that this is a blocking operation for the duration of the internal temperature measurement conversion.

Calls `fetch_temperature()` after triggering the hold mode temperature measurement.  See `fetch_temperature()` for
Args, Returns, and Behaviors info.  

<br/>

<a id="trigger_temperature_nohold"></a>

---

# trigger_temperature_nohold () - Trigger measurement in no-hold mode

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

<br/>

<a id="fetch_temperature"></a>

---

# fetch_temperature (tempunits='C') - Retrieve measured temperature

***HTU21D class member function***


### Args
`tempunits` (str, default 'C', case-independent)
- Must be 'C', 'F' or 'K'


### Returns
- Temperature value in specified tempunits on success
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

<br/>

<a id="read_RH"></a>

---

# read_RH () - Trigger a hold mode relative humidity measurement and return the measured RH

***HTU21D class member function***

NOTE that this is a blocking operation for the duration of the internal RH measurement conversion.

Calls `fetch_RH()` after triggering the hold mode RH measurement.  See `fetch_RH()` for
Args, Returns, and Behaviors info.

<br/>

<a id="trigger_RH_nohold"></a>

---

# trigger_RH_nohold () - Trigger measurement in no-hold mode

***HTU21D class member function***

Issue a no-hold mode RH measurement.  The tool script code normally will follow up with a separate call to `fetch_RH()`.


### Returns
- 0 on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- Uses the no-hold RH measurement trigger.  Tool script code must separately call `fetch_RH()` to
obtain the measured result after an appropriate delay. See the datasheet for measurement times based on the resolution settings.
- If the measurement is still in progress then I2C_ERROR is returned, and `fetch_RH()` should be called again later.

<br/>

<a id="fetch_RH"></a>

---

# fetch_RH () - Retrieve measured relative humidity

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
