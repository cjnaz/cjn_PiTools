#!/usr/bin/env python3
"""SHT3x library for Raspberry Pi

No Clock Stretch.
Setting and reading of Temp/RH alert levels
"""
#==========================================================
#
#  Chris Nelson, Copyright 2023-2024
#
# V1.1 241112  Read error bug fix (crashed when read_temprh_data didn't get 6 bytes back)
# V1.0 230510  New
#
# Changes pending TODO
#   write_reg, read_reg methods with retrys, used by all other methods
#   
#==========================================================

__version__ = "V1.1 241112"

from crc import Calculator, Configuration   # Dependency - pip install crc
import time
# from time import sleep
import logging

SHT3x_ADDRS =               [0x44, 0x45]
SOFT_RESET =                [0x30, 0xa2]
DO_MEASUREMENTS =           [0x24, 0x00]    # Single shot, High repeatability, No clock stretching
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
sht3x_logger.setLevel(logging.WARNING)             # Set default logging level for this module


class SHT3x:
    # def __init__(self, device_name, pio_handle, i2c_handle):
    def __init__(self, device_name, device_addr, pi_i2c_handle):
        """
        pio_handle is from pigpio.pi()
        i2c_handle is from pio.i2c_open()
        """
        self.device_name = device_name
        self.device_addr = device_addr
        if self.device_addr not in SHT3x_ADDRS:
            raise ValueError (f"SHT3x device address must be 0x44 or 0x45.  Receeived <0x{device_addr:0>x}>")
        self.pi_i2c_handle  = pi_i2c_handle


    def soft_reset(self, reset_wait=RESET_WAIT):
        """Issue soft reset.
        reset_wait time is blocking

        Returns
            0 for successful operation
            I2C_ERROR (-256) on I2C IO error
        """
        try:        # TODO add retry loop logic
            self.pi_i2c_handle.i2c_write_device(self.device_addr, SOFT_RESET)
            time.sleep (reset_wait)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
        # if sht3x_logger.level == logging.DEBUG:      # Avoid unnecessary read_status_reg, unless debug logging
            sht3x_logger.debug (f"<{self.device_name}> Success - Status reg:  0x{self.read_status_reg(internal=True):0>4x}")
        return 0


    def heater_enable(self):
        """Issue header_enable
        Returns
            0 for successful operation
            I2C_ERROR (-256) on I2C IO error
        """
        try:        # TODO add retry loop logic
            self.pi_i2c_handle.i2c_write_device(self.device_addr, HEATER_ENABLE)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
        # if sht3x_logger.level == logging.DEBUG:      # Avoid unnecessary read_status_reg, unless debug logging
            sht3x_logger.debug (f"<{self.device_name}> Success - Status reg:  0x{self.read_status_reg(internal=True):0>4x}")
        return 0


    def heater_disable(self):
        """Issue header_disable
        Returns
            0 for successful operation
            I2C_ERROR (-256) on I2C IO error
        """
        try:        # TODO add retry loop logic
            self.pi_i2c_handle.i2c_write_device(self.device_addr, HEATER_DISABLE)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
        # if sht3x_logger.level == logging.DEBUG:      # Avoid unnecessary read_status_reg, unless debug logging
            sht3x_logger.debug (f"<{self.device_name}> Success - Status reg:  0x{self.read_status_reg(internal=True):0>4x}")
        return 0


    def read_temprh_data(self, tempunits='F', repeatability='High'):      # legacy
         return self.single_shot(tempunits, repeatability)
    

    def single_shot(self, tempunits='F', repeatability='High', reading_wait=READING_WAIT):
        """
        Blocking
        Trigger single shot reading and retrieve temperature and RH data
        Returns temperature / RH tuple, or 
            CRC_ERROR (-255) on invalid returned data from sensor
            I2C_ERROR (-256) on I2C IO error
        
        If tempunits != 'F' then temp value is returned in 'C' (no error checking).
        """
        try:
            bytes_code = SINGLE_SHOT_MODES[repeatability + '_noCS']
        except:
            raise ValueError (f"Invalid Single Shot mode selection - received repeatability <{repeatability}>")

        try:
            self.pi_i2c_handle.i2c_write_device(self.device_addr, bytes_code)
            time.sleep(reading_wait)
            return self.fetch_data(tempunits, send_fetch=False)
        except Exception as e:
            # raise ??
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
        try:
            bytes_code = PERIODIC_DA_MODES[repeatability + '_' + str(mps)]
        except:
            raise ValueError (f"Invalid Periodic Data Acquisition mode selection - received repeatability <{repeatability}>, mps: <{mps}>")

        try:
            self.pi_i2c_handle.i2c_write_device(self.device_addr, bytes_code)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
        # if sht3x_logger.level == logging.DEBUG:      # Avoid unnecessary read_status_reg, unless debug logging
            sht3x_logger.debug (f"<{self.device_name}> Success - Status reg:  0x{self.read_status_reg(internal=True):0>4x}")
        return 0


    def stop_periodic_DA (self):
        try:
            self.pi_i2c_handle.i2c_write_device(self.device_addr, BREAK)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
        # if sht3x_logger.level == logging.DEBUG:      # Avoid unnecessary read_status_reg, unless debug logging
            sht3x_logger.debug (f"<{self.device_name}> Success - Status reg:  0x{self.read_status_reg(internal=True):0>4x}")
        return 0


    def fetch_data(self, tempunits='F', send_fetch=True):
        """
        Docstring for fetch_data
        
        :param self: Description
        :param tempunits: Description
        :param send_fetch: Description

        Status bit 0x0040 indicates data is available

        """
        try:
            if send_fetch:
                self.pi_i2c_handle.i2c_write_device(self.device_addr, FETCH_DATA)
            (count, data) = self.pi_i2c_handle.i2c_read_device(self.device_addr, 6)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR, I2C_ERROR
        
        if count != 6:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR - error code <{count}>")
            return I2C_ERROR, I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
        # if sht3x_logger.level == logging.DEBUG:
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
            temp_rslt = -45 + (175 * rawtemp / (2**16 -1))
            if tempunits == 'F':
                temp_rslt = temp_rslt *1.8 +32

        sht3x_logger.debug (f"<{self.device_name}> Calculated temp ({tempunits}):     {temp_rslt:>5.1f}")

        # Process RH data
        if crc_calc.checksum(bytes([data[3], data[4]])) != data[5]:
            sht3x_logger.debug (f"<{self.device_name}> RH data CRC error")
            RH_rslt = CRC_ERROR
        else:
            rawRH = ((data[3] <<8) | data[4]) & 0xFFFF
            RH_rslt = 100 * rawRH / (2**16 -1)

        sht3x_logger.debug (f"<{self.device_name}> Calculated RH:           {RH_rslt:>5.1f}")

        return temp_rslt, RH_rslt


    def ART (self):
        try:
            self.pi_i2c_handle.i2c_write_device(self.device_addr, ART)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
        # if sht3x_logger.level == logging.DEBUG:      # Avoid unnecessary read_status_reg, unless debug logging
            sht3x_logger.debug (f"<{self.device_name}> Success - Status reg:  0x{self.read_status_reg(internal=True):0>4x}")
        return 0




    def read_status_reg(self, internal=False):
        try:
            self.pi_i2c_handle.i2c_write_device(self.device_addr, READ_STATUS_REGISTER)
            (count, data) = self.pi_i2c_handle.i2c_read_device(self.device_addr, 3)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if count != 3:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR - error code <{count}>")
            return I2C_ERROR


        if not internal:
            sht3x_logger.debug (f"<{self.device_name}> status reg raw data: 0x{data[0]:0>2x} 0x{data[1]:0>2x} 0x{data[2]:0>2x},  calc CRC: <0x{crc_calc.checksum(bytes([data[0], data[1]])):0>2x}>")
        
        return ((data[0] <<8) | data[1]) & 0xFFFF


    def clear_status_reg(self, debug=False):
        try:
            self.pi_i2c_handle.i2c_write_device(self.device_addr, CLEAR_STATUS_REGISTER)
        except Exception as e:
            sht3x_logger.debug (f"<{self.device_name}> I2C_ERROR\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        if sht3x_logger.isEnabledFor(logging.DEBUG):
        # if sht3x_logger.level == logging.DEBUG:      # Avoid unnecessary read_status_reg, unless debug logging
            sht3x_logger.debug (f"<{self.device_name}> Success - Status reg:  0x{self.read_status_reg(internal=True):0>4x}")
        return 0

# Single shot meas start (eq 2C06) pulls the measurement data back in teh same I2C transaction per section 4.3, 4.4.
# Periodic Data Acquisition Mode - free running eg, 30 32
#   Repeatability High/Medium/Low, mps
# Readout of periodic mode data E0 00
# ART (accelerated response time) 2B 32
# Break - Stop periodic acq 30 93
# init needs support for addr 44 or 45

# After sending a command to the sensor a minimal
# waiting time of 1ms is needed before another command
# can be received by the sensor.


# if __name__ == '__main__': 

#     import pigpio
#     import time

#     I2C_BUS      = 1
#     I2C_SCL_GPIO = 3
#     I2C_SDA_GPIO = 2
#     SHT3X_ADDR   = 0x44

#     logging.getLogger().setLevel(logging.DEBUG)

#     pio = pigpio.pi()
#     pio.set_mode(I2C_SCL_GPIO, pigpio.ALT0)    # set pins to I2C mode
#     pio.set_mode(I2C_SDA_GPIO, pigpio.ALT0)

#     sht3x_i2c  = pio.i2c_open(I2C_BUS, SHT3X_ADDR)
#     sht3x_instance = SHT3x("xyz", pio, sht3x_i2c)

#     sht3x_instance.soft_reset()
#     time.sleep(0.1)                             # Spec 1.5ms soft reset time
#     print (f"status reg: {sht3x_instance.read_status_reg():0>4x}")
#     sht3x_instance.clear_status_reg()
#     sht3x_instance.read_status_reg(diag=True)
#     sht3x_instance.read_temprh_data()
#     sht3x_instance.read_temprh_data(tempunits='C', diag=True)

#     pio.i2c_close(sht3x_i2c)
#     pio.stop()
