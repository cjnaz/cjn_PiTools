#!/usr/bin/env python3
"""Demo/test for SHT3x

Produce / compare to golden results:
    ./SHT3x-demo.py > testrun.log

    Expected differences:
        The status register may show undocumented status bit(s) set (e.g., 0x0040)
        Measured temp/rh values
        cjn_PiTools.SHT3x handle addresses
        For the PeriodicDA tests the alignment of passing/failing fetch_data results will shift
"""

#==========================================================
#
#  Chris Nelson, Copyright 2026
#
# 1.0 260401 - New
#
#==========================================================

__version__ =   '1.0'
TOOLNAME =      'SHT3x_demo'

import argparse
import re
import time
import pigpio

from cjnfuncs.core              import set_toolname, setuplogging, logging, set_logging_level
from cjn_PiTools.shared         import pi_i2c
from cjn_PiTools.SHT3x          import SHT3x
from cjn_PiTools.PCA9548        import PCA9548


PCA9548_RESBD =         {'addr': 0x71, 'name': 'PCA9548_Res'}
PCA9548_IRRBD =         {'addr': 0x75, 'name': 'PCA9548_Irr'}
RESET_GPIO =            25
RELAY_3V3_GPIO =        21
RELAY_5V0_GPIO =        26


set_toolname(TOOLNAME)
setuplogging(ConsoleLogFormat="{module:>35}.{funcName:30} - {levelname:>8}:  {message}")
set_logging_level(logging.DEBUG)
logging.getLogger('cjn_PiTools.shared').setLevel(logging.DEBUG)
logging.getLogger('cjn_PiTools.PCA9548').setLevel(logging.DEBUG)
logging.getLogger('cjn_PiTools.SHT3x').setLevel(logging.DEBUG)


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
pca9548_resBd_handle_pigpio.write_control_reg (0b110)      # Enable Channels 1 and 2 (SHT3x devices available at 0x44 and 0x45)

# Instantiate and configure SHT3x sensors
sht3x_44_inst_smbus =   SHT3x('sht3x44', 0x44, i2c_bus_handle_smbus, do_reset=False)
sht3x_44_inst_pigpio =  SHT3x('sht3x44', 0x44, i2c_bus_handle_pigpio, do_reset=False)
sht3x_45_inst_smbus =   SHT3x('sht3x45', 0x45, i2c_bus_handle_smbus, do_reset=False)
sht3x_45_inst_pigpio =  SHT3x('sht3x45', 0x45, i2c_bus_handle_pigpio, do_reset=False)

# sht3x_44_inst_smbus.clear_status_reg()
# sht3x_45_inst_smbus.clear_status_reg()


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
cli_args = parser.parse_args()


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
    # Basic demo single shot temp/RH pass cases
    if check_tnum('1a'):
        def func():
            sht3x_44_inst_pigpio.soft_reset()
            return sht3x_44_inst_pigpio.single_shot()

        dotest ("Single Shot pigpio api, default C, High, CS", "Temp & RH results", func)


    if check_tnum('1b'):
        def func():
            sht3x_44_inst_pigpio.soft_reset()
            return sht3x_44_inst_pigpio.single_shot(tempunits='F', repeatability='Low', reading_wait=0.2)

        dotest ("Single Shot pigpio api - F, Low, 0.2sec", "Temp & RH results", func)


    if check_tnum('1c'):
        def func():
            sht3x_44_inst_smbus.soft_reset()
            return sht3x_44_inst_smbus.single_shot(tempunits='k', repeatability='Low', reading_wait=0.008)

        dotest ("Single Shot smbus api, K, Low, 8ms", "Temp & RH results", func)


    if check_tnum('1d'):
        def func():
            sht3x_44_inst_pigpio.soft_reset()
            trigger_time = time.time()
            values = sht3x_44_inst_pigpio.single_shot()
            logging.info (f"Single shot High_CS total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            return values

        dotest ("single_shot & fetch_data execution time pigpio api, default C, High, CS", "Temp & RH results", func)


    if check_tnum('1e'):
        def func():
            sht3x_44_inst_smbus.soft_reset()
            trigger_time = time.time()
            values = sht3x_44_inst_smbus.single_shot()
            logging.info (f"Single shot High_CS total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            return values

        dotest ("single_shot & fetch_data execution time smbus api, default C, High, CS", "Temp & RH results", func)


    if check_tnum('1f'):
        def func():
            sht3x_44_inst_pigpio.soft_reset()
            trigger_time = time.time()
            values = sht3x_44_inst_pigpio.single_shot(repeatability='Medium')
            logging.info (f"Single shot Medium_CS total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            return values

        dotest ("single_shot & fetch_data execution time pigpio api, default C, Medium, CS", "Temp & RH results", func)


    if check_tnum('1g'):
        def func():
            sht3x_44_inst_smbus.soft_reset()
            trigger_time = time.time()
            values = sht3x_44_inst_smbus.single_shot(repeatability='Medium')
            logging.info (f"Single shot Medium_CS total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            return values

        dotest ("single_shot & fetch_data execution time smbus api, default C, Medium, CS", "Temp & RH results", func)


    if check_tnum('1h'):
        def func():
            sht3x_44_inst_pigpio.soft_reset()
            trigger_time = time.time()
            values = sht3x_44_inst_pigpio.single_shot(repeatability='Low')
            logging.info (f"Single shot Low_CS total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            return values

        dotest ("single_shot & fetch_data execution time pigpio api, default C, Low, CS", "Temp & RH results", func)


    if check_tnum('1i'):
        def func():
            sht3x_44_inst_smbus.soft_reset()
            trigger_time = time.time()
            values = sht3x_44_inst_smbus.single_shot(repeatability='Low')
            logging.info (f"Single shot Low_CS total execution time: {(time.time() - trigger_time)*1000:5.3f} ms")
            return values

        dotest ("single_shot & fetch_data execution time smbus api, default C, Low, CS", "Temp & RH results", func)


    if check_tnum('1j'):
        def func():
            sht3x_44_inst_smbus.soft_reset()
            logging.info (f"Trigger only (no fetch_data) Single shot High_CS returned: {sht3x_44_inst_smbus.single_shot(reading_wait=0, fetch_data=False)}")
            logging.info ("Wait a bit")
            time.sleep (0.2)
            logging.info (f"fetch_data() returned:  {sht3x_44_inst_smbus.fetch_data()}")

        dotest ("Separate single_shot (High_noCS) and fetch_data(), smbus api", "None", func)


    #-------------------------------------------------------------------------
    # Basic demo mode settings pass cases
    if check_tnum('2a'):
        def func():
            logging.info (f"soft_reset()        returned {sht3x_44_inst_pigpio.soft_reset()}")
            logging.info (f"heater_enable()     returned {sht3x_44_inst_pigpio.heater_enable()}")
            logging.info (f"heater_disable()    returned {sht3x_44_inst_pigpio.heater_disable()}")
            logging.info (f"heater_enable()     returned {sht3x_44_inst_pigpio.heater_enable()}")
            logging.info (f"read_status_reg()   returned 0x{sht3x_44_inst_pigpio.read_status_reg(quiet=False):0>4x}")
            logging.info (f"clear_status_reg()  returned {sht3x_44_inst_pigpio.clear_status_reg()}")
            logging.info (f"soft_reset()        returned {sht3x_44_inst_pigpio.soft_reset()}")
            logging.info (f"read_status_reg()   returned 0x{sht3x_44_inst_pigpio.read_status_reg(quiet=False):0>4x}")

        dotest ("Heater control & status register - pigpio api", "None", func)


    if check_tnum('2b'):
        def func():
            logging.info (f"soft_reset()        returned {sht3x_44_inst_smbus.soft_reset()}")
            logging.info (f"heater_enable()     returned {sht3x_44_inst_smbus.heater_enable()}")
            logging.info (f"heater_disable()    returned {sht3x_44_inst_smbus.heater_disable()}")
            logging.info (f"heater_enable()     returned {sht3x_44_inst_smbus.heater_enable()}")
            logging.info (f"read_status_reg()   returned 0x{sht3x_44_inst_smbus.read_status_reg(quiet=False):0>4x}")
            logging.info (f"clear_status_reg()  returned {sht3x_44_inst_smbus.clear_status_reg()}")
            logging.info (f"soft_reset()        returned {sht3x_44_inst_smbus.soft_reset()}")
            logging.info (f"read_status_reg()   returned 0x{sht3x_44_inst_smbus.read_status_reg(quiet=False):0>4x}")

        dotest ("Heater control & status register - smbus api", "None", func)


    #-------------------------------------------------------------------------
    # Periodic DA - fetch_data() called more frequently (0.20) than periodic_DA new data rate (various)

    def measXcount(mps, meas_count, sht3x_handle):
        sht3x_handle.soft_reset()
        if mps == 'ART':
            logging.info (f"start_ART() returned {sht3x_handle.start_ART()}")
        else:
            logging.info (f"start_periodic_DA(mps={mps}) returned {sht3x_handle.start_periodic_DA(mps=mps)}")
        for _ in range (meas_count):
            logging.info ("")
            logging.info (f"read_status_reg() returned: 0x{sht3x_handle.read_status_reg(quiet=False):0>4x}")
            logging.info (f"fetch_data() returned: {sht3x_handle.fetch_data()}")
            time.sleep(0.2)

        logging.info ("End of loop")
        logging.info (f"stop_periodic_DA() returned {sht3x_handle.stop_periodic_DA()}")
        logging.info (f"read_status_reg() returned: 0x{sht3x_handle.read_status_reg(quiet=False):0>4x}")
        logging.info (f"Final1 fetch_data() returned: {sht3x_handle.fetch_data()}")
        logging.info (f"read_status_reg() returned: 0x{sht3x_handle.read_status_reg(quiet=False):0>4x}")
        logging.info (f"Final2 fetch_data() returned: {sht3x_handle.fetch_data()}")


    if check_tnum('3ap'):
        dotest ("Periodic DA mps=4;    fetch_data default 'C'", "~4/5 measurements pass", measXcount, 4, 7, sht3x_44_inst_pigpio)

    if check_tnum('3as'):
        dotest ("Periodic DA mps=4;    fetch_data default 'C'", "~4/5 measurements pass", measXcount, 4, 7, sht3x_44_inst_smbus)

    if check_tnum('3bp'):
        dotest ("Periodic DA mps=0.5;  fetch_data default 'C'", "~1/10 measurements pass", measXcount, 0.5, 12, sht3x_44_inst_pigpio)

    if check_tnum('3bs'):
        dotest ("Periodic DA mps=0.5;  fetch_data default 'C'", "~1/10 measurements pass", measXcount, 0.5, 12, sht3x_44_inst_smbus)

    if check_tnum('3c'):
        dotest ("Periodic DA mps=1;    fetch_data default 'C'", "~1/5 measurements pass", measXcount, 1, 7, sht3x_44_inst_pigpio)

    if check_tnum('3d'):
        dotest ("Periodic DA mps=2;    fetch_data default 'C'", "~1/3 measurements pass", measXcount, 2, 6, sht3x_44_inst_pigpio)

    if check_tnum('3e'):
        dotest ("Periodic DA mps=10;   fetch_data default 'C'", "All measurements pass", measXcount, 10, 12, sht3x_44_inst_pigpio)

    if check_tnum('3f'):
        dotest ("ART mode (mps=4);     fetch_data default 'C'", "~4/5 measurements pass", measXcount, 'ART', 7, sht3x_44_inst_pigpio)



    #-------------------------------------------------------------------------
    # Read two sensors at diff addresses
    if check_tnum('4a'):
        def func():
            logging.info (f"sht3x_44_inst_pigpio soft_reset()       returned {sht3x_44_inst_pigpio.soft_reset()}")
            logging.info (f"sht3x_44_inst_pigpio clear_status_reg() returned {sht3x_44_inst_pigpio.clear_status_reg()}")
            logging.info (f"sht3x_44_inst_pigpio single_shot()      returned {sht3x_44_inst_pigpio.single_shot()}")
            logging.info (f"sht3x_44_inst_pigpio read_status_reg()  returned 0x{sht3x_44_inst_pigpio.read_status_reg(quiet=False):0>4x}")

            logging.info (f"sht3x_45_inst_pigpio soft_reset()       returned {sht3x_45_inst_pigpio.soft_reset()}")
            logging.info (f"sht3x_45_inst_pigpio clear_status_reg() returned {sht3x_45_inst_pigpio.clear_status_reg()}")
            logging.info (f"sht3x_45_inst_pigpio single_shot()      returned {sht3x_45_inst_pigpio.single_shot()}")
            logging.info (f"sht3x_45_inst_pigpio read_status_reg()  returned 0x{sht3x_45_inst_pigpio.read_status_reg(quiet=False):0>4x}")
            logging.info (f"sht3x_45_inst_pigpio soft_reset()       returned {sht3x_45_inst_pigpio.soft_reset()}")

        dotest ("Read two sensors at diff addresses - pigpio api", "None", func)

    if check_tnum('4b'):
        def func():
            logging.info (f"sht3x_44_inst_smbus soft_reset()       returned {sht3x_44_inst_smbus.soft_reset()}")
            logging.info (f"sht3x_44_inst_smbus clear_status_reg() returned {sht3x_44_inst_smbus.clear_status_reg()}")
            logging.info (f"sht3x_44_inst_smbus single_shot()      returned {sht3x_44_inst_smbus.single_shot()}")
            logging.info (f"sht3x_44_inst_smbus read_status_reg()  returned 0x{sht3x_44_inst_smbus.read_status_reg(quiet=False):0>4x}")

            logging.info (f"sht3x_45_inst_smbus soft_reset()       returned {sht3x_45_inst_smbus.soft_reset()}")
            logging.info (f"sht3x_45_inst_smbus clear_status_reg() returned {sht3x_45_inst_smbus.clear_status_reg()}")
            logging.info (f"sht3x_45_inst_smbus single_shot()      returned {sht3x_45_inst_smbus.single_shot()}")
            logging.info (f"sht3x_45_inst_smbus read_status_reg()  returned 0x{sht3x_45_inst_smbus.read_status_reg(quiet=False):0>4x}")
            logging.info (f"sht3x_45_inst_smbus soft_reset()       returned {sht3x_45_inst_smbus.soft_reset()}")

        dotest ("Read two sensors at diff addresses - smbus api", "None", func)

    if check_tnum('4c'):
        def func():
            logging.info (f"sht3x_44_inst_smbus soft_reset()       returned {       sht3x_44_inst_smbus.soft_reset()}")
            logging.info (f"sht3x_45_inst_pigpio   soft_reset()       returned {    sht3x_45_inst_pigpio.soft_reset()}")
            logging.info (f"sht3x_44_inst_pigpio   clear_status_reg() returned {    sht3x_44_inst_pigpio.clear_status_reg()}")
            logging.info (f"sht3x_45_inst_smbus clear_status_reg() returned {       sht3x_45_inst_smbus.clear_status_reg()}")
            logging.info (f"sht3x_44_inst_smbus single_shot()      returned {       sht3x_44_inst_smbus.single_shot()}")
            logging.info (f"sht3x_45_inst_pigpio   single_shot()      returned {    sht3x_45_inst_pigpio.single_shot()}")
            logging.info (f"sht3x_44_inst_pigpio   read_status_reg()  returned 0x{  sht3x_44_inst_pigpio.read_status_reg(quiet=False):0>4x}")
            logging.info (f"sht3x_45_inst_smbus read_status_reg()  returned 0x{     sht3x_45_inst_smbus.read_status_reg(quiet=False):0>4x}")

        dotest ("Read two sensors at diff addresses - mixed up pigpio & smbus apis", "None", func)


    #-------------------------------------------------------------------------
    # Alert registers
    if check_tnum('5a'):
        def func():
            logging.info ("\n\nWrite alert registers")
            logging.info (f"clear_status_reg()                  returned {sht3x_44_inst_pigpio.clear_status_reg()}")
            logging.info (f"write_alert_reg('High_Set'...)      returned {sht3x_44_inst_pigpio.write_alert_reg('High_Set',  100, 80)}")
            logging.info (f"write_alert_reg('High_Clear'...)    returned {sht3x_44_inst_pigpio.write_alert_reg('High_Clear', 90, 70)}")
            logging.info (f"write_alert_reg('Low_Clear'...)     returned {sht3x_44_inst_pigpio.write_alert_reg('Low_Clear',  50, 65)}")
            logging.info (f"write_alert_reg('Low_Set'...)       returned {sht3x_44_inst_pigpio.write_alert_reg('Low_Set',    40, 60)}")

            logging.info ("\n\nRead alert registers")
            logging.info (f"read_alert_reg('High_Set'...)       returned {sht3x_44_inst_pigpio.read_alert_reg('High_Set')}")
            logging.info (f"read_alert_reg('High_Clear'...)     returned {sht3x_44_inst_pigpio.read_alert_reg('High_Clear')}")
            logging.info (f"read_alert_reg('Low_Clear'...)      returned {sht3x_44_inst_pigpio.read_alert_reg('Low_Clear')}")
            logging.info (f"read_alert_reg('Low_Set'...)        returned {sht3x_44_inst_pigpio.read_alert_reg('Low_Set')}")
            logging.info (f"read_status_reg()                   returned {sht3x_44_inst_pigpio.read_status_reg()}")

            logging.info ("\n\nStart DA to cause low alerts")
            logging.info (f"start_periodic_DA()                 returned {sht3x_44_inst_pigpio.start_periodic_DA(mps=10)}")
            time.sleep (0.2)
            logging.info (f"read_status_reg()                   returned {sht3x_44_inst_pigpio.read_status_reg()}")
            logging.info (f"stop_periodic_DA()                  returned {sht3x_44_inst_pigpio.stop_periodic_DA()}")
            logging.info (f"read_status_reg()                   returned {sht3x_44_inst_pigpio.read_status_reg()}")

            logging.info ("\n\nDo clear status reg")
            logging.info (f"clear_status_reg()                  returned {sht3x_44_inst_pigpio.clear_status_reg()}")
            logging.info (f"read_status_reg()                   returned {sht3x_44_inst_pigpio.read_status_reg()}")

            logging.info ("\n\nDo fetch data")
            logging.info (f"fetch_data()                  returned {sht3x_44_inst_pigpio.fetch_data()}")
            logging.info (f"read_status_reg()                   returned {sht3x_44_inst_pigpio.read_status_reg()}")

            logging.info ("\n\nSoft reset then Read alert registers")
            logging.info (f"soft_reset()                        returned {sht3x_44_inst_pigpio.soft_reset()}")
            logging.info (f"read_alert_reg('High_Set'...)       returned {sht3x_44_inst_pigpio.read_alert_reg('High_Set')}")
            logging.info (f"read_alert_reg('High_Clear'...)     returned {sht3x_44_inst_pigpio.read_alert_reg('High_Clear')}")
            logging.info (f"read_alert_reg('Low_Clear'...)      returned {sht3x_44_inst_pigpio.read_alert_reg('Low_Clear')}")
            logging.info (f"read_alert_reg('Low_Set'...)        returned {sht3x_44_inst_pigpio.read_alert_reg('Low_Set')}")
            logging.info (f"read_status_reg()                   returned {sht3x_44_inst_pigpio.read_status_reg()}")


        dotest ("Set alert registers, cause low temp & rh alerts", "None", func)


    #-------------------------------------------------------------------------
    # Error cases
    if check_tnum('13a'):
        def func():
            sht3x_40_inst_pio =     SHT3x('sht3x40', 0x40, sht3x_44_inst_pigpio)

        dotest ("Bad sensor address", "ValueError: SHT3x device address must be 0x44 or 0x45.  Received <0x40>", func)


    if check_tnum('13b'):
        def func():
            pca9548_resBd_handle_pigpio.write_control_reg ('7')         # No SHT3x connected at address 0x44
            return sht3x_44_inst_pigpio.soft_reset()

        dotest ("Attempt soft_reset() with inaccessible device - pigpio api", "-256 (I2C_ERROR)", func)

        pca9548_resBd_handle_pigpio.write_control_reg (0b110)           # Reenable Channels 1 and 2 (SHT3x devices available at 0x44 and 0x45)


    if check_tnum('13c'):
        def func():
            pca9548_resBd_handle_pigpio.write_control_reg ('7')
            return sht3x_44_inst_pigpio.fetch_data(send_fetch=False)

        dotest ("Attempt fetch_data() with inaccessible device - pigpio api", "(-256, -256) (I2C_ERROR)", func)

        pca9548_resBd_handle_pigpio.write_control_reg (0b110)


    if check_tnum('13d'):
        def func():
            pca9548_resBd_handle_pigpio.write_control_reg ('7')
            return sht3x_44_inst_smbus.soft_reset()

        dotest ("Attempt soft_reset() with inaccessible device - smbus api", "-256 (I2C_ERROR)", func)

        pca9548_resBd_handle_pigpio.write_control_reg (0b110)


    if check_tnum('13e'):
        def func():
            pca9548_resBd_handle_pigpio.write_control_reg ('7')
            return sht3x_44_inst_smbus.fetch_data(send_fetch=False)

        dotest ("Attempt fetch_data() with inaccessible device - smbus api", "(-256, -256) (I2C_ERROR)", func)

        pca9548_resBd_handle_pigpio.write_control_reg (0b110)


    if check_tnum('13f'):
        def func():
            return sht3x_44_inst_smbus.single_shot(repeatability="NOTA")

        dotest ("Attempt fetch_data() with invalid repeatability - smbus api", "ValueError: Invalid Single Shot mode selection - received repeatability <NOTA>", func)


    if check_tnum('13g'):
        def func():
            return sht3x_44_inst_pigpio.start_periodic_DA(repeatability="NOTA", mps='16')

        dotest ("Attempt start_periodic_DA() with invalid repeatability & mps - pigpio api", "ValueError: Invalid Periodic Data Acquisition mode selection - received repeatability <NOTA>, mps: <16>", func)


    if check_tnum('13h'):
        def func():
            sht3x_44_inst_pigpio.start_periodic_DA()
            temp, rh = sht3x_44_inst_pigpio.fetch_data(force_CRC_fail=True)
            sht3x_44_inst_pigpio.stop_periodic_DA()
            return temp, rh

        dotest ("fetch_data() CRC fail - pigpio api", "(-255, -255)", func)


    if check_tnum('13i'):
        def func():
            return sht3x_44_inst_pigpio.read_status_reg(force_CRC_fail=True)

        dotest ("read_status_reg() CRC fail - pigpio api", "-255", func)


    if check_tnum('13j'):
        def func():
            sht3x_44_inst_smbus.soft_reset()
            return sht3x_44_inst_smbus.single_shot(reading_wait=0.0001)

        dotest ("Single Shot smbus api, C, High, 0.1ms - measurement busy", "(-256, -256) (I2C_ERROR)", func)
        time.sleep (0.02)   # Let the measurement complete


    if check_tnum('13k'):
        def func():
            sht3x_44_inst_pigpio.soft_reset()
            return sht3x_44_inst_pigpio.single_shot(reading_wait=0.0001)

        dotest ("Single Shot pigpio api, C, High, 0.1ms - measurement busy", "(-256, -256) (I2C_ERROR)", func)
        time.sleep (0.02)   # Let the measurement complete


    if check_tnum('13l'):
        def func():
            sht3x_44_inst_pigpio.soft_reset()
            return sht3x_44_inst_pigpio.single_shot(reading_wait=-2)

        dotest ("Single Shot invalid reading_wait", "ValueError: <sht3x44> Invalid reading_wait value - expecting -1 or >= 0.0 - received <-2>", func)


    if check_tnum('13m'):
        def func():
            sht3x_44_inst_pigpio.soft_reset()
            return sht3x_44_inst_pigpio.single_shot(reading_wait=['hello'])

        dotest ("Single Shot invalid reading_wait", "ValueError: <sht3x44> Invalid reading_wait value - expecting -1 or >= 0.0 - received <['hello']>", func)


    # NOTE:  A CRC error on the write data to the alert registers causes a stuck I2C bus error, requiring 
    # a power cycle to recover.
    if check_tnum('13n', include0=False):
        def func():
            sht3x_44_inst_pigpio.soft_reset()
            value = sht3x_44_inst_pigpio.write_alert_reg('High_Clear', 10, 20, force_CRC_fail=True)
            sht3x_44_inst_pigpio.read_status_reg()
            return value

        dotest ("write_alert_reg with bad CRC", "-256 (I2C_ERROR)", func)


    #-------------------------------------------------------------------------
    # Development/testing/debug
    if check_tnum('50', include0=False):

        logging.info ("Test 50 setup")
        remote_pio = pigpio.pi('testhost.cjn.lan')
        pio_i2c_bus_handle =     pi_i2c(remote_pio)
        sht3x_44_inst_pigpio =     SHT3x('sht3x44', 0x44, pio_i2c_bus_handle)
        sht3x_45_inst_pigpio =     SHT3x('sht3x45', 0x45, pio_i2c_bus_handle)


        def func():
            sht3x_44_inst_pigpio.soft_reset()
            return sht3x_44_inst_pigpio.single_shot()

        dotest ("Single Shot pigpio api remote (run from testhost2), default C, High, 16ms", "Pass", func)

        pio_i2c_bus_handle.close()
        remote_pio.stop()

        exit()


    if check_tnum('51', include0=False):

        def func():
            pca9548_resBd_handle_pigpio =   PCA9548(PCA9548_RESBD['name'], PCA9548_RESBD['addr'], i2c_bus_handle_pigpio)
            pca9548_resBd_handle_pigpio.write_control_reg ('0')
            pca9548_irrBd_handle_pigpio =   PCA9548(PCA9548_IRRBD['name'], PCA9548_IRRBD['addr'], i2c_bus_handle_pigpio)
            pca9548_irrBd_handle_pigpio.write_control_reg ('0')

            irr_sht3x = SHT3x('IrrBd_SHT3x_I2C1', 0x44, i2c_bus_handle_pigpio)
            print (irr_sht3x.single_shot())

            # sht3x_44_inst_pigpio.clear_status_reg()
            # sht3x_44_inst_pigpio.soft_reset()
            # sht3x_44_inst_pigpio.read_status_reg()
            # # sht3x_44_inst_pigpio.write_alert_reg('High_Set', 60, 80, tempunits='C')
            # sht3x_44_inst_pigpio.read_alert_reg('High_Set',   tempunits='C')
            # # sht3x_44_inst_pigpio.read_alert_reg('High_Set')
            # sht3x_44_inst_pigpio.read_alert_reg('High_Clear', tempunits='C')
            # sht3x_44_inst_pigpio.read_alert_reg('Low_Clear',  tempunits='C')
            # sht3x_44_inst_pigpio.read_alert_reg('Low_Set',    tempunits='C')

            # sht3x_44_inst_pigpio.write_alert_reg('High_Set',  40, 50, tempunits='C')
            # sht3x_44_inst_pigpio.read_alert_reg('High_Set',   tempunits='C')
            # sht3x_44_inst_pigpio.soft_reset()
            # sht3x_44_inst_pigpio.read_alert_reg('High_Set',   tempunits='C')
            # # sht3x_44_inst_pigpio.read_status_reg()


        dotest ("SHT3x on Irr board I2C1 (PCA9548 ch0)", "Pass", func)


    if check_tnum('52', include0=False):

        def func():
            sht3x_44_inst_pigpio.soft_reset()
            # sht3x_44_inst_pigpio.write_alert_reg('High_Set', 60, 80, tempunits='C')
            sht3x_44_inst_pigpio.read_alert_reg('High_Set',   tempunits='C')
            sht3x_44_inst_pigpio.read_alert_reg('High_Set')
            sht3x_44_inst_pigpio.read_alert_reg('High_Clear', tempunits='C')
            sht3x_44_inst_pigpio.read_alert_reg('Low_Clear',  tempunits='C')
            sht3x_44_inst_pigpio.read_alert_reg('Low_Set',    tempunits='C')

            sht3x_44_inst_pigpio.write_alert_reg('High_Set',  40, 50, tempunits='C')
            sht3x_44_inst_pigpio.read_alert_reg('High_Set',   tempunits='C')
            sht3x_44_inst_pigpio.read_status_reg()


        dotest ("read_alert_reg", "Pass", func)


    logging.warning (f"\n\n---- Cleanup --------------------------------------------------------")

    i2c_bus_handle_pigpio.close()
    pio.stop()

    i2c_bus_handle_smbus.close()