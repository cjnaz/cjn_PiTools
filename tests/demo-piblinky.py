#!/usr/bin/env python3
"""Demo/test for PiBlinky

Produce / compare to golden results:
    ./demo-piblinky.py -vv &> testrun.log
  or
    ./demo-piblinky.py --host GPIO -vv &> testrun.log

    Expected differences:
        Log order can shift due to 3 independent threads
"""

#==========================================================
#
#  Chris Nelson, 2024-2026
#
#==========================================================

__version__ = "1.0"

import argparse
import time
import logging
import re

import queue

from cjn_PiTools.PiBlinky import piblinky, CMD_EXIT, CMD_RESTORE, CMD_SAVE

BLU_LED_GPIO    = 4
RED_LED_GPIO    = 17
YEL_LED_GPIO    = 20

HOST = 'localhost'   # Default interface mode - pigpio hostname/'localhost', or 'GPIO' for using RPi.GPIO
PIGPIO_PORT = 8888


def main():
    # Instantiate the Status LED threads
    BLU_LED_q       = queue.Queue()
    BLU_LED_inst    = piblinky("BLU", daemon, BLU_LED_GPIO, BLU_LED_q)
    BLU_LED_th      = BLU_LED_inst.start()

    RED_LED_q       = queue.Queue()
    RED_LED_inst    = piblinky("RED", daemon, RED_LED_GPIO, RED_LED_q)
    RED_LED_th      = RED_LED_inst.start()

    YEL_LED_q       = queue.Queue()
    YEL_LED_inst    = piblinky("YEL", daemon, YEL_LED_GPIO, YEL_LED_q)
    YEL_LED_th      = YEL_LED_inst.start()


    #-----------------------------------------------------------------------------------
    def print_test_header(header):
        global tnum
        piblinky_logger.info (f"""\n
======================================================================================================
***** Test number {tnum}: {header} *****
======================================================================================================""")


    tnum_parse = re.compile(r"([\d]+)([\w]*)")
    def check_tnum(tnum_in, include0='0'):
        global tnum
        tnum = tnum_in
        if args.test == include0  or  args.test == tnum_in:  return True
        try:
            if int(args.test) == int(tnum_parse.match(tnum_in).group(1)):  return True
        except:  pass
        return False
    #-----------------------------------------------------------------------------------


    #===============================================================================================
    if check_tnum('1'):
        print_test_header ("Blink all three LEDs 10 times fast")

        BLU_LED_q.put ([50, "10", 10])
        RED_LED_q.put ([50, "10", 10])
        YEL_LED_q.put ([50, "10", 10])
        time.sleep (1.5)

    #===============================================================================================
    if check_tnum('2'):
        print_test_header ("Blink YEL continuously, interrupted by new command after 3s, BLU on, Red off")

        YEL_LED_q.put ([100, "10", -1])             # Continuous 200ms period blinks
        BLU_LED_q.put ([0, "1", 1])                 # On
        RED_LED_q.put ([0, "0", 1])                 # Off
        time.sleep (3)
        YEL_LED_q.put ([0, "0", 1])                 # Turn YEL off
        time.sleep (1)

    #===============================================================================================
    if check_tnum('3a'):
        print_test_header ("Error Restore without Save")

        BLU_LED_q.put ([100, "10", 5, CMD_RESTORE])
        time.sleep(0.5)

    #===============================================================================================
    if check_tnum('3b'):
        print_test_header ("Save a blink pattern, apply a new one, then restore the prior one")

        BLU_LED_q.put ([500, "10", 2])              # 1s x2 blinks (2 blinks with on and off times = 500ms)
        time.sleep (3)
        BLU_LED_q.put ([50, "1000", -1, CMD_SAVE])  # A 50ms blink over 200ms, repeated continuously, while saving above 1s blinks
        time.sleep (3)
        BLU_LED_q.put ([0,"0",0, CMD_RESTORE])      # Re-execute the prior saved 1s x2 blinks
        time.sleep (3)
        BLU_LED_q.put ([0,"0",0, CMD_RESTORE])      # Re-execute the prior saved 1s x2 blinks again
        time.sleep (3)

    #===============================================================================================
    if check_tnum('4'):
        print_test_header ("Bad bittime value")

        BLU_LED_q.put (['500x', "10", 2])
        time.sleep(0.5)

    #===============================================================================================
    if check_tnum('5'):
        print_test_header ("Bad bitstream")

        BLU_LED_q.put ([100, "102", 2])
        time.sleep(1)

    #===============================================================================================
    if check_tnum('6'):
        print_test_header ("Bad repeat count")

        BLU_LED_q.put ([100, "10", 'a'])
        time.sleep(0.5)

    #===============================================================================================
    if check_tnum('7'):
        print_test_header ("Bad option flag")

        BLU_LED_q.put ([100, "10", 5, 7])
        time.sleep(0.5)


    #===============================================================================================
    if check_tnum('10', include0=False):
        # Run individually.  This test breaks Cleanup.
        print_test_header ("Force bit write errors - pigpio mode only")

        BLU_LED_q.put ([100, "10", 5])
        time.sleep(2)

        daemon.stop()       # pigpio daemon disconnected
        BLU_LED_q.put ([100, "10", 5])
        time.sleep(2)




    piblinky_logger.info (f"""\n
======================================================================================================
Cleanup
======================================================================================================""")

    BLU_LED_q.put ([0, "0", 1, CMD_EXIT])
    YEL_LED_q.put ([0, "0", 1, CMD_EXIT])
    RED_LED_q.put ([100, "0 111 001 001 001", 1, CMD_EXIT]) # Blink RED then on solid on exit

    time.sleep(2)                                           # Wait for any in-flight LED writes
    BLU_LED_th.join()
    RED_LED_th.join()
    YEL_LED_th.join()

    if args.host == 'GPIO':
        pass                    # No cleanup since GPIO is imported within piblinky, not this code.
    else:
        daemon.stop()           # pigpio

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-t', '--test', default='0',
                        help="Test number to run (default 0 runs most all tests (those without untrapped errors))")
    parser.add_argument('--host', type=str, default=HOST,
                        help=f"Hostname for pigpio, or 'GPIO' for RPi.GPIO usage (Default <{HOST}>)")
    parser.add_argument('--port', type=str, default=PIGPIO_PORT,
                        help=f"Port number for pigpio (Default <{PIGPIO_PORT}>)")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Print status and activity messages")
    args = parser.parse_args()

    logging.basicConfig()

    piblinky_logger = logging.getLogger('cjn_PiTools.PiBlinky')
    piblinky_logger.setLevel(logging.WARNING)

    if args.verbose:
        piblinky_logger.setLevel(logging.DEBUG)

    if args.host == 'GPIO':
        daemon = 'GPIO'
    else:
        import pigpio
        daemon = pigpio.pi(args.host, args.port)

    main()