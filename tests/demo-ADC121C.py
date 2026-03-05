#!/usr/bin/env python3
"""Demo/test for ADC121C

Produce / compare to golden results:
    ./demo-SHT3x.py > testrun.log

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
#       Channel 3:  ADC121C ADC1 at address 0x50, Jack SOIL 1
#           ADC121C chips use 4.2V reference
#       Channel 3:  ADC121C ADC2 at address 0x51, Jack SOIL 2
#       Channel 4:  MCP23008_IO_ADDR at address 0x70 
#           Bit 0: OUT 1
#           Bit 1: OUT 2 - ADC test pulldown
#           Bit 2: OUT 3 - ADC test pullup
#           Bit 3: OUT 4
#           Bit 4: S1 input with weak pullup
#           Bit 5: S2 input with weak pullup
#           Bit 6: S3 input with weak pullup
#           Bit 7: NC
#       Channel 4:  MCP23008_7SEG_ADDR at address 0x71
#           All bits as outputs serving as pulldowns on common anode 7-segment display
#           Segment selects in DIG_2_SEG are inverted when written to MCP23008_7SEG_ADDR
#       Channel 5:  ADC121C ADC3 at address 0x52, Jack SOIL 3
#       Channel 5:  ADC121C ADC4 at address 0x50, Jack SOIL 4
#       Channels 6 and 7: No connect
#
# 1.0 260212 - New
#
#==========================================================

__version__ =   '1.0'
TOOLNAME =      'demo_ADC121C'

import argparse
import re
import time
import pigpio

from cjnfuncs.core              import set_toolname, setuplogging, logging, set_logging_level
from cjn_PiTools.shared         import pi_i2c
from cjn_PiTools.ADC121C        import ADC121C
from cjn_PiTools.PCA9548        import PCA9548
from cjn_PiTools.MCP23008       import mcp23008


PCA9548_RESBD =     {'addr': 0x71, 'name': 'PCA9548_Res'}
PCA9548_IRRBD =     {'addr': 0x75, 'name': 'PCA9548_Irr'}
MCP23008_IO_ADDR =  0x20
MCP23008_ADC_CH =   3
MCP23008_IO_CH =    4


set_toolname(TOOLNAME)
setuplogging(ConsoleLogFormat="{module:>35}.{funcName:30} - {levelname:>8}:  {message}")
set_logging_level(logging.DEBUG)
logging.getLogger('cjn_PiTools.shared').setLevel(logging.DEBUG)
logging.getLogger('cjn_PiTools.ADC121C').setLevel(logging.DEBUG)


parser = argparse.ArgumentParser(description=__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-t', '--test', default='0',
                    help="Test number to run (default 0) - 0 runs all tests")
parser.add_argument('-x', '--expand-exception', action='store_true',
                    help="Expand exceptions with trace stack for test debug")
cli_args = parser.parse_args()


logging.warning (f"\n\n---- Test Init ------------------------------------------------------")


# Get i2c bus and device handles
pio =                   pigpio.pi()
i2c_bus_handle_pio =    pi_i2c(pio)
i2c_bus_handle_smbus =  pi_i2c('smbus')

pca9548_resBd_handle_pigpio =   PCA9548(PCA9548_RESBD['name'], PCA9548_RESBD['addr'], i2c_bus_handle_pio)
pca9548_irrBd_handle_pigpio =   PCA9548(PCA9548_IRRBD['name'], PCA9548_IRRBD['addr'], i2c_bus_handle_pio)

pca9548_resBd_handle_pigpio.write_control_reg ('0')
pca9548_irrBd_handle_pigpio.write_control_reg ('4')
MCP23008_IO_inst_pio =      mcp23008('MCP23008_IO', MCP23008_IO_ADDR, i2c_bus_handle_pio,
                                     IO_dir_init=0xF0, out_bits_init=0x00, ins_pullups_init=0xf0)

pca9548_irrBd_handle_pigpio.write_control_reg ('3')
ADC121C_50_inst_pigpio =    ADC121C('ADC121C_50', 0x50, i2c_bus_handle_pio, Vref=4.2)
ADC121C_51_inst_pigpio =    ADC121C('ADC121C_51', 0x51, i2c_bus_handle_pio, Vref=4.2)

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


# selective write_config_reg after init
# alert low/high reg write/read
# See alert flag set in read_conversion_result
# See alert flags set in alert_status_register
# see auto clear or not (alert hold)

#===============================================================================================
if __name__ == '__main__':

    #-------------------------------------------------------------------------
    # Basic demo read temp/RH pass cases
    if check_tnum('1a'):
        dotest ("read_conversion_result pigpio api", "(0, voltage value)", ADC121C_50_inst_pigpio.read_conversion_result)

    if check_tnum('1b'):
        # def func():
        #     alert, val = ADC121C_50_inst_smbus.read_conversion_result()
        #     return ADC121C_50_inst_smbus.read_conversion_result()           # Address Pointer Register write skipped on 2nd call

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
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0010, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nDisable pulldown.  VIN = ~2.1V.  Still in low alert due to hysteresis 0.7V.")
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nEnable pullup.  VIN = ~2.8V.  Low alert clears.")
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0100, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nDisable pullup.  VIN = ~2.1V.  No alert.")
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
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
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0100, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nDisable pullup.  VIN = ~2.1V.  Still in high alert due to hysteresis 0.7V.")
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nEnable pulldown.  VIN = ~1.4V.  High alert clears.")
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0010, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nDisable pulldown.  VIN = ~2.1V.  No alert.")
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
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
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0100, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\nEnable pulldown.  VIN = ~1.4V.  Low alert.")
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0010, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_alert_status()

            logging.info ("\n Disable pulldown.  VIN = ~2.1V.  Both alerts still set.")
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
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
            ADC121C_51_inst_pigpio.write_config(cycle_time=0b111)  # Auto Conversion mode
            ADC121C_51_inst_pigpio.read_config()
            ADC121C_51_inst_pigpio.write_highest_conversion()   # Clear the registers
            ADC121C_51_inst_pigpio.write_lowest_conversion()
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()

            logging.info ("\nEnable pulldown.  VIN = ~1.4V.")
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0010, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()

            logging.info ("\nDisable pulldown, Enable pullup.  VIN = ~2.8V.")
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0100, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()

            logging.info ("\nDisable pullup.  VIN = ~2.1V.")
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()

            logging.info ("\nStop Auto Conversion")
            ADC121C_51_inst_pigpio.write_config()
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()
            ADC121C_51_inst_pigpio.write_highest_conversion()   # Clear the registers
            ADC121C_51_inst_pigpio.write_lowest_conversion()
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()

            logging.info ("\nCapture highest/lowest in Normal mode")
            ADC121C_51_inst_pigpio.read_conversion_result()
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            MCP23008_IO_inst_pio.set_bits(0b0010, 0x0F)         # Enable pulldown
            time.sleep (0.1)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')
            ADC121C_51_inst_pigpio.read_conversion_result()
            ADC121C_51_inst_pigpio.read_highest_conversion()
            ADC121C_51_inst_pigpio.read_lowest_conversion()

            pca9548_irrBd_handle_pigpio.write_control_reg('4')  # Disable pulldown
            MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
            pca9548_irrBd_handle_pigpio.write_control_reg('3')

        dotest ("demo capture lowest and highest readings", "None", func)


    #-------------------------------------------------------------------------
    # write_config with config_byte
    if check_tnum('4a'):
        def func():
            ADC121C_50_inst_pigpio.write_config(config_byte=0b10101001, cycle_time=0b111)
            return ADC121C_50_inst_pigpio.read_config()
        dotest ("write_config with config_byte wins over individual settings", "169 (0b10101001)", func)

    if check_tnum('4b'):
        def func():
            xx = ADC121C('ADC_xx', 0x50, i2c_bus_handle_smbus, Vref=4.2, config_byte=0b10101001, polarity=1)
            xx.read_config()
            xx.write_config(cycle_time=0b010)
            return xx.read_config()
        dotest ("init with config_byte, then write_config with individual setting", "65 (0b01000001)", func)


    # #-------------------------------------------------------------------------
    # # Error cases
    if check_tnum('13a'):
        dotest ("Slave address out of range", "ValueError: ADC121C device address must be one of <0x50, 0x51, 0x52, 0x54, 0x55, 0x56, 0x58, 0x59, 0x5a>.  Received <0x60>",
                ADC121C, 'ADC121C_50', 0x60, i2c_bus_handle_pio, Vref=4.2)

    if check_tnum('13b'):
        dotest ("Invalid slave address", "ValueError: ADC121C device address must be one of <0x50, 0x51, 0x52, 0x54, 0x55, 0x56, 0x58, 0x59, 0x5a>.  Received <Hello>",
                ADC121C, 'ADC121C_50', 'Hello', i2c_bus_handle_pio, Vref=4.2)

    if check_tnum('13c'):
        def func():
            xx = ADC121C('ADC121C_5a', 0x5a, i2c_bus_handle_pio, Vref=4.2)
            return xx.read_config()
        dotest ("Device inaccessible during init", "-256 (Later accesses return I2C_ERROR)", func)

    if check_tnum('13d'):
        def func():
            pca9548_irrBd_handle_pigpio.write_control_reg('4')
            return ADC121C_51_inst_pigpio.read_conversion_result()

        dotest ("Device inaccessible after successful init", "(-256, -256)", func)
        pca9548_irrBd_handle_pigpio.write_control_reg('3')

    if check_tnum('13e'):
        dotest ("Invalid value to write_alert_status", "ValueError: clear_over and clear_under must be ints 0 or 1 - received <a, 0>",
                ADC121C_51_inst_pigpio.write_alert_status, clear_over='a')

    if check_tnum('13f'):
        dotest ("Invalid cycle_time value to write_config", "ValueError: cycle_time must be int between 0b000 and 0b111 - received <-1>",
                ADC121C_51_inst_pigpio.write_config, cycle_time=-1)

    if check_tnum('13g'):
        def func():
            xx = ADC121C('ADC121C_5a', 0x5a, i2c_bus_handle_pio, Vref=4.2, alert_hold=5)
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
                ADC121C, 'ADC121C_50', 0x50, i2c_bus_handle_pio, Vref=4.2, config_byte=0xFFF)



    # if check_tnum('9b'):
    #     def func():
    #         pca9548_class_handle.write_control_reg (7)          # No SHT3x connected at address 0x44
    #         return sht3x_44_inst_pio.soft_reset()

    #     dotest ("Attempt soft_reset() with inaccessible device - pigpio api", "I2C_ERROR -256", func)

    #     # Restore to default i2c network config
    #     pca9548_class_handle.write_control_reg ('0b110')        # Enable Channels 1 and 2 (SHT3x devices available at 0x44 and 0x45)


    # if check_tnum('9c'):
    #     def func():
    #         pca9548_class_handle.write_control_reg (7)
    #         return sht3x_44_inst_pio.fetch_data(send_fetch=False)

    #     dotest ("Attempt fetch_data() with inaccessible device - pigpio api", "I2C_ERROR (-256, -256)", func)

    #     # Restore to default i2c network config
    #     pca9548_class_handle.write_control_reg ('0b110')


    # if check_tnum('9d'):
    #     def func():
    #         pca9548_class_handle.write_control_reg (7)
    #         return sht3x_44_inst_smbus.soft_reset()

    #     dotest ("Attempt soft_reset() with inaccessible device - smbus api", "I2C_ERROR -256", func)

    #     # Restore to default i2c network config
    #     pca9548_class_handle.write_control_reg ('0b110')


    # if check_tnum('9e'):
    #     def func():
    #         pca9548_class_handle.write_control_reg (7)
    #         return sht3x_44_inst_smbus.fetch_data(send_fetch=False)

    #     dotest ("Attempt fetch_data() with inaccessible device - smbus api", "I2C_ERROR (-256, -256)", func)

    #     # Restore to default i2c network config
    #     pca9548_class_handle.write_control_reg ('0b110')


    # if check_tnum('9f'):
    #     def func():
    #         return sht3x_44_inst_smbus.single_shot(repeatability="NOTA")

    #     dotest ("Attempt fetch_data() with invalid repeatability - smbus api", "ValueError: Invalid Single Shot mode selection - received repeatability <NOTA>", func)


    # if check_tnum('9g'):
    #     def func():
    #         return sht3x_44_inst_pio.start_periodic_DA(repeatability="NOTA", mps='16')

    #     dotest ("Attempt start_periodic_DA() with invalid repeatability & mps - pigpio api", "ValueError: Invalid Periodic Data Acquisition mode selection - received repeatability <NOTA>, mps: <16>", func)


    # if check_tnum('9h'):
    #     def func():
    #         sht3x_44_inst_pio.start_periodic_DA()
    #         temp, rh = sht3x_44_inst_pio.fetch_data(force_CRC_fail=True)
    #         sht3x_44_inst_pio.stop_periodic_DA()
    #         return temp, rh

    #     dotest ("fetch_data() CRC fail - pigpio api", "(-255, -255)", func)


    # if check_tnum('9i'):
    #     def func():
    #         return sht3x_44_inst_pio.read_status_reg(force_CRC_fail=True)

    #     dotest ("read_status_reg() CRC fail - pigpio api", "-255", func)


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

        pca9548_irrBd_handle_pigpio.write_control_reg('4')
        MCP23008_IO_inst_pio.set_bits(0b0010, 0x0F)
        time.sleep (0.1)
        pca9548_irrBd_handle_pigpio.write_control_reg('3')
        print (ADC121C_51_inst_pigpio.read_conversion_result())
        print (ADC121C_51_inst_pigpio.read_conversion_result())

        pca9548_irrBd_handle_pigpio.write_control_reg('4')
        MCP23008_IO_inst_pio.set_bits(0b0100, 0x0F)
        time.sleep (0.1)
        pca9548_irrBd_handle_pigpio.write_control_reg('3')
        print (ADC121C_51_inst_pigpio.read_conversion_result())
        print (ADC121C_51_inst_pigpio.read_conversion_result())

        pca9548_irrBd_handle_pigpio.write_control_reg('4')
        MCP23008_IO_inst_pio.set_bits(0b0000, 0x0F)
        time.sleep (0.1)
        pca9548_irrBd_handle_pigpio.write_control_reg('3')
        print (ADC121C_51_inst_pigpio.read_conversion_result())
        print (ADC121C_51_inst_pigpio.read_conversion_result())



    #     def func():
    #         sht3x_44_inst_pio.clear_status_reg()
    #         sht3x_44_inst_pio.soft_reset()
    #         sht3x_44_inst_pio.read_status_reg()
    #         # sht3x_44_inst_pio.write_alert_reg('High_Set', 60, 80, tempunits='C')
    #         sht3x_44_inst_pio.read_alert_reg('High_Set',   tempunits='C')
    #         # sht3x_44_inst_pio.read_alert_reg('High_Set')
    #         sht3x_44_inst_pio.read_alert_reg('High_Clear', tempunits='C')
    #         sht3x_44_inst_pio.read_alert_reg('Low_Clear',  tempunits='C')
    #         sht3x_44_inst_pio.read_alert_reg('Low_Set',    tempunits='C')

    #         sht3x_44_inst_pio.write_alert_reg('High_Set',  40, 50, tempunits='C')
    #         sht3x_44_inst_pio.read_alert_reg('High_Set',   tempunits='C')
    #         sht3x_44_inst_pio.soft_reset()
    #         sht3x_44_inst_pio.read_alert_reg('High_Set',   tempunits='C')
    #         # sht3x_44_inst_pio.read_status_reg()


    #     dotest ("read_alert_reg", "Pass", func)


    # if check_tnum('52', include0=False):

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

    i2c_bus_handle_pio.close()
    pio.stop()

    i2c_bus_handle_smbus.close()