# All functions return -256 on any I2C comm error.  No exceptions raised to higher level code.
import time
import logging

IODIR_REG  = 0x00           # 1= In, 0= Out
IOCON_REG  = 0x05
IOCON_BITS = 0b00100000     # Disable Sequential Operation (addr pointer does not auto-increment)
GPPU_REG   = 0x06           # Input pullup enables
GPIO_REG   = 0x09           # Write output pin values, read input pin values
I2C_ERROR  = -256

class mcp23008:

    def __init__(self, device_name, pio_handle, i2c_handle, IO_dir, out_bits, ins_pullups, ntrys=2, retry_wait=0.25):
        self.device_name = device_name
        self.pio_handle  = pio_handle
        self.i2c_handle  = i2c_handle
        self.IO_dir_init = IO_dir
        self.out_bits    = self.out_bits_init = out_bits
        self.ins_pullups_init = ins_pullups
        self.ntrys       = ntrys
        self.retry_wait  = retry_wait

        mcp23008.initialize(self)       # Using this style to avoid invoking child method when this class is inherited 


    def initialize(self):
        if I2C_ERROR == mcp23008.write_reg(self, "IOCON", IOCON_REG, IOCON_BITS):
            logging.warning(f"<{self.device_name}> init of reg IOCON failed")
            return I2C_ERROR
        self.out_bits = self.out_bits_init
        if I2C_ERROR == mcp23008.IODIR(self, self.IO_dir_init):                   # Set which pins are ins/outs
            logging.warning(f"<{self.device_name}> init of reg IODIR failed")
            return I2C_ERROR
        if I2C_ERROR == mcp23008.set_bits(self, self.out_bits_init, 0xff):        # Set all output pin states
            logging.warning(f"<{self.device_name}> init of reg GPIO  failed")
            return I2C_ERROR
        if I2C_ERROR == mcp23008.GPPU(self, self.ins_pullups_init):               # For input pins, pullup enables
            logging.warning(f"<{self.device_name}> init of reg GPPU  failed")
            return I2C_ERROR
        # logging.debug (f"Initialize of <{self.device_name}> success")
        return 0


    def IODIR(self, IO_dir):
        # 1= In, 0= Out
        return mcp23008.write_reg(self, "IODIR", IODIR_REG, IO_dir)


    def GPPU(self, ins_pullups):
        # For input pins, pullup enables
        return mcp23008.write_reg(self, "GPPU ", GPPU_REG, ins_pullups)


    def set_bits(self, out_bits, mask):
        bits = out_bits & 0xff
        self.out_bits = self.out_bits | (bits | mask)      # Set mask-selected 1s
        self.out_bits = self.out_bits & ~(~bits & mask)    # Clear mask-selected 0s
        return mcp23008.write_reg(self, "GPIO ", GPIO_REG, self.out_bits)
                

    def read_bits(self):
        return mcp23008.read_reg(self, "GPIO ", GPIO_REG)


    def write_reg(self, regname, reg, byte):
        for trynum in range(self.ntrys):
            try:
                self.pio_handle.i2c_write_byte_data (self.i2c_handle, reg, byte)
                logging.debug (f"Write <{self.device_name}> Reg {regname}: {byte:0>8b}")
                return byte
            except:
                logging.debug (f"Write try# {trynum} FAILED <{self.device_name}> Reg {regname}: {byte:0>8b}")
            if trynum < self.ntrys - 1:
                time.sleep(self.retry_wait)
            else:
                logging.warning (f"Write FAILED <{self.device_name}> Reg {regname}: {byte:0>8b}")
                return I2C_ERROR


    def read_reg(self, regname, reg):
        for trynum in range(self.ntrys):
            try:
                byte = self.pio_handle.i2c_read_byte_data (self.i2c_handle, reg)
                logging.debug (f"Read  <{self.device_name}> Reg {regname}: {byte:0>8b}")
                return byte
            except:
                logging.debug (f"Read  try# {trynum} FAILED <{self.device_name}> Reg {regname}")
            if trynum < self.ntrys - 1:
                time.sleep(self.retry_wait)
            else:
                logging.warning (f"Read  FAILED <{self.device_name}> Reg {regname}")
                return I2C_ERROR


    def dump(self):
        reg = mcp23008.read_reg(self, 'IOCON', IOCON_REG)
        logging.warning(f"  <{self.device_name}> IOCON:  0x{reg:0>2x} / {reg:0>8b}")
        reg = mcp23008.read_reg(self, 'IODIR', IODIR_REG)
        logging.warning(f"  <{self.device_name}> IODIR:  0x{reg:0>2x} / {reg:0>8b}")
        reg = mcp23008.read_reg(self, 'GPIO ', GPIO_REG)
        logging.warning(f"  <{self.device_name}> GPIO:   0x{reg:0>2x} / {reg:0>8b}")
        reg = mcp23008.read_reg(self, 'GPPU ', GPPU_REG)
        logging.warning(f"  <{self.device_name}> GPPU:   0x{reg:0>2x} / {reg:0>8b}")
