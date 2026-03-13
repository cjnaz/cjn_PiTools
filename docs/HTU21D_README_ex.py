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