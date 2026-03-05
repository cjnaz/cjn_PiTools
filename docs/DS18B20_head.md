# DS18B20 high-featured library/driver for Raspberry Pi using the w1_therm kernel driver

Skip to [API documentation](#links)

This module provides a clean and mostly complete (*) API for DS18B20 temperature sensors 
using the w1_therm kernel driver.  Also provided is a command line interface for interactive dev/debug.

Supports:
- Reading temperatures
- Bulk parallel conversion of temperatures for all sensors on the bus
- Resolution setting and Alarm thresholds setting in scratchpad
- Setting and measuring actual conversion (temperature measurement) time
- Scratchpad save/restore to/from EEPROM
- Multiple w1 busses

(*) Not supported:
 - Alarm search - I've not found any useful documentation for triggering an alarm search nor reading back the in-alarm sensor list.  I'm happy to add the feature if I only knew how.
 - 'features' register (conversion error check and poll for completion)
 - async_io (just needs development)
 - Other sensor models

Tested on Python 3.9.2 and kernel version 6.1.21-v7+ #1642 SMP Mon Apr  3 17:20:52 BST 2023, and should work on similar kernel versions since about 2020.

Do read the [fine datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf).


<br>

## Setup / Installation

If you wish to use the `bulk_convert_trigger ()` api (without root privilege) it is necessary to setup/install the W1 bus initialization module [initW1buses](https://github.com/cjnaz/cjn_PiTools/initW1buses.md).  Alternately, run your tool script with root privilege.


<br>

## Using the API

Example code:
```
#!/usr/bin/env python3
# DS18B20_README_ex.py available in the docs directory in the github repo

import logging
from cjn_PiTools.DS18B20 import DS18B20

logging.basicConfig()
logging.getLogger('cjn_PiTools.DS18B20').setLevel(logging.DEBUG)


sensor = DS18B20('28-0b2280337113', 'My_DS18B20')
logging.info (f"Current temperature for sensor {sensor.device_name} / {sensor.device_id}:  {sensor.read_temperature(tempunits='F'):7.3f} F")
```

And running it:
```
$ ./DS18B20_README_ex.py 
DEBUG:cjn_PiTools.DS18B20:28-0b2280337113 / My_DS18B20 - w1_slave file content:
8e 01 3c 0f 7f ff 7f 10 3a : crc=3a YES
8e 01 3c 0f 7f ff 7f 10 3a t=24875
DEBUG:cjn_PiTools.DS18B20:28-0b2280337113 / My_DS18B20 - temperature:   76.775 F
```

<br>

## Enabling debug logging

To enabled debug logging from this module's classes/functions, add this to your tool script code:

     logging.getLogger('cjn_PiTools.DS18B20').setLevel(logging.DEBUG)


<br>

## Command Line Interface and Demo

Once installed a cli tool is available.  The cli tool provides some useful debug and configuration features (such as setting and permanently saving 
the resolution setting), and also a few demonstration cases (such as triggering a bulk/parallel conversion on multiple sensors and reading back their values).

```
$ DS18B20 --help
usage: DS18B20 [-h] [-m MODE] [-n NAME] [-r RESOLUTION] [-L TL] [-H TH] [-c CONV_TIME] [-v] [-V] [DeviceID]

DS18B20 driver and CLI/demo for Raspberry Pi

Modes:
    0:  Dump info for all sensors (-m 0)  (DeviceID is optional, ignored for mode 0 only)
    1:  Get current temp (<DeviceID> -m 1)
    2:  Read scratchpad (<DeviceID> -m 2)
    3:  Get current resolution (<DeviceID> -m 3)
    4:  Set resolution (<DeviceID> -m 4 -r 9)
    5:  Get current alarm temps (<DeviceID> -m 5)
    6:  Set alarm temps (<DeviceID> -m 6 -L 20 -H 30)
    7:  Send bulk_convert_trigger (<DeviceID> -m 7)
    8:  Save scratchpad to EEPROM (<DeviceID> -m 8)
    9:  Restore EEPROM to scratchpad (<DeviceID> -m 9)
    10: Get current conversion time (<DeviceID> -m 10)
    11: Set conversion time or start measurement (<DeviceID> -m 11 -c 1)
    12: Get parasitic/external power status (<DeviceID> -m 12)

    20: Minimal example for README (<DeviceID> -m 20)
    21: Demonstrate saving alarm/resolution to EEPROM and restoring (<DeviceID> -m 21)
    22: Demonstrate bulk/parallel temperature conversions and sensor reads (<DeviceID> -m 22) (Supply the DeviceID of one of the sensors on the bus of interest.)
1.1

positional arguments:
  DeviceID              ID of target device, eg 28-0b2280337113

optional arguments:
  -h, --help            show this help message and exit
  -m MODE, --mode MODE  Test mode select (default 0, you probably also want -v or -vv)
  -n NAME, --name NAME  Name of the sensor to be displayed (default DS18B20)
  -r RESOLUTION, --resolution RESOLUTION
                        Resolution value (9, 10, 11, or 12) to be set with --mode 4 (default 12)
  -L TL, --TL TL        TL alarm value (degrees C) to be set with --mode 6 (default -25)
  -H TH, --TH TH        TH alarm value (degrees C) to be set with --mode 6 (default 50)
  -c CONV_TIME, --conv-time CONV_TIME
                        Conversion time setting or trigger measurement operation  (default 0 - set to spec value)
  -v, --verbose         Print info-level (-v) and debug-level (-vv) status and activity messages
  -V, --version         Print version number and exit
```

<br>

## Using the CLI for debug

Mode 2 calls `read_scratchpad()` which invokes a dump and parse of a sensor's return results register, `w1_slave`:

```
$ DS18B20 28-0b228004203c --name "My_Sensor" --mode 2 -vv
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / My_Sensor - w1_slave file content:
8b 01 3c 0f 7f ff 7f 10 6c : crc=6c YES
8b 01 3c 0f 7f ff 7f 10 6c t=24687
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / My_Sensor - temperature code:  01 8b   24.688 C,   76.438 F,  297.837 K
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / My_Sensor - High alarm limit:  3c      60 C,      140.000 F,  333.150 K
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / My_Sensor - Low  alarm limit:  0f      15 C,       59.000 F,  288.150 K
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / My_Sensor - Resolution:        7f      12
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / My_Sensor - Sensor root directory:     /sys/bus/w1/devices/28-0b228004203c
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / My_Sensor - Bus master root directory: /sys/bus/w1/devices/w1_bus_master1
        DS18B20.cli                  -     INFO:  ['8b', '01', '3c', '0f', '7f', 'ff', '7f', '10', '6c', ':', 'crc=6c', 'YES']
```

Mode 0 (the default mode) invokes a similar dump for every sensor found on the host, across all w1 busses, and includes conversion time and external power status:

```
$ DS18B20
        DS18B20.cli                  -     INFO:  Sensor </sys/bus/w1/devices/28-0b228004203c> on bus master </sys/bus/w1/devices/w1_bus_master1>:
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / DS18B20 - w1_slave file content:
8a 01 3c 0f 7f ff 7f 10 2f : crc=2f YES
8a 01 3c 0f 7f ff 7f 10 2f t=24625
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / DS18B20 - temperature code:  01 8a   24.625 C,   76.325 F,  297.775 K
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / DS18B20 - High alarm limit:  3c      60 C,      140.000 F,  333.150 K
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / DS18B20 - Low  alarm limit:  0f      15 C,       59.000 F,  288.150 K
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / DS18B20 - Resolution:        7f      12
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / DS18B20 - Sensor root directory:     /sys/bus/w1/devices/28-0b228004203c
        DS18B20.read_scratchpad      -    DEBUG:  28-0b228004203c / DS18B20 - Bus master root directory: /sys/bus/w1/devices/w1_bus_master1
        DS18B20.get_conv_time        -    DEBUG:  28-0b228004203c / DS18B20 - Current conversion time:   750
        DS18B20.get_ext_power        -    DEBUG:  28-0b228004203c / DS18B20 - External power status:     1
        DS18B20.cli                  -     INFO:  Sensor </sys/bus/w1/devices/28-0b2280337113> on bus master </sys/bus/w1/devices/w1_bus_master1>:
        DS18B20.read_scratchpad      -    DEBUG:  28-0b2280337113 / DS18B20 - w1_slave file content:
91 01 3c 0f 7f ff 7f 10 94 : crc=94 YES
91 01 3c 0f 7f ff 7f 10 94 t=25062
        DS18B20.read_scratchpad      -    DEBUG:  28-0b2280337113 / DS18B20 - temperature code:  01 91   25.062 C,   77.113 F,  298.212 K
        DS18B20.read_scratchpad      -    DEBUG:  28-0b2280337113 / DS18B20 - High alarm limit:  3c      60 C,      140.000 F,  333.150 K
        DS18B20.read_scratchpad      -    DEBUG:  28-0b2280337113 / DS18B20 - Low  alarm limit:  0f      15 C,       59.000 F,  288.150 K
        DS18B20.read_scratchpad      -    DEBUG:  28-0b2280337113 / DS18B20 - Resolution:        7f      12
        DS18B20.read_scratchpad      -    DEBUG:  28-0b2280337113 / DS18B20 - Sensor root directory:     /sys/bus/w1/devices/28-0b2280337113
        DS18B20.read_scratchpad      -    DEBUG:  28-0b2280337113 / DS18B20 - Bus master root directory: /sys/bus/w1/devices/w1_bus_master1
        DS18B20.get_conv_time        -    DEBUG:  28-0b2280337113 / DS18B20 - Current conversion time:   750
        DS18B20.get_ext_power        -    DEBUG:  28-0b2280337113 / DS18B20 - External power status:     1
```


<br>

## References
  - [https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf](https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf)
  - [https://docs.kernel.org/w1/slaves/w1_therm.html](https://docs.kernel.org/w1/slaves/w1_therm.html)
  - [https://docs.kernel.org/w1/w1-generic.html](https://docs.kernel.org/w1/w1-generic.html)
  - [https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-driver-w1_therm](https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-driver-w1_therm)

