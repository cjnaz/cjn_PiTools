#!/usr/bin/env python3
"""ADC121C* library for Raspberry Pi
"""
#==========================================================
#
#  Chris Nelson, Copyright 2026
#
#==========================================================

import time
import logging

CONVERSION_RSLT_REG_PTR =       0x00
ALERT_STATUS_REG_PTR =          0X01
CONFIG_REG_PTR =                0x02
LOW_LIMIT_REG_PTR =             0x03
HIGH_LIMIT_REG_PTR =            0x04
HYSTERESIS_REG_PTR =            0x05
LOWEST_CONVERSION_REG_PTR =     0x06
HIGHEST_CONVERSION_REG_PTR =    0x07

I2C_ERROR =                     -256
ADC121_ADDRS =                  [0x50, 0x51, 0x52, 0x54, 0x55, 0x56, 0x58, 0x59, 0x5a]


adc121c_logger =                logging.getLogger('cjn_PiTools.ADC121C')

# I2C operation ADC121C:
#     The first data byte of every write operation is stored in the address pointer register.
#     This value selects the register that the following data bytes will be written to or read from.
#     Write a register send sequence:
#       1) ADC address, write Address Pointer Register byte, write 1 or 2 bytes of target register data (same sequence)
#     Read a register send sequence:
#       1) ADC address, write Address Pointer Register byte
#       2) ADC address, read 1 or 2 byte register data
#       If the (address) pointer is preset correctly, a read operation can occur without first writing 
#       the address pointer register (skip step 1)


#=====================================================================================
#=====================================================================================
#  C l a s s   A D C 1 2 1 C
#=====================================================================================
#=====================================================================================

class ADC121C:
    """
## Class ADC121C (device_name, device_addr, pi_i2c_bus_handle, Vref, config_byte=None, cycle_time=0b000, alert_hold=0, alert_flag_en=0, alert_pin_en=0, polarity=0 ) - ADC121Cxxx library for Raspberry Pi

Create an ADC121C family device instance

### Args
`device_name` (str)
- User defined name for this instance, e.g., 'PCA9548'
- Not validated as valid string

`device_addr` (int)
- I2C bus address for this instance, e.g., 0x70

`pi_i2c_bus_handle` (cjn_PiTools.shared.pi_i2c instance)
- Get an instance handle in the tools script code and pass it to this device instantiation

`Vref` (float)
- ADC reference voltage
- `read_conversion_result()` returned 12-bit code is multiplied by this value to return measured voltage

`config_byte` (int, optional, default None)
- Used for direct setting of the configuration register to a byte value during instantiation
- Must be in range 0x00 to 0xFF

`cycle_time` (int, default 0b000)
- Value for the 3-bit Cycle Time field in the configuration register
- Must be in range 0b000 to 0b111
- Default 0b000 is Automatic Mode Disabled
- This value will be used as the default value in later `write_config()` calls

`alert_hold` (int, default 0)
- Value for the Alert Hold field in the configuration register
- Must be 0 or 1
- Default 0 is Alert Hold disabled - alerts will self-clear
- This value will be used as the default value in later `write_config()` calls

`alert_flag_en` (int, default 0)
- Value for the Alert Flag Enable field in the configuration register
- Must be 0 or 1
- Default 0 is Alert Flag disabled - disable alert status bit [D15] in the Conversion Result register
- This value will be used as the default value in later `write_config()` calls

`alert_pin_en` (int, default 0)
- Value for the Alert Pin Enable field in the configuration register
- Must be 0 or 1
- Default 0 is Alert Pin disabled - disable the ALERT output pin
- This value will be used as the default value in later `write_config()` calls
- NOTE:  The Alert Pin function is not tested. (I'm using the ADC121C027 (no alert pin))

`polarity` (int, default 0)
- Value for the alert pin Polarity field in the configuration register
- Must be 0 or 1
- Default 0 - the ALERT pin to active low
- This value will be used as the default value in later `write_config()` calls
- NOTE:  The Alert Pin function is not tested. (I'm using the ADC121C027 (no alert pin))


### Class instance variables
- `device_name` (str)
- `device_addr` (int)
- `Vref` (float)
- `cycle_time` (int)
- `alert_hold` (int)
- `alert_flag_en` (int)
- `alert_pin_en` (int)
- `polarity` (int)


### Behaviors and rules
- Debug logging may be enabled in the tool script code by setting this module's logging level:

        logging.getLogger('cjn_PiTools.ADC121C').setLevel(logging.DEBUG)
"""

    def __init__(self, device_name, device_addr, pi_i2c_bus_handle, Vref, config_byte=None,
                 cycle_time=0b000, alert_hold=0, alert_flag_en=0, alert_pin_en=0, polarity=0):
                # default All disabled:  Auto conversion mode, Alert Hold, Alert Flag, Alert Pin

        self.device_name =          device_name
        self.device_addr =          device_addr
        self.pi_i2c_bus_handle =    pi_i2c_bus_handle
        self.Vref =                 Vref
        self.cycle_time =           cycle_time
        self.alert_hold =           alert_hold
        self.alert_flag_en =        alert_flag_en
        self.alert_pin_en =         alert_pin_en
        self.polarity =             polarity

        self.conv_rslt_reg_addressed = False
        # self.ntrys =                ntrys
        # self.retry_wait =           retry_wait

        if self.device_addr not in ADC121_ADDRS:
            xx = ", ".join(f"0x{v:02x}" for v in ADC121_ADDRS)
            yy = f"0x{device_addr:0>2x}"  if isinstance(device_addr, int)  else device_addr
            raise ValueError (f"ADC121C device address must be one of <{xx}>.  Received <{yy}>")
        ADC121C.write_config(self, config_byte, cycle_time, alert_hold, alert_flag_en, alert_pin_en, polarity)        # Use base class implementation when this class is inherited

        api = 'smbus'  if self.pi_i2c_bus_handle.api == 'smbus'  else 'pigpio'
        adc121c_logger.debug (f"<{self.device_name}> New ADC121C device defined at addr <0x{self.device_addr:0>2x}> using api <{api}> on i2c bus <{self.pi_i2c_bus_handle.i2c_bus_num}>")


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ c o n v e r s i o n _ r e s u l t
    #=====================================================================================
    #=====================================================================================

    def read_conversion_result(self):
        """
## read_conversion_result () - Return the measured voltage

***ADC121C class member function***


### Args TODO
`tempunits` (str, default 'C')
- Must be 'C', 'F' or 'K', else ValueError is raised.


### Returns
- Tuple (Alert Flag bit, Measured Voltage)
- Tuple (I2C_ERROR, I2C_ERROR) on any communication errors
- Raises `ValueError` if tempunits is not valid  TODO


### Behaviors and rules
- The 12-bit code read from the device is scaled by Vref and returned as the measured voltage
- Setting the register Address Pointer to the Conversion Result register is skipped on consecutive calls
to `read_conversion_result()`
"""
        # returns tuple (alert_flag, conv_result)
        adc121c_logger.debug (f"<{self.device_name}> ***** read_conversion_result()")

        try:
            if not self.conv_rslt_reg_addressed:
                self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [CONVERSION_RSLT_REG_PTR])
                self.conv_rslt_reg_addressed = True
            (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 2)
            conv_result = (((data[0] & 0x0f) << 8) | (data[1] & 0xff)) / 4096 * self.Vref
            alert_flag = 1  if data[0] & 0x80  else 0
            adc121c_logger.debug (f"Conversion result <{self.device_name}>:  (0x{data[0]:0>2x} 0x{data[1]:0>2x}) = <{conv_result:5.3f}V>, Alert flag <{alert_flag}>")
            return alert_flag, conv_result

        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR, I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ a l e r t _ s t a t u s
    #=====================================================================================
    #=====================================================================================

    def read_alert_status(self):
        """
## read_alert_status () - Return Over-range and Under-range alerts 

***ADC121C class member function***


### Returns
- Tuple (over_range_alert, under_range_alert) as integers (0 or 1)
- 1 indicates respective over-range or under-range altert
- Tuple (I2C_ERROR, I2C_ERROR) on any communication errors
"""
        # returns tuple (over_range_alert, under_range_alert)
        adc121c_logger.debug (f"<{self.device_name}> ***** read_alert_status()")

        try:
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [ALERT_STATUS_REG_PTR])
            self.conv_rslt_reg_addressed = False
            alert_status_reg_value = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 1)[1][0]

            over_range_alert =      (alert_status_reg_value & 0b00000010) >> 1
            under_range_alert =     alert_status_reg_value & 0b00000001
            adc121c_logger.debug (f"over_range_alert: <{over_range_alert}>, under_range_alert: <{under_range_alert}>")
            return over_range_alert, under_range_alert

        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR, I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  w r i t e _ a l e r t _ s t a t u s
    #=====================================================================================
    #=====================================================================================

    def write_alert_status(self, clear_over=0, clear_under=0):
        """
## write_alert_status (clear_over=0, clear_under=0) - Selectively clear the Over-range and Under-range alert flags

***ADC121C class member function***

### Args
`clear_over` (int, default 0)
- Must be 0 or 1
- If 1, clear the Over Range Alert Flag

`clear_under` (int, default 0)
- Must be 0 or 1
- If 1, clear the Under Range Alert Flag


### Returns
- 0 on success
- I2C_ERROR on any communication errors
"""
        if clear_over not in [0, 1]  or  clear_under not in [0, 1]:
            raise ValueError (f"clear_over and clear_under must be ints 0 or 1 - received <{clear_over}, {clear_under}>")

        try:
            write_byte = clear_over << 1  |  clear_under
            adc121c_logger.debug (f"<{self.device_name}> ***** write_alert_status() <0b{write_byte:0>8b}>")
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [ALERT_STATUS_REG_PTR, write_byte])
            self.conv_rslt_reg_addressed = False
            return 0

        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  w r i t e _ c o n f i g
    #=====================================================================================
    #=====================================================================================

    def write_config(self, config_byte=None, cycle_time=None, alert_hold=None, alert_flag_en=None, alert_pin_en=None, polarity=None):

        if config_byte:
            if not isinstance(config_byte, int)  or  config_byte < 0x00  or config_byte > 0xff:
                raise ValueError (f"config_byte must be int between 0x00 and 0xff - received <{config_byte}>")
            config_reg_value = config_byte
        else:
            config_reg_value = 0x00

            _cycle_time = cycle_time  if cycle_time is not None  else self.cycle_time
            if not isinstance(_cycle_time, int)  or  _cycle_time < 0b000  or _cycle_time > 0b111:
                raise ValueError (f"cycle_time must be int between 0b000 and 0b111 - received <{_cycle_time}>")
            config_reg_value |= _cycle_time << 5

            _alert_hold = alert_hold  if alert_hold is not None  else self.alert_hold
            if _alert_hold not in [0, 1]:
                raise ValueError (f"alert_hold must be int 0 or 1 - received <{_alert_hold}>")
            config_reg_value |= _alert_hold << 4

            _alert_flag_en = alert_flag_en  if alert_flag_en is not None  else self.alert_flag_en
            if _alert_flag_en not in [0, 1]:
                raise ValueError (f"alert_flag_en must be int 0 or 1 - received <{_alert_flag_en}>")
            config_reg_value |= _alert_flag_en << 3

            _alert_pin_en = alert_pin_en  if alert_pin_en is not None  else self.alert_pin_en
            if _alert_pin_en not in [0, 1]:
                raise ValueError (f"alert_pin_en must be int 0 or 1 - received <{_alert_pin_en}>")
            config_reg_value |= _alert_pin_en << 2

            _polarity = polarity  if polarity is not None  else self.polarity
            if _polarity not in [0, 1]:
                raise ValueError (f"polarity must be int 0 or 1 - received <{_polarity}>")
            config_reg_value |= _polarity

        adc121c_logger.debug (f"<{self.device_name}> ***** write_config() <0b{config_reg_value:0>8b}>")


        try:
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [CONFIG_REG_PTR, config_reg_value])
            self.conv_rslt_reg_addressed = False
        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR

        return 0


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ c o n f i g
    #=====================================================================================
    #=====================================================================================

    def read_config(self):
        # Returns config reg byte
        adc121c_logger.debug (f"<{self.device_name}> ***** read_config()")

        try:
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [CONFIG_REG_PTR])
            self.conv_rslt_reg_addressed = False
            config_reg_value = self.pi_i2c_bus_handle.i2c_read_device (self.device_addr, 1)[1][0]
                # i2c_read_device returns tuple (num_returned_bytes (1), [one_byte])
                # get the one_byte, which is config register value
        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR

        if adc121c_logger.isEnabledFor(logging.DEBUG):
            cycle_time_value =      config_reg_value >> 5
            alert_hold_value =      (config_reg_value & 0b00010000) >> 4
            alert_flag_en_value =   (config_reg_value & 0b00001000) >> 3
            alert_pin_en_value =    (config_reg_value & 0b00000100) >> 2
            polarity_value =        config_reg_value & 0b00000001

            xx = f"<{self.device_name}> configuration register <0b{config_reg_value:0>8b}> settings:\n"
            xx += f"  cycle_time:     <0b{cycle_time_value:0>3b}>\n"
            xx += f"  alert_hold:     <{alert_hold_value}>\n"
            xx += f"  alert_flag_en:  <{alert_flag_en_value}>\n"
            xx += f"  alert_pin_en:   <{alert_pin_en_value}>\n"
            xx += f"  polarity:       <{polarity_value}>"
            adc121c_logger.debug (xx)

        return config_reg_value


    #=====================================================================================
    #=====================================================================================
    #  w r i t e _ v l o w _ a l e r t _ l i m i t
    #=====================================================================================
    #=====================================================================================

    def write_vlow_alert_limit(self, vlow):
        # returns 0 on success, or I2C_ERROR

        if not isinstance(vlow, (int, float))  or  vlow < 0.0  or  vlow > self.Vref:
            raise ValueError (f"vlow out of range 0.0V to VRef ({self.Vref:5.3f}) - received <{vlow}>")
        vlow_reg_value = int(vlow / self.Vref * 4096)
        msB = (vlow_reg_value & 0x0F00) >> 8
        lsB = (vlow_reg_value & 0x00FF)
        try:
            adc121c_logger.debug (f"<{self.device_name}> ***** write_vlow_alert_limit() <{vlow:5.3f}V>  <[ 0x{msB:0>2x} 0x{lsB:0>2x} ]>")
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [LOW_LIMIT_REG_PTR, msB, lsB])
            self.conv_rslt_reg_addressed = False
            return 0

        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ v l o w _ a l e r t _ l i m i t
    #=====================================================================================
    #=====================================================================================

    def read_vlow_alert_limit(self):
        # returns float vlow limit value voltage
        adc121c_logger.debug (f"<{self.device_name}> ***** read_vlow_alert_limit()")

        try:
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [LOW_LIMIT_REG_PTR])
            self.conv_rslt_reg_addressed = False
            (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 2)
            vlow_limit_value = (((data[0] & 0x0f) << 8) | (data[1] & 0xff)) / 4096 * self.Vref
            adc121c_logger.debug (f"VLow limit <{self.device_name}>:  (0x{data[0]:0>2x} 0x{data[1]:0>2x}) = <{vlow_limit_value:5.3f}V>")
            return vlow_limit_value

        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  w r i t e _ v h i g h _ a l e r t _ l i m i t
    #=====================================================================================
    #=====================================================================================

    def write_vhigh_alert_limit(self, vhigh):
        # returns 0 on success, or I2C_ERROR

        if not isinstance(vhigh, (int, float))  or  vhigh < 0.0  or  vhigh > self.Vref:
            raise ValueError (f"vhigh out of range 0.0V to VRef ({self.Vref:5.3f}) - received <{vhigh}>")
        vhigh_reg_value = int((vhigh - 0.001) / self.Vref * 4096)   # Avoid vhigh=Vref resulting in 0x0000
        msB = (vhigh_reg_value & 0x0F00) >> 8
        lsB = (vhigh_reg_value & 0x00FF)
        try:
            adc121c_logger.debug (f"<{self.device_name}> ***** write_vhigh_alert_limit() <{vhigh:5.3f}V>  <[ 0x{msB:0>2x} 0x{lsB:0>2x} ]>")
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [HIGH_LIMIT_REG_PTR, msB, lsB])
            self.conv_rslt_reg_addressed = False
            return 0

        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ v h i g h _ a l e r t _ l i m i t
    #=====================================================================================
    #=====================================================================================

    def read_vhigh_alert_limit(self):
        # returns float vhigh limit value voltage
        adc121c_logger.debug (f"<{self.device_name}> ***** read_vhigh_alert_limit()")

        try:
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [HIGH_LIMIT_REG_PTR])
            self.conv_rslt_reg_addressed = False
            (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 2)
            vhigh_limit_value = (((data[0] & 0x0f) << 8) | (data[1] & 0xff)) / 4096 * self.Vref
            adc121c_logger.debug (f"VHigh limit <{self.device_name}>:  (0x{data[0]:0>2x} 0x{data[1]:0>2x}) = <{vhigh_limit_value:5.3f}V>")
            return vhigh_limit_value

        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  w r i t e _ a l e r t _ h y s t e r e s i s
    #=====================================================================================
    #=====================================================================================

    def write_alert_hysteresis(self, vhyst):
        # returns 0 on success, or I2C_ERROR

        if not isinstance(vhyst, (int, float))  or  vhyst < 0.0  or  vhyst > self.Vref:
            raise ValueError (f"vhyst out of range 0.0V to VRef ({self.Vref:5.3f}) - received <{vhyst}>")
        vhyst_reg_value = int(vhyst / self.Vref * 4096)
        msB = (vhyst_reg_value & 0x0F00) >> 8
        lsB = (vhyst_reg_value & 0x00FF)
        try:
            adc121c_logger.debug (f"<{self.device_name}> ***** write_alert_hysteresis() <{vhyst:5.3f}V>  <[ 0x{msB:0>2x} 0x{lsB:0>2x} ]>")
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [HYSTERESIS_REG_PTR, msB, lsB])
            self.conv_rslt_reg_addressed = False
            return 0

        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ a l e r t _ h y s t e r e s i s
    #=====================================================================================
    #=====================================================================================

    def read_alert_hysteresis(self):
        # returns float vhyst limit value voltage
        adc121c_logger.debug (f"<{self.device_name}> ***** read_alert_hysteresis()")

        try:
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [HYSTERESIS_REG_PTR])
            self.conv_rslt_reg_addressed = False
            (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 2)
            vhyst_value = (((data[0] & 0x0f) << 8) | (data[1] & 0xff)) / 4096 * self.Vref
            adc121c_logger.debug (f"vhyst value <{self.device_name}>:  (0x{data[0]:0>2x} 0x{data[1]:0>2x}) = <{vhyst_value:5.3f}V>")
            return vhyst_value

        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  w r i t e _ l o w e s t _ c o n v e r s i o n
    #=====================================================================================
    #=====================================================================================

    def write_lowest_conversion(self):
        # returns 0 on success, or I2C_ERROR
        # A write to this register sets the reg to 0x0FFF (Vref)

        msB = 0x0f
        lsB = 0xff
        try:
            adc121c_logger.debug (f"<{self.device_name}> ***** write_lowest_conversion() <{self.Vref:5.3f}V>  <[ 0x{msB:0>2x} 0x{lsB:0>2x} ]>")
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [LOWEST_CONVERSION_REG_PTR, msB, lsB])
            self.conv_rslt_reg_addressed = False
            return 0

        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ l o w e s t _ c o n v e r s i o n
    #=====================================================================================
    #=====================================================================================

    def read_lowest_conversion(self):
        # returns float vmin lowest conversion voltage
        # only valid when Automatic Conversion mode is active.
        # Reads after Automatic Conversion is stopped may show errant low voltage, e.g., 0V, while highest conversion capture remains correct
        # Seems incorrect:  The value of this register will update
        # automatically when the automatic conversion mode is enabled, but is NOT updated in the normal mode.
        adc121c_logger.debug (f"<{self.device_name}> ***** read_lowest_conversion()")

        try:
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [LOWEST_CONVERSION_REG_PTR])
            self.conv_rslt_reg_addressed = False
            (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 2)
            vmin_value = (((data[0] & 0x0f) << 8) | (data[1] & 0xff)) / 4096 * self.Vref
            adc121c_logger.debug (f"vmin value <{self.device_name}>:  (0x{data[0]:0>2x} 0x{data[1]:0>2x}) = <{vmin_value:5.3f}V>")
            return vmin_value

        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  w r i t e _ h i g h e s t _ c o n v e r s i o n
    #=====================================================================================
    #=====================================================================================

    def write_highest_conversion(self): #, vset=None):
        # returns 0 on success, or I2C_ERROR
        # A write to this register sets the reg to 0x0000 (0V)

        msB = 0x00
        lsB = 0x00
        try:
            adc121c_logger.debug (f"<{self.device_name}> ***** write_highest_conversion() <0.000V>  <[ 0x{msB:0>2x} 0x{lsB:0>2x} ]>")
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [HIGHEST_CONVERSION_REG_PTR, msB, lsB])
            self.conv_rslt_reg_addressed = False
            return 0

        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR


    #=====================================================================================
    #=====================================================================================
    #  r e a d _ h i g h e s t _ c o n v e r s i o n
    #=====================================================================================
    #=====================================================================================

    def read_highest_conversion(self):
        # returns float vmin lowest conversion voltage
        # only valid when Automatic Conversion mode is active.  Reads 
        adc121c_logger.debug (f"<{self.device_name}> ***** read_highest_conversion()")

        try:
            self.pi_i2c_bus_handle.i2c_write_device (self.device_addr, [HIGHEST_CONVERSION_REG_PTR])
            self.conv_rslt_reg_addressed = False
            (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 2)
            vmax_value = (((data[0] & 0x0f) << 8) | (data[1] & 0xff)) / 4096 * self.Vref
            adc121c_logger.debug (f"vmax value <{self.device_name}>:  (0x{data[0]:0>2x} 0x{data[1]:0>2x}) = <{vmax_value:5.3f}V>")
            return vmax_value

        except Exception as e:
            adc121c_logger.debug (f"<{self.device_name}> exception:  {type(e).__name__}: {e}")
            return I2C_ERROR



    # def read(self):
    #     for trynum in range(self.ntrys):
    #         try:
    #             (count, data) = self.pi_i2c_bus_handle.i2c_read_device(self.device_addr, 2)
    #             rslt = (((data[0] & 0x0f) << 8) | (data[1] & 0xff)) / 4096 * self.Vref
    #             adc121c_logger.debug (f"Conversion result <{self.device_name}>:  (0x{data[0]:0>2x} 0x{data[1]:0>2x}) = {rslt:5.3f} V")
    #             return rslt
    #         except:
    #             adc121c_logger.debug (f"Read  try# {trynum} FAILED <{self.device_name}>")
    #         if trynum < self.ntrys - 1:
    #             time.sleep(self.retry_wait)
    #         else:
    #             adc121c_logger.warning (f"Read  FAILED <{self.device_name}>")
    #             return I2C_ERROR


