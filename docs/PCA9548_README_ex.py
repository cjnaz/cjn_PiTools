#!/usr/bin/env python3
# PCA9548_README_ex.py available in the docs directory in the github repo

import logging
from cjn_PiTools.shared import pi_i2c
from cjn_PiTools.PCA9548 import PCA9548

logging.basicConfig()
logging.getLogger('cjn_PiTools.PCA9548').setLevel(logging.DEBUG)


pio_i2c_bus_handle =    pi_i2c('smbus')
PCA9548_0x71 =          PCA9548('My_PCA9548', 0x71, pio_i2c_bus_handle)

# Apply a channel enable mask and read the control register back
PCA9548_0x71.write_control_reg(0x55)
print (f"<{PCA9548_0x71.device_name}> Control register: <0b{PCA9548_0x71.read_control_reg():0>8b}>")


# Disable all channels
PCA9548_0x71.write_control_reg('-1')
# or
PCA9548_0x71.write_control_reg(0x00)

# Select specific channel 0-7
PCA9548_0x71.write_control_reg('3')

# Clean up
pio_i2c_bus_handle.close()