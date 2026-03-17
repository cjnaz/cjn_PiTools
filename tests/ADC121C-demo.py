#!/usr/bin/env python3
"""Demo/test for ADC121C

Produce / compare to golden results:
    ./ADC121C-demo.py > testrun.log

    ./ADC121C-demo.py | diff ADC121C-golden.txt -
        Expected differences:
            Measured register values and voltages
            Addresses of cjn_PiTools.shared.pi_i2c objects in test 13
"""

#==========================================================
#
#  Chris Nelson, Copyright 2026
#
# 1.0 260212 - New
#
#==========================================================

__version__ =   '1.0'
TOOLNAME =      'ADC121C_demo'

import argparse
import re
import time
import pigpio

from cjnfuncs.core              import set_toolname, setuplogging, logging, set_logging_level
from cjn_PiTools.shared         import pi_i2c
from cjn_PiTools.ADC121C        import ADC121C
from cjn_PiTools.PCA9548        import PCA9548
from cjn_PiTools.MCP23008       import MCP23008


PCA9548_RESBD =     {'addr': 0x71, 'name': 'PCA9548_Res'}
PCA9548_IRRBD =     {'addr': 0x75, 'name': 'PCA9548_Irr'}
MCP23008_IO_ADDR =  0x20
MCP23008_ADC_CH =   '3'
MCP23008_IO_CH =    '4'
RESET_GPIO =        25
RELAY_3V3_GPIO =    21
RELAY_5V0_GPIO =    26


set_toolname(TOOLNAME)
setuplogging(ConsoleLogFormat="{module:>35}.{funcName:30} - {levelname:>8}:  {message}")
set_logging_level(logging.DEBUG)
logging.getLogger('cjn_PiTools.shared').setLevel(logging.DEBUG)
logging.getLogger('cjn_PiTools.ADC121C').setLevel(logging.DEBUG)
logging.getLogger('cjn_PiTools.PCA9548').setLevel(logging.DEBUG)
logging.getLogger('cjn_PiTools.MCP23008').setLevel(logging.DEBUG)


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

# Turn on power control relays which power devices plugged into the Board_1 I2C jacks
pio.write(RELAY_3V3_GPIO, 1)
pio.write(RELAY_5V0_GPIO, 1)
time.sleep(0.1)
pio.write(RESET_GPIO, 1)            # De-assert reset on Board_1 pca9548
time.sleep(0.1)

# Instantiate and configure I2C bus switches
pca9548_resBd_handle_pigpio =   PCA9548(PCA9548_RESBD['name'], PCA9548_RESBD['addr'], i2c_bus_handle_pigpio)
pca9548_irrBd_handle_pigpio =   PCA9548(PCA9548_IRRBD['name'], PCA9548_IRRBD['addr'], i2c_bus_handle_pigpio)
pca9548_resBd_handle_pigpio.write_control_reg ('0')

# Instantiate and configure IO expander for ADC input level shifting
pca9548_irrBd_handle_pigpio.write_control_reg (MCP23008_IO_CH)
MCP23008_IO_inst_pio =      MCP23008('MCP23008_IO', MCP23008_IO_ADDR, i2c_bus_handle_pigpio,
                                     IODIR_init=0xF0, GPIO_init=0x00, GPPU_init=0xf0)

# Instantiate and configure ADCs
pca9548_irrBd_handle_pigpio.write_control_reg (MCP23008_ADC_CH)
ADC121C_50_inst_pigpio =    ADC121C('ADC121C_50', 0x50, i2c_bus_handle_pigpio, Vref=4.2)
ADC121C_51_inst_pigpio =    ADC121C('ADC121C_51', 0x51, i2c_bus_handle_pigpio, Vref=4.2)

ADC121C_50_inst_smbus =     ADC121C('ADC121C_50', 0x50, i2c_bus_handle_smbus, Vref=4.2)
ADC121C_51_inst_smbus =     ADC121C('ADC121C_51', 0x51, i2c_bus_handle_smbus, Vref=4.2)


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
    # Basic demo read temp/RH pass cases
    if check_tnum('1a'):
        dotest ("read_conversion_result pigpio api", "(0, voltage value)", ADC121C_50_inst_pigpio.read_conversion_result)

    if check_tnum('1b'):
        dotest ("read_conversion_result smbus api", "(0, voltage value)", ADC121C_50_inst_smbus.read_conversion_result)

    if check_tnum('1c'):
        def func():
            ADC121C_50_inst_smbus.read_alert_status()
            alert, val = ADC121C_50_inst_smbus.read_conversion_result()
            alert, val = ADC121C_50_inst_smbus.read_conversion_result()
            ADC121C_50_inst_smbus.read_alert_status()
            alert, val = ADC121C_50_inst_smbus.read_conversion_result()
            return ADC121C_50_inst_smbus.read_conversion_result()           # Address Pointer Register write skipped on 2nd call

        dotest ("read_conversion_result without redundant write register select", "(0, voltage value)", func)


    #-------------------------------------------------------------------------
    # Alert cases
    #-------------------------------------------------------------------------

    if check_tnum('2a'):
        def func():
            ADC121C_51_inst_pigpio.write_vlow_alert_limit(1.5)
            ADC121C_51_inst_pigpio.read_vlow_alert_limit()
            ADC121C_51_inst_pigpio.write_vhigh_alert_limit(4.2)
            ADC121C_51_inst_pigpio.read_vhigh_alert_limit()
            ADC121C_51_inst_pigpio.write_alert_hysteresis(0.7)
            ADC121C_51_inst_pigpio.read_alert_hysteresis()
            ADC121C_51_inst_pigpio.write_config(cycle_time=0b111, alert_flag_en=1)  # Auto Conversion mode
            ADC121C_51_inst_pigpio.read_config()
            ADC121C_51_inst_pigpio.write_alert_status(clear_over=1, clear_under=1)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nEnable pulldown.  VIN = ~1.4V.  Low alert.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0010, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nDisable pulldown.  VIN = ~2.1V.  Still in low alert due to hysteresis 0.7V.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nEnable pullup.  VIN = ~2.8V.  Low alert clears.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0100, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nDisable pullup.  VIN = ~2.1V.  No alert.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nStop Auto Conversion")
            ADC121C_51_inst_pigpio.write_config()
            return ADC121C_51_inst_pigpio.read_conversion_result()

        dotest ("demo low limit alert and recover", "(0, voltage value)", func)

    if check_tnum('2b'):
        def func():
            ADC121C_51_inst_pigpio.write_vlow_alert_limit(0)
            ADC121C_51_inst_pigpio.read_vlow_alert_limit()
            ADC121C_51_inst_pigpio.write_vhigh_alert_limit(2.7)
            ADC121C_51_inst_pigpio.read_vhigh_alert_limit()
            ADC121C_51_inst_pigpio.write_alert_hysteresis(0.7)
            ADC121C_51_inst_pigpio.read_alert_hysteresis()
            ADC121C_51_inst_pigpio.write_config(cycle_time=0b111, alert_flag_en=1)  # Auto Conversion mode
            ADC121C_51_inst_pigpio.read_config()
            ADC121C_51_inst_pigpio.write_alert_status(clear_over=1, clear_under=1)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nEnable pullup.  VIN = ~2.8V.  High alert.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0100, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nDisable pullup.  VIN = ~2.1V.  Still in high alert due to hysteresis 0.7V.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nEnable pulldown.  VIN = ~1.4V.  High alert clears.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0010, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nDisable pulldown.  VIN = ~2.1V.  No alert.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nStop Auto Conversion")
            ADC121C_51_inst_pigpio.write_config()
            return ADC121C_51_inst_pigpio.read_conversion_result()

        dotest ("demo high limit alert and recover", "(0, voltage value)", func)


    if check_tnum('2c'):
        def func():
            ADC121C_51_inst_pigpio.write_vlow_alert_limit(1.5)
            ADC121C_51_inst_pigpio.write_vhigh_alert_limit(2.7)
            ADC121C_51_inst_pigpio.write_alert_hysteresis(0.1)
            ADC121C_51_inst_pigpio.write_config(cycle_time=0b111, alert_flag_en=1, alert_hold=1)
            ADC121C_51_inst_pigpio.read_config()
            ADC121C_51_inst_pigpio.write_alert_status(clear_over=1, clear_under=1)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nEnable pullup.  VIN = ~2.8V.  High alert.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0100, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nEnable pulldown.  VIN = ~1.4V.  Low alert.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0010, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\n Disable pulldown.  VIN = ~2.1V.  Both alerts still set.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()
            ADC121C_51_inst_pigpio.write_alert_status(clear_over=1)
            ADC121C_51_inst_pigpio.read_alert_status()
            ADC121C_51_inst_pigpio.write_alert_status(clear_under=1)
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nStop Auto Conversion")
            ADC121C_51_inst_pigpio.write_config()
            return ADC121C_51_inst_pigpio.read_conversion_result()

        dotest ("demo high limit alert with Alert Hold", "(0, voltage value)", func)


    #-------------------------------------------------------------------------
    # Capture lowest and highest readings
    if check_tnum('3'):
        def func():
            ADC121C_51_inst_pigpio.write_config(cycle_time=0b111)   # Auto Conversion mode
            ADC121C_51_inst_pigpio.read_config()
            ADC121C_51_inst_pigpio.write_highest_conversion()       # Clear the registers
            ADC121C_51_inst_pigpio.write_lowest_conversion()
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()

            logging.info ("\nEnable pulldown.  VIN = ~1.4V.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0010, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()

            logging.info ("\nDisable pulldown, Enable pullup.  VIN = ~2.8V.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0100, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()

            logging.info ("\nDisable pullup.  VIN = ~2.1V.")
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()

            logging.info ("\nStop Auto Conversion")
            ADC121C_51_inst_pigpio.write_config()
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()
            ADC121C_51_inst_pigpio.write_highest_conversion()               # Clear the registers
            ADC121C_51_inst_pigpio.write_lowest_conversion()
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()

            logging.info ("\nCapture highest/lowest in Normal mode")
            ADC121C_51_inst_pigpio.read_conversion_result()
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            MCP23008_IO_inst_pio.set_bits(0b0010, 0x0F)                     # Enable pulldown
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()

            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)   # Disable pulldown
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)

        dotest ("demo capture lowest and highest readings", "None", func)


    #-------------------------------------------------------------------------
    # write_config with config_byte
    if check_tnum('4a'):
        def func():
            ADC121C_50_inst_pigpio.write_config(config_byte=0b10101001,
                         cycle_time=0b111, alert_hold=0, alert_flag_en=0, alert_pin_en=0, polarity=1)
            return ADC121C_50_inst_pigpio.read_config()
        dotest ("write_config with config_byte wins over individual settings and defaults", "169 (0b10101001)", func)

    if check_tnum('4b'):
        def func():
            logging.info ("Instantiation with both config_byte and individuals (ignored)")
            xx = ADC121C('ADC_xx', 0x50, i2c_bus_handle_smbus, Vref=4.2, config_byte=0b10111111,
                         cycle_time=0b000, alert_hold=0, alert_flag_en=0, alert_pin_en=0, polarity=0)
            xx.read_config()

            logging.info ("write_config with new config_byte overriding defaults from config_byte at instantiation")
            xx.write_config(config_byte=0b11000010, alert_hold=0, alert_flag_en=0, alert_pin_en=0, polarity=0)
            xx.read_config()

            logging.info ("write_config with individuals overriding defaults from config_byte at instantiation")
            xx.write_config(cycle_time=0b010, alert_hold=0, alert_flag_en=0, alert_pin_en=0, polarity=0)
            xx.read_config()

            logging.info ("write_config using instantiation defaults")
            xx.write_config()
            return xx.read_config()
        dotest ("config instantiation defaults from config_byte", "189 (0b10111101)", func)

    if check_tnum('4c'):
        def func():
            logging.info ("Instantiation with individuals")
            xx = ADC121C('ADC_xx', 0x50, i2c_bus_handle_smbus, Vref=4.2,
                         cycle_time=0b001, alert_flag_en=1, alert_pin_en=1, alert_hold=1, polarity=1)
            xx.read_config()

            logging.info ("write_config with config_byte overriding defaults from instantiation")
            xx.write_config(config_byte=0xff)
            xx.read_config()

            logging.info ("write_config with individuals overriding defaults from instantiation")
            xx.write_config(cycle_time=0b110, alert_hold=0, alert_flag_en=0, alert_pin_en=0, polarity=0)
            xx.read_config()

            logging.info ("write_config using instantiation defaults")
            xx.write_config()
            return xx.read_config()
        dotest ("config instantiation defaults from indiv settings", "61 (0b00111101)", func)

    if check_tnum('4d'):
        def func():
            logging.info ("Instantiation with defaults")
            xx = ADC121C('ADC_xx', 0x50, i2c_bus_handle_smbus, Vref=4.2)
            xx.read_config()

            logging.info ("write_config with individuals overriding defaults from instantiation")
            xx.write_config(cycle_time=0b110, alert_hold=1, alert_flag_en=1, alert_pin_en=1, polarity=1)
            xx.read_config()

            logging.info ("write_config using instantiation defaults")
            xx.write_config()
            return xx.read_config()
        dotest ("config instantiation default defaults", "0 (0b00000000)", func)


    # #-------------------------------------------------------------------------
    # # Error cases
    if check_tnum('13a'):
        dotest ("Slave address out of range", "ValueError: ADC121C device address must be one of <0x50, 0x51, 0x52, 0x54, 0x55, 0x56, 0x58, 0x59, 0x5a>.  Received <0x60>",
                ADC121C, 'ADC121C_50', 0x60, i2c_bus_handle_pigpio, Vref=4.2)

    if check_tnum('13b'):
        dotest ("Invalid slave address", "ValueError: ADC121C device address must be one of <0x50, 0x51, 0x52, 0x54, 0x55, 0x56, 0x58, 0x59, 0x5a>.  Received <Hello>",
                ADC121C, 'ADC121C_50', 'Hello', i2c_bus_handle_pigpio, Vref=4.2)

    if check_tnum('13c'):
        def func():
            xx = ADC121C('ADC121C_5a', 0x5a, i2c_bus_handle_pigpio, Vref=4.2)
            return xx.read_config()
        dotest ("Device inaccessible during init", "-256 (Later accesses return I2C_ERROR)", func)

    if check_tnum('13d'):
        def func():
            pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
            return ADC121C_51_inst_pigpio.read_conversion_result()

        dotest ("Device inaccessible after successful init", "(-256, -256)", func)
        pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)

    if check_tnum('13e'):
        dotest ("Invalid value to write_alert_status", "ValueError: clear_over and clear_under must be ints 0 or 1 - received <a, 0>",
                ADC121C_51_inst_pigpio.write_alert_status, clear_over='a')

    if check_tnum('13f'):
        dotest ("Invalid cycle_time value to write_config", "ValueError: cycle_time must be int between 0b000 and 0b111 - received <-1>",
                ADC121C_51_inst_pigpio.write_config, cycle_time=-1)

    if check_tnum('13g'):
        def func():
            xx = ADC121C('ADC121C_5a', 0x5a, i2c_bus_handle_pigpio, Vref=4.2, alert_hold=5)
            xx.write_config(cycle_time=3)
            return xx
        dotest ("Invalid alert_hold value from init during later write_config during init", "ValueError: alert_hold must be int 0 or 1 - received <5>", func)

    if check_tnum('13h'):
        dotest ("Out of range write_vlow_alert_limit", "ValueError: vlow out of range 0.0V to VRef (4.200) - received <5>",
                ADC121C_51_inst_pigpio.write_vlow_alert_limit, 5)

    if check_tnum('13i'):
        dotest ("Invalid write_vlow_alert_limit", "ValueError: vlow out of range 0.0V to VRef (4.200) - received <hello>",
                ADC121C_51_inst_pigpio.write_vlow_alert_limit, 'hello')

    if check_tnum('13j'):
        dotest ("Invalid config_byte to write_config", "ValueError: config_byte must be int between 0x00 and 0xff - received <1365>",
                ADC121C_51_inst_pigpio.write_config, 0x555)

    if check_tnum('13k'):
        dotest ("Invalid config_byte in init", "ValueError: config_byte must be int between 0x00 and 0xff - received <4095>",
                ADC121C, 'ADC121C_50', 0x50, i2c_bus_handle_pigpio, Vref=4.2, config_byte=0xFFF)



    # #-------------------------------------------------------------------------
    # # Development/testing/debug
    if check_tnum('50', include0=False):

        logging.info ("Test 50")


        ADC121C_50_inst_pigpio.write_config(alert_flag_en=1, cycle_time=0b111, alert_hold=1)
        ADC121C_50_inst_pigpio.read_config()
        ADC121C_50_inst_pigpio.write_vlow_alert_limit(0.0)
        print (ADC121C_50_inst_pigpio.read_vlow_alert_limit())
        print (ADC121C_50_inst_pigpio.read_conversion_result())
        print (ADC121C_50_inst_pigpio.read_alert_status())

        ADC121C_50_inst_pigpio.write_vlow_alert_limit(4.0)
        print (ADC121C_50_inst_pigpio.read_vlow_alert_limit())
        print (ADC121C_50_inst_pigpio.read_conversion_result())
        print (ADC121C_50_inst_pigpio.read_alert_status())

        print (ADC121C_50_inst_pigpio.write_vlow_alert_limit(0.0))
        # print (ADC121C_50_inst_pigpio.read_vlow_limit_reg())
        print (ADC121C_50_inst_pigpio.read_conversion_result())
        print (ADC121C_50_inst_pigpio.read_alert_status())
        print (ADC121C_50_inst_pigpio.write_alert_status(clear_over=1, clear_under=1))
        print (ADC121C_50_inst_pigpio.read_alert_status())
        print (ADC121C_50_inst_pigpio.read_conversion_result())

        print (ADC121C_50_inst_pigpio.read_alert_hysteresis())
        print (ADC121C_50_inst_pigpio.write_alert_hysteresis(1))
        print (ADC121C_50_inst_pigpio.read_alert_hysteresis())

        print (ADC121C_50_inst_pigpio.write_config(cycle_time=0b000))
        print (ADC121C_50_inst_pigpio.read_lowest_conversion())
        print (ADC121C_50_inst_pigpio.read_highest_conversion())
        print (ADC121C_50_inst_pigpio.write_lowest_conversion())
        print (ADC121C_50_inst_pigpio.write_highest_conversion())
        print (ADC121C_50_inst_pigpio.read_lowest_conversion())
        print (ADC121C_50_inst_pigpio.read_highest_conversion())
        # print (ADC121C_50_inst_pigpio.write_lowest_conversion_reg())
        # print (ADC121C_50_inst_pigpio.read_lowest_conversion_reg())
        print (ADC121C_50_inst_pigpio.write_config(cycle_time=0b001))
        print (ADC121C_50_inst_pigpio.read_lowest_conversion())
        print (ADC121C_50_inst_pigpio.read_highest_conversion())
        print (ADC121C_50_inst_pigpio.write_config(cycle_time=0b000))
        print (ADC121C_50_inst_pigpio.read_lowest_conversion())
        print (ADC121C_50_inst_pigpio.read_highest_conversion())
        print (ADC121C_50_inst_pigpio.write_lowest_conversion())
        print (ADC121C_50_inst_pigpio.write_highest_conversion())
        print (ADC121C_50_inst_pigpio.read_lowest_conversion())
        print (ADC121C_50_inst_pigpio.read_highest_conversion())



    if check_tnum('51', include0=False):    # wiggle the VIN offset ckt
        logging.info ("Test 51")
        print (ADC121C_51_inst_pigpio.read_conversion_result())

        pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
        MCP23008_IO_inst_pio.set_bits(0b0010, 0x0F)
        time.sleep (0.1)
        pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
        print (ADC121C_51_inst_pigpio.read_conversion_result())
        print (ADC121C_51_inst_pigpio.read_conversion_result())

        pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
        MCP23008_IO_inst_pio.set_bits(0b0100, 0x0F)
        time.sleep (0.1)
        pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
        print (ADC121C_51_inst_pigpio.read_conversion_result())
        print (ADC121C_51_inst_pigpio.read_conversion_result())

        pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_IO_CH)
        MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
        time.sleep (0.1)
        pca9548_irrBd_handle_pigpio.write_control_reg(MCP23008_ADC_CH)
        print (ADC121C_51_inst_pigpio.read_conversion_result())
        print (ADC121C_51_inst_pigpio.read_conversion_result())


    if check_tnum('52', include0=False):
        logging.info ("Test 52 - write_config Behaviors notes")
        xx = ADC121C('ADC_xx', 0x50, i2c_bus_handle_smbus, Vref=4.2, cycle_time=0b100, alert_flag_en=1, alert_pin_en=1)
        xx.read_config()
        xx.write_config(cycle_time=0b001, alert_hold=1, alert_pin_en=0, polarity=1)
        xx.read_config()
        # xx.write_config(config_byte=0b11111111)
        # xx.read_config()


    logging.warning (f"\n\n---- Cleanup --------------------------------------------------------")

    i2c_bus_handle_pigpio.close()
    pio.stop()

    i2c_bus_handle_smbus.close()