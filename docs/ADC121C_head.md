# ADC121C (and related family) ADC driver for Raspberry Pi

Skip to [API documentation](#links)

This module provides a clean and complete API for the ADC121C ADC, and related family devices, including:
- ADC121C021, ADC121C021Q, and ADC121C027 12-bit ADCs
- ADC101C021, ADC101C021Q, and ADC101C027 10-bit ADCs
- ADC081C021, ADC081C021Q, and ADC081C027 8-bit ADCs

Supports both smbus and pigpio (local and remote) interfaces/APIs

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

