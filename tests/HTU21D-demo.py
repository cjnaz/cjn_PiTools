#!/usr/bin/env python3
"""Demo/test for HTU21D

Produce / compare to golden results:
    ./HTU21D-demo.py > testrun.log

    ./HTU21D-demo.py | diff HTU21D-golden.txt -
        Expected differences:
            Measured raw byte codes, temperatures and RHs
            Measurement times in tests 1 and 6
            Object memory address in test 13g
"""

#==========================================================
#
#  Chris Nelson, Copyright 2026
#
# 1.0 260212 - New
#
#==========================================================

__version__ =   '1.0'
TOOLNAME =      'HTU21D_demo'

import argparse
import re
import time
import pigpio

from cjnfuncs.core              import set_toolname, setuplogging, logging, set_logging_level

from cjn_PiTools.shared         import pi_i2c, I2C_ERROR
from cjn_PiTools.HTU21D         import HTU21D
from cjn_PiTools.PCA9548        import PCA9548


PCA9548_RESBD =     {'addr': 0x71, 'name': 'PCA9548_Res'}
HTU21D_IO_CH =      '6'
RESET_GPIO =        25
RELAY_3V3_GPIO =    21
RELAY_5V0_GPIO =    26


set_toolname(TOOLNAME)
setuplogging(ConsoleLogFormat="{module:>35}.{funcName:30} - {levelname:>8}:  {message}")
set_logging_level(logging.DEBUG)
logging.getLogger('cjn_PiTools.shared').setLevel(logging.DEBUG)
logging.getLogger('cjn_PiTools.HTU21D').setLevel(logging.DEBUG)
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

# Turn on power control relays which power devices plugged into the Board_1 I2C jacks
pio.write(RELAY_3V3_GPIO, 1)
pio.write(RELAY_5V0_GPIO, 1)
time.sleep(0.1)
pio.write(RESET_GPIO, 1)            # De-assert reset on Board_1 pca9548
time.sleep(0.1)

# Instantiate and configure I2C bus switch
pca9548_resBd_handle_pigpio =   PCA9548(PCA9548_RESBD['name'], PCA9548_RESBD['addr'], i2c_bus_handle_pigpio)
pca9548_resBd_handle_pigpio.write_control_reg (HTU21D_IO_CH)

# Instantiate HTU21D handles
htu21d_inst_pipgio =    HTU21D('HTU21D_pigpio', i2c_bus_handle_pigpio)
htu21d_inst_smbus  =    HTU21D('HTU21D_smbus', i2c_bus_handle_smbus)


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
        def func():
            htu21d_inst_pipgio.soft_reset()         # Included in all tests to avoid impact of any prior test settings
            trigger_time = time.time()
            temp = htu21d_inst_pipgio.read_temperature()
            logging.info (f"Temperature measure total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            trigger_time = time.time()
            htu21d_inst_pipgio.read_RH()
            logging.info (f"RH measure total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            return temp

        dotest ("read temp & RH data pigpio api, default C", "24.858002929687494", func)

    if check_tnum('1b'):
        def func():
            htu21d_inst_smbus.soft_reset()
            trigger_time = time.time()
            temp = htu21d_inst_smbus.read_temperature(tempunits='f')
            logging.info (f"Temperature measure total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            trigger_time = time.time()
            htu21d_inst_smbus.read_RH()
            logging.info (f"RH measure total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            return temp

        dotest ("read temp & RH data smbus api, tempunits F", "76.57065869140624", func)

    if check_tnum('1c'):
        def func():
            htu21d_inst_pipgio.soft_reset()
            htu21d_inst_pipgio.trigger_temperature_nohold()
            for _ in range (10):
                temp = htu21d_inst_pipgio.fetch_temperature(tempunits='F')
                if temp != I2C_ERROR:
                    break
                time.sleep (0.01)

            htu21d_inst_pipgio.trigger_RH_nohold()
            for _ in range (10):
                RH = htu21d_inst_pipgio.fetch_RH()
                if RH != I2C_ERROR:
                    break
                time.sleep (0.006)

            return temp

        dotest ("No Hold mode read temp & RH data pigpio api, tempunits F", "76.57065869140624", func)

    if check_tnum('1d'):
        def func():
            htu21d_inst_smbus.soft_reset()
            htu21d_inst_smbus.trigger_temperature_nohold()
            for _ in range (10):
                temp = htu21d_inst_smbus.fetch_temperature(tempunits='K')
                if temp != I2C_ERROR:
                    break
                time.sleep (0.01)
            # htu21d_inst_smbus.read_RH()
            htu21d_inst_smbus.trigger_RH_nohold()
            for _ in range (10):
                RH = htu21d_inst_smbus.fetch_RH()
                if RH != I2C_ERROR:
                    break
                time.sleep (0.005)

            return temp

        dotest ("No Hold mode read temp & RH data smbus api, tempunits K", "298.21177978515624", func)



    #-------------------------------------------------------------------------
    # User register pass cases
    if check_tnum('2a'):
        def func():
            htu21d_inst_pipgio.soft_reset()
            user_reg = htu21d_inst_pipgio.read_user_reg()
            return user_reg

        dotest ("read user register default (after soft_reset) pigpio api", "2", func)

    if check_tnum('2b'):
        def func():
            htu21d_inst_pipgio.soft_reset()

            logging.info ("\nSet resolution=0b01 8/12 - user reg: 0b00000011")
            htu21d_inst_pipgio.write_user_reg(resolution=0b01)
            logging.info (f"user reg: 0b{htu21d_inst_pipgio.read_user_reg():0>8b}")

            logging.info ("\nSet resolution=0b10 10/13, heater_enable=1 - user reg: 0b10000110")
            htu21d_inst_pipgio.write_user_reg(resolution=0b10, heater_enable=1)
            logging.info (f"user reg: 0b{htu21d_inst_pipgio.read_user_reg():0>8b}")

            logging.info ("\nNo args, no changes - user reg: 0b10000110")
            htu21d_inst_pipgio.write_user_reg()
            logging.info (f"user reg: 0b{htu21d_inst_pipgio.read_user_reg():0>8b}")

            logging.info ("\nSet resolution=0b11 11/11, heater_enable=0, OTP_reload_disable=0 - user reg: 0b10000001")
            htu21d_inst_pipgio.write_user_reg(resolution=0b11, heater_enable=0, OTP_reload_disable=0)
            logging.info (f"user reg: 0b{htu21d_inst_pipgio.read_user_reg():0>8b}")

            logging.info ("\nSet heater_enable=1, OTP_reload_disable=0 - user reg: 0b10000101")
            htu21d_inst_pipgio.write_user_reg(heater_enable=1, OTP_reload_disable=0)
            logging.info (f"user reg: 0b{htu21d_inst_pipgio.read_user_reg():0>8b}")

            logging.info ("\nsoft_reset()  12/14 - user reg: 0b00000010")
            htu21d_inst_pipgio.soft_reset()
            logging.info (f"user reg: 0b{htu21d_inst_pipgio.read_user_reg():0>8b}")

        dotest ("write user register with various settings - pigpio api", "None", func)


    #-------------------------------------------------------------------------
    # Return values = 0
    if check_tnum('3'):
        def func():
            logging.info (f"soft_reset() returned:                  {htu21d_inst_pipgio.soft_reset()}")
            logging.info (f"write_user_reg() returned:              {htu21d_inst_pipgio.write_user_reg()}")
            logging.info (f"trigger_temperature_nohold() returned:  {htu21d_inst_pipgio.trigger_temperature_nohold()}")
            htu21d_inst_pipgio.soft_reset()     # I2C_ERROR without this
            logging.info (f"trigger_RH_nohold() returned:           {htu21d_inst_pipgio.trigger_RH_nohold()}")
            htu21d_inst_pipgio.soft_reset()

        dotest ("Check return values = 0, pigpio api", "None", func)


    #-------------------------------------------------------------------------
    # Heater control
    if check_tnum('4a'):
        def func():
            logging.info (f"soft_reset() returned:                  {htu21d_inst_pipgio.soft_reset()}")
            logging.info (f"read_temperature() returned:            {htu21d_inst_pipgio.read_temperature():5.3f}")

            logging.info ("Enable heater")
            htu21d_inst_pipgio.write_user_reg(heater_enable=1)

            for xx in range (10):
                time.sleep(0.5)
                logging.info (f"read_temperature() <{xx}>:              {htu21d_inst_pipgio.read_temperature('c'):5.3f}")

            logging.info ("Disable heater")
            htu21d_inst_pipgio.write_user_reg(heater_enable=0)

            for xx in range (10):
                time.sleep(0.5)
                logging.info (f"read_temperature() <{xx}>:              {htu21d_inst_pipgio.read_temperature('c'):5.3f}")

        dotest ("Demo heater on/off effect", "None", func)


    if check_tnum('4b'):
        def func():
            htu21d_inst_pipgio.soft_reset()
            htu21d_inst_pipgio.read_user_reg()
            htu21d_inst_pipgio.write_user_reg(heater_enable=1)
            htu21d_inst_pipgio.read_user_reg()
            htu21d_inst_pipgio.soft_reset()
            htu21d_inst_pipgio.read_user_reg()

        dotest ("Heater enable is actually cleared by soft_reset(), pigpio api", "None", func)


    #-------------------------------------------------------------------------
    # Trigger no-hold operation causes all other operations to fail until conversion complete
    if check_tnum('5a'):
        def func():
            logging.info (f"soft_reset() returned:                  {htu21d_inst_pipgio.soft_reset()}")
            logging.info (f"trigger_temperature_nohold() returned:  {htu21d_inst_pipgio.trigger_temperature_nohold()}")

            logging.info ("\nAll operation fails during triggered conversion")
            logging.info (f"read_user_reg() returned:               {htu21d_inst_pipgio.read_user_reg()}")
            logging.info (f"write_user_reg() returned:              {htu21d_inst_pipgio.write_user_reg()}")
            logging.info (f"trigger_temperature_nohold() returned:  {htu21d_inst_pipgio.trigger_temperature_nohold()}")
            logging.info (f"trigger_RH_nohold() returned:           {htu21d_inst_pipgio.trigger_RH_nohold()}")
            logging.info (f"read_temperature() returned:            {htu21d_inst_pipgio.read_temperature()}")

            logging.info ("\nDelay for conversion completion - new trigger accepted")
            time.sleep (0.05)
            logging.info (f"trigger_temperature_nohold() returned:  {htu21d_inst_pipgio.trigger_temperature_nohold()}")

            logging.info ("\nsoft_reset cancels conversion")
            logging.info (f"soft_reset() returned:                  {htu21d_inst_pipgio.soft_reset()}")
            logging.info (f"read_temperature() returned:            {htu21d_inst_pipgio.read_temperature()}")
            # logging.info (f"fetch_temperature() returned:           {htu21d_inst_pipgio.fetch_temperature()}")

        dotest ("Trigger no-hold operation causes all other operations to fail until conversion complete, pigpio api", "None", func)


    #-------------------------------------------------------------------------
    # Check execution times at various resolutions
    if check_tnum('6a'):
        def func():
            htu21d_inst_pipgio.soft_reset()
            trigger_time = time.time()
            htu21d_inst_pipgio.read_temperature()
            logging.info (f"Temperature measure total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            trigger_time = time.time()
            htu21d_inst_pipgio.read_RH()
            logging.info (f"RH measure total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")

        dotest ("Resolution code 0b00 - Temp 14 bits, RH 12 bits", "None", func)

    if check_tnum('6b'):
        def func():
            htu21d_inst_pipgio.soft_reset()
            htu21d_inst_pipgio.write_user_reg(resolution=0b01)
            trigger_time = time.time()
            htu21d_inst_pipgio.read_temperature()
            logging.info (f"Temperature measure total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            trigger_time = time.time()
            htu21d_inst_pipgio.read_RH()
            logging.info (f"RH measure total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")

        dotest ("Resolution code 0b01 - Temp 12 bits, RH 8 bits", "None", func)

    if check_tnum('6c'):
        def func():
            htu21d_inst_pipgio.soft_reset()
            htu21d_inst_pipgio.write_user_reg(resolution=0b10)
            trigger_time = time.time()
            htu21d_inst_pipgio.read_temperature()
            logging.info (f"Temperature measure total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            trigger_time = time.time()
            htu21d_inst_pipgio.read_RH()
            logging.info (f"RH measure total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")

        dotest ("Resolution code 0b10 - Temp 13 bits, RH 10 bits", "None", func)

    if check_tnum('6d'):
        def func():
            htu21d_inst_pipgio.soft_reset()
            htu21d_inst_pipgio.write_user_reg(resolution=0b11)
            trigger_time = time.time()
            htu21d_inst_pipgio.read_temperature()
            logging.info (f"Temperature measure total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            trigger_time = time.time()
            htu21d_inst_pipgio.read_RH()
            logging.info (f"RH measure total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")

        dotest ("Resolution code 0b11 - Temp 11 bits, RH 11 bits", "None", func)


    #-------------------------------------------------------------------------
    # Error cases
    if check_tnum('13a'):
        pca9548_resBd_handle_pigpio.write_control_reg('5')
        def func():
            logging.info (f"soft_reset() returned:                  {htu21d_inst_pipgio.soft_reset()}")
            logging.info (f"trigger_temperature_nohold() returned:  {htu21d_inst_pipgio.trigger_temperature_nohold()}")
            logging.info (f"read_user_reg() returned:               {htu21d_inst_pipgio.read_user_reg()}")
            logging.info (f"write_user_reg() returned:              {htu21d_inst_pipgio.write_user_reg()}")
            logging.info (f"trigger_temperature_nohold() returned:  {htu21d_inst_pipgio.trigger_temperature_nohold()}")
            logging.info (f"trigger_RH_nohold() returned:           {htu21d_inst_pipgio.trigger_RH_nohold()}")
            logging.info (f"read_temperature() returned:            {htu21d_inst_pipgio.read_temperature()}")
            logging.info (f"read_RH() returned:                     {htu21d_inst_pipgio.read_RH()}")
            logging.info (f"fetch_temperature() returned:           {htu21d_inst_pipgio.fetch_temperature()}")
            logging.info (f"fetch_RH() returned:                    {htu21d_inst_pipgio.fetch_RH()}")
        dotest ("Device not accessible - all APIs return I2C_ERROR", "None", func)
        pca9548_resBd_handle_pigpio.write_control_reg(HTU21D_IO_CH)

    if check_tnum('13b'):
        dotest ("write_user_reg invalid resolution", "ValueError: <HTU21D_pigpio> resolution value must be in range 0 to 3 - received <7>",
                htu21d_inst_pipgio.write_user_reg, resolution=0b111)

    if check_tnum('13c'):
        dotest ("write_user_reg invalid resolution", "ValueError: <HTU21D_pigpio> resolution value must be in range 0 to 3 - received <[3]>",
                htu21d_inst_pipgio.write_user_reg, resolution=[0b11])

    if check_tnum('13d'):
        dotest ("write_user_reg invalid heater enable", "ValueError: <HTU21D_pigpio> heater_enable value must be in range 0 or 1 - received <a>",
                htu21d_inst_pipgio.write_user_reg, heater_enable='a')

    if check_tnum('13e'):
        dotest ("write_user_reg invalid OTP reload disable", "ValueError: <HTU21D_pigpio> OTP_reload_disable value must be in range 0 or 1 - received <-1>",
                htu21d_inst_pipgio.write_user_reg, OTP_reload_disable=-1)

    if check_tnum('13f'):
        dotest ("read_temperature with invalid tempunits", "ValueError: <HTU21D_pigpio> tempunits must be 'C', 'F', or 'K' - received <q>",
                htu21d_inst_pipgio.read_temperature, tempunits='q')

    if check_tnum('13g'):
        pca9548_resBd_handle_pigpio.write_control_reg('5')
        dotest ("Instantiate unavailable sensor", "RuntimeError: <Unavailable> soft_reset during instantiation failed",
                HTU21D, 'Unavailable', i2c_bus_handle_pigpio)
        pca9548_resBd_handle_pigpio.write_control_reg(HTU21D_IO_CH)



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