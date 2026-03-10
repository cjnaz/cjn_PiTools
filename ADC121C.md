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
- [write_config](#write_config)
- [read_config](#read_config)
- [write_vlow_alert_limit](#write_vlow_alert_limit)
- [read_vlow_alert_limit](#read_vlow_alert_limit)
- [write_vhigh_alert_limit](#write_vhigh_alert_limit)
- [read_vhigh_alert_limit](#read_vhigh_alert_limit)
- [write_alert_hysteresis](#write_alert_hysteresis)
- [read_alert_hysteresis](#read_alert_hysteresis)
- [write_lowest_conversion](#write_lowest_conversion)
- [read_lowest_conversion](#read_lowest_conversion)
- [write_highest_conversion](#write_highest_conversion)
- [read_highest_conversion](#read_highest_conversion)



<br/>

<a id="ADC121C"></a>

---

# Class ADC121C (device_name, device_addr, pi_i2c_bus_handle, Vref, config_byte=None, cycle_time=0b000, alert_hold=0, alert_flag_en=0, alert_pin_en=0, polarity=0 ) - ADC121Cxxx library for Raspberry Pi

Create an ADC121C family device instance

### Args
`device_name` (str)
- User defined name for this instance, e.g., 'My_ADC121C'
- Not validated as valid string

`device_addr` (int)
- I2C bus address for this instance, e.g., 0x50

`pi_i2c_bus_handle` (cjn_PiTools.shared.pi_i2c instance)
- Get a `pi_i2c` instance handle in the tools script code and pass it to this device instantiation

`Vref` (float)
- ADC reference voltage
- `read_conversion_result()` returned 12-bit code is scaled by this value to return the measured voltage

`config_byte` (int, default None)
- Used for explicit setting of the configuration register to a byte value during instantiation
- Must be in range 0x00 to 0xFF
- Bit 1 (Reserved) is always forced to `0`, per the specification
- If `config_byte` is an int, the field values within the `config_byte` are used as the default values in later `write_config()` calls
- `config_byte` takes precedent over the below individual field settings, if both are given at instantiation

`cycle_time` (int, default 0b000)
- Value for the 3-bit Cycle Time field in the configuration register
- Must be in range 0b000 to 0b111
- Default 0b000 is Normal Mode (automatic conversion mode disabled)
- This value (or the field bits within `config_byte` if specified) are used as the default value in later `write_config()` calls

`alert_hold` (int, default 0)
- Value for the Alert Hold field in the configuration register
- Must be 0 or 1
- Default 0 is Alert Hold disabled - alerts will self-clear
- This value (or the field bit within `config_byte` if specified) are used as the default value in later `write_config()` calls

`alert_flag_en` (int, default 0)
- Value for the Alert Flag Enable field in the configuration register
- Must be 0 or 1
- Default 0 is Alert Flag disabled - disable alert status bit [D15] in the Conversion Result register
- This value (or the field bit within `config_byte` if specified) are used as the default value in later `write_config()` calls

`alert_pin_en` (int, default 0)
- Value for the Alert Pin Enable field in the configuration register
- Must be 0 or 1
- Default 0 is Alert Pin disabled - disable the ALERT output pin
- This value (or the field bit within `config_byte` if specified) are used as the default value in later `write_config()` calls
- NOTE:  The Alert Pin function is not tested. (I'm using the ADC121C027 (no alert pin))

`polarity` (int, default 0)
- Value for the alert pin Polarity field in the configuration register
- Must be 0 or 1
- Default 0 - the ALERT pin is active low
- This value (or the field bit within `config_byte` if specified) are used as the default value in later `write_config()` calls
- NOTE:  The Alert Pin function is not tested. (I'm using the ADC121C027 (no alert pin))


### Class instance variables - as passed in at instantiation
- `device_name` (str)
- `device_addr` (int)
- `Vref` (float)
- `cycle_time` (int)
- `alert_hold` (int)
- `alert_flag_en` (int)
- `alert_pin_en` (int)
- `polarity` (int)


### Behaviors and rules
- All configuration register fields default to `0`:
  - `cycle_time` defaults to 0b000 - Normal mode (automatic conversion mode disabled)
  - `alert_hold`, `alert_flag_en`, and `alert_pin_en` each default to 0 - Disabled
  - `polarity` defaults to 0 - the alert pin is active low if `alert_pin_en` = 1
- If `config_byte` is an int the bit fields are parsed out and saved as their default values in the respective 
class instance variables, above.
- if `config_byte` is None then the individual field settings are used and saved as the default values in later 
calls to `write_config()`
- Settings via config_byte take precedent over settings via individual fields.
- Debug logging may be enabled in the tool script code by setting this module's logging level:

        logging.getLogger('cjn_PiTools.ADC121C').setLevel(logging.DEBUG)

<br/>

<a id="read_conversion_result"></a>

---

# read_conversion_result () - Return the measured voltage

***ADC121C class member function***


### Returns
- Tuple (Alert Flag bit, Measured Voltage (float))
- Tuple (I2C_ERROR, I2C_ERROR) on I2C IO error

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
- Tuple (I2C_ERROR, I2C_ERROR) on I2C IO error

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
- I2C_ERROR on I2C IO error

<br/>

<a id="write_config"></a>

---

# write_config (config_byte=None, cycle_time=None, alert_hold=None, alert_flag_en=None, alert_pin_en=None, polarity=None) - Set operating modes

***ADC121C class member function***

The config register may be written entirely using `config_byte` or by individual field settings,
with their default values set at instantiation.


### Args
`config_byte` (int, default None)
- Used for explicit setting of the configuration register to a byte value
- Must be in range 0x00 to 0xFF
- Bit 1 (Reserved) is always forced to `0`, per the specification
- If an int then the entire configuration register byte is written using this value, and the following args are ignored
- If None then the configuration register is built from the following args, with their default values set at instantiation

`cycle_time` (int, default None)
- Value for the 3-bit Cycle Time field in the configuration register
- Must be in range 0b000 to 0b111
- If an int (and `config_byte` is None) then the 3-bit Cycle Time field is set to this value
- If None (and `config_byte` is None), then the default value set at instantiation is used

`alert_hold` (int, default None)
- Value for the Alert Hold field in the configuration register
- Must be 0 or 1
- If an int (and `config_byte` is None) then the field is set to this value
- If None (and `config_byte` is None), then the default value set at instantiation is used

`alert_flag_en` (int, default None)
- Value for the Alert Flag Enable field in the configuration register
- Must be 0 or 1
- If an int (and `config_byte` is None) then the field is set to this value
- If None (and `config_byte` is None), then the default value set at instantiation is used

`alert_pin_en` (int, default None)
- Value for the Alert Pin Enable field in the configuration register
- Must be 0 or 1
- If an int (and `config_byte` is None) then the field is set to this value
- If None (and `config_byte` is None), then the default value set at instantiation is used

`polarity` (int, default None)
- Value for the Polarity field in the configuration register
- Must be 0 or 1
- If an int (and `config_byte` is None) then the field is set to this value
- If None (and `config_byte` is None), then the default value set at instantiation is used


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
- Raises `ValueError` if any args have illegal values


### Behaviors and rules
- If `config_byte` is an int (not None), then the configuration register will be written with this value.  This 
feature gives the tool script explicit control over the configuration register.
- If `config_byte` is None then the individual field args passed in on this call are overlaid on the field value defaults established at instantiation
to construct the configuration byte.  For example:
  - At instantiation, `cycle_time=0b100`, `alert_flag_en=1`, `alert_pin_en=1` and other fields default to 0
  - On this call, `cycle_time=0b001`, `alert_hold=1`, `alert_pin_en=0`, and `polarity=1`
  - The resultant configuration byte is 0b00111001 - `cycle_time=0b001`, `alert_hold=1`, `alert_flag_en=1`, `alert_pin_en=0`, and `polarity=1`

<br/>

<a id="read_config"></a>

---

# read_config () - Return the content of the configuration register 

***ADC121C class member function***


### Returns
- Configuration register byte on success
- I2C_ERROR on I2C IO error



### Behaviors and rules
- If debug logging is enabled then the configuration register value is decoded, e.g.,

        ADC121C.read_config     -    DEBUG:  <ADC_xx> configuration register <0b00111000> settings:
        cycle_time:     <0b001>
        alert_hold:     <1>
        alert_flag_en:  <1>
        alert_pin_en:   <0>
        polarity:       <0>

<br/>

<a id="write_vlow_alert_limit"></a>

---

# write_vlow_alert_limit (vlow) - Set the Vlow alert register voltage level

***ADC121C class member function***


### Args
`vlow` (float or int)
- Allowed range 0 to Vref (no 'V' units)


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
- Raises ValueError if `vlow` is invalid

<br/>

<a id="read_vlow_alert_limit"></a>

---

# read_vlow_alert_limit () - Return the Vlow alert register voltage level

***ADC121C class member function***


### Returns
- Vlow alert level voltage (float) on success
- I2C_ERROR on I2C IO error

<br/>

<a id="write_vhigh_alert_limit"></a>

---

# write_vhigh_alert_limit (vhigh) - Set the Vhigh alert register voltage level

***ADC121C class member function***


### Args
`vhigh` (float or int)
- Allowed range 0 to Vref (no 'V' units)


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
- Raises ValueError if `vhigh` is invalid

<br/>

<a id="read_vhigh_alert_limit"></a>

---

# read_vhigh_alert_limit () - Return the Vhigh alert register voltage level

***ADC121C class member function***


### Returns
- Vhigh alert level voltage (float) on success
- I2C_ERROR on I2C IO error

<br/>

<a id="write_alert_hysteresis"></a>

---

# write_alert_hysteresis (vhyst) - Set the Vhyst alert register voltage level

***ADC121C class member function***


### Args
`vhyst` (float or int)
- Allowed range 0 to Vref (no 'V' units)


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
- Raises ValueError if `vhyst` is invalid

<br/>

<a id="read_alert_hysteresis"></a>

---

# read_alert_hysteresis () - Return the Vhyst alert register voltage level

***ADC121C class member function***


### Returns
- Vhyst alert level voltage on success
- I2C_ERROR on I2C IO error

<br/>

<a id="write_lowest_conversion"></a>

---

# write_lowest_conversion () - Reset the lowest conversion capture register

***ADC121C class member function***

The reset state is 0x0FFF (maximum count value, effectively Vref).


### Returns
- 0 on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- See notes on `read_lowest_conversion()`

<br/>

<a id="read_lowest_conversion"></a>

---

# read_lowest_conversion () - Return the lowest conversion register voltage level

***ADC121C class member function***

The register value is converted to a voltage based on Vref.


### Returns
- The lowest measured/captured voltage (float) on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- The datasheet says that the capture lowest/highest conversion results only works with Automatic Conversion modes (Cycle Time codes 0b001 thru 0b111).
I find that the capture lowest/highest feature also works in Normal mode (Cycle Time code 0b000).
- If switching from an Automatic Conversion mode to Normal mode note that the lowest conversion register may capture code 0x0000 (0.0V).
If using the capture lowest/highest conversion feature it is best to read these registers before stopping the Automatic Conversion
mode (switching to Normal mode).

<br/>

<a id="write_highest_conversion"></a>

---

# write_highest_conversion () - Reset the highest conversion capture register

***ADC121C class member function***

The reset state is 0x0000 (minimum count value, effectively 0.0V).


### Returns
- 0 on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- See notes on `read_lowest_conversion()`

<br/>

<a id="read_highest_conversion"></a>

---

# read_highest_conversion () - Return the highest conversion register voltage level

***ADC121C class member function***

The register value is converted to a voltage based on Vref.


### Returns
- The highest measured/captured voltage (float) on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- See notes on `read_lowest_conversion()`
