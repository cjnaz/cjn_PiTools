#!/usr/bin/env python3
"""Demo/test for shared

Produce / compare to golden results:
    ./shared-demo.py > testrun.log

    Expected differences:
        None
"""

#==========================================================
#
#  Chris Nelson, Copyright 2026
#
# 1.0 260401 - New
#
#==========================================================

__version__ =   '1.0'
TOOLNAME =      'shared_demo'

import argparse
import re
import pigpio

from cjnfuncs.core              import set_toolname, setuplogging, logging, set_logging_level

from cjn_PiTools.shared         import pi_i2c, CtoF, FtoC, CtoK, KtoC, calculate_dew_point


PCA9548_RESBD = {'addr': 0x71, 'name': 'PCA9548_Res'}
PCA9548_IRRBD = {'addr': 0x75, 'name': 'PCA9548_Irr'}


set_toolname(TOOLNAME)
setuplogging(ConsoleLogFormat="{module:>35}.{funcName:30} - {levelname:>8}:  {message}")
set_logging_level(logging.DEBUG)
logging.getLogger('cjn_PiTools.shared').setLevel(logging.DEBUG)


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
        i2c_bus_handle_smbus.i2c_write_device (PCA9548_IRRBD['addr'], [0x50])

        dotest ("i2c_read_device - smbus api", "(1, [80]) (0x50)", i2c_bus_handle_smbus.i2c_read_device, 0x75, 1)


    if check_tnum('2g'):
        i2c_bus_handle_smbus.i2c_write_device (PCA9548_RESBD['addr'], [0x80])

        dotest ("i2c_read_device target inaccessible - pigpio api", "OSError: i2c_read_device failed - error code <-83>",
                i2c_bus_handle_pigpio.i2c_read_device, 0x75, 1)


    if check_tnum('2h'):
        i2c_bus_handle_smbus.i2c_write_device (PCA9548_RESBD['addr'], [0x80])

        dotest ("i2c_read_device target inaccessible - smbus api", "OSError: [Errno 121] Remote I/O error",
                i2c_bus_handle_smbus.i2c_read_device, 0x75, 1)


    #-------------------------------------------------------------------------
    # Tests for i2c_write_byte & i2c_read_byte

    if check_tnum('5a'):
        def func():
            i2c_bus_handle_pigpio.i2c_write_byte (PCA9548_RESBD['addr'], 0xaa)
            return i2c_bus_handle_pigpio.i2c_read_byte (PCA9548_RESBD['addr'])

        dotest ("i2c_write_byte / i2c_read_byte - pigpio api", "170 (0xAA)", func)


    if check_tnum('5b'):
        def func():
            i2c_bus_handle_smbus.i2c_write_byte (PCA9548_RESBD['addr'], 0xa5)
            return i2c_bus_handle_smbus.i2c_read_byte (PCA9548_RESBD['addr'])

        dotest ("i2c_write_byte / i2c_read_byte - smbus api", "165 (0xA5)", func)


    if check_tnum('5g'):
        def func():
            i2c_bus_handle_pigpio.i2c_write_byte (PCA9548_RESBD['addr'], 0x80)
            return i2c_bus_handle_pigpio.i2c_read_byte (PCA9548_IRRBD['addr'])

        dotest ("i2c_read_byte target inaccessible - pigpio api", "error: 'I2C read failed'", func)


    if check_tnum('5h'):
        def func():
            i2c_bus_handle_smbus.i2c_write_byte (PCA9548_RESBD['addr'], 0x80)
            return i2c_bus_handle_smbus.i2c_read_byte (PCA9548_IRRBD['addr'])

        dotest ("i2c_read_byte target inaccessible - smbus api", "OSError: [Errno 121] Remote I/O error", func)


    #-------------------------------------------------------------------------
    # Temperature functions

    if check_tnum('8a'):
        dotest ("CtoF", "77.0", CtoF, 25)


    if check_tnum('8b'):
        dotest ("FtoC", "62.22222222222222", FtoC, 144)


    if check_tnum('8c'):
        dotest ("CtoK", "298.15", CtoK, 25)


    if check_tnum('8d'):
        dotest ("KtoC", "26.350000000000023", KtoC, 299.5)


    if check_tnum('8e'):
        dotest ("calculate_dew_point return C", "13.851583599891661", calculate_dew_point, 25.0, 50.0)


    if check_tnum('8f'):
        def func():
            return CtoF(calculate_dew_point(25, 50))
        dotest ("calculate_dew_point, return F", "56.93285047980499", func)


    if check_tnum('8m'):
        dotest ("CtoF arg error str", "TypeError: can't multiply sequence by non-int of type 'float'", CtoF, '25')


    if check_tnum('8n'):
        dotest ("CtoF arg error list", "TypeError: can't multiply sequence by non-int of type 'float'", CtoF, [25])


    if check_tnum('8o'):
        dotest ("calculate_dew_point invalid tempC", "TypeError: can't multiply sequence by non-int of type 'float'",
                calculate_dew_point, [25], 50)


    if check_tnum('8p'):
        dotest ("calculate_dew_point invalid RH", "TypeError: can't multiply sequence by non-int of type 'float'",
                calculate_dew_point, 25, '50')


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
    