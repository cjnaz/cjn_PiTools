# cjn_PiFuncs - Functions for Raspberry Pi projects

## cjn_PiFuncs is comprised of several modules (follow links to respective documentation)

NOTE:  Since relative links to other .md files do not work on PyPI, please go to the [cjn_PiFuncs GitHub repo](https://github.com/cjnaz/cjn_PiFuncs) to read the documentation. 

module | Description/Purpose
--|--
[PiBlinky](docs/PiBlinky.md)      | A multiple threaded LED driver for Raspberry Pi
[PiOLED](docs/PiOLED.md)          | Display multi-line messages on a shared Raspberry Pi connected OLED display

Developed and tested on Raspbian GNU/Linux 11 (bullseye) and Python 3.9.2, and supported on all higher versions.

In this documentation, "tool script" refers to a Python project that imports and uses cjn_PiFuncs. Some may be simple scripts, and others may themselves be installed packages.

<br/>

## Installation and usage

If using the RPi.GPIO driver:
```
pip install cjn_PiFuncs
```

If using the pigpio driver:

    pip install cjn_PiFuncs[pigpio]

and you will also need to install the `pigpiod` daemon and start it manually or at boot:


You may also set cjn_PiFuncs as a dependency in your tool scripts package pyproject.toml or setup.py.


<br/>

## Key changes since the prior major public release (this is the first release)

- New.  Bundled PiBlinky and PiOLED

<br/>

## Revision history
- 1.0 260210 - New.  Bundled PiBlinky and PiOLED
