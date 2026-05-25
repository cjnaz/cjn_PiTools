# PCA9548 I2C port expander library for Raspberry Pi

Skip to the [API documentation](#links)

This module provides a clean and complete API for the PCA9548A/TCA9548A 8-Channel I2C Switch (aka I2C port expander).
It also provides a command line interface for interactive dev/debug.

Supports:
- Reading and writing the PCA9548 control register via API and CLI
- Always-enabled channel(s) for I2C bus monitoring
- Detailed debug-level visibility on operations
- Both smbus and pigpio (local and remote) interfaces/APIs

Tested on Python 3.9.2.

Do read the [fine datasheet](https://www.ti.com/lit/gpn/pca9548a).


<br>

## Using the API

Example code:
```
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


# Disable all channels using str '-1'
PCA9548_0x71.write_control_reg('-1')
# or write the control register with all 0s
PCA9548_0x71.write_control_reg(0x00)

# Enable one specific channel 0-7 using str
PCA9548_0x71.write_control_reg('3')

# Clean up
pio_i2c_bus_handle.close()
```

And running it:
```
$ ./PCA9548_README_ex.py 
DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> New PCA9548 device defined at addr <0x71> using api <smbus> on i2c bus <1>, Monitor channel(s) enabled: <>
DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> ***** write_control_reg()
DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> New mask:     <0b01010101>, channels <0 2 4 6>
DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> ***** read_control_reg()
DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> Current mask: <0b01010101>, channels <0 2 4 6>
<My_PCA9548> Control register: <0b01010101>
DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> ***** write_control_reg()
DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> New mask:     <0b00000000>, channels <>
DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> ***** write_control_reg()
DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> New mask:     <0b00000000>, channels <>
DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> ***** write_control_reg()
DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> New mask:     <0b00001000>, channels <3>
```

<br>

## Enabling a monitor channel

At instantiation, a channel (or multiple channels) may be designated as a monitor channel.  This channel will always be
enabled, and can be used for monitoring/tracing bus activity.  Here's an example of designating channel 7 as a monitor channel, and enabling I2C bus traffic on channel 2:

    PCA9548_0x71 = PCA9548('My_PCA9548', 0x71, pio_i2c_bus_handle, monitor_ch='7')
    PCA9548_0x71.write_control_reg('2')
    PCA9548_0x71.read_control_reg()

Monitor channels can be seen as enabled in the debug logging at instantiation, and in `write_control_reg()` and `read_control_reg()` calls:

    DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> New PCA9548 device defined at addr <0x71> using api <smbus> on i2c bus <1>, Monitor channel(s) enabled: <7>
    DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> ***** write_control_reg()
    DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> New mask:     <0b10000100>, channels <2 7>
    DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> ***** read_control_reg()
    DEBUG:cjn_PiTools.PCA9548:<My_PCA9548> Current mask: <0b10000100>, channels <2 7>

<br>

## Enabling debug logging

To enabled debug logging from this module's classes/functions, add this to your tool script code:

     logging.getLogger('cjn_PiTools.PCA9548').setLevel(logging.DEBUG)


<br>

## Command Line Interface

Once installed a CLI tool is available.
NOTE that the set `Mask` value operates a bit differently between the API and CLI.
- For the CLI, `Mask` is always received as a str, and if it is between '0' to '7' then it is taken as an individual channel enable
- To apply a byte value to the control register the `Mask` value must use binary or hex notation (start with '0b' or '0x')
- '-1' to clear the control register is a special case

```
$ PCA9548 -h
usage: PCA9548 [-h] [-n NAME] [-A {smbus,pigpio}] [-H HOST] [-p PORT] [-v] [-V] {set,get} {0x70,0x71,0x72,0x73,0x74,0x75,0x76,0x77} [Mask]

PCA9548 set/get channel setting for Raspberry Pi

Mask values for set command
    0-7 enables that specific channel
    -1 sets the control register to 0b00000000 (no channels enabled)
    0xNN or 0bNNNNNNN sets the control register to this specific bit_mask (range 0x00 to 0xFF)
1.1

positional arguments:
  {set,get}             Operation command:  set or get
  {0x70,0x71,0x72,0x73,0x74,0x75,0x76,0x77}
                        I2C address of PCA9548 device 0x70 - 0x77
  Mask                  Set control register to this value (required for set operation)

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  PCA9548 device/function name (default PCA9548)
  -A {smbus,pigpio}, --api {smbus,pigpio}
                        Either 'smbus' or 'pigpio' (default 'pigpio')
  -H HOST, --host HOST  pigpio api target host (default 'localhost')
  -p PORT, --port PORT  pigpio api target host port number (default 8888)
  -v, --verbose         Print debug-level status and activity messages
  -V, --version         Print version number and exit
```

Example usage:
```
$ PCA9548 set 0x71 0b00110011 -vv
                             shared.__init__                       -    DEBUG:  Set up <pigpio> mode for i2c_bus_num <1>
                            PCA9548.__init__                       -    DEBUG:  <PCA9548> New PCA9548 device defined at addr <0x71> using api <pigpio> on i2c bus <1>
                            PCA9548.write_control_reg              -    DEBUG:  <PCA9548> ***** write_control_reg()
                            PCA9548.write_control_reg              -    DEBUG:  <PCA9548> New mask:     <0b00110011>, channels <0 1 4 5>
                             shared.i2c_write_byte                 -    DEBUG:  Using api <<pipio.pi host=localhost port=8888>> write bus <1> addr <0x71> data <0x33>
                             shared.get_pigpio_i2c_device_handle   -    DEBUG:  New i2c_device_handle: <0> for addr <0x71>
                             shared.close                          -    DEBUG:  Closing i2c_device_handle <0>

$ PCA9548 get 0x71
                            PCA9548.__init__                       -    DEBUG:  <PCA9548> New PCA9548 device defined at addr <0x71> using api <pigpio> on i2c bus <1>
                            PCA9548.read_control_reg               -    DEBUG:  <PCA9548> ***** read_control_reg()
                            PCA9548.read_control_reg               -    DEBUG:  <PCA9548> Current mask: <0b00110011>, channels <0 1 4 5>

$ PCA9548 set 7
usage: PCA9548 [-h] [-n NAME] [-A {smbus,pigpio}] [-H HOST] [-p PORT] [-v] [-V] {set,get} {0x70,0x71,0x72,0x73,0x74,0x75,0x76,0x77} [Mask]
PCA9548: error: argument Address: invalid choice: '7' (choose from '0x70', '0x71', '0x72', '0x73', '0x74', '0x75', '0x76', '0x77')

$ PCA9548 set 0x71 7
                            PCA9548.__init__                       -    DEBUG:  <PCA9548> New PCA9548 device defined at addr <0x71> using api <pigpio> on i2c bus <1>
                            PCA9548.write_control_reg              -    DEBUG:  <PCA9548> ***** write_control_reg()
                            PCA9548.write_control_reg              -    DEBUG:  <PCA9548> New mask:     <0b10000000>, channels <7>

$ PCA9548 set 0x71 -1
                            PCA9548.__init__                       -    DEBUG:  <PCA9548> New PCA9548 device defined at addr <0x71> using api <pigpio> on i2c bus <1>
                            PCA9548.write_control_reg              -    DEBUG:  <PCA9548> ***** write_control_reg()
                            PCA9548.write_control_reg              -    DEBUG:  <PCA9548> New mask:     <0b00000000>, channels <>

```