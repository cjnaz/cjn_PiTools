#!/usr/bin/env python3
"""Demo/test for PiBlinky

Produce / compare to golden results:
    ./PiBlinky-demo.py > testrun.log

    Expected differences:
        Log order can shift due to independent PiBlinky threads
"""

#==========================================================
#
#  Chris Nelson, 2024-2026
#
# 1.0 260401 - New
#
#==========================================================

__version__ =   "1.0"
TOOLNAME =      'PiBlinky_demo'

import argparse
import time
import logging
import re
import queue
import pigpio

from cjnfuncs.core import           set_toolname, setuplogging, logging, set_logging_level
from cjn_PiTools.PiBlinky import    PiBlinky, CMD_EXIT, CMD_RESTORE, CMD_SAVE

BLU_LED_GPIO    = 4
RED_LED_GPIO    = 17
YEL_LED_GPIO    = 20

HOST = 'localhost'
PIGPIO_PORT = 8888


set_toolname(TOOLNAME)
# setuplogging(ConsoleLogFormat="{module:>35}.{funcName:30} - {levelname:>8}:  {message}")
set_logging_level(logging.DEBUG)
set_logging_level(logging.DEBUG, 'cjn_PiTools.PiBlinky')


parser = argparse.ArgumentParser(description=__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-t', '--test', default='0',
                    help="Test number to run (default 0) - 0 runs all tests")
parser.add_argument('-x', '--expand-exception', action='store_true',
                    help="Expand exceptions with trace stack for test debug")
parser.add_argument('--host', type=str, default=HOST,
                    help=f"Hostname for pigpio, or 'GPIO' for RPi.GPIO usage (Default <{HOST}>)")
parser.add_argument('--port', type=str, default=PIGPIO_PORT,
                    help=f"Port number for pigpio (Default <{PIGPIO_PORT}>)")
cli_args = parser.parse_args()


logging.warning (f"\n\n---- Test Init ------------------------------------------------------")

if cli_args.host == 'GPIO':
    api = 'GPIO'
else:
    api = pigpio.pi(cli_args.host, cli_args.port)

# Instantiate the Status LED threads
BLU_LED_q       = queue.Queue()
BLU_LED_inst    = PiBlinky("BLU", api, BLU_LED_GPIO, BLU_LED_q)
BLU_LED_th      = BLU_LED_inst.start()

RED_LED_q       = queue.Queue()
RED_LED_inst    = PiBlinky("RED", api, RED_LED_GPIO, RED_LED_q)
RED_LED_th      = RED_LED_inst.start()

YEL_LED_q       = queue.Queue()
YEL_LED_inst    = PiBlinky("YEL", api, YEL_LED_GPIO, YEL_LED_q)
YEL_LED_th      = YEL_LED_inst.start()

BLUx_LED_th = None


def print_test_header(desc):
    global tnum
    logging.warning (f"""\n
======================================================================================================
Test {tnum} - {desc}
""")


def dotest (desc, expect, func, *args, **kwargs):
    logging.warning (f"\n\n==============================================================================================\n" +
                     f"Test {tnum} - {desc}\n" +
                     f"  GIVEN:      {args}, {kwargs}\n" +
                     f"  EXPECT:     {expect}")
    try:
        result = func(*args, **kwargs)
        logging.warning (f"\n  RETURNED:   {result}")
        return result
    except Exception as e:
        if cli_args.expand_exception:
            logging.exception (f"\n  RAISED:     {type(e).__name__}: {e}")
        else:
            logging.error (f"\n  RAISED:     {type(e).__name__}: {e}")
        return e


tnum_parse = re.compile(r"([\d]+)([\w]*)")
def check_tnum(tnum_in, include0='0'):
    global tnum
    tnum = tnum_in
    if cli_args.test == include0  or  cli_args.test == tnum_in:  return True
    try:
        if int(cli_args.test) == int(tnum_parse.match(tnum_in).group(1)):  return True
    except:  pass
    return False


#===============================================================================================
if __name__ == '__main__':

    #-------------------------------------------------------------------------
    # Pass cases and feature demos
    if check_tnum('1a'):
        print_test_header ("Blink all three LEDs 10 times fast")

        BLU_LED_q.put ([50, "10", 10])
        RED_LED_q.put ([50, "10", 10])
        YEL_LED_q.put ([50, "10", 10])
        time.sleep (1.5)

    if check_tnum('1b'):
        print_test_header ("Blink YEL continuously, interrupted by new command after 3s, BLU on, RED off")

        YEL_LED_q.put ([100, "10", -1])             # Continuous 200ms period blinks
        BLU_LED_q.put ([0, "1", 1])                 # On
        RED_LED_q.put ([0, "0", 1])                 # Off
        time.sleep (3)
        YEL_LED_q.put ([0, "0", 1])                 # Turn YEL off
        time.sleep (1)

    if check_tnum('1c'):
        print_test_header ("Save a blink pattern, apply a new one, then restore the prior one")

        BLU_LED_q.put ([500, "10", 2])              # 1s x2 blinks (2 blinks with on and off times = 500ms)
        time.sleep (3)
        BLU_LED_q.put ([50, "1000", -1, CMD_SAVE])  # A 50ms blink over 200ms, repeated continuously, while saving above 1s blinks
        time.sleep (3)
        BLU_LED_q.put ([0,"0",0, CMD_RESTORE])      # Re-execute the prior saved 1s x2 blinks
        time.sleep (3)
        BLU_LED_q.put ([0,"0",0, CMD_RESTORE])      # Re-execute the prior saved 1s x2 blinks again
        time.sleep (3)


    #-------------------------------------------------------------------------
    # Demo corner case options
    if check_tnum('2a'):
        print_test_header ("play_cnt 0")

        BLU_LED_q.put ([100, " 1 1 1 1 0 1 0 1 0 1 0 ", 0])
        time.sleep (1.5)

    if check_tnum('2b'):
        print_test_header ("play_cnt 1")

        BLU_LED_q.put ([100, "11110101010", 1])
        time.sleep (1.5)

    if check_tnum('2c'):
        print_test_header ("play_cnt 2")

        BLU_LED_q.put ([100, "11110101010", 2])
        time.sleep (2.5)

    if check_tnum('2d'):
        BLUx_LED_q       = queue.Queue()
        BLUx_LED_inst    = PiBlinky('BLUx', api, BLU_LED_GPIO, BLUx_LED_q, inverted=1)
        BLUx_LED_th      = BLUx_LED_inst.start()
        def func():
            BLUx_LED_q.put ([100, "1111111010101", 2])
            time.sleep (3.5)

        dotest ("inverted = 1", "None", func)

    if check_tnum('2e'):
        logging.info ("LED turned on")
        BLU_LED_q.put ([0, "1", 1])
        time.sleep (0.5)
        dotest ("Empty bitstream", "None", BLU_LED_q.put, [1000, "", 2])
        logging.info ("LED unchanged")
        YEL_LED_q.put ([100, "10", 3])
        time.sleep (0.6)



    #-------------------------------------------------------------------------
    # Error cases
    if check_tnum('13a'):
        print_test_header ("Error Restore without Save")

        BLUx_LED_q       = queue.Queue()
        BLUx_LED_inst    = PiBlinky("BLUx", api, BLU_LED_GPIO, BLUx_LED_q)
        BLUx_LED_th      = BLUx_LED_inst.start()

        BLUx_LED_q.put ([100, "10", 5, CMD_RESTORE])
        time.sleep(0.5)

    if check_tnum('13b'):
        print_test_header ("Bad bittime value")

        BLU_LED_q.put (['500x', "10", 2])
        time.sleep(0.5)

    if check_tnum('13c'):
        print_test_header ("Bad bitstream")

        BLU_LED_q.put ([100, "102", 2])
        time.sleep(1)

    if check_tnum('13d'):
        print_test_header ("Bad play_cnt")

        BLU_LED_q.put ([100, "10", 'a'])
        time.sleep(0.5)

    if check_tnum('13e'):
        print_test_header ("Bad option flag")

        BLU_LED_q.put ([100, "10", 5, 7])
        time.sleep(0.5)

    if check_tnum('13f')  and  not api == 'GPIO':
        apix = pigpio.pi(cli_args.host, cli_args.port)
        BLUx_LED_q       = queue.Queue()
        BLUx_LED_inst    = PiBlinky('BLUx', apix, BLU_LED_GPIO, BLUx_LED_q)
        BLUx_LED_th      = BLUx_LED_inst.start()
        def func():

            BLUx_LED_q.put ([100, "10", 5])
            time.sleep(2)

            apix.stop()       # pigpio daemon disconnected
            BLUx_LED_q.put ([100, "10", 5])
            time.sleep(2)

        dotest ("pigpio died", "None, Logged: AttributeError: 'NoneType' object has no attribute 'send'", func)


    #-------------------------------------------------------------------------
    # Error during instantiation
    if check_tnum('14a'):
        def func():
            BLUx_LED_q       = queue.Queue()
            BLUx_LED_inst    = PiBlinky(5, api, BLU_LED_GPIO, BLUx_LED_q)
            BLUx_LED_th      = BLUx_LED_inst.start()

        dotest ("Invalid instance name", "ValueError: LED_name must be str - received <5> - <class 'int'>", func)

    if check_tnum('14b'):
        def func():
            BLUx_LED_q       = queue.Queue()
            BLUx_LED_inst    = PiBlinky('BLUx', api, 30, BLUx_LED_q)
            BLUx_LED_th      = BLUx_LED_inst.start()

        dotest ("Invalid GPIO channel number", "ValueError: <BLUx> gpio_num must be a valid GPIO Broadcom SOC channel number - received <30> - <class 'int'>", func)

    if check_tnum('14c'):
        def func():
            BLUx_LED_q       = queue.Queue()
            BLUx_LED_inst    = PiBlinky('BLUx', api, ['hello'], BLUx_LED_q)
            BLUx_LED_th      = BLUx_LED_inst.start()

        dotest ("Invalid GPIO channel number", "ValueError: <BLUx> gpio_num must be a valid GPIO Broadcom SOC channel number - received <['hello']> - <class 'list'>", func)

    if check_tnum('14d'):
        def func():
            BLUx_LED_q       = queue.Queue()
            BLUx_LED_inst    = PiBlinky('BLUx', api, BLU_LED_GPIO, BLUx_LED_q, inverted='Hello')
            BLUx_LED_th      = BLUx_LED_inst.start()

        dotest ("Invalid inverted", "ValueError: <BLUx> inverted must be int 0 or 1 - received <Hello> - <class 'str'>", func)

    if check_tnum('14e'):
        def func():
            BLUx_LED_q       = queue.Queue()
            BLUx_LED_inst    = PiBlinky('BLUx', api, BLU_LED_GPIO, BLUx_LED_q, inverted=2)
            BLUx_LED_th      = BLUx_LED_inst.start()

        dotest ("Invalid inverted", "ValueError: <BLUx> inverted must be int 0 or 1 - received <2> - <class 'int'>", func)



    #-------------------------------------------------------------------------
    # Development/testing/debug
    if check_tnum('50', include0=False):

        print_test_header ("Development/debug")
        BLU_LED_q.put ([100, "10", 5, 7])
        time.sleep(0.5)



    logging.warning (f"\n\n---- Cleanup --------------------------------------------------------")

    BLU_LED_q.put ([0, "0", 1, CMD_EXIT])
    YEL_LED_q.put ([0, "0", 1, CMD_EXIT])
    RED_LED_q.put ([100, "0 111 001 001 001", 1, CMD_EXIT]) # Blink RED then on solid on exit

    if BLUx_LED_th is not None  and  BLUx_LED_th.is_alive():
        BLUx_LED_q.put ([0, "", 1, CMD_EXIT])

    time.sleep(2)                                           # Wait for any in-flight LED writes
    BLU_LED_th.join()
    RED_LED_th.join()
    YEL_LED_th.join()

    if cli_args.host == 'GPIO':
        pass                    # No cleanup since GPIO is imported within piblinky, not this code.
    else:
        api.stop()              # pigpio
