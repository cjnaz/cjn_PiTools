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