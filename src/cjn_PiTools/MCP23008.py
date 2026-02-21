#!/usr/bin/env python3
# All functions return -256 on any I2C comm error.  No exceptions raised to higher level code.
import time
import logging

MCP23008_ADDRS = [0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27]

# Register addresses    Reg long name           Bit function in that register
IODIR_REG =     0x00 #  I/O Direction           1= In, 0= Out
IPOL_REG =      0x01 #  Input Polarity          1= Show inverted state when reading GPIO_REG
GPINTEN_REG =   0x02 #  Interrupt on Change     1= Enabled
DEFVAL_REG =    0x03 #  Default Compare         Expected non-interrupt state
INTCON_REG =    0x04 #  Interrupt pin behavior  1= Interrupt on != DEFVAL_REG, 0= Interrupt on change
IOCON_REG =     0x05 #  Configuration
GPPU_REG =      0x06 #  Input Pullup Enable     1= Pullup enabled
INTF_REG =      0x07 #  Interrupt Flag          1= Pin caused interrupt
INTCAP_REG =    0x08 #  Interrupt Capture       Pin states when interrupt occurred
GPIO_REG =      0x09 #  Port pin states         Write output pin values, read input pin values
OLAT_REG =      0x0A #  Output Latch            Output pin states, as written


IOCON_BITS = 0b00100000     # Disable Sequential Operation (addr pointer does not auto-increment)
I2C_ERROR  = -256

mcp23008_logger = logging.getLogger('cjn_PiTools.MCP23008')


class mcp23008:

    def __init__(self, device_name, device_addr, pi_i2c_bus_handle,
                 IO_dir_init, out_bits_init, ins_pullups_init,
                 ntrys=2, retry_wait=0.25):

        self.device_name =          device_name
        self.device_addr =          device_addr
        self.pi_i2c_bus_handle =    pi_i2c_bus_handle

        self.IO_dir_init =          IO_dir_init       # TODO init states for interrupt registers
        self.out_bits_init =        out_bits_init
        self.ins_pullups_init =     ins_pullups_init

        self.ntrys =                ntrys
        self.retry_wait =           retry_wait

        self.out_bits =             0x00        # Current state, init to placeholder

        if self.device_addr not in MCP23008_ADDRS:
            raise ValueError (f"MCP23008 device address must be in range of 0x20 to 0x27.  Received <0x{device_addr:0>2x}>")

        mcp23008.initialize(self)       # Using this style to avoid invoking child method when this class is inherited 

        api = 'smbus'  if self.pi_i2c_bus_handle.api == 'smbus'  else 'pigpio'
        mcp23008_logger.debug (f"<{self.device_name}> New MCP23008 device defined at addr <0x{self.device_addr:0>2x}> using api <{api}> on i2c bus <{self.pi_i2c_bus_handle.i2c_bus_num}>")


    def initialize(self):       # TODO odd mix of write_reg and reg-specific methods
        if I2C_ERROR == mcp23008.write_reg(self, "IOCON", IOCON_REG, IOCON_BITS):
            mcp23008_logger.warning(f"<{self.device_name}> init of reg IOCON failed")
            return I2C_ERROR

        if I2C_ERROR == mcp23008.IODIR(self, self.IO_dir_init):                   # Set which pins are ins/outs
            mcp23008_logger.warning(f"<{self.device_name}> init of reg IODIR failed")
            return I2C_ERROR

        self.out_bits = self.out_bits_init
        if I2C_ERROR == mcp23008.set_bits(self, self.out_bits_init, 0xff):        # Set all output pin states
            mcp23008_logger.warning(f"<{self.device_name}> init of reg GPIO  failed")
            return I2C_ERROR

        if I2C_ERROR == mcp23008.GPPU(self, self.ins_pullups_init):               # For input pins, set pullup enables
            mcp23008_logger.warning(f"<{self.device_name}> init of reg GPPU  failed")
            return I2C_ERROR
        return 0


    def IODIR(self, IO_dir):
        # 1= In, 0= Out
        return mcp23008.write_reg(self, "IODIR", IODIR_REG, IO_dir)


    def GPPU(self, ins_pullups):
        # For input pins, pullup enables
        return mcp23008.write_reg(self, "GPPU ", GPPU_REG, ins_pullups)


    def set_bits(self, out_bits, mask):
        # Affects only pins set to Out mode
        bits = out_bits & 0xff
        self.out_bits = self.out_bits | (bits | mask)      # Set mask-selected 1s
        self.out_bits = self.out_bits & ~(~bits & mask)    # Clear mask-selected 0s
        return mcp23008.write_reg(self, "GPIO ", GPIO_REG, self.out_bits)
                

    def read_bits(self):
        return mcp23008.read_reg(self, "GPIO ", GPIO_REG)


    def write_reg(self, regname, reg, byte):
        for trynum in range(self.ntrys):
            try:
                payload = [reg, byte]
                self.pi_i2c_bus_handle.i2c_write_device(self.device_addr, payload)
                mcp23008_logger.debug (f"Write <{self.device_name}> Reg {regname}: {byte:0>8b}")
                return byte
            except Exception as e:
                mcp23008_logger.debug (f"Write try# {trynum} FAILED <{self.device_name}> Reg {regname}: {byte:0>8b}\n  {type(e).__name__}: {e})")
            if trynum < self.ntrys - 1:
                time.sleep(self.retry_wait)
            else:
                mcp23008_logger.warning (f"Write FAILED <{self.device_name}> Reg {regname}: {byte:0>8b}")
                return I2C_ERROR


    def read_reg(self, regname, reg):   # Returns 1 byte
        for trynum in range(self.ntrys):
            try:
                count, bytes_list = self.pi_i2c_bus_handle.i2c_read_i2c_block_data(self.device_addr, reg, 1)
                mcp23008_logger.debug (f"Read  <{self.device_name}> Reg {regname}: {bytes_list[0]:0>8b}")
                return bytes_list[0]
            except Exception as e:
                mcp23008_logger.debug (f"Read  try# {trynum} FAILED <{self.device_name}> Reg {regname}\n  {type(e).__name__}: {e})")
            if trynum < self.ntrys - 1:
                time.sleep(self.retry_wait)
            else:
                mcp23008_logger.warning (f"Read  FAILED <{self.device_name}> Reg {regname}")
                return I2C_ERROR


    def dump(self):
        reg = mcp23008.read_reg(self, 'IOCON', IOCON_REG)
        mcp23008_logger.info(f"  <{self.device_name}> IOCON:  0x{reg:0>2x} / {reg:0>8b}")
        reg = mcp23008.read_reg(self, 'IODIR', IODIR_REG)
        mcp23008_logger.info(f"  <{self.device_name}> IODIR:  0x{reg:0>2x} / {reg:0>8b}")
        reg = mcp23008.read_reg(self, 'GPIO ', GPIO_REG)
        mcp23008_logger.info(f"  <{self.device_name}> GPIO:   0x{reg:0>2x} / {reg:0>8b}")
        reg = mcp23008.read_reg(self, 'GPPU ', GPPU_REG)
        mcp23008_logger.info(f"  <{self.device_name}> GPPU:   0x{reg:0>2x} / {reg:0>8b}")
