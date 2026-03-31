# MCP23008 8-Bit I/O Expander library for Raspberry Pi

Skip to the [API documentation](#links)

This module provides a clean and complete API for the MCP23008 8-Bit I/O Expander.  The SPI-based MCP23S08 is not supported.

Supports:
- Configuration of the IO pins and interrupt features
- Per-pin settings control
- Detailed debug-level visibility on operations
- Both smbus and pigpio (local and remote) interfaces/APIs

Tested on Python 3.9.2.

NOTE:  My applications don't use the INT pin.
Full access to all of the registers is implemented, but the functionality of the interrupt hardware is not tested.

Do read the [fine datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/MCP23008-MCP23S08-Data-Sheet-20001919F.pdf).


<br>

## Using the API

Example code:
```
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

logging.info (f"<{my_iochip.device_name}> GPIO after initialization:                   <0b{my_iochip.read_reg('GPIO'):0>8b}>")
my_iochip.set_bits('OLAT', bits=0b0100, mask=0b1100)
logging.info (f"<{my_iochip.device_name}> GPIO after upper 2 output bits were flipped: <0b{my_iochip.read_reg('GPIO'):0>8b}>")
logging.info (my_iochip.registers_dump())


# Clean up
i2c_bus_handle.close()
```

And running it:
```
$ ./MCP23008_README_ex.py 
INFO:root:<My_IOchip> GPIO after initialization:                   <0b11111010>
INFO:root:<My_IOchip> GPIO after upper 2 output bits were flipped: <0b11110110>
INFO:root:
  IODIR   :  Init value: 0b11110000, Cached value: 0b11110000, Read value: 0b11110000
  IPOL    :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b00000000
  GPINTEN :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b00000000
  DEFVAL  :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b00000000
  INTCON  :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b00000000
  IOCON   :  Init value: 0b00100000, Cached value: 0b00100000, Read value: 0b00100000
  GPPU    :  Init value: 0b11110000, Cached value: 0b11110000, Read value: 0b11110000
  INTF    :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b00000000
  INTCAP  :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b00000000
  GPIO    :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b11110110
  OLAT    :  Init value: 0b00001010, Cached value: 0b00000110, Read value: 0b00000110
```

- 'GPIO Read value' shows that the upper 4 bits (inputs with weak pullups enabled) read as logic 1, and the lower 4 output pin states as captured by their input buffers.
- 'OLAT Read value' shows 0b0110 on the lower 4 bits (programmed output states) after `my_iochip.set_bits()` modified the upper two output pins.

<br>

## Enabling debug logging

To enabled debug logging from this module's classes/functions, add this to your tool script code:

     logging.getLogger('cjn_PiTools.MCP23008').setLevel(logging.DEBUG)


<br>

## Setting the base configuration at instantiation

**Key to understand:** The APIs in this library are not tied to the specific registers.  Rather, when using these APIs the target registers are called out by string names, e.g., 'IODIR' and 'OLAT'.

The MCP23008 has 11 registers, listed below (see the datasheet for register details).  Without any customization, the default
configuration applied to a device is:
- All pins are configured as inputs with weak pullups turned off
- No interrupt features are enabled


- The registers and their default initialization values are:

    Reg name | Default initialization value | Notes
    --- | --- | ---
    'IODIR'   | 0b11111111 | All pins default to input mode
    'IPOL'    | 0b00000000 | See datasheet for interrupt related settings
    'GPINTEN' | 0b00000000
    'DEFVAL': | 0b00000000
    'INTCON': | 0b00000000
    'IOCON':  | 0b00100000 | Auto increment disabled, all other features per datasheet default
    'GPPU':   | 0b00000000 | All input pins default to weak pullups disabled
    'INTF':   | 0b00000000
    'INTCAP': | 0b00000000
    'GPIO':   | 0b00000000 | Read input pin states using the GPIO register
    'OLAT':   | 0b00000000 | Set output pin states using the OLAT register

Likely, you'll need changes to the default configuration.
At instantiation you have the ability to override the default configuration settings by providing an `init_settings` dictionary.
The format of the dictionary is `{'reg name1': init value1, 'reg name2': init value2, ... }`, as shown in the above example.  The device is initialized as the last step in instantiation, and it may be set back to the initialized state at any time by calling `my_iochip.initialize()`.

<br>

## The primary APIs for doing IO

The APIs `set_registers()`, `set_bits()`, `read_reg()` work on any register.

- `set_registers()` - Writing to any (or all) of the registers may be done with the `set_registers()` API. `set_registers()` takes a dictionary of `register:value` pairs just like `init_settings` in instantiation.  To set the output-enabled IO bits write to the OLAT register: `my_iochip.set_registers({'OLAT': 0b00001001})`.  Note that this API causes all eight bits of the target register(s) to be written.  Input pins are don't care in the OLAT register.

- `set_bits()` - Individual bits in a register may be selectively set/cleared using the `set_bits()` API.  In this example the `mask` arg selects the upper two output pins to be set per the `bits` arg: `my_iochip.set_bits('OLAT', bits=0b0100, mask=0b1100)`. Not mask selected output pins are left unchanged.  Input pins are don't care in the OLAT register.

- `read_reg()` - To read pins configured as inputs, read the GPIO register using `read_reg()`, e.g., `my_iochip.read_reg('GPIO')`.  Decode the pins states in your code as needed.

