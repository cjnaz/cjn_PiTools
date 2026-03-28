#!/usr/bin/env python3
"""Demo/test for DS18B20

Produce / compare to golden results:
    sudo /path_to/venvs/pydev-3.9/bin/python ./DS18B20-demo.py > testrun.log

    Expected differences:
        Log timestamps, w1_slave file content, and temperature values
"""

#==========================================================
#
#  Chris Nelson, Copyright 2026
#
# 1.0 260401 - New
#
#==========================================================

__version__ =   '1.0'
TOOLNAME =      'DS18B20_demo'

import argparse
import re

from cjnfuncs.core          import set_toolname, setuplogging, logging, set_logging_level
from cjn_PiTools.DS18B20    import DS18B20


set_toolname(TOOLNAME)
setuplogging(ConsoleLogFormat="{asctime} {module:>35}.{funcName:30} - {levelname:>8}:  {message}")
set_logging_level(logging.DEBUG)
logging.getLogger('cjn_PiTools.DS18B20').setLevel(logging.DEBUG)


parser = argparse.ArgumentParser(description=__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-t', '--test', default='0',
                    help="Test number to run (default 0) - 0 runs all tests")
parser.add_argument('-x', '--expand-exception', action='store_true',
                    help="Expand exceptions with trace stack for test debug")
cli_args = parser.parse_args()


logging.warning (f"\n\n---- Test Init ------------------------------------------------------")


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


sensor_7113 = DS18B20('28-0b2280337113', 'My_7113')
sensor_203c = DS18B20('28-0b228004203c', 'My_203c')


if sensor_7113.get_alarm_temps() != '-55 125'  or  sensor_7113.get_resolution() != 12  or  sensor_7113.get_conv_time() != 750:
    logging.debug (f"sensor_7113.set_alarm_temps(-55, 125)     returned: <{sensor_7113.set_alarm_temps(-55, 125)}>")
    logging.debug (f"sensor_7113.set_resolution(12)            returned: <{sensor_7113.set_resolution(12)}>")
    logging.debug (f"sensor_7113.copy_scratchpad()             returned: <{sensor_7113.copy_scratchpad()}>")


#===============================================================================================
if __name__ == '__main__':

    #-------------------------------------------------------------------------
    # Basic demo read temp pass cases
    if check_tnum('1a'):
        dotest ("sensor_7113.read_temperature, value in F", "Temperature F", sensor_7113.read_temperature, tempunits='f')

    if check_tnum('1b'):
        dotest ("sensor_203c.read_temperature, value in C", "Temperature C", sensor_203c.read_temperature)

    if check_tnum('1c'):
        dotest ("sensor_203c.read_temperature2, value in K", "Temperature K", sensor_203c.read_temperature2, tempunits='k')

    if check_tnum('1d'):
        dotest ("sensor_7113.read_scratchpad", "Scratchpad list", sensor_7113.read_scratchpad)


    #-------------------------------------------------------------------------
    # bulk_convert_trigger and get readings
    if check_tnum('2'):
        def func():
            logging.debug (f"sensor_7113.bulk_convert_trigger() returned: <{sensor_7113.bulk_convert_trigger()}>")
            logging.debug (f"sensor_7113.bulk_convert_status() returned: <{sensor_7113.bulk_convert_status()}>")
            logging.debug (f"sensor_203c.read_temperature2() returned: <{sensor_203c.read_temperature2()}>")
            logging.debug (f"sensor_7113.bulk_convert_status() returned: <{sensor_7113.bulk_convert_status()}>")
            logging.debug (f"sensor_7113.read_temperature2() returned: <{sensor_7113.read_temperature2(tempunits='c')}>")
            logging.debug (f"sensor_7113.bulk_convert_status() returned: <{sensor_7113.bulk_convert_status()}>")

        dotest ("bulk_convert_trigger sequence", "None (pass, no exceptions)", func)


    #-------------------------------------------------------------------------
    # get/set resolution and observe measurement/conversion time - requires sudo/root priv
    if check_tnum('3a'):
        def func():
            logging.debug (f"sensor_7113.get_resolution()   returned: <{sensor_7113.get_resolution()}>")
            logging.debug (f"sensor_7113.set_resolution(9)  returned: <{sensor_7113.set_resolution(9)}>")
            logging.debug (f"sensor_7113.get_conv_time()    returned: <{sensor_7113.get_conv_time()}>")
            logging.debug (f"sensor_7113.read_temperature() returned: <{sensor_7113.read_temperature()}>")
        dotest ("Resolution 9", "None (pass, no exceptions)", func)

    if check_tnum('3b'):
        def func():
            logging.debug (f"sensor_7113.get_resolution()   returned: <{sensor_7113.get_resolution()}>")
            logging.debug (f"sensor_7113.set_resolution(10) returned: <{sensor_7113.set_resolution(10)}>")
            logging.debug (f"sensor_7113.get_conv_time()    returned: <{sensor_7113.get_conv_time()}>")
            logging.debug (f"sensor_7113.read_temperature() returned: <{sensor_7113.read_temperature()}>")
        dotest ("Resolution 10", "None (pass, no exceptions)", func)

    if check_tnum('3c'):
        def func():
            logging.debug (f"sensor_7113.get_resolution()   returned: <{sensor_7113.get_resolution()}>")
            logging.debug (f"sensor_7113.set_resolution(11) returned: <{sensor_7113.set_resolution(11)}>")
            logging.debug (f"sensor_7113.get_conv_time()    returned: <{sensor_7113.get_conv_time()}>")
            logging.debug (f"sensor_7113.read_temperature() returned: <{sensor_7113.read_temperature()}>")
        dotest ("Resolution 11", "None (pass, no exceptions)", func)

    if check_tnum('3d'):
        def func():
            logging.debug (f"sensor_7113.get_resolution()   returned: <{sensor_7113.get_resolution()}>")
            logging.debug (f"sensor_7113.set_resolution(12) returned: <{sensor_7113.set_resolution(12)}>")
            logging.debug (f"sensor_7113.get_conv_time()    returned: <{sensor_7113.get_conv_time()}>")
            logging.debug (f"sensor_7113.read_temperature() returned: <{sensor_7113.read_temperature()}>")
        dotest ("Resolution 12", "None (pass, no exceptions)", func)


    #-------------------------------------------------------------------------
    # get/set conversion time - requires sudo/root priv
    if check_tnum('4'):
        def func():
            logging.debug (f"sensor_7113.set_resolution(9)  returned: <{sensor_7113.set_resolution(9)}>")
            logging.debug (f"sensor_7113.get_conv_time()    returned: <{sensor_7113.get_conv_time()}>")
            logging.debug (f"sensor_7113.read_temperature() returned: <{sensor_7113.read_temperature()}>")

            logging.debug (f"sensor_7113.set_conv_time(120) returned: <{sensor_7113.set_conv_time(120)}>")
            logging.debug (f"sensor_7113.read_temperature() returned: <{sensor_7113.read_temperature()}>")

            logging.debug (f"sensor_7113.set_conv_time(250) returned: <{sensor_7113.set_conv_time(250)}>")
            logging.debug (f"sensor_7113.read_temperature() returned: <{sensor_7113.read_temperature()}>")

            logging.debug (f"sensor_7113.set_conv_time(1)   returned: <{sensor_7113.set_conv_time(1)}>")
            logging.debug (f"sensor_7113.read_temperature() returned: <{sensor_7113.read_temperature()}>")

            logging.debug (f"sensor_7113.set_conv_time(0)   returned: <{sensor_7113.set_conv_time(0)}>")
            logging.debug (f"sensor_7113.read_temperature() returned: <{sensor_7113.read_temperature()}>")

        dotest ("set_conv_time to 120/250ms, measured, and default", "None (pass, no exceptions)", func)


    #-------------------------------------------------------------------------
    # get_alarm_temps/set_alarm_temps
    if check_tnum('5'):
        def func():
            logging.debug (f"sensor_7113.recall_E2()                 returned: <{sensor_7113.recall_E2()}>")
            logging.debug (f"sensor_7113.get_alarm_temps()           returned: <{sensor_7113.get_alarm_temps()}>")
            logging.debug (f"sensor_7113.set_alarm_temps(20, 30)     returned: <{sensor_7113.set_alarm_temps(20, 30)}>")
            logging.debug (f"sensor_7113.get_alarm_temps()           returned: <{sensor_7113.get_alarm_temps()}>")

            logging.debug (f"sensor_7113.set_alarm_temps('31', '19') returned: <{sensor_7113.set_alarm_temps('31', '19')}>")
            logging.debug (f"sensor_7113.get_alarm_temps()           returned: <{sensor_7113.get_alarm_temps()}>")

        dotest ("get_alarm_temps/set_alarm_temps", "None (pass, no exceptions)", func)


    #-------------------------------------------------------------------------
    # get_ext_power status

    if check_tnum('6'):
        dotest ("sensor_203c.get_ext_power", "1", sensor_203c.get_ext_power)


    #-------------------------------------------------------------------------
    # Save/restore from EEPROM
    if check_tnum('7'):
        def func():
            logging.debug (f"sensor_7113.recall_E2()                 returned: <{sensor_7113.recall_E2()}>")
            logging.debug (f"sensor_7113.get_alarm_temps()           returned: <{sensor_7113.get_alarm_temps()}>")
            logging.debug (f"sensor_7113.get_resolution()            returned: <{sensor_7113.get_resolution()}>")
            logging.debug ("")

            logging.debug (f"sensor_7113.set_alarm_temps(20, 30)     returned: <{sensor_7113.set_alarm_temps(20, 30)}>")
            logging.debug (f"sensor_7113.set_resolution(10)          returned: <{sensor_7113.set_resolution(10)}>")
            logging.debug (f"sensor_7113.copy_scratchpad()           returned: <{sensor_7113.copy_scratchpad()}>")
            logging.debug (f"sensor_7113.set_alarm_temps(25, 18)     returned: <{sensor_7113.set_alarm_temps(25, 28)}>")
            logging.debug (f"sensor_7113.set_resolution(11)          returned: <{sensor_7113.set_resolution(11)}>")
            logging.debug (f"sensor_7113.recall_E2()                 returned: <{sensor_7113.recall_E2()}>")
            logging.debug (f"sensor_7113.get_alarm_temps()           returned: <{sensor_7113.get_alarm_temps()}>")
            logging.debug (f"sensor_7113.get_resolution()            returned: <{sensor_7113.get_resolution()}>")
            logging.debug ("")

            # Reset to default values
            logging.debug (f"sensor_7113.set_alarm_temps(-55, 125)   returned: <{sensor_7113.set_alarm_temps(-55, 125)}>")
            logging.debug (f"sensor_7113.set_resolution(12)          returned: <{sensor_7113.set_resolution(12)}>")
            logging.debug (f"sensor_7113.copy_scratchpad()           returned: <{sensor_7113.copy_scratchpad()}>")
            logging.debug (f"sensor_7113.recall_E2()                 returned: <{sensor_7113.recall_E2()}>")
            logging.debug (f"sensor_7113.get_alarm_temps()           returned: <{sensor_7113.get_alarm_temps()}>")
            logging.debug (f"sensor_7113.get_resolution()            returned: <{sensor_7113.get_resolution()}>")

        dotest ("Save/restore from EEPROM", "None (pass, no exceptions)", func)


    #-------------------------------------------------------------------------
    # Error cases

    if check_tnum('13a'):
        dotest ("sensor not found", "FileNotFoundError: [Errno 2] No such file or directory: '/sys/bus/w1/devices/28-0b2280337000'",
                DS18B20,'28-0b2280337000', 'My_7000')

    if check_tnum('13b'):
        def func():
            xyz = DS18B20 ('28-0b2280337113', {x:y})
            logging.debug (f"xyz.get_alarm_temps()           returned: <{xyz.get_alarm_temps()}>")
        dotest ("Invalid device_name", "NameError: name 'x' is not defined", func)
                

    if check_tnum('13c'):
        dotest ("Invalid temp in set_alarm_temps()", "ValueError: <28-0b2280337113 / My_7113> alarm temps must be int or str values between -55 C and 125 C - received <a, b>",
                sensor_7113.set_alarm_temps, 'a', 'b')

    if check_tnum('13d'):
        dotest ("Invalid temp in set_alarm_temps()", "ValueError: <28-0b2280337113 / My_7113> alarm temps must be int or str values between -55 C and 125 C - received <-56, 125>",
                sensor_7113.set_alarm_temps, '-56', 125)

    if check_tnum('13e'):
        dotest ("Invalid value in set_resolution()", "ValueError: <28-0b2280337113 / My_7113> resolution value must be int or str 9, 10, 11 or 12 - received <['George']>",
                sensor_7113.set_resolution, ['George'])

    if check_tnum('13f'):
        dotest ("Invalid value in set_resolution()", "ValueError: <28-0b2280337113 / My_7113> resolution value must be int or str 9, 10, 11 or 12 - received <13>",
                sensor_7113.set_resolution, 13)

    if check_tnum('13g'):
        dotest ("Invalid value in set_conv_time()", "ValueError: <28-0b2280337113 / My_7113> conv_setting value must be int or str => 0",
                sensor_7113.set_conv_time, -1)

    if check_tnum('13h'):
        dotest ("Invalid value in set_conv_time()", "ValueError: <28-0b2280337113 / My_7113> conv_setting value must be int or str => 0",
                sensor_7113.set_conv_time, 'George')

    if check_tnum('13i'):
        dotest ("Invalid tempunits in read_temperature()", "ValueError: <28-0b2280337113 / My_7113> tempunits must be 'C', 'F', or 'K' - received <M>",
                sensor_7113.read_temperature, tempunits='M')



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


    # logging.warning (f"\n\n---- Cleanup --------------------------------------------------------")

