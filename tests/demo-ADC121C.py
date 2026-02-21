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
# 1.0 260212 - New
#
#==========================================================

__version__ =   '1.0'
TOOLNAME =      'demo_ADC121C'

import argparse
import re
import time
# import subprocess
# from pathlib import Path
# import shutil
import pigpio

from cjnfuncs.core              import set_toolname, setuplogging, logging, set_logging_level

from cjn_PiTools.shared         import pi_i2c
from cjn_PiTools.ADC121C          import ADC121C
from cjn_PiTools.PCA9548        import PCA9548


set_toolname(TOOLNAME)


setuplogging(ConsoleLogFormat="{module:>35}.{funcName:30} - {levelname:>8}:  {message}")
set_logging_level(logging.DEBUG)


parser = argparse.ArgumentParser(description=__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-t', '--test', default='0',
                    help="Test number to run (default 0) - 0 runs all tests")
args = parser.parse_args()


# --------------------------------------------------------------------
logging.getLogger('cjn_PiTools.ADC121C').setLevel(logging.DEBUG)
logging.getLogger('cjn_PiTools.shared').setLevel(logging.DEBUG)
logging.getLogger('cjn_PiTools.PCA9548').setLevel(logging.DEBUG)

# Get i2c bus and device handles
pio =                   pigpio.pi()
pio_i2c_bus_handle =    pi_i2c(pio)

pca9548_resBd_handle =  PCA9548('PCA9548_71', 0x71, pio_i2c_bus_handle)
pca9548_irrBd_handle =  PCA9548('PCA9548_75', 0x75, pio_i2c_bus_handle)
pca9548_resBd_handle.write_control_reg ('0')
pca9548_irrBd_handle.write_control_reg ('3')

ADC121C_50_inst_pio =     ADC121C('ADC121C_50', 0x50, pio_i2c_bus_handle, Vref=4.2)
ADC121C_51_inst_pio =     ADC121C('ADC121C_51', 0x51, pio_i2c_bus_handle, Vref=4.2)

# ***** i2c bus 1 test boards configuration *****
#
# Board 1 (connected directly to RPi I2C bus 1)
#   PCA9548 address 0x71
#       Channel 0:  Connected to Board 2 PCA9548
#       Channel 1:  SHT3x at address 0x44
#       Channel 2:  SHT3x at address 0x45
#
# Board 2 (connected to Board 1 PCA9548 Channel 0)
#   PCA9548 address 0x75
#       Channel 0:  SHT3x at address 0x44

# smbus_i2c_bus_handle =  pi_i2c('smbus')
# sht3x_44_inst_smbus =   SHT3x('sht3x44', 0x44, smbus_i2c_bus_handle)
# sht3x_44_inst_smbus.clear_status_reg()
# sht3x_45_inst_smbus =   SHT3x('sht3x45', 0x45, smbus_i2c_bus_handle)
# sht3x_45_inst_smbus.clear_status_reg()

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
        logging.error (f"\n  RAISED:     {type(e).__name__}: {e}")
        # logging.exception (f"\n  RAISED:     {type(e).__name__}: {e}")
        return e


tnum_parse = re.compile(r"([\d]+)([\w]*)")
def check_tnum(tnum_in, include0='0'):
    global tnum
    tnum = tnum_in
    if args.test == include0  or  args.test == tnum_in:  return True
    try:
        if int(args.test) == int(tnum_parse.match(tnum_in).group(1)):  return True
    except:  pass
    return False

#===============================================================================================

if __name__ == '__main__':

    #-------------------------------------------------------------------------
    # Basic demo read temp/RH pass cases
    if check_tnum('1a'):
        def func():
            return ADC121C_50_inst_pio.read()

        dotest ("Read pigpio api", "Pass", func)

    # if check_tnum('1b'):
    #     def func():
    #         sht3x_44_inst_pio.soft_reset()
    #         return sht3x_44_inst_pio.single_shot(tempunits='C', repeatability='Low', reading_wait=1)

    #     dotest ("Read pigpio api", "Pass", func)

    # if check_tnum('1c'):
    #     def func():
    #         sht3x_44_inst_smbus.soft_reset()
    #         return sht3x_44_inst_smbus.single_shot()

    #     dotest ("Single Shot smbus api, default F, High, 16ms", "Pass", func)


    # #-------------------------------------------------------------------------
    # # Basic demo mode settings pass cases
    # if check_tnum('2a'):
    #     def func():
    #         logging.info (f"soft_reset()        returned {sht3x_44_inst_pio.soft_reset()}")
    #         logging.info (f"heater_enable()     returned {sht3x_44_inst_pio.heater_enable()}")
    #         logging.info (f"heater_disable()    returned {sht3x_44_inst_pio.heater_disable()}")
    #         logging.info (f"heater_enable()     returned {sht3x_44_inst_pio.heater_enable()}")
    #         logging.info (f"read_status_reg()   returned 0x{sht3x_44_inst_pio.read_status_reg(decode=True):0>4x}")
    #         logging.info (f"clear_status_reg()  returned {sht3x_44_inst_pio.clear_status_reg()}")
    #         logging.info (f"soft_reset()        returned {sht3x_44_inst_pio.soft_reset()}")
    #         logging.info (f"read_status_reg()   returned 0x{sht3x_44_inst_pio.read_status_reg(decode=True):0>4x}")

    #     dotest ("Heater control & status register - pigpio api", "None", func)


    # if check_tnum('2b'):
    #     def func():
    #         logging.info (f"soft_reset()        returned {sht3x_44_inst_smbus.soft_reset()}")
    #         logging.info (f"heater_enable()     returned {sht3x_44_inst_smbus.heater_enable()}")
    #         logging.info (f"heater_disable()    returned {sht3x_44_inst_smbus.heater_disable()}")
    #         logging.info (f"heater_enable()     returned {sht3x_44_inst_smbus.heater_enable()}")
    #         logging.info (f"read_status_reg()   returned 0x{sht3x_44_inst_smbus.read_status_reg(decode=True):0>4x}")
    #         logging.info (f"clear_status_reg()  returned {sht3x_44_inst_smbus.clear_status_reg()}")
    #         logging.info (f"soft_reset()        returned {sht3x_44_inst_smbus.soft_reset()}")
    #         logging.info (f"read_status_reg()   returned 0x{sht3x_44_inst_smbus.read_status_reg(decode=True):0>4x}")

    #     dotest ("Heater control & status register - smbus api", "None", func)


    # #-------------------------------------------------------------------------
    # # Periodic DA - fetch_data() called more frequently (0.20) than periodic_DA new data rate (various)

    # def meas4sec(mps, sht3x_handle):
    #     sht3x_44_inst_pio.soft_reset()
    #     if mps == 'ART':
    #         logging.info (f"ART() returned {sht3x_handle.ART()}")
    #     else:
    #         logging.info (f"start_periodic_DA(mps=4) returned {sht3x_handle.start_periodic_DA(mps=mps)}")
    #     for _ in range (20):
    #         logging.info ("")
    #         logging.info (f"read_status_reg() returned: 0x{sht3x_handle.read_status_reg(decode=True):0>4x}")
    #         # sht3x_instance.read_status_reg()
    #         logging.info (f"fetch_data() returned: {sht3x_handle.fetch_data()}")
    #         time.sleep(0.2)

    #     logging.info ("End of loop")
    #     logging.info (f"stop_periodic_DA() returned {sht3x_handle.stop_periodic_DA()}")
    #     logging.info (f"read_status_reg() returned: 0x{sht3x_handle.read_status_reg(decode=True):0>4x}")
    #     logging.info (f"Final1 fetch_data() returned: {sht3x_handle.fetch_data()}")
    #     logging.info (f"read_status_reg() returned: 0x{sht3x_handle.read_status_reg(decode=True):0>4x}")
    #     logging.info (f"Final2 fetch_data() returned: {sht3x_handle.fetch_data()}")


    # if check_tnum('3ap'):
    #     dotest ("Periodic DA mps=4;    fetch_data default 'F'", "~4/5 measurements pass", meas4sec, 4, sht3x_44_inst_pio)

    # if check_tnum('3as'):
    #     dotest ("Periodic DA mps=4;    fetch_data default 'F'", "~4/5 measurements pass", meas4sec, 4, sht3x_44_inst_smbus)

    # if check_tnum('3bp'):
    #     dotest ("Periodic DA mps=0.5;  fetch_data default 'F'", "~1/10 measurements pass", meas4sec, 0.5, sht3x_44_inst_pio)

    # if check_tnum('3bs'):
    #     dotest ("Periodic DA mps=0.5;  fetch_data default 'F'", "~1/10 measurements pass", meas4sec, 0.5, sht3x_44_inst_smbus)

    # if check_tnum('3c'):
    #     dotest ("Periodic DA mps=1;    fetch_data default 'F'", "~1/5 measurements pass", meas4sec, 1, sht3x_44_inst_pio)

    # if check_tnum('3d'):
    #     dotest ("Periodic DA mps=2;    fetch_data default 'F'", "~1/3 measurements pass", meas4sec, 2, sht3x_44_inst_pio)

    # if check_tnum('3e'):
    #     dotest ("Periodic DA mps=10;   fetch_data default 'F'", "All measurements pass", meas4sec, 10, sht3x_44_inst_pio)

    # if check_tnum('3f'):
    #     dotest ("ART mode (mps=4);     fetch_data default 'F'", "~4/5 measurements pass", meas4sec, 'ART', sht3x_44_inst_pio)



    # #-------------------------------------------------------------------------
    # # Read two sensors at diff addresses
    # if check_tnum('4a'):
    #     def func():
    #         logging.info (f"sht3x_44_inst_pio soft_reset()       returned {sht3x_44_inst_pio.soft_reset()}")
    #         logging.info (f"sht3x_44_inst_pio clear_status_reg() returned {sht3x_44_inst_pio.clear_status_reg()}")
    #         logging.info (f"sht3x_44_inst_pio single_shot()      returned {sht3x_44_inst_pio.single_shot()}")
    #         logging.info (f"sht3x_44_inst_pio read_status_reg()  returned 0x{sht3x_44_inst_pio.read_status_reg(decode=True):0>4x}")

    #         logging.info (f"sht3x_45_inst_pio soft_reset()       returned {sht3x_45_inst_pio.soft_reset()}")
    #         logging.info (f"sht3x_45_inst_pio clear_status_reg() returned {sht3x_45_inst_pio.clear_status_reg()}")
    #         logging.info (f"sht3x_45_inst_pio single_shot()      returned {sht3x_45_inst_pio.single_shot()}")
    #         logging.info (f"sht3x_45_inst_pio read_status_reg(decode=True)  returned 0x{sht3x_45_inst_pio.read_status_reg(decode=True):0>4x}")
    #         logging.info (f"sht3x_45_inst_pio soft_reset()       returned {sht3x_45_inst_pio.soft_reset()}")

    #     dotest ("Read two sensors at diff addresses - pigpio api", "None", func)

    # if check_tnum('4b'):
    #     def func():
    #         logging.info (f"sht3x_44_inst_smbus soft_reset()       returned {sht3x_44_inst_smbus.soft_reset()}")
    #         logging.info (f"sht3x_44_inst_smbus clear_status_reg() returned {sht3x_44_inst_smbus.clear_status_reg()}")
    #         logging.info (f"sht3x_44_inst_smbus single_shot()      returned {sht3x_44_inst_smbus.single_shot()}")
    #         logging.info (f"sht3x_44_inst_smbus read_status_reg()  returned 0x{sht3x_44_inst_smbus.read_status_reg(decode=True):0>4x}")

    #         logging.info (f"sht3x_45_inst_smbus soft_reset()       returned {sht3x_45_inst_smbus.soft_reset()}")
    #         logging.info (f"sht3x_45_inst_smbus clear_status_reg() returned {sht3x_45_inst_smbus.clear_status_reg()}")
    #         logging.info (f"sht3x_45_inst_smbus single_shot()      returned {sht3x_45_inst_smbus.single_shot()}")
    #         logging.info (f"sht3x_45_inst_smbus read_status_reg()  returned 0x{sht3x_45_inst_smbus.read_status_reg(decode=True):0>4x}")
    #         logging.info (f"sht3x_45_inst_smbus soft_reset()       returned {sht3x_45_inst_smbus.soft_reset()}")

    #     dotest ("Read two sensors at diff addresses - smbus api", "None", func)

    # if check_tnum('4c'):
    #     def func():
    #         logging.info (f"sht3x_44_inst_smbus soft_reset()       returned {sht3x_44_inst_smbus.soft_reset()}")
    #         logging.info (f"sht3x_45_inst_pio   soft_reset()       returned {sht3x_45_inst_pio.soft_reset()}")
    #         logging.info (f"sht3x_44_inst_pio   clear_status_reg() returned {sht3x_44_inst_pio.clear_status_reg()}")
    #         logging.info (f"sht3x_45_inst_smbus clear_status_reg() returned {sht3x_45_inst_smbus.clear_status_reg()}")
    #         logging.info (f"sht3x_44_inst_smbus single_shot()      returned {sht3x_44_inst_smbus.single_shot()}")
    #         logging.info (f"sht3x_45_inst_pio   single_shot()      returned {sht3x_45_inst_pio.single_shot()}")
    #         logging.info (f"sht3x_44_inst_pio   read_status_reg()  returned 0x{sht3x_44_inst_pio.read_status_reg(decode=True):0>4x}")
    #         logging.info (f"sht3x_45_inst_smbus read_status_reg()  returned 0x{sht3x_45_inst_smbus.read_status_reg(decode=True):0>4x}")

    #     dotest ("Read two sensors at diff addresses - mixed up pigpio & smbus apis", "None", func)


    # #-------------------------------------------------------------------------
    # # Error cases
    # if check_tnum('9a'):
    #     def func():
    #         sht3x_40_inst_pio =     SHT3x('sht3x40', 0x40, pio_i2c_bus_handle)

    #     dotest ("Bad sensor address", "ValueError: SHT3x device address must be 0x44 or 0x45.  Received <0x40>", func)


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


    # if check_tnum('51', include0=False):

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

    pio_i2c_bus_handle.close()
    pio.stop()

    # smbus_i2c_bus_handle.close()