#!/usr/bin/env python3
"""initW1busses

Set user write permissions on therm_bulk_read for each found bus.
Run at boot via systemd.
"""

import importlib.metadata
__version__ = importlib.metadata.version(__package__ or __name__)


#==========================================================
#
#  Chris Nelson, Copyright 2024 - 2026
#
#==========================================================

import logging
import sys
import os
import time
from pathlib import Path
import argparse
import RPi.GPIO as GPIO
# import pigpio

import importlib.metadata
__version__ = importlib.metadata.version(__package__ or __name__)

# RELAY_3V3_GPIO  = 21
w1_buses_root_path =  Path('/sys/devices/')



def cli():
    # global pio

    parser = argparse.ArgumentParser(description=__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-g', '--GPIO', type=int,
                        help="Optional GPIO pin number to be set to output 1 before the delay time")
    parser.add_argument('-d', '--delay', type=int, default=20,
                        help="Delay time before setting therm_bulk_read permission (default 20)")
    parser.add_argument('-V', '--version', action='version', version=__version__,
                        help="Print version number and exit")
    args = parser.parse_args()


    # try:
    #     pio = pigpio.pi()
    #     if not pio.connected:
    #         logging.error(f"pigpio handle request failed.  Aborting.")
    #         sys.exit(1)
    # except:
    #     logging.exception(f"pigpio handle request failed.  Aborting.")
    #     sys.exit(1)

    # pio.write(RELAY_3V3_GPIO, 1)
    # pio.stop()

    if args.GPIO:
        gpio = args.GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(gpio, GPIO.OUT)
        GPIO.output(gpio, 1)
        logging.warning(f"Set GPIO <{gpio}> to Output 1")

    time.sleep (args.delay)

    buses_list = list(w1_buses_root_path.glob('w1_bus*'))
    if len(buses_list) == 0:
        logging.error("Found no W1 busses - Aborting")
        return 1
    
    try:
        for bus in buses_list:
            tbr = bus / 'therm_bulk_read'
            os.chmod (tbr, 0o666)
            logging.warning (f"Found and enabled everyone write access to <{tbr}>")
    except Exception as e:
        logging.error(f"Failed to set permission on W1 bus <{bus}> - Aborting.\n  {type(e).__name__}: {e}")
        return 1
    
    return 0    # Successful completion code monitored by systemd


if __name__ == '__main__':
    sys.exit(cli())
