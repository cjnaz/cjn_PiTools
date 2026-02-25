#!/usr/bin/env python3
"""Demo/test for shared

Produce / compare to golden results:
    ./demo-shared.py > testrun.log

    ./fsactivity_plugin_test.py | diff fsactivity_plugin_test.golden -
        Expected differences:
            File timestamps and ages for newfile, george, mahesh
            Ages for too old tests 2e, 2f, 4e, 4f, 6b1, 6b2, 6c
"""

#==========================================================
#
#  Chris Nelson, Copyright 2026
#
# ***** i2c bus 1 test boards configuration *****
#
# Board 1 (connected directly to RPi I2C bus 1)
#   PCA9548 address 0x71
#       Channel 0:  Connected to Board 2 PCA9548
#       Channel 1:  Connected to SHT3x at address 0x44
#       Channel 2:  Connected to SHT3x at address 0x45
#       Channel 6:  Connected to HTU21D at address 0x40
#
# Board 2 (connected to Board 1 PCA9548 Channel 0)
#   PCA9548 address 0x75
#       Channel 0:  Jack I2C1 with SHT3x at address 0x44
#       Channel 1:  Jack I2C2
#       Channel 2:  Jack I2C3
#       Channel 3:  ADC121C ADC1 at address 0x50
#           ADC121C chips use 4.2V reference
#       Channel 3:  ADC121C ADC2 at address 0x51
#       Channel 4:  MCP23008_IO_ADDR at address 0x70 
#           Lower 4 bits as outputs, 4 upper bits as inputs with weak pullups
#       Channel 4:  MCP23008_7SEG_ADDR at address 0x71
#           All bits as outputs serving as pulldowns on common anode 7-segment display
#           Segment selects in DIG_2_SEG are inverted when written to MCP23008_7SEG_ADDR
#       Channel 5:  ADC121C ADC3 at address 0x52
#       Channel 5:  ADC121C ADC4 at address 0x50
#       Channels 6 and 7: No connect
#
# 1.0 260212 - New
#
#==========================================================

__version__ =   '1.0'
TOOLNAME =      'demo_shared'

PCA9548_RESBD = {'addr': 0x71, 'name': 'PCA9548_Res'}
PCA9548_IRRBD = {'addr': 0x75, 'name': 'PCA9548_Irr'}

# A minimum set of devices are defined to enable tests for this module


import argparse
import re
# import time
# import subprocess
# from pathlib import Path
# import shutil
import pigpio

from cjnfuncs.core              import set_toolname, setuplogging, logging, set_logging_level

from cjn_PiTools.shared         import pi_i2c
from cjn_PiTools.PCA9548        import PCA9548, build_bit_map, bit_map_to_channel_str


set_toolname(TOOLNAME)
setuplogging(ConsoleLogFormat="{module:>35}.{funcName:30} - {levelname:>8}:  {message}")
set_logging_level(logging.DEBUG)
logging.getLogger('cjn_PiTools.shared').setLevel(logging.DEBUG)
logging.getLogger('cjn_PiTools.PCA9548').setLevel(logging.DEBUG)


parser = argparse.ArgumentParser(description=__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-t', '--test', default='0',
                    help="Test number to run (default 0) - 0 runs all tests")
parser.add_argument('-x', '--expand-exception', action='store_true',
                    help="Expand exceptions with trace stack for test debug")
cli_args = parser.parse_args()


logging.warning (f"\n\n---- Test Init ------------------------------------------------------")


# Get i2c bus and device handles
pio =                   pigpio.pi()
i2c_bus_handle_pigpio = pi_i2c(pio)
i2c_bus_handle_smbus =  pi_i2c('smbus')

# pca9548_resBd_handle_pigpio =      PCA9548(PCA9548_RESBD['name'], PCA9548_RESBD['addr'], i2c_bus_handle_pio)
# pca9548_irrBd_handle_pigpio =      PCA9548(PCA9548_IRRBD['name'], PCA9548_IRRBD['addr'], i2c_bus_handle_pio)

# pca9548_resBd_handle_smbus =    PCA9548(PCA9548_RESBD['name'], PCA9548_RESBD['addr'], i2c_bus_handle_smbus)
# pca9548_irrBd_handle_smbus =    PCA9548(PCA9548_IRRBD['name'], PCA9548_IRRBD['addr'], i2c_bus_handle_smbus)


def dotest (desc, expect, func, *args, **kwargs):
    logging.warning (f"\n\n==============================================================================================\n" +
                     f"Test {tnum} - {desc}\n" +
                     f"  GIVEN:      {args}, {kwargs}\n" +
                     f"  EXPECT:     {expect}")
    try:
        result = func(*args, **kwargs)
        logging.warning (f"  RETURNED:\n{result}")
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
    # Tests for i2c_write_device
    if check_tnum('1a'):
        dotest ("i2c_write_device write 1 byte - pigpio api", "1",
                i2c_bus_handle_pigpio.i2c_write_device, PCA9548_RESBD['addr'], [0x55])


    if check_tnum('1b'):
        dotest ("i2c_write_device write 1 byte - smbus api", "1",
                i2c_bus_handle_smbus.i2c_write_device, PCA9548_RESBD['addr'], [0x55])


    if check_tnum('1c'):
        dotest ("i2c_write_device empty bytes_list - pigpio api", "ValueError: Illegal bytes_list received: <[]>",
                i2c_bus_handle_pigpio.i2c_write_device, PCA9548_RESBD['addr'], [])


    if check_tnum('1d'):
        dotest ("i2c_write_device empty bytes_list - smbus api", "ValueError: Illegal bytes_list received: <[]>",
                i2c_bus_handle_smbus.i2c_write_device, PCA9548_RESBD['addr'], [])


    if check_tnum('1e'):
        dotest ("i2c_write_device invalid bytes_list - pigpio api", "TypeError: 'str' object cannot be interpreted as an integer",
                i2c_bus_handle_pigpio.i2c_write_device, PCA9548_RESBD['addr'], ['help'])


    if check_tnum('1f'):
        dotest ("i2c_write_device invalid bytes_list - smbus api", "TypeError: an integer is required (got type str)",
                i2c_bus_handle_smbus.i2c_write_device, PCA9548_RESBD['addr'], ['help'])


    if check_tnum('1g'):
        def func():
            i2c_bus_handle_pigpio.i2c_write_device (PCA9548_RESBD['addr'], [0x80])
            xx = i2c_bus_handle_pigpio.i2c_write_device (PCA9548_IRRBD['addr'], [0x55])
            return xx

        dotest ("i2c_write_device target inaccessible - pigpio api", "error: 'I2C write failed'", func)


    if check_tnum('1h'):
        def func():
            i2c_bus_handle_smbus.i2c_write_device (PCA9548_RESBD['addr'], [0x80])
            xx = i2c_bus_handle_smbus.i2c_write_device (PCA9548_IRRBD['addr'], [0x55])
            return xx

        dotest ("i2c_write_device target inaccessible - smbus api", "OSError: [Errno 121] Remote I/O error", func)


    #-------------------------------------------------------------------------
    # Tests for i2c_read_device
    if check_tnum('2a'):
        i2c_bus_handle_pigpio.i2c_write_device (PCA9548_RESBD['addr'], [0x01])
        i2c_bus_handle_pigpio.i2c_write_device (PCA9548_IRRBD['addr'], [0x55])

        dotest ("i2c_read_device - pigpio api", "(1, [85]) (0x55)", i2c_bus_handle_pigpio.i2c_read_device, 0x75, 1)


    if check_tnum('2b'):
        i2c_bus_handle_smbus.i2c_write_device (PCA9548_RESBD['addr'], [0x01])
        i2c_bus_handle_smbus.i2c_write_device (PCA9548_IRRBD['addr'], [0x55])

        dotest ("i2c_read_device - smbus api", "(1, [85]) (0x55)", i2c_bus_handle_smbus.i2c_read_device, 0x75, 1)


    if check_tnum('2g'):
        i2c_bus_handle_smbus.i2c_write_device (PCA9548_RESBD['addr'], [0x80])

        dotest ("i2c_read_device target inaccessible - pigpio api", "OSError: i2c_read_device failed - error code <-83>",
                i2c_bus_handle_pigpio.i2c_read_device, 0x75, 1)


    if check_tnum('2h'):
        i2c_bus_handle_smbus.i2c_write_device (PCA9548_RESBD['addr'], [0x80])

        dotest ("i2c_read_device target inaccessible - smbus api", "OSError: [Errno 121] Remote I/O error", i2c_bus_handle_smbus.i2c_read_device, 0x75, 1)


    #-------------------------------------------------------------------------
    # Tests for i2c_read_byte
    if check_tnum('5a'):
        i2c_bus_handle_pigpio.i2c_write_device (PCA9548_RESBD['addr'], [0x55])

        dotest ("i2c_read_byte - pigpio api", "85 (0x55)",
                i2c_bus_handle_pigpio.i2c_read_byte, PCA9548_IRRBD['addr'])


    if check_tnum('5b'):
        i2c_bus_handle_smbus.i2c_write_device (PCA9548_RESBD['addr'], [0x55])

        dotest ("i2c_read_byte - smbus api", "85 (0x55)",
                i2c_bus_handle_smbus.i2c_read_byte, PCA9548_RESBD['addr'])


    if check_tnum('5g'):
        i2c_bus_handle_pigpio.i2c_write_device (PCA9548_RESBD['addr'], [0x80])

        dotest ("i2c_read_byte target inaccessible - pigpio api", "error: 'I2C read failed'",
                i2c_bus_handle_pigpio.i2c_read_byte, PCA9548_IRRBD['addr'])

    if check_tnum('5h'):
        i2c_bus_handle_smbus.i2c_write_device (PCA9548_RESBD['addr'], [0x80])

        dotest ("i2c_read_byte target inaccessible - smbus api", "OSError: [Errno 121] Remote I/O error",
                i2c_bus_handle_smbus.i2c_read_byte, PCA9548_IRRBD['addr'])




    # #-------------------------------------------------------------------------
    # # Development/testing/debug
    # if check_tnum('50', include0=False):

    #     logging.info ("Test 50 setup")
    #     remote_pio = pigpio.pi('testhost.cjn.lan')
    #     pio_i2c_bus_handle =     pi_i2c(remote_pio)
    #     sht3x_44_inst_pio =     SHT3x('sht3x44', 0x44, pio_i2c_bus_handle)
    #     sht3x_45_inst_pio =     SHT3x('sht3x45', 0x45, pio_i2c_bus_handle)


    #     def func():
    #         sht3x_44_inst_pio.soft_reset()
    #         return sht3x_44_inst_pio.single_shot()

    #     dotest ("Single Shot pigpio api remote (run from testhost2), default F, High, 16ms", "Pass", func)

    #     pio_i2c_bus_handle.close()
    #     remote_pio.stop()

    #     exit()


    logging.warning (f"\n\n---- Cleanup --------------------------------------------------------")

    i2c_bus_handle_pigpio.close()
    pio.stop()

    i2c_bus_handle_smbus.close()
    