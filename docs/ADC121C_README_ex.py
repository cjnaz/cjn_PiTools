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