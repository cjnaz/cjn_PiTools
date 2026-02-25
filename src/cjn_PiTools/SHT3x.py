#!/usr/bin/env python3
"""SHT3x library for Raspberry Pi

No Clock Stretch.
"""
#==========================================================
#
#  Chris Nelson, Copyright 2023-2026
#   
#==========================================================

# __version__ = "V1.1 241112"

import time
import sys

from crc import Calculator, Configuration
from cjnfuncs.core import set_toolname, logging, setuplogging, set_logging_level

TOOLNAME = 'SHT3x'

SHT3x_ADDRS =               [0x44, 0x45]
SOFT_RESET =                [0x30, 0xa2]
FETCH_DATA =                [0xe0, 0x00]
ART =                       [0x2b, 0x32]
READ_STATUS_REGISTER =      [0xf3, 0x2d]
CLEAR_STATUS_REGISTER =     [0x30, 0x41]
HEATER_ENABLE =             [0x30, 0x6d]
HEATER_DISABLE =            [0x30, 0x66]
BREAK =                     [0x30, 0x93]
SINGLE_SHOT_MODES = {
            "High_noCS":    [0x24, 0x00],
            "Medium_noCS":  [0x24, 0x0b],
            "Low_noCS":     [0x24, 0x16]  }
PERIODIC_DA_MODES = {
            'High_0.5':     [0x20, 0x32],
            'Medium_0.5':   [0x20, 0x24],
            'Low_0.5':      [0x20, 0x2f],
            'High_1':       [0x21, 0x30],
            'Medium_1':     [0x21, 0x26],
            'Low_1':        [0x21, 0x2d],
            'High_2':       [0x22, 0x36],
            'Medium_2':     [0x22, 0x20],
            'Low_2':        [0x22, 0x2b],
            'High_4':       [0x23, 0x34],
            'Medium_4':     [0x23, 0x22],
            'Low_4':        [0x23, 0x29],
            'High_10':      [0x27, 0x37],
            'Medium_10':    [0x27, 0x21],
            'Low_10':       [0x27, 0x2a]  }
READ_ALERT_MODES = {
            'High_Set':     [0xe1, 0x1f],
            'High_Clear':   [0xe1, 0x14],
            'Low_Clear':    [0xe1, 0x09],
            'Low_Set':      [0xe1, 0x02]  }
WRITE_ALERT_MODES = {
            'High_Set':     [0x61, 0x1d],
            'High_Clear':   [0x61, 0x16],
            'Low_Clear':    [0x61, 0x0b],
            'Low_Set':      [0x61, 0x00]  }

READING_WAIT = 0.016                        # Temp and RH readings take up to 15.5ms (high repeatability)
RESET_WAIT   = 0.003                        # Soft reset spec wait is 1.5ms

I2C_ERROR = -256
CRC_ERROR = -255


crc_calc_config = Configuration(
    width=8,
    polynomial=0x31,
    init_value=0xFF,
    final_xor_value=0x00,
    reverse_input=False,
    reverse_output=False)
crc_calc = Calculator(crc_calc_config)


sht3x_logger = logging.getLogger('cjn_PiTools.SHT3x')


class SHT3x:
    def __init__(self, device_name, device_addr, pi_i2c_bus_handle):
        """
        pi_i2c_bus_handle is from pi.i2c()
        """
        self.device_name =          device_name
        self.device_addr =          device_addr
        self.pi_i2c_bus_handle =    pi_i2c_bus_handle

        if self.device_addr not in SHT3x_ADDRS:
            raise ValueError (f"SHT3x device address must be 0x44 or 0x45.  Received <0x{device_addr:0>2x}>")

        api = 'smbus'  if self.pi_i2c_bus_handle.api == 'smbus'  else 'pigpio'
        sht3x_logger.debug (f"<{self.device_name}> New SHT3x device defined at addr <0x{self.device_addr:0>2x}> using api <{api}> on i2c bus <{self.pi_i2c_bus_handle.i2c_bus_num}>")


    def soft_reset(self, reset_wait=RESET_WAIT):
        """Issue soft reset.
        reset_wait time is blocking

        Returns
            0 for successful operation
            I2C_ERROR (-256) on I2C IO error
        """
        sht3x_logger.debug (f"<{self.device_name}> ***** soft_reset()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, SOFT_RESET)
            time.sleep (reset_wait)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


    def single_shot(self, tempunits='F', repeatability='High', reading_wait=READING_WAIT):
        """
        Blocking
        Trigger single shot reading and retrieve temperature and RH data
        Returns temperature / RH tuple, or 
            CRC_ERROR (-255) on invalid returned data from sensor
            I2C_ERROR (-256) on I2C IO error
        
        If tempunits != 'F' then temp value is returned in 'C' (no error checking).
        """
        sht3x_logger.debug (f"<{self.device_name}> ***** single_shot()")
        try:
            bytes_code = SINGLE_SHOT_MODES[repeatability + '_noCS']
        except:
            raise ValueError (f"Invalid Single Shot mode selection - received repeatability <{repeatability}>")

        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, bytes_code)
            time.sleep(reading_wait)
            return self.fetch_data(tempunits, send_fetch=False)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR, I2C_ERROR

# If no data available to be read from the device then:
# DEBUG:  SHT3x.read_temprh_data <sht3x> i2c_read_device failed - error code <-83>
# PI_I2C_READ_FAILED

    def start_periodic_DA (self, repeatability='High', mps=2):
        """
        Docstring for start_periodic_DA
        
        :param self: Description
        :param repeatability: Description
        :param mps: Description

        Status bit 0x0020 indicates in Periodic / free running measurment mode

        """
        sht3x_logger.debug (f"<{self.device_name}> ***** start_periodic_DA()")
        try:
            bytes_code = PERIODIC_DA_MODES[repeatability + '_' + str(mps)]
        except:
            raise ValueError (f"Invalid Periodic Data Acquisition mode selection - received repeatability <{repeatability}>, mps: <{mps}>")

        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, bytes_code)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


    def stop_periodic_DA (self):
        sht3x_logger.debug (f"<{self.device_name}> ***** stop_periodic_DA()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, BREAK)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


    def fetch_data(self, tempunits='F', send_fetch=True, force_CRC_fail=False):
        """
        Docstring for fetch_data
        
        :param self: Description
        :param tempunits: Description
        :param send_fetch: Description

        Status bit 0x0040 indicates data is available

        """
        sht3x_logger.debug (f"<{self.device_name}> ***** fetch_data()")
        try:
            if send_fetch:
                self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, FETCH_DATA)

            (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 6)

        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR, I2C_ERROR
        
        if count != 6:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR - error code <{count}>")
            return I2C_ERROR, I2C_ERROR

        if force_CRC_fail:
            data[2] = data[5] = 0x00

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            xx =  f"<{self.device_name}> Temp/RH raw data:\n"
            xx += f"  temp data returned bytes: 0x{data[0]:0>2x} 0x{data[1]:0>2x} 0x{data[2]:0>2x},  calc CRC: <0x{crc_calc.checksum(bytes([data[0], data[1]])):0>2x}>\n"
            xx += f"  RH   data returned bytes: 0x{data[3]:0>2x} 0x{data[4]:0>2x} 0x{data[5]:0>2x},  calc CRC: <0x{crc_calc.checksum(bytes([data[3], data[4]])):0>2x}>"
            sht3x_logger.debug (xx)

        # Process temp data
        if crc_calc.checksum(bytes([data[0], data[1]])) != data[2]:
            sht3x_logger.debug (f"<{self.device_name}> temp data CRC error")
            temp_rslt = CRC_ERROR
        else:
            rawtemp = ((data[0] <<8) | data[1]) & 0xFFFF
            temp_rslt = decode_temp (rawtemp)
            # temp_rslt = -45 + (175 * rawtemp / (2**16 -1))
            if tempunits == 'F':
                temp_rslt = temp_rslt *1.8 +32

        sht3x_logger.debug (f"<{self.device_name}> Calculated temp ({tempunits}):     {temp_rslt:>5.1f}")

        # Process RH data
        if crc_calc.checksum(bytes([data[3], data[4]])) != data[5]:
            sht3x_logger.debug (f"<{self.device_name}> RH data CRC error")
            RH_rslt = CRC_ERROR
        else:
            rawRH = ((data[3] <<8) | data[4]) & 0xFFFF
            RH_rslt = decode_rh(rawRH)
            # RH_rslt = 100 * rawRH / (2**16 -1)

        sht3x_logger.debug (f"<{self.device_name}> Calculated RH:           {RH_rslt:>5.1f}")

        return temp_rslt, RH_rslt


    def ART (self):
        sht3x_logger.debug (f"<{self.device_name}> ***** ART()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, ART)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


    def read_status_reg(self, quiet=False, force_CRC_fail=False):
        if not quiet:
            sht3x_logger.debug (f"<{self.device_name}> ***** read_status_reg()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, READ_STATUS_REGISTER)
            (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 3)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if count != 3:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR - error code <{count}>")
            return I2C_ERROR

        if force_CRC_fail:
            data[2] = 0x00

        if not quiet:
            sht3x_logger.debug (f"<{self.device_name}> status reg raw data: 0x{data[0]:0>2x} 0x{data[1]:0>2x} 0x{data[2]:0>2x},  calc CRC: <0x{crc_calc.checksum(bytes([data[0], data[1]])):0>2x}>")

        if crc_calc.checksum(bytes([data[0], data[1]])) != data[2]:
            sht3x_logger.debug (f"<{self.device_name}> status register data CRC error")
            return CRC_ERROR
        
        reg_value = ((data[0] <<8) | data[1]) & 0xFFFF
        if not quiet:
            if reg_value & 0x8000:
                sht3x_logger.info ("  At least one pending alert")
            if reg_value & 0x4000:
                sht3x_logger.info ("  Reserved (undocumented)")
            if reg_value & 0x2000:
                sht3x_logger.info ("  Heater ON")
            if reg_value & 0x1000:
                sht3x_logger.info ("  Reserved (undocumented)")
            if reg_value & 0x0800:
                sht3x_logger.info ("  RH tracking alert")
            if reg_value & 0x0400:
                sht3x_logger.info ("  T  tracking alert")
            if reg_value & 0x0200:
                sht3x_logger.info ("  Reserved (undocumented)")
            if reg_value & 0x0100:
                sht3x_logger.info ("  Reserved (undocumented)")
            if reg_value & 0x0080:
                sht3x_logger.info ("  New data available - stale data overwritten? (undocumented)")
            if reg_value & 0x0040:
                sht3x_logger.info ("  New data available? (undocumented)")
            if reg_value & 0x0020:
                sht3x_logger.info ("  PeriodicDA running? (undocumented)")
            if reg_value & 0x0010:
                sht3x_logger.info ("  System reset detected")
            if reg_value & 0x0008:
                sht3x_logger.info ("  Reserved (undocumented)")
            if reg_value & 0x0004:
                sht3x_logger.info ("  Reserved (undocumented)")
            if reg_value & 0x0002:
                sht3x_logger.info ("  Last command not processed")
            if reg_value & 0x0001:
                sht3x_logger.info ("  Checksum of last write transfer failed")

        return reg_value


    def clear_status_reg(self):
        sht3x_logger.debug (f"<{self.device_name}> ***** clear_status_reg()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, CLEAR_STATUS_REGISTER)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


# After sending a command to the sensor a minimal
# waiting time of 1ms is needed before another command
# can be received by the sensor.

    def heater_enable(self):
        """Issue header_enable
        Returns
            0 for successful operation
            I2C_ERROR (-256) on I2C IO error
        """
        sht3x_logger.debug (f"<{self.device_name}> ***** heater_enable()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, HEATER_ENABLE)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


    def heater_disable(self):
        """Issue header_disable
        Returns
            0 for successful operation
            I2C_ERROR (-256) on I2C IO error
        """
        sht3x_logger.debug (f"<{self.device_name}> ***** heater_disable()")
        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, HEATER_DISABLE)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
            sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(quiet=True):0>4x}")
        return 0


    def read_alert_reg(self, reg_select, tempunits='F', force_CRC_fail=False):
        try:
            reg_code = READ_ALERT_MODES[reg_select]
        except:
            raise ValueError (f"Invalid Alert Register selection - received <{reg_select}>")
        sht3x_logger.debug (f"<{self.device_name}> ***** read_alert_reg() <{reg_select}>")

        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, reg_code)
            (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 3)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if count != 3:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR - error code <{count}>")
            return I2C_ERROR

        if force_CRC_fail:
            data[2] = 0x00
        if crc_calc.checksum(bytes([data[0], data[1]])) != data[2]:
            sht3x_logger.debug (f"<{self.device_name}> Alert register data CRC error")
            return CRC_ERROR
        
        temp, rh = decode_alert_word (data[0] <<8 | data[1], tempunits)
        sht3x_logger.debug (f"<{self.device_name}> <{reg_select}> temp: <{temp:5.1f}{tempunits}>, rh: <{rh:5.1f}%>")

        return temp, rh


    def write_alert_reg(self, reg_select, temp, rh, tempunits='F'):
        try:
            reg_code = WRITE_ALERT_MODES[reg_select]
        except:
            raise ValueError (f"Invalid Alert Register selection - received <{reg_select}>")
        # sht3x_logger.debug (f"<{self.device_name}> ***** write_alert_reg() <{reg_select}>")

        tempC = temp
        if tempunits.lower() == 'f':
            tempC = (temp - 32.0) / 1.8

        if tempC < -40.0  or  tempC > 125.0:
            raise ValueError (f"Invalid temperature value - Expecting -40C <= temp_value <= 125C - received <{tempC}C>")

        tempbits =  int((tempC + 45.0) / (175/65535)) >> 7
        rhbits =    int(rh / 100.0 * 65535) & 0xfe00
        regbits = rhbits | tempbits
        sht3x_logger.debug (f"<{self.device_name}> ***** write_alert_reg() <{reg_select}>: <{decode_alert_word(regbits, tempunits)}>")
        # sht3x_logger.debug (f"decode_alert_word: <{decode_alert_word(regbits, tempunits)}>")
        MSB = regbits >> 8
        LSB = regbits & 0xff
        regCRC = crc_calc.checksum(bytes([MSB, LSB]))

        payload = reg_code
        payload.append(MSB)
        payload.append(LSB)
        payload.append(regCRC)

        # xx = ''
        # for item in payload:
        #     xx += (f"0x{item:0>2x} ")
        # sht3x_logger.debug (f"<{self.device_name}> <{reg_select}> payload: [ {xx}]")

        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, payload)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        # if sht3x_logger.isEnabledFor(logging.DEBUG):
        #     # time.sleep (.005)
        #     sht3x_logger.debug (f"<{self.device_name}> Status reg:  0x{self.read_status_reg(internal=True):0>4x}")
        return 0



def decode_temp (tempbits):     # returns tempC
    return -45.0 + (175 * tempbits / 65535)   #(2**16 -1))

def decode_rh (rhbits):
    return 100.0 * rhbits / 65535


def decode_alert_word (word, tempunits):
    # Upper 7 bits are the RH value MSBs
    # Lower 9 bits are the Temp value MSBs
    # Returns tuple (temp (in C or F), rh)

    tempbits = (word & 0x01ff) << 7
    temp = decode_temp(tempbits)
    if tempunits.lower() == 'f':
        temp = temp *1.8 +32.0

    rh = decode_rh (word & 0xfe00)
    return temp, rh


# def int_handler(sig, frame):
#     cleanup()
#     sys.exit(0)


#=====================================================================================
#=====================================================================================
#  c l i
#=====================================================================================
#=====================================================================================

def cli():

    global api_mode, api, pi_i2c_bus_handle, SHT3x_instance

    import time
    import argparse
    import importlib.metadata
    __version__ = importlib.metadata.version(__package__ or __name__)

    from cjn_PiTools.shared import pi_i2c

    desc = """SHT3x for Raspberry Pi
    Mode    Function
    0       single_shot measurement
    1       PeriodicDA
    2       read_status_register
    3       clear_status_register
    4       soft_reset
    5       heater_enable
    6       heater_disable
    7       read_alert_reg limits (all 4)
    8       write_alert_reg (one at a time)
"""

    DEFAULT_NAME_BASE = "SHT3x" # plus _addr_api_bus
    SHT3X_ADDRS_STR = ['0x44', '0x45']
    ALERT_REG_CHOICES = ['High_Set', 'High_Clear', 'Low_Clear', 'Low_Set']


    parser = argparse.ArgumentParser(description=desc + __version__, formatter_class=argparse.RawTextHelpFormatter)
    # parser.add_argument('Command', choices=['set', 'get'],
    #                     help=f"Operation command:  set or get")
    # parser.add_argument('Address', choices=PCA9548_ADDRS_STR,
    #                     help=f"I2C address of PCA9548 device 0x70 - 0x77 (default 0x70)")
    # parser.add_argument('Mask', nargs='?',
    #                     help=f"Set control register to this value (required for set operation)")

    parser.add_argument('-m', '--mode', type=int, default=0,
                        help=f"Interactive mode selection (default 0)")
    parser.add_argument('-t', '--tempunits', default='F',
                        help=f"Temperature entry/display units (F or C, default F)")
    parser.add_argument('--alert-reg', choices=ALERT_REG_CHOICES,
                        help=f"Alert register to write for --mode 8)")
    parser.add_argument('--Temp-value', type=float,
                        help=f"Temperature value to write for --mode 8)")
    parser.add_argument('--RH-value', type=float,
                        help=f"RH value to write for --mode 8)")

    parser.add_argument('-n', '--name', default=DEFAULT_NAME_BASE,
                        help=f"SHT3x device name (default {DEFAULT_NAME_BASE} + addr + api)")
    parser.add_argument('-a', '--addr', choices=SHT3X_ADDRS_STR, default='0x44',
                        help=f"SHT3x device address (default 0x44")
    parser.add_argument('-A', '--api', choices=['smbus', 'pigpio'], default='pigpio',
                        help=f"Either 'smbus' or 'pigpio' (default 'pigpio')")
    parser.add_argument('-b', '--bus', type=int, default=1,
                        help=f"I2C bus number (default 1)")
    parser.add_argument('-H', '--host', default='localhost',
                        help=f"pigpio api target host (default 'localhost')")
    parser.add_argument('-p', '--port', type=int, default=8888,
                        help=f"pigpio api target host port number (default 8888)")

    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Print debug-level status and activity messages")
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + __version__,
                        help="Print version number and exit")
    args = parser.parse_args()

    set_toolname(TOOLNAME)
    setuplogging(ConsoleLogFormat="{module:>12}.{funcName:30} - {levelname:>8}:  {message}")

    sht3x_logger.setLevel([logging.WARNING, logging.INFO, logging.DEBUG][args.verbose])
    logging.getLogger('cjn_PiTools.shared').setLevel([logging.WARNING, logging.INFO, logging.DEBUG][args.verbose])
    set_logging_level(logging.DEBUG)


    # Set up interface/api
    address = int (args.addr, 16)
    api_mode = args.api

    if api_mode == 'pigpio':
        import pigpio
        api =   pigpio.pi(args.host, args.port)
    else:
        api =   'smbus'

    pi_i2c_bus_handle = pi_i2c(api, i2c_bus_num=args.bus)
    name =              args.name + '_' + args.addr + '_' + api_mode
    SHT3x_instance =    SHT3x(name, address, pi_i2c_bus_handle)

    if args.mode == 0:
        temp, rh = SHT3x_instance.single_shot(tempunits=args.tempunits)
        logging.info (f"{name} - Temperature: {temp:5.1f}{args.tempunits}, RH: {rh:4.1f}%,  Status reg: 0x{SHT3x_instance.read_status_reg(quiet=True):0>4x}")

    if args.mode == 1:
        logging.info ("Running Periodic Data Acquisition mode at 2 mps.  Ctrl-C to terminate.")
        import signal
        signal.signal(signal.SIGINT,  cleanup)      # Ctrl-C  ( 2)
        SHT3x_instance.start_periodic_DA()
        while 1:
            temp, rh = SHT3x_instance.fetch_data(tempunits=args.tempunits)
            time.sleep(0.51)
            logging.info (f"{name} - Temperature: {temp:5.1f}{args.tempunits}, RH: {rh:4.1f}%,  Status reg: 0x{SHT3x_instance.read_status_reg(quiet=True):0>4x}")

    if args.mode == 2:
        # status_reg = SHT3x_instance.read_status_reg()
        logging.info (f"read_status_reg()       Status reg:  0x{SHT3x_instance.read_status_reg():0>4x}")
        

    if args.mode == 3:
        SHT3x_instance.clear_status_reg()
        logging.info (f"clear_status_reg()      Status reg:  0x{SHT3x_instance.read_status_reg(quiet=True):0>4x}")

    if args.mode == 4:
        SHT3x_instance.soft_reset()
        logging.info (f"soft_reset()            Status reg:  0x{SHT3x_instance.read_status_reg(quiet=True):0>4x}")

    if args.mode == 5:
        SHT3x_instance.heater_enable()
        logging.info (f"heater_enable()         Status reg:  0x{SHT3x_instance.read_status_reg(quiet=True):0>4x}")

    if args.mode == 6:
        SHT3x_instance.heater_disable()
        logging.info (f"heater_disable()        Status reg:  0x{SHT3x_instance.read_status_reg(quiet=True):0>4x}")

    if args.mode == 7:
        logging.info (f"read_alert_reg()  High_Set    {SHT3x_instance.read_alert_reg('High_Set',   tempunits=args.tempunits)}")
        logging.info (f"read_alert_reg()  High_Clear  {SHT3x_instance.read_alert_reg('High_Clear', tempunits=args.tempunits)}")
        logging.info (f"read_alert_reg()  Low_Clear   {SHT3x_instance.read_alert_reg('Low_Clear',  tempunits=args.tempunits)}")
        logging.info (f"read_alert_reg()  Low_Set     {SHT3x_instance.read_alert_reg('Low_Set',    tempunits=args.tempunits)}")

    if args.mode == 8:
        if  args.Temp_value is None  or  args.RH_value is None:
            logging.error ("Both --Temp-value and --RH-value are required - Aborting")
            cleanup()
        SHT3x_instance.write_alert_reg(args.alert_reg, args.Temp_value, args.RH_value, args.tempunits)
        logging.info (f"read_alert_reg()  {args.alert_reg}    {SHT3x_instance.read_alert_reg(args.alert_reg,   tempunits=args.tempunits)}")


def cleanup(sig, frame):
    SHT3x_instance.stop_periodic_DA()
    pi_i2c_bus_handle.close()
    if api_mode == 'pigpio':
        api.stop()
    sys.exit()

    cleanup(1, 2)

    # Cleanup


if __name__ == '__main__':
    sys.exit(cli())
