#!/usr/bin/env python3
# MCP23008_README_ex.py available in the docs directory in the github repo

import logging
from cjn_PiTools.shared import pi_i2c
from cjn_PiTools.MCP23008 import MCP23008

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
# logging.getLogger('cjn_PiTools.MCP23008').setLevel(logging.DEBUG)

IOCHIP_CONFIG = {
    'IODIR': 0b11110000,    # Upper 4 bits are ins, lower 4 are outs
    'GPPU' : 0b11110000,    # Enable weak pullups on inputs
    'OLAT' : 0b00001010,    # Set the four outputs
    }


i2c_bus_handle =    pi_i2c('smbus')
my_iochip =         MCP23008('My_IOchip', 0x20, i2c_bus_handle, init_settings=IOCHIP_CONFIG)

logging.info (f"<{my_iochip.device_name}> After initialization:                   <0b{my_iochip.read_reg('GPIO'):0>8b}>")
my_iochip.set_bits('OLAT', bits=0b0100, mask=0b1100)
logging.info (f"<{my_iochip.device_name}> After upper 2 output bits were flipped: <0b{my_iochip.read_reg('GPIO'):0>8b}>")
logging.info (my_iochip.registers_dump())


# Clean up
i2c_bus_handle.close()