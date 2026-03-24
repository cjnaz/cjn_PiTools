# cjn_PiTools - A collection of modules for Raspberry Pi projects

## cjn_PiTools is comprised of several modules (follow links to respective documentation)

NOTE:  These links point to the github repo since relative links to other .md files do not work on PyPI.

Module | Description/Purpose
--|--
[PiBlinky](https://github.com/cjnaz/cjn_PiTools/blob/main/PiBlinky.md)       | A multiple threaded LED driver for Raspberry Pi
[PiOLED](https://github.com/cjnaz/cjn_PiTools/blob/main/PiOLED.md)           | Display multi-line messages on a shared Raspberry Pi connected OLED display
[DS18B20](https://github.com/cjnaz/cjn_PiTools/blob/main/DS18B20.md)         | DS18B20 temperature sensor library using the w1_therm kernel driver
[initW1buses](https://github.com/cjnaz/cjn_PiTools/blob/main/initW1buses.md) | Initialize the W1 buses and set write permission on found therm_bulk_read file(s)
[ADC121C](https://github.com/cjnaz/cjn_PiTools/blob/main/ADC121C.md)         | ADC121C* 12-bit ADC library for Raspberry Pi
[HTU21D](https://github.com/cjnaz/cjn_PiTools/blob/main/HTU21D.md)           | HTU21D Temperature/RH sensor library for Raspberry Pi
[MCP23008](https://github.com/cjnaz/cjn_PiTools/blob/main/MCP23008.md)       | MCP23008 8-Bit I/O Expander library for Raspberry Pi
[PCA9548](https://github.com/cjnaz/cjn_PiTools/blob/main/PCA9548.md)         | PCA9548A/TCA9548A I2C port expander library for Raspberry Pi
[shared](https://github.com/cjnaz/cjn_PiTools/blob/main/shared.md)           | Classes and functions used across cjn_PiTools

More to come!
- Drivers for SHT3x and HTU21D temp/RH sensors
- Driver for ADC121C027 ADC
- Driver for MCP23008 IO expander
- Driver for PCA9548s I2C expander

In most cases, these drivers will work with both `RPi.GPIO` or `smbus2` (for local control) and `pigpio` for (local and remote control).

Developed and tested on Raspbian GNU/Linux 11 (bullseye) and Python 3.9.2, and supported on all higher versions.

In this documentation, "tool script" refers to a Python project that imports and uses cjn_PiTools. Some may be simple scripts, and others may themselves be installed packages.

<br/>

## Installation and usage

If using the RPi.GPIO and/or smbus2 drivers:

    pip install cjn_PiTools


If using the pigpio driver:

    pip install cjn_PiTools[pigpio]

- And you will also need to install the pigpiod daemon (`sudo apt install pigpiod`) and start it manually or at boot.  Here's a systemd service file for starting pigpiod at boot:

        [Unit]
        Description=Daemon required to control GPIO pins via pigpio

        [Service]
        ExecStart=/usr/local/bin/pigpiod -l
        Type=forking
        TimeoutStopSec=20

        [Install]
        WantedBy=multi-user.target



<br/>

## Key changes since the prior major public release (1.0)

- V1.1 added ADC121C, HTU21D, MCP23008, PCA9548, and SHT3x drivers

<br/>

## Revision history
- 1.1 260401 - Added ADC121C, HTU21D, MCP23008, PCA9548, and SHT3x drivers
- 1.0 260207 - New.  Bundled PiBlinky, PiOLED, initW1buses, and DS18B20 modules
