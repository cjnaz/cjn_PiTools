#!/usr/bin/env python3
"""initW1busses

1. Optionally enable power to the W1 bus(es) by setting a GPIO,
2. Delay to allow the kernel to scan for W1 devices, and 
3. Set user write permissions on therm_bulk_read for each found bus.

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

import importlib.metadata
__version__ = importlib.metadata.version(__package__ or __name__)

from cjnfuncs.core          import set_toolname
from cjnfuncs.deployfiles   import deploy_files

# Configs / Constants
TOOLNAME =                  'initW1buses'
w1_buses_root_path =        Path('/sys/devices/')

set_toolname (TOOLNAME)


def cli():
    parser = argparse.ArgumentParser(description=__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-g', '--GPIO', type=int,
                        help="Optional GPIO pin number to be set to output 1 before the delay time")
    parser.add_argument('-d', '--delay', type=int, default=20,
                        help="Delay time in seconds before setting therm_bulk_read permission (default 20)")
    parser.add_argument('--setup-user', action='store_true',
                        help=f"Install starter files in user space")
    parser.add_argument('-V', '--version', action='version', version=__version__,
                        help="Print version number and exit")
    args = parser.parse_args()

    # Deploy starter files
    if args.setup_user:
        logging.getLogger('cjnfuncs.deployfiles').setLevel(logging.INFO)
        deploy_files([
            { 'source': 'initW1buses.service', 'target_dir': 'USER_CONFIG_DIR', 'file_stat': 0o644},
            ]) #, overwrite=True)
        sys.exit()


    # Do the initialization
    if args.GPIO:
        gpio = args.GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(gpio, GPIO.OUT)
        GPIO.output(gpio, 1)
        logging.warning(f"Set GPIO <{gpio}> to Output 1")

    logging.warning(f"Waiting {args.delay} seconds for W1 devices discovery")
    time.sleep (args.delay)

    buses_list = list(w1_buses_root_path.glob('w1_bus*'))
    if len(buses_list) == 0:
        logging.error("Found no W1 busses - Aborting")
        return 1
    
    errored = False
    for bus in buses_list:
        try:
            tbr = bus / 'therm_bulk_read'
            os.chmod (tbr, 0o666)
            logging.warning (f"Found and enabled write access to <{tbr}>")
        except Exception as e:
            logging.warning (f"Failed to enable write access to <{tbr}> - Skipping\n  {type(e).__name__}: {e}")
            errored = True
    
    if errored:
        return 1
    else:
        return 0    # Successful completion code monitored by systemd


if __name__ == '__main__':
    sys.exit(cli())
