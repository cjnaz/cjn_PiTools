#!/usr/bin/env python3
"""
HTU21D library for Raspberry Pi
"""
#==========================================================
#
#  Chris Nelson, Copyright 2022-2026
#   
#==========================================================

import time
# from time import sleep
from cjnfuncs.core import set_toolname, logging, setuplogging, set_logging_level

HTU21D_ADDRS =                  [0x40]

TRIGGER_TEMP_MEASURE_HOLD =     0xE3
TRIGGER_RH_MEASURE_HOLD =       0xE5
# TRIGGER_TEMP_MEASURE_NOHOLD =   0xF3
# TRIGGER_RH_MEASURE_NOHOLD =     0xF5
READ_USER_REG =                 0xE7
WRITE_USER_REG =                0xE6
SOFT_RESET =                    0xFE
READING_WAIT =                  0.055                    # Temp and RH readings take up to 50ms
RESET_WAIT =                    0.05 #0.02                     # Soft reset spec wait is 15ms

htu21d_logger = logging.getLogger('cjn_PiTools.HTU21D')


class HTU21D:
    def __init__(self, device_name, device_addr, pi_i2c_bus_handle):
        self.device_name =          device_name
        self.device_addr =          device_addr
        self.pi_i2c_bus_handle =    pi_i2c_bus_handle

        if self.device_addr not in HTU21D_ADDRS:
            raise ValueError (f"HTU21D device address must be 0x40.  Received <0x{device_addr:0>2x}>")

        api = 'smbus'  if self.pi_i2c_bus_handle.api == 'smbus'  else 'pigpio'
        htu21d_logger.debug (f"<{self.device_name}> New HTU21D device defined at addr <0x{self.device_addr:0>2x}> using api <{api}> on i2c bus <{self.pi_i2c_bus_handle.i2c_bus_num}>")

    # def __init__(self, pio_handle, i2c_handle, debug=False):
        # self.pio_handle = pio_handle
        # self.i2c_device = i2c_handle
        # self.debug = debug


    def soft_reset(self): # , debug=False):
        """Issue soft reset, and wait
        Returns
            0 for successful operation
            -256 for an I2C error
        """
        try:
            # n = self.pio_handle.i2c_write_byte(self.i2c_device, SOFT_RESET)  # returns 0x00 on ack, and 0x05 on no response
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, SOFT_RESET)  # returns 0x00 on ack, and 0x05 on no response
            time.sleep (RESET_WAIT)  # spec requires 15ms
        except:
            htu21d_logger.debug (f"HTU21D soft_reset failed.")
            return -256
        htu21d_logger.debug (f"HTU21D soft_reset success.")#  UserReg read back: 0x{self.read_user_reg():0>2x}")
        return 0


    def read_user_reg(self):
        """Read the user register byte
        Returns UserReg value, or
            -256 for an I2C error
        """
        try:
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, READ_USER_REG)
            (count, byteArray) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 1) # vacuum up those bytes
        except:
            htu21d_logger.debug (f"HTU21D read_user_reg failed.")
            return -256
        if count != 1:
            htu21d_logger.debug (f"HTU21D read_user_reg failed - bad byte count returned.")
            return -256
        htu21d_logger.debug (f"HTU21D read_user_reg:  0x{byteArray[0]:0>2x}")

        return byteArray[0]


    def write_user_reg(self, value):
        """Write the user register byte
        Returns
            0 for successful operation
            -256 for an I2C error
        """
        try:
            self.pi_i2c_bus_handle.i2c_write_byte_data(self.device_addr, WRITE_USER_REG, value)
        except:
            htu21d_logger.debug (f"HTU21D write_user_reg failed.")
            return -256
        htu21d_logger.debug (f"HTU21D write_user_reg: 0x{value:0>2x}")
        return 0

    def read_temp_data(self, scale='F'):
        """Read 3 temperature bytes from the sensor
        Returns temperature value in F (default) or C, or
            -255 CRC error (invalid returned data from sensor)
            -256 for an I2C error
        """
        try:
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, TRIGGER_TEMP_MEASURE_HOLD)
            time.sleep(READING_WAIT)
            (count, bytes3) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 3)
        except:
            htu21d_logger.debug ("HTU21D.read_temp_data i2c_read_device failed")
            return -256  # I2C read error  TODO
        htu21d_logger.debug (f"HTU21D.read_temp_data returned bytes:          0x{bytes3[0]:0>2x} 0x{bytes3[1]:0>2x} 0x{bytes3[2]:0>2x}")

        if not self.crc8_check(bytes3):
            htu21d_logger.debug ("HTU21D.read_temp_data CRC error")
            return -255  # bad CRC

        MSB = bytes3[0]
        LSB = bytes3[1]
        rawtemp = ((MSB <<8) | LSB) & 0xFFFC  # Lower two bits of LSB are status bits to be cleared
        htu21d_logger.debug (f"HTU21D.read_temp_data Raw temp:                {rawtemp:x} hex, {rawtemp:d} decimal")

        # Apply datasheet formula:  Temp = -46.85 + (175.72 * <sensor data> / 2^16
        temp = -46.85 + (175.72 * rawtemp / 2**16)
        if scale == 'F':
            temp = temp *1.8 +32
        htu21d_logger.debug (f"HTU21D.read_temp_data Calculated temp ({scale}):     {temp}")
        return temp


    def read_RH_data(self):
        """Read 3 relative humidity bytes from the sensor"""
        """Read 3 relative humidity bytes from the sensor
        Returns relative humidity value in %, or
            -255 CRC error (invalid returned data from sensor)
            -256 for an I2C error
        """
        try:
            self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, TRIGGER_RH_MEASURE_HOLD)
            time.sleep(READING_WAIT)
            (count, bytes3) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 3)
        except:
            htu21d_logger.debug ("HTU21D.read_RH_data i2c_read_device failed")
            return -256  # I2C read error

        htu21d_logger.debug (f"HTU21D.read_RH_data returned bytes:      0x{bytes3[0]:0>2x} 0x{bytes3[1]:0>2x} 0x{bytes3[2]:0>2x}")

        if not self.crc8_check(bytes3):
            print ("HTU21D.read_RH_data CRC error")
            return -255  # bad CRC

        MSB = bytes3[0]
        LSB = bytes3[1]
        rawRH = ((MSB <<8) | LSB) & 0xFFFC  # Lower two bits of LSB are status bits to be cleared
        htu21d_logger.debug (f"HTU21D.read_RH_data Raw RH:              {rawRH:x} hex, {rawRH:d} decimal")

        # Apply datasheet formula:  RH = -6 + 125 * <sensor data> / 2^16
        RH = -6.0 + (125 * rawRH / 2**16)
        htu21d_logger.debug (f"HTU21D.read_RH_data Calculated RH:       {RH}")
        return RH


    def crc8_check(self, value):
       """Calculate the CRC8 for the data received"""
       if len(value) != 3:
            return False

       # Ported from Sparkfun Arduino HTU21D Library:   https://github.com/sparkfun/HTU21D_Breakout
       remainder = ( ( value[0] << 8 ) + value[1] ) << 8
       remainder |= value[2]

       # POLYNOMIAL = 0x0131 = x^8 + x^5 + x^4 + 1
       # divisor = 0x988000 is the 0x0131 polynomial shifted to farthest left of three bytes
       divisor = 0x988000

       for i in range(0, 16):
           if( remainder & 1 << (23 - i) ):
               remainder ^= divisor

           divisor = divisor >> 1

       if remainder == 0:
           return True
       else:
           return False


# if __name__ == '__main__': 

#     import pigpio
#     import argparse

#     I2C_SCL_GPIO        = 3
#     I2C_SDA_GPIO        = 2

#     parser = argparse.ArgumentParser(description=__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
#     parser.add_argument('-c', '--channel', type=int,
#                         help="Channel select for pca9548 (0-7)")
#     parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + __version__,
#                         help="Return version number and exit.")

#     args = parser.parse_args()


#     pio = pigpio.pi()

#     pio.set_mode(I2C_SCL_GPIO, pigpio.ALT0)    # set to I2C mode
#     pio.set_mode(I2C_SDA_GPIO, pigpio.ALT0)

#     if args.channel is not None:
#         pca9548_i2c = pio.i2c_open(1, 0x71)
#         bitmask = 0x01 << args.channel
#         pio.i2c_write_byte(pca9548_i2c, bitmask)

#     htu21d_i2c  = pio.i2c_open(1, 0x40)
#     htu21d = HTU21D(pio, htu21d_i2c, debug=True)


#     htu21d.read_user_reg()
#     htu21d.soft_reset()
#     htu21d.read_user_reg()

#     print (f"{htu21d.read_temp_data(scale='C'):>4.1f} C")
#     print (f"{htu21d.read_temp_data():>4.1f} F")
#     print (f"{htu21d.read_RH_data():>4.1f} %")

#     print (f"0x{htu21d.read_user_reg():0>2x} (before following write 0x03)")
#     htu21d.write_user_reg(3)
#     htu21d.read_user_reg()

#     htu21d.write_user_reg(4)
#     htu21d.read_user_reg()
