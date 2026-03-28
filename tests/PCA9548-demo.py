#!/usr/bin/env python3
"""Demo/test for PCA9548

Produce / compare to golden results:
    ./PCA9548-demo.py > testrun.log

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
TOOLNAME =      'PCA9548_demo'


import argparse
import re
import pigpio

from cjnfuncs.core              import set_toolname, setuplogging, logging, set_logging_level
from cjn_PiTools.shared         import pi_i2c
from cjn_PiTools.PCA9548        import PCA9548


PCA9548_RESBD = {'addr': 0x71, 'name': 'PCA9548_Res'}
PCA9548_IRRBD = {'addr': 0x75, 'name': 'PCA9548_Irr'}


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

pca9548_resBd_handle_pigpio =   PCA9548(PCA9548_RESBD['name'], PCA9548_RESBD['addr'], i2c_bus_handle_pigpio)
pca9548_irrBd_handle_pigpio =   PCA9548(PCA9548_IRRBD['name'], PCA9548_IRRBD['addr'], i2c_bus_handle_pigpio)

pca9548_resBd_handle_smbus =    PCA9548(PCA9548_RESBD['name'], PCA9548_RESBD['addr'], i2c_bus_handle_smbus)
pca9548_irrBd_handle_smbus =    PCA9548(PCA9548_IRRBD['name'], PCA9548_IRRBD['addr'], i2c_bus_handle_smbus)


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
    # Basic demo write/read PCA9548 control register
    if check_tnum('1a'):
        def func():
            pca9548_resBd_handle_pigpio.write_control_reg (0x55)
            return pca9548_resBd_handle_pigpio.read_control_reg ()

        dotest ("write and read the control reg - pigpio api", "85 (0x55)", func)

    if check_tnum('1b'):
        def func():
            pca9548_resBd_handle_smbus.write_control_reg (0xaa)
            return pca9548_resBd_handle_smbus.read_control_reg ()

        dotest ("write and read the control reg - api smbus", "170 (0xaa)", func)

    if check_tnum('1c'):
        def func():
            pca9548_resBd_handle_smbus.write_control_reg (0xaa)
            logging.info (f"channel_enable_bit_map:  0b{pca9548_resBd_handle_smbus.channel_enable_bit_map:0>8b}")
            pca9548_resBd_handle_smbus.read_control_reg()

            pca9548_resBd_handle_pigpio.write_control_reg (0xff)
            logging.info (f"channel_enable_bit_map:  0b{pca9548_resBd_handle_pigpio.channel_enable_bit_map:0>8b}")
            pca9548_resBd_handle_pigpio.read_control_reg()

            pca9548_resBd_handle_smbus.write_control_reg('5')
            logging.info (f"channel_enable_bit_map:  0b{pca9548_resBd_handle_smbus.channel_enable_bit_map:0>8b}")
            pca9548_resBd_handle_smbus.read_control_reg()

        dotest ("Mix it up across apis", "None, no exception", func)


    #-------------------------------------------------------------------------
    # Exercise build_bit_map()
    if check_tnum('2a'):
        def func():
            return pca9548_resBd_handle_smbus._build_bit_map (0)

        dotest ("int value 0", "0", func)

    if check_tnum('2b'):
        def func():
            return pca9548_resBd_handle_smbus._build_bit_map (0x55)

        dotest ("int value 0x55", "85 (0x55)", func)

    if check_tnum('2c'):
        def func():
            return pca9548_resBd_handle_smbus._build_bit_map ('0')

        dotest ("str '0'", "1 - channel 0 enabled", func)

    if check_tnum('2d'):
        def func():
            return pca9548_resBd_handle_smbus._build_bit_map ('7')

        dotest ("str '7'", "128 (decimal) - channel 7 enabled", func)

    if check_tnum('2e'):
        def func():
            return pca9548_resBd_handle_smbus._build_bit_map ('-1')

        dotest ("str -1", "0 - No channel enabled", func)

    if check_tnum('2f'):
        def func():
            return pca9548_resBd_handle_smbus._build_bit_map ('Hello')

        dotest ("str 'Hello'", "ValueError: invalid literal for int() with base 10: 'Hello'", func)

    if check_tnum('2g'):
        def func():
            return pca9548_resBd_handle_smbus._build_bit_map ('9')

        dotest ("str '9'", "ValueError: <PCA9548_Res> channel_value (str) must be int range -1 to 7 - received <9>", func)


    #-------------------------------------------------------------------------
    # Exercise bit_map_to_channel_str()
    if check_tnum('3a'):
        dotest ("bit_map 1", "0 (str)", pca9548_resBd_handle_smbus._bit_map_to_channel_str, 1)

    if check_tnum('3b'):
        dotest ("bit_map 0x55", "0 2 4 6 (str)", pca9548_resBd_handle_smbus._bit_map_to_channel_str, 0x55)

    if check_tnum('3c'):
        dotest ("bit_map 0xff", "0 1 2 3 4 5 6 7 (str)", pca9548_resBd_handle_smbus._bit_map_to_channel_str, 0xff)

    if check_tnum('3d'):
        dotest ("bit_map 0", "'' (empty str)", pca9548_resBd_handle_smbus._bit_map_to_channel_str, 0)



    #-------------------------------------------------------------------------
    # Error conditions
    if check_tnum('13a'):
        def func():
            bad_addr_handle =  PCA9548('PCA9548_Bad', 0x80, i2c_bus_handle_pigpio)

        dotest ("Bad I2C address", "ValueError: <PCA9548_Bad> PCA9548 device.addr must be 0x70 - 0x77, received <0x80>", func)

    if check_tnum('13b'):
        def func():
            bad_name_handle =  PCA9548(['PCA9548_Bad'], 0x71, i2c_bus_handle_pigpio)

        dotest ("Bad device.name", "ValueError: PCA9548 device.name must be str, received <['PCA9548_Bad']>", func)

    if check_tnum('13c'):
        def func():
            pca9548_resBd_handle_pigpio.write_control_reg (0x1ff)

        dotest ("Int bit-map out of range", "ValueError: <PCA9548_Res> channel_value (int) must be int range 0x00 to 0xFF - received <511> / <0x1ff>", func)

    if check_tnum('13d'):
        def func():
            pca9548_resBd_handle_pigpio.write_control_reg ('7c')

        dotest ("Bad string channel select", "ValueError: invalid literal for int() with base 10: '7c'", func)

    if check_tnum('13e'):
        def func():
            pca9548_resBd_handle_pigpio.write_control_reg ('-2')

        dotest ("String channel select out of range", "ValueError: <PCA9548_Res> channel_value (str) must be int range -1 to 7 - received <-2>", func)

    if check_tnum('13f'):
        def func():
            pca9548_resBd_handle_pigpio.write_control_reg ('8')

        dotest ("String channel select out of range", "ValueError: <PCA9548_Res> channel_value (str) must be int range -1 to 7 - received <8>", func)

    if check_tnum('13g'):
        def func():
            pca9548_resBd_handle_pigpio.write_control_reg ('4')
            return pca9548_irrBd_handle_pigpio.write_control_reg (0x55)

        dotest ("PCA9548_Irr not accessible for write - pigpio api", "-256 (I2C_ERROR)", func)

    if check_tnum('13h'):
        def func():
            pca9548_resBd_handle_smbus.write_control_reg ('4')
            return pca9548_irrBd_handle_smbus.write_control_reg (0x55)

        dotest ("PCA9548_Irr not accessible for write - smbus api", "-256 (I2C_ERROR)", func)

    if check_tnum('13i'):
        def func():
            pca9548_resBd_handle_pigpio.write_control_reg ('0')
            pca9548_irrBd_handle_pigpio.write_control_reg (0x55)
            pca9548_resBd_handle_pigpio.write_control_reg ('4')
            return pca9548_irrBd_handle_pigpio.read_control_reg()

        dotest ("PCA9548_Irr not accessible for read - pigpio api", "-256 (I2C_ERROR)", func)

    if check_tnum('13j'):
        def func():
            pca9548_resBd_handle_smbus.write_control_reg ('0')
            pca9548_irrBd_handle_smbus.write_control_reg (0x55)
            pca9548_resBd_handle_smbus.write_control_reg ('4')
            return pca9548_irrBd_handle_smbus.read_control_reg()

        dotest ("PCA9548_Irr not accessible for read - api smbus", "-256 (I2C_ERROR)", func)


    # if check_tnum('50', include0=False):

    #     def func():
    #         sht3x_44_inst_pio.soft_reset()
    #         # sht3x_44_inst_pio.write_alert_reg('High_Set', 60, 80, tempunits='C')
    #         sht3x_44_inst_pio.read_alert_reg('High_Set',   tempunits='C')
    #         sht3x_44_inst_pio.read_alert_reg('High_Set')
    #         sht3x_44_inst_pio.read_alert_reg('High_Clear', tempunits='C')
    #         sht3x_44_inst_pio.read_alert_reg('Low_Clear',  tempunits='C')
    #         sht3x_44_inst_pio.read_alert_reg('Low_Set',    tempunits='C')

    #         sht3x_44_inst_pio.write_alert_reg('High_Set',  40, 50, tempunits='C')
    #         sht3x_44_inst_pio.read_alert_reg('High_Set',   tempunits='C')
    #         sht3x_44_inst_pio.read_status_reg()


    #     dotest ("read_alert_reg", "Pass", func)


    logging.warning (f"\n\n---- Cleanup --------------------------------------------------------")

    i2c_bus_handle_pigpio.close()
    pio.stop()

    i2c_bus_handle_smbus.close()
    