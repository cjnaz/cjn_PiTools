# SHT3x Temperature/RH sensor library for Raspberry Pi

Skip to [API documentation](#links)

This module provides a clean and complete API for the SHT3x series of temperature/RH sensors, including SHT30, SHT31, and SHT35.

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

temp, rh =          my_sht3x.single_shot()
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
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> ***** clear_status_reg()
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> Status reg:  0x0000
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> New SHT3x device defined at addr <0x44> using api <smbus> on i2c bus <1>
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> ***** single_shot()  <High_CS>
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> ***** fetch_data()
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> Temp/RH raw data:
  temp data returned bytes: 0x66 0xba 0xea,  calc CRC: <0xea>
  RH   data returned bytes: 0x6c 0x07 0xf7,  calc CRC: <0xf7>
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> Calculated temp (C):      25.2
DEBUG:cjn_PiTools.SHT3x:<My_SHT3x> Calculated RH:            42.2
WARNING:root:Current temperature for sensor My_SHT3x:   25.224 C,  RH:   42.199 %
```

<br>

## Enabling debug logging

To enabled debug logging from this module's classes/functions, add this to your tool script code:

     logging.getLogger('cjn_PiTools.SHT3x').setLevel(logging.DEBUG)


