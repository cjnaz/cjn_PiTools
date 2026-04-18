#!/usr/bin/env python3
"""MCP23008 8-Bit I/O Expander library for Raspberry Pi
"""

#==========================================================
#
#  Chris Nelson, Copyright 2026
#
#==========================================================

import logging
from .shared import I2C_ERROR

# Configs / Constants
MCP23008_ADDRS = [0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27]

# Register addresses    Reg long name           Bit function in that register
IODIR_ADDR =    0x00 #  I/O Direction           1= In, 0= Out
IPOL_ADDR =     0x01 #  Input Polarity          1= Show inverted state when reading GPIO_REG
GPINTEN_ADDR =  0x02 #  Interrupt on Change     1= Enabled
DEFVAL_ADDR =   0x03 #  Default Compare         Expected non-interrupt state
INTCON_ADDR =   0x04 #  Interrupt pin behavior  1= Interrupt on != DEFVAL_REG, 0= Interrupt on change
IOCON_ADDR =    0x05 #  Configuration
GPPU_ADDR =     0x06 #  Input Pullup Enable     1= Pullup enabled
INTF_ADDR =     0x07 #  Interrupt Flag          1= Pin caused interrupt
INTCAP_ADDR =   0x08 #  Interrupt Capture       Pin states when interrupt occurred
GPIO_ADDR =     0x09 #  Port pin states         Write output pin values, read input pin values
OLAT_ADDR =     0x0A #  Output Latch            Output pin states, as written

mcp23008_logger = logging.getLogger('cjn_PiTools.MCP23008')



#=====================================================================================
#=====================================================================================
#  C l a s s   M C P 2 3 0 0 8
#=====================================================================================
#=====================================================================================

class MCP23008:
    """
## Class MCP23008 (device_name, device_addr, pi_i2c_bus_handle, init_settings={}) - MCP23008 library for Raspberry Pi

Create an MCP23008 device instance.  The SPI-based MCP23S08 is not supported.

### Args
`device_name` (str)
- User defined name for this instance, e.g., 'My_MCP23008'

`device_addr` (int)
- I2C bus address for this instance, e.g., 0x20
- Must be in the range of 0x20 to 0x27

`pi_i2c_bus_handle` (cjn_PiTools.shared.pi_i2c instance)
- Get a `pi_i2c` instance handle in the tools script code and pass it to this device instantiation

`init_settings` (dict, default {})
- Override default initialization values.  See Behaviors, below.
- The dictionary format is {'reg name1': init value1, 'reg name2': init value2, ... }
- Values must be ints in range 0x00 to 0xFF
- These specified values are used as the initialization values during device instantiation and later calls to `initialize()`


### Returns
- MCP23008 handle on success
- Raises ValueError if args checks fail
- Raises I2C_ERROR I2C IO error


### Class instance variables
- `device_name` (str) - as passed in at instantiation
- `device_addr` (int) - as passed in at instantiation
- `registers` (dictionary of dictionaries)
  - The top level dictionary is keyed using the register names
  - Each register-specific dictionary has these keys:
    - 'addr' is this register's address - used internally in this module
    - 'init' is the initialization value for this register
    - 'cached' is the cached (last written) value to this register
  - The registers and their default initialization values are:

    Reg name | Default initialization value | Notes
    --- | --- | ---
    'IODIR'   | 0b11111111 | All pins default to input mode
    'IPOL'    | 0b00000000 | See datasheet for interrupt related settings
    'GPINTEN' | 0b00000000
    'DEFVAL': | 0b00000000
    'INTCON': | 0b00000000
    'IOCON':  | 0b00100000 | Auto increment disabled, all other features per datasheet default
    'GPPU':   | 0b00000000 | All input pins default to weak pullups disabled
    'INTF':   | 0b00000000
    'INTCAP': | 0b00000000
    'GPIO':   | 0b00000000 | Read input pin states using the GPIO register
    'OLAT':   | 0b00000000 | Set output pin states using the OLAT register


### Behaviors and rules
- The APIs in this class accept names of registers as strings, e.g., 'GPIO'.  The names of the registers are listed above.
- Set output pin states using the 'OLAT' register, not the 'GPIO' register, since 'OLAT' is written after GPIO during 
initialization, and output pin state is only tracked/cached on 'OLAT'.
- `initialize()` is called as part of instantiation, and thus applies the `init_settings` values overlaid 
on the default initialization values listed above.
- Debug logging may be enabled in the tool script code by setting this module's logging level:

        logging.getLogger('cjn_PiTools.MCP23008').setLevel(logging.DEBUG)
"""
    def __init__(self, device_name, device_addr, pi_i2c_bus_handle, init_settings={}):

        self.device_name =          device_name
        self.device_addr =          device_addr
        self.pi_i2c_bus_handle =    pi_i2c_bus_handle

        if not isinstance(device_name, str):
            raise ValueError (f"device_name must be str - Received <{device_name}>")

        if self.device_addr not in MCP23008_ADDRS:
            raise ValueError (f"<{self.device_name}> Device address must be in range of 0x20 to 0x27 - Received <{device_addr}>")

        self.registers = {  # Register default and initialization values
            'IODIR':    {'addr': IODIR_ADDR,   'init': 0b11111111, 'cached':0},  # Pin is configured as an input
            'IPOL':     {'addr': IPOL_ADDR,    'init': 0b00000000, 'cached':0},  # GPIO register bit will reflect the same logic state of the input pin
            'GPINTEN':  {'addr': GPINTEN_ADDR, 'init': 0b00000000, 'cached':0},  # Disable GPIO input pin for interrupt-on-change event
            'DEFVAL':   {'addr': DEFVAL_ADDR,  'init': 0b00000000, 'cached':0},  # Default pin value 0
            'INTCON':   {'addr': INTCON_ADDR,  'init': 0b00000000, 'cached':0},  # Pin value is compared against the previous pin init
            'IOCON':    {'addr': IOCON_ADDR,   'init': 0b00100000, 'cached':0},  # Disable Sequential Operation, Interrupt output active drive & active low, SDA slew rate control enabled
            'GPPU':     {'addr': GPPU_ADDR,    'init': 0b00000000, 'cached':0},  # Pull-up disabled
            'INTF':     {'addr': INTF_ADDR,    'init': 0b00000000, 'cached':0},  # Interrupt flags
            'INTCAP':   {'addr': INTCAP_ADDR,  'init': 0b00000000, 'cached':0},  # Interrupt capture
            'GPIO':     {'addr': GPIO_ADDR,    'init': 0b00000000, 'cached':0},  # Outputs set to drive 0
            'OLAT':     {'addr': OLAT_ADDR,    'init': 0b00000000, 'cached':0}   # Output latch - write via GPIO
            }
        
        # Overlay init_settings over defaults
        for item in init_settings:

            # Screen for init_settings not a valid dictionary
            try:
                value = init_settings[item]
            except Exception as e:
                raise ValueError (f"<{self.device_name}> Malformed init_settings - Received <{init_settings}>")

            # Screen for invalid register name
            if not isinstance(item, str)  or  item not in self.registers:
                raise ValueError (f"<{self.device_name}> Invalid register name - Received <{item}>")

            # Screen for value not an int or out of range
            if not isinstance(value, int)  or  value < 0x00  or  value > 0xFF:
                raise ValueError (f"<{self.device_name}> <{item}> init_settings illegal value - Received <{value}>")

            self.registers[item]['init'] = value

        rslt = self.initialize()
        if rslt == I2C_ERROR:
            raise OSError (f"<{self.device_name}> I2C communication error")

        # Dump initialized state
        if mcp23008_logger.isEnabledFor(logging.DEBUG):
            reg_dump = self.registers_dump()
            if reg_dump == I2C_ERROR:
                raise OSError (f"<{self.device_name}> I2C communication error")
            mcp23008_logger.debug(f"<{self.device_name}> initialized registers:{reg_dump}")

        api = 'smbus'  if self.pi_i2c_bus_handle.api == 'smbus'  else 'pigpio'
        mcp23008_logger.debug (f"<{self.device_name}> New MCP23008 device defined at addr <0x{self.device_addr:0>2x}> using api <{api}> on i2c bus <{self.pi_i2c_bus_handle.i2c_bus_num}>")


    #=====================================================================================
    #=====================================================================================
    #  i n i t i a l i z e
    #=====================================================================================
    #=====================================================================================

    def initialize(self):
        """
## initialize () - Set all registers to their instantiation values

***MCP23008 class member function***


### Returns
- 0 on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- All registers are reset to their initialization states as defined at instantiation (default values overlaid by
`init_settings`).  See the class header documentation.
"""
        mcp23008_logger.debug (f"<{self.device_name}> ***** initialize()")
        for item in self.registers:
            init = self.registers[item]['init']
            try:
                self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [self.registers[item]['addr'], init])
            except Exception as e:
                mcp23008_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
                return I2C_ERROR
            self.registers[item]['cached'] = init
        return 0


    #=====================================================================================
    #=====================================================================================
    #  r e g i s t e r s _ d u m p
    #=====================================================================================
    #=====================================================================================

    def registers_dump(self):
        """
## registers_dump () - Return string listing the state of all registers

***MCP23008 class member function***


### Returns
- I2C_ERROR on I2C IO error
- On success, returns formatted string listing of all registers, along with their initialization values, cached
values, and current read values, e.g.,

        IODIR   :  Init value: 0b11110000, Cached value: 0b11110000, Read value: 0b11110000
        IPOL    :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b00000000
        GPINTEN :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b00000000
        DEFVAL  :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b00000000
        INTCON  :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b00000000
        IOCON   :  Init value: 0b00100000, Cached value: 0b00100000, Read value: 0b00100000
        GPPU    :  Init value: 0b11110000, Cached value: 0b11110000, Read value: 0b11110000
        INTF    :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b00000000
        INTCAP  :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b00000000
        GPIO    :  Init value: 0b00000000, Cached value: 0b00000000, Read value: 0b11110110
        OLAT    :  Init value: 0b00000110, Cached value: 0b00000110, Read value: 0b00000110

        
### Behaviors and rules
- The GPIO read value shows both output and input pin states.  'GPIO's cached value should be ignored.
"""
        mcp23008_logger.debug (f"<{self.device_name}> ***** registers_dump()")
        xx = ''
        for item in self.registers:
            try:
                self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, [self.registers[item]['addr']])
                count, bytes_list = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 1)
            except Exception as e:
                mcp23008_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
                return I2C_ERROR

            init_value =    self.registers[item]['init']
            cached_value =  self.registers[item]['cached']
            read_value =    bytes_list[0]
            xx += f"\n  {item:8}:  Init value: 0b{init_value:0>8b}, Cached value: 0b{cached_value:0>8b}, Read value: 0b{read_value:0>8b}"
        return xx


    #=====================================================================================
    #=====================================================================================
    #  s e t _ r e g i s t e r s
    #=====================================================================================
    #=====================================================================================

    def set_registers(self, reg_dict):
        """
## set_registers (reg_dict) - Writes new values to a series of registers

***MCP23008 class member function***


### Args
`reg_dict` (dict)
- The dictionary format is {'reg name1': value1, 'reg name2': value2, ... } (same as `init_settings` in class instantiation)
- Values must be ints in range 0x00 to 0xFF
- These specified values are written to the respective registers and saved to the 'cached' fields in the 
`registers` instance attribute


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
- Raises ValueError on issues with the `reg_dict` content

        
### Behaviors and rules
- Each register is written in full.  See `set_bits()` for setting specific bits within a register
"""
        mcp23008_logger.debug (f"<{self.device_name}> ***** set_registers()")
        for item in reg_dict:

            # Screen for reg_dict not a valid dictionary
            try:
                value = reg_dict[item]
            except Exception as e:
                raise ValueError (f"<{self.device_name}> Malformed reg_dict - Received <{reg_dict}>")

            # Screen for invalid register name
            if not isinstance(item, str)  or  item not in self.registers:
                raise ValueError (f"<{self.device_name}> Invalid register name - Received <{item}>")

            # Screen for value not an int or out of range
            if not isinstance(value, int)  or  value < 0x00  or  value > 0xFF:
                raise ValueError (f"<{self.device_name}> <{item}> illegal value - Received <{value}>")

            # Write the register
            try:
                self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [self.registers[item]['addr'], value])
                mcp23008_logger.debug (f"<{self.device_name}> Reg <{item}> set to <0b{value:0>8b}>")
            except Exception as e:
                mcp23008_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
                return I2C_ERROR

            # If successful, cache the value
            self.registers[item]['cached'] = value
        return 0


    #=====================================================================================
    #=====================================================================================
    #  s e t _ b i t s
    #=====================================================================================
    #=====================================================================================

    def set_bits(self, reg_name, bits, mask):
        """
## set_bits (reg_name, bits, mask) - Sets `mask`-selected bits of register `reg_name` to the `bits` value

***MCP23008 class member function***

This method is useful for setting features/values on specific pins while leaving other pin unchanged.
Examples:
- Turn on or off interrupt modes on specific input pins
- Set a specific output pin to a value


### Args
`reg_name` (str)
- One of the defined register names

`bits` (int)
- An integer value whose `mask`-selected bits will be applied to the register `reg_name`
- Must be in the range of 0x00 to 0xFF

`mask` (int)
- The mask selecting which bits will be applied to the register `reg_name`
- Logic 1 selects an active/applied bit position, while logic 0 masked bits are unchanged
- Must be in the range of 0x00 to 0xFF


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
- Raises ValueError on issues with the args

        
### Behaviors and rules
- `mask`-selected bits are modified using the `reg_name`'s 'cached' field.  In other words, the bit changes 
are made to the cached value, not the value read from the device.
- The modified register value is saved to 'cached'
"""
        mcp23008_logger.debug (f"<{self.device_name}> ***** set_bits()")

        # Screen for invalid register name
        if not isinstance(reg_name, str)  or  reg_name not in self.registers:
            raise ValueError (f"<{self.device_name}> Invalid register name - Received <{reg_name}>")

        # Screen bits and mask for not an int or out of range
        if not isinstance(bits, int)  or  bits < 0  or  bits > 0xFF:
            raise ValueError (f"<{self.device_name}> Invalid bits value - Received <{bits}>")
        if not isinstance(mask, int)  or  mask < 0  or  mask > 0xFF:
            raise ValueError (f"<{self.device_name}> Invalid mask value - Received <{mask}>")

        # Merge the changed bits into the cached value
        value = self.registers[reg_name]['cached']  # Cached    1010 1010
        _bits = bits & mask                         # _bits=    0000 0110
        _value = value & ~mask                      # _value=   1010 0000
        value = _value | _bits                      # value=    1010 0110

        # Write the register
        try:
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [self.registers[reg_name]['addr'], value])
            mcp23008_logger.debug (f"<{self.device_name}> Reg <{reg_name}> set to <0b{value:0>8b}>")
        except Exception as e:
            mcp23008_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        # If successful, cache the value
        self.registers[reg_name]['cached'] = value

        return 0


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ r e g
    #=====================================================================================
    #=====================================================================================

    def read_reg(self, reg_name):
        """
## read_reg (reg_name) - Return the value of the specified register as read from the device

***MCP23008 class member function***


### Args
`reg_name` (str)
- One of the defined register names


### Returns
- Device register value (int) on success
- I2C_ERROR on I2C IO error
- Raises ValueError on invalid `reg_name`
"""
        mcp23008_logger.debug (f"<{self.device_name}> ***** read_reg()")

        # Screen for invalid register name
        if not isinstance(reg_name, str)  or  reg_name not in self.registers:
            raise ValueError (f"<{self.device_name}> Invalid register name - Received <{reg_name}>")

        try:
            self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, [self.registers[reg_name]['addr']])
            count, bytes_list = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 1)
        except Exception as e:
            mcp23008_logger.debug (f"<{self.device_name}> exception:\n  {type(e).__name__}: {e}")
            return I2C_ERROR

        return bytes_list[0]


