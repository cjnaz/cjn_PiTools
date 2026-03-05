# ADC121C (and related family) ADC driver for Raspberry Pi

Skip to [API documentation](#links)

This module provides a clean and complete API for the ADC121C ADC, and related family devices, including:
- ADC121C021, ADC121C021Q, and ADC121C027 12-bit ADCs
- ADC101C021, ADC101C021Q, and ADC101C027 10-bit ADCs
- ADC081C021, ADC081C021Q, and ADC081C027 8-bit ADCs

Tested on Python 3.9.2.

Do read the [fine datasheet](https://www.ti.com/lit/ds/symlink/adc121c021.pdf?ts=1772539859300&ref_url=https%253A%252F%252Fwww.ti.com%252Fproduct%252FADC121C021).


<br>

## Using the API

Example code:
```
#!/usr/bin/env python3
# ADC121C_README_ex.py available in the docs directory in the github repo

import logging
from cjn_PiTools.shared import pi_i2c
from cjn_PiTools.ADC121C import ADC121C

logging.basicConfig()
logging.getLogger('cjn_PiTools.ADC121C').setLevel(logging.DEBUG)

VA =                    4.2        # Supply and reference voltage

pio_i2c_bus_handle =    pi_i2c('smbus')
ADC121C_0x50 =          ADC121C('My_ADC121C', 0x50, pio_i2c_bus_handle, VA)

print (f"<{ADC121C_0x50.device_name}> measured: <{ADC121C_0x50.read()}>")

# Clean up
pio_i2c_bus_handle.close()
```

And running it:
```
$ ./ADC121C_README_ex.py 
DEBUG:cjn_PiTools.ADC121C:Initialize of <My_ADC121C> success
DEBUG:cjn_PiTools.ADC121C:<My_ADC121C> New ADC121C device defined at addr <0x50> using api <smbus> on i2c bus <1>
DEBUG:cjn_PiTools.ADC121C:Conversion result <My_ADC121C>:  (0x07 0xfd) = 2.097 V
<My_ADC121C> measured: <2.096923828125>
```

<br>

## Enabling debug logging

To enabled debug logging from this module's classes/functions, add this to your tool script code:

     logging.getLogger('cjn_PiTools.ADC121C').setLevel(logging.DEBUG)



<a id="links"></a>
         
<br>

---

# Links to classes, methods, and functions

- [ADC121C](#ADC121C)
- [read_conversion_result](#read_conversion_result)
- [read_alert_status](#read_alert_status)
- [write_alert_status](#write_alert_status)



<br/>

<a id="ADC121C"></a>

---

# Class ADC121C (device_name, device_addr, pi_i2c_bus_handle, Vref, config_byte=None, cycle_time=0b000, alert_hold=0, alert_flag_en=0, alert_pin_en=0, polarity=0 ) - ADC121Cxxx library for Raspberry Pi

Create an ADC121C family device instance

### Args
`device_name` (str)
- User defined name for this instance, e.g., 'PCA9548'
- Not validated as valid string

`device_addr` (int)
- I2C bus address for this instance, e.g., 0x70

`pi_i2c_bus_handle` (cjn_PiTools.shared.pi_i2c instance)
- Get an instance handle in the tools script code and pass it to this device instantiation

`Vref` (float)
- ADC reference voltage
- `read_conversion_result()` returned 12-bit code is multiplied by this value to return measured voltage

`config_byte` (int, optional, default None)
- Used for direct setting of the configuration register to a byte value during instantiation
- Must be in range 0x00 to 0xFF

`cycle_time` (int, default 0b000)
- Value for the 3-bit Cycle Time field in the configuration register
- Must be in range 0b000 to 0b111
- Default 0b000 is Automatic Mode Disabled
- This value will be used as the default value in later `write_config()` calls

`alert_hold` (int, default 0)
- Value for the Alert Hold field in the configuration register
- Must be 0 or 1
- Default 0 is Alert Hold disabled - alerts will self-clear
- This value will be used as the default value in later `write_config()` calls

`alert_flag_en` (int, default 0)
- Value for the Alert Flag Enable field in the configuration register
- Must be 0 or 1
- Default 0 is Alert Flag disabled - disable alert status bit [D15] in the Conversion Result register
- This value will be used as the default value in later `write_config()` calls

`alert_pin_en` (int, default 0)
- Value for the Alert Pin Enable field in the configuration register
- Must be 0 or 1
- Default 0 is Alert Pin disabled - disable the ALERT output pin
- This value will be used as the default value in later `write_config()` calls
- NOTE:  The Alert Pin function is not tested. (I'm using the ADC121C027 (no alert pin))

`polarity` (int, default 0)
- Value for the alert pin Polarity field in the configuration register
- Must be 0 or 1
- Default 0 - the ALERT pin to active low
- This value will be used as the default value in later `write_config()` calls
- NOTE:  The Alert Pin function is not tested. (I'm using the ADC121C027 (no alert pin))


### Class instance variables
- `device_name` (str)
- `device_addr` (int)
- `Vref` (float)
- `cycle_time` (int)
- `alert_hold` (int)
- `alert_flag_en` (int)
- `alert_pin_en` (int)
- `polarity` (int)


### Behaviors and rules
- Debug logging may be enabled in the tool script code by setting this module's logging level:

        logging.getLogger('cjn_PiTools.ADC121C').setLevel(logging.DEBUG)

<br/>

<a id="read_conversion_result"></a>

---

# read_conversion_result () - Return the measured voltage

***ADC121C class member function***


### Args TODO
`tempunits` (str, default 'C')
- Must be 'C', 'F' or 'K', else ValueError is raised.


### Returns
- Tuple (Alert Flag bit, Measured Voltage)
- Tuple (I2C_ERROR, I2C_ERROR) on any communication errors
- Raises `ValueError` if tempunits is not valid  TODO


### Behaviors and rules
- The 12-bit code read from the device is scaled by Vref and returned as the measured voltage
- Setting the register Address Pointer to the Conversion Result register is skipped on consecutive calls
to `read_conversion_result()`

<br/>

<a id="read_alert_status"></a>

---

# read_alert_status () - Return Over-range and Under-range alerts 

***ADC121C class member function***


### Returns
- Tuple (over_range_alert, under_range_alert) as integers (0 or 1)
- 1 indicates respective over-range or under-range altert
- Tuple (I2C_ERROR, I2C_ERROR) on any communication errors

<br/>

<a id="write_alert_status"></a>

---

# write_alert_status (clear_over=0, clear_under=0) - Selectively clear the Over-range and Under-range alert flags

***ADC121C class member function***

### Args
`clear_over` (int, default 0)
- Must be 0 or 1
- If 1, clear the Over Range Alert Flag

`clear_under` (int, default 0)
- Must be 0 or 1
- If 1, clear the Under Range Alert Flag


### Returns
- 0 on success
- I2C_ERROR on any communication errors
