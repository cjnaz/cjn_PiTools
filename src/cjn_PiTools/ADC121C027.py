
__version__ = "V1.0 230512"

import time
import logging

CONV_RSLT_REG = 0x00
CONF_REG      = 0x02
I2C_ERROR     = -256


class adc121c027:

    def __init__(self, device_name, pio_handle, i2c_handle, Vref, ntrys=2, retry_wait=0):
        self.device_name    = device_name
        self.pio_handle     = pio_handle
        self.i2c_handle     = i2c_handle
        self.Vref           = Vref
        self.ntrys          = ntrys
        self.retry_wait     = retry_wait

        adc121c027.initialize(self)


    def initialize(self):
        # Initialization:
            # Auto conv mode disabled
            # Alert Hold, Flag Enable, Pin all disabled
            # (Alert pin active low)
        try:
            self.pio_handle.i2c_write_byte_data (self.i2c_handle, CONF_REG, 0b00000000)
        except:
            logging.debug (f"Initialize of <{self.device_name}> failed")
            return I2C_ERROR
        logging.debug (f"Initialize of <{self.device_name}> success")
        return 0


    def read(self):
        for trynum in range(self.ntrys):
            try:
                self.pio_handle.i2c_write_byte(self.i2c_handle, CONV_RSLT_REG)
                (count, data) = self.pio_handle.i2c_read_device(self.i2c_handle, 2)
                rslt = (((data[0] & 0x0f) << 8) | (data[1] & 0xff)) / 4096 * self.Vref
                logging.debug (f"Conversion result <{self.device_name}>:  (0x{data[0]:0>2x} 0x{data[1]:0>2x}) = {rslt:5.3f} V")
                return rslt
            except:
                logging.debug (f"Read  try# {trynum} FAILED <{self.device_name}>")
            if trynum < self.ntrys - 1:
                time.sleep(self.retry_wait)
            else:
                logging.warning (f"Read  FAILED <{self.device_name}>")
                return I2C_ERROR

