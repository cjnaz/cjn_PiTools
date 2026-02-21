#!/usr/bin/env python3
"""PCA9548 I2C port expander library for Raspberry Pi
"""
#==========================================================
#
#  Chris Nelson, Copyright 2026
#
# V1.0 260212  New
#
#==========================================================

import sys
from cjnfuncs.core              import set_toolname, setuplogging, logging, set_logging_level

TOOLNAME =  'PCA9548'
I2C_ERROR  = -256
PCA9548_ADDRS = [0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77]

__version__ = "V1.1 241112"

PCA9548_logger = logging.getLogger('cjn_PiTools.PCA9548')


class PCA9548:
    def __init__ (self, device_name, device_addr, pi_i2c_bus_handle):
        self.device_name = device_name
        self.device_addr = device_addr
        if self.device_addr not in PCA9548_ADDRS:
            raise ValueError (f"PCA9548 device address must be 0x70 - 0x77, received <0x{device_addr:0>x}>")
        self.pi_i2c_bus_handle  = pi_i2c_bus_handle
        api = 'smbus'  if self.pi_i2c_bus_handle.api == 'smbus'  else 'pigpio'
        PCA9548_logger.debug (f"<{self.device_name}> New PCA9548 device defined at addr <0x{self.device_addr:0>2x}> using api <{api}> on i2c bus <{self.pi_i2c_bus_handle.i2c_bus_num}>")
        self.channel_mask = '0b00000000'


    def write_control_reg (self, write_value):
        """
        write_value is processed thru build_mask_str(), which returns a channel_enable_mask int between 0x00 and 0xFF
        The channel_enable_mask is written to the control register and saved in self.channel_enable_mask
        """
        PCA9548_logger.debug (f"<{self.device_name}> ***** write_control_reg()")

        channel_enable_mask = build_mask_bit_map(write_value)

        if PCA9548_logger.isEnabledFor(logging.DEBUG):
            PCA9548_logger.debug (f"<{self.device_name}> New mask:     <{channel_enable_mask:0>8b}>, channels <{mask_to_channel_str(channel_enable_mask)}>")
            # PCA9548_logger.debug (f"<{self.device_name}> New mask:     <{bit_mask_str}>, channels <{mask_to_numstr(bit_mask)}>")


        # self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, bit_mask)
        # self.channel_mask = f"0x{bit_mask:0>8b}"
        self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, channel_enable_mask)
        self.channel_enable_mask = channel_enable_mask


    def read_control_reg (self):
        PCA9548_logger.debug (f"<{self.device_name}> ***** read_control_reg()")

        channel_enable_mask = self.pi_i2c_bus_handle.i2c_read_byte(self.device_addr)

        if PCA9548_logger.isEnabledFor(logging.DEBUG):
            PCA9548_logger.debug (f"<{self.device_name}> Current mask: <0b{channel_enable_mask:0>8b}>, channels <{mask_to_channel_str(channel_enable_mask)}>")
        return channel_enable_mask


def build_mask_bit_map (channel_value):
    """
    Accepts channel_value
        int 0x00 to 0xFF:  Set channels per bit mask
        str -1:  Unset all channels (same as int 0x00)
        str 0-7:  Set individual channel

    Returns int value in range 0x00 to 0xFF
    Raises ValueError if channel_value cannot be converted to int between -1 to 7
    """
    # Handle newvalue variations

    if isinstance(channel_value, int):
        return channel_value
    
    if isinstance(channel_value, str):
        xx = int(channel_value)

        if xx < -1  or  xx > 7:
            raise ValueError (f"channel_value must be int range -1 to 7 - received <{channel_value}>")
        
        if xx == -1:
            return 0x00
        else:
            return 0x01 << int(xx)
        

def mask_to_channel_str(bit_mask):
    ch_str = ''
    bit_mask_str = f"{bit_mask:0>8b}"
    for x in range(0, 8):
        if bit_mask_str[7-x] == '1':
            ch_str += str(x) + ' '
    return ch_str[:-1]     # trim trailing space



#=====================================================================================
#=====================================================================================
#  c l i
#=====================================================================================
#=====================================================================================

def cli():

    import time
    import argparse
    import datetime
    import sys
    import importlib.metadata
    __version__ = importlib.metadata.version(__package__ or __name__)

    from cjn_PiTools.shared import pi_i2c

    desc = """PCA9548 set/get channel setting for Raspberry Pi

Mask values for set command
    Int value 0-7 selects that specific channel
    0xNN or 0bNNNNNNN sets the control register to that specific bit_mask
"""

    DEFAULT_NAME = "PCA9548"
    PCA9548_ADDRS_STR = ['0x70', '0x71', '0x72', '0x73', '0x74', '0x75', '0x76', '0x77']


    parser = argparse.ArgumentParser(description=desc + __version__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('Command', choices=['set', 'get'],
                        help=f"Operation command:  set or get")
    parser.add_argument('Address', choices=PCA9548_ADDRS_STR,
                        help=f"I2C address of PCA9548 device 0x70 - 0x77 (default 0x70)")
    parser.add_argument('Mask', nargs='?',
                        help=f"Set control register to this value (required for set operation)")

    parser.add_argument('-n', '--name', default=DEFAULT_NAME,
                        help=f"PCA9548 device/function name (default {DEFAULT_NAME})")
    parser.add_argument('-A', '--api', choices=['smbus', 'pigpio'], default='pigpio',
                        help=f"Either 'smbus' or 'pigpio' (default 'pigpio')")
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
    setuplogging(ConsoleLogFormat="{module:>35}.{funcName:25} - {levelname:>8}:  {message}")
    set_logging_level(logging.DEBUG)

    PCA9548_logger.setLevel(logging.DEBUG)
    logging.getLogger('cjn_PiTools.shared').setLevel([logging.WARNING, logging.INFO, logging.DEBUG][args.verbose])


    # Set up interface/api
    address = int (args.Address, 16)
    # try:
    #     address = int (args.Address, 16)
    # except:
    #     logging.error (f"PCA9548 device address must be 0x70 - 0x77, received <{args.Address}> - Aborting")
    #     sys.exit(1)

    if args.api == 'pigpio':
        import pigpio
        api =           pigpio.pi(args.host, args.port)
    else:
        api =           'smbus'

    pi_i2c_bus_handle =     pi_i2c(api)
    PCA9548_instance =  PCA9548(args.name, address, pi_i2c_bus_handle)


    # Commands
    if args.Command == 'set':
        if args.Mask is None:
            logging.error (f"Mask value required for set command - Aborting")
            sys.exit(1)
        PCA9548_instance.write_control_reg(args.Mask)

    if args.Command == 'get':
        reg_value = PCA9548_instance.read_control_reg()


    # Cleanup
    pi_i2c_bus_handle.close()
    if args.api == 'pigpio':
        api.stop()


if __name__ == '__main__':
    sys.exit(cli())
