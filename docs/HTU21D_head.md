# HTU21D Temperature/RH sensor library for Raspberry Pi

Skip to the [API documentation](#links)

This module provides a clean and complete API for the HTU21D temperature/RH sensor

Supports:
- Reading temperature and RH values using either I2C bus hold mode (aka clock stretching) or no-hold mode
- Writing and reading the User Register (aka the config/status register)
- Asserting a soft_reset
- Detailed debug-level visibility on operations
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

     logging.getLogger('cjn_PiTools.HTU21D').setLevel(logging.DEBUG)


