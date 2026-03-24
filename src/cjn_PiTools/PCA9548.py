#!/usr/bin/env python3
"""PCA9548 I2C port expander library for Raspberry Pi
"""
#==========================================================
#
#  Chris Nelson, Copyright 2026
#
#==========================================================

import sys
from cjnfuncs.core              import set_toolname, setuplogging, logging, set_logging_level

TOOLNAME =  'PCA9548'
I2C_ERROR  = -256
PCA9548_ADDRS = [0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77]

PCA9548_logger = logging.getLogger('cjn_PiTools.PCA9548')

#=====================================================================================
#=====================================================================================
#  C l a s s   P C A 9 5 4 8
#=====================================================================================
#=====================================================================================

class PCA9548:
    """
## Class PCA9548 (device_name, device_addr, pi_i2c_bus_handle) - PCA9548 I2C port expander library for Raspberry Pi

### Args
`device_name` (str)
- User defined name for this instance, e.g., 'PCA9548'
- Not validated as valid string

`device_addr` (int)
- I2C bus address for this instance, e.g., 0x70

`pi_i2c_bus_handle` (cjn_PiTools.shared.pi_i2c instance)
- Get an instance handle in the tools script code and pass it to this device instantiation


### Class instance variables
`device_name` (str)
- As from instantiation

`device_addr` (int)
- As from instantiation

`channel_enable_bit_map` (int)
- Current mask of enabled channels (1=enabled) - value range 0x00 to 0xFF


### Behaviors and rules
- Debug logging may be enabled in the tool script code by setting this module's logging level:

        logging.getLogger('cjn_PiTools.PCA9548').setLevel(logging.DEBUG)

    """

    def __init__ (self, device_name, device_addr, pi_i2c_bus_handle):
        self.device_name =          device_name
        self.device_addr =          device_addr
        self.pi_i2c_bus_handle =    pi_i2c_bus_handle

        if not isinstance (self.device_name, str):
            raise ValueError (f"PCA9548 device.name must be str, received <{device_name}>")

        if self.device_addr not in PCA9548_ADDRS:
            raise ValueError (f"PCA9548 device.addr must be 0x70 - 0x77, received <0x{device_addr:0>x}>")

        api = 'smbus'  if self.pi_i2c_bus_handle.api == 'smbus'  else 'pigpio'
        PCA9548_logger.debug (f"<{self.device_name}> New PCA9548 device defined at addr <0x{self.device_addr:0>2x}> using api <{api}> on i2c bus <{self.pi_i2c_bus_handle.i2c_bus_num}>")


    #=====================================================================================
    #=====================================================================================
    #  w r i t e _ c o n t r o l _ r e g
    #=====================================================================================
    #=====================================================================================

    def write_control_reg (self, write_value):
        """
## write_control_reg (write_value) - Set the control register channel selection to a new enable mask value

***PCA9548 class member function***

The `write_value` is written to the control register and saved in `channel_enable_bit_map`


### Args
`write_value` (int or str)
- Value to be applied to the control register - resolves to between 0x00 and 0xFF
  - If int value:  Used directly as the channel enable mask
  - If str '-1':  Sets the channel enable mask to 0x00 (no channels enabled)
  - If str '0' to '7': Enables the individual channel, and disables all others, e.g., '2' resolves to 0b00000100
- Resolved value is also saved to the instance variable `channel_enable_bit_map`


### Returns
- `channel_enable_bit_map` value on success
- I2C_ERROR if unable to write to the control register
- Raises ValueError if `write_value` is not valid
        """

        PCA9548_logger.debug (f"<{self.device_name}> ***** write_control_reg()")

        channel_enable_bit_map = build_bit_map(write_value)

        if PCA9548_logger.isEnabledFor(logging.DEBUG):
            PCA9548_logger.debug (f"<{self.device_name}> New mask:     <0b{channel_enable_bit_map:0>8b}>, channels <{bit_map_to_channel_str(channel_enable_bit_map)}>")

        try:
            result = self.pi_i2c_bus_handle.i2c_write_byte(self.device_addr, channel_enable_bit_map)
            self.channel_enable_bit_map = channel_enable_bit_map
        except Exception as e:
            PCA9548_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR

        return channel_enable_bit_map


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ c o n t r o l _ r e g
    #=====================================================================================
    #=====================================================================================

    def read_control_reg (self):
        """
## read_control_reg () - Get the current channel enable mask from the control register

***PCA9548 class member function***


### Returns
- Current control register value on success
- I2C_ERROR if unable to read from the control register
        """

        PCA9548_logger.debug (f"<{self.device_name}> ***** read_control_reg()")

        try:
            current_ch_enable_mask = self.pi_i2c_bus_handle.i2c_read_byte(self.device_addr)
        except Exception as e:
            PCA9548_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR

        if PCA9548_logger.isEnabledFor(logging.DEBUG)  and  current_ch_enable_mask >= 0x00:  # TODO pigpio returns negative error codes.  Log and return I2C_ERROR
            PCA9548_logger.debug (f"<{self.device_name}> Current mask: <0b{current_ch_enable_mask:0>8b}>, channels <{bit_map_to_channel_str(current_ch_enable_mask)}>")
        return current_ch_enable_mask



#=====================================================================================
#=====================================================================================
#  private functions
#=====================================================================================
#=====================================================================================

def build_bit_map (channel_value):
    """
    Accepts channel_value
        int 0x00 to 0xFF:  Set channels per bit mask
        str -1:  Unset all channels (same as int 0x00)
        str 0-7:  Set individual channel

    Returns int value in range 0x00 to 0xFF
    Raises ValueError if channel_value cannot be converted to int between -1 to 7
    """

    if isinstance(channel_value, int):
        if channel_value < 0x00  or  channel_value > 0xFF:
            raise ValueError (f"channel_value (int) must be int range 0x00 to 0xFF - received <{channel_value}> / <0x{channel_value:0>2x}>")
        return channel_value
    
    if isinstance(channel_value, str):  # Raises ValueError if not a valid int
        xx = int(channel_value)

        if xx < -1  or  xx > 7:
            raise ValueError (f"channel_value (str) must be int range -1 to 7 - received <{channel_value}>")
        
        if xx == -1:
            return 0x00
        else:
            return 0x01 << int(xx)
        

def bit_map_to_channel_str(bit_mask):
    """
    returns str of enabled channels for logging
    e.g., 0b00000101 returns '0 2'
    """
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
    """PCA9548 set/get channel setting for Raspberry Pi

Mask values for set command
    0-7 selects that specific channel
    -1 sets the control regiser to 0b00000000 (no channels selected)
    0xNN or 0bNNNNNNN sets the control register to this specific bit_mask (range 0x00 to 0xFF)
"""

    # import time
    import argparse
    # import datetime
    import sys
    import importlib.metadata
    __version__ = importlib.metadata.version(__package__ or __name__)

    from cjn_PiTools.shared import pi_i2c


    DEFAULT_NAME = "PCA9548"
    PCA9548_ADDRS_STR = ['0x70', '0x71', '0x72', '0x73', '0x74', '0x75', '0x76', '0x77']


    parser = argparse.ArgumentParser(description=cli.__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('Command', choices=['set', 'get'],
                        help=f"Operation command:  set or get")
    parser.add_argument('Address', choices=PCA9548_ADDRS_STR,
                        help=f"I2C address of PCA9548 device 0x70 - 0x77")
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
    setuplogging(ConsoleLogFormat="{module:>35}.{funcName:30} - {levelname:>8}:  {message}")
    set_logging_level(logging.DEBUG)

    PCA9548_logger.setLevel(logging.DEBUG)
    logging.getLogger('cjn_PiTools.shared').setLevel([logging.WARNING, logging.INFO, logging.DEBUG][args.verbose])


    # Set up interface/api
    address = int (args.Address, 16)

    if args.api == 'pigpio':
        import pigpio
        api =           pigpio.pi(args.host, args.port)
    else:
        api =           'smbus'

    pi_i2c_bus_handle = pi_i2c(api)
    PCA9548_instance =  PCA9548(args.name, address, pi_i2c_bus_handle)


    # Commands
    if args.Command == 'set':
        if args.Mask is None:
            logging.error (f"Mask value required for set command - Aborting")
            sys.exit(1)
        try:
            mask = args.Mask
            if args.Mask.startswith('0x'):
                mask = int (mask, 16)
            elif args.Mask.startswith('0b'):
                mask = int (mask, 2)
            if isinstance(mask, int)  and  (mask < 0x00  or  mask > 0xFF):
                raise ValueError ("Hex or binary value out of range 0x00 to 0xFF")
        except Exception as e:
            logging.error (f"Illegal Mask value - received <{args.Mask}> - Aborting\n  {type(e).__name__}: {e}")
            sys.exit(1)
        
        PCA9548_instance.write_control_reg(mask)


    if args.Command == 'get':
        reg_value = PCA9548_instance.read_control_reg()


    # Cleanup
    pi_i2c_bus_handle.close()
    if args.api == 'pigpio':
        api.stop()


if __name__ == '__main__':
    sys.exit(cli())
