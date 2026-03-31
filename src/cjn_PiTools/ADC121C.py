#!/usr/bin/env python3
"""ADC121C* 12-bit ADC library for Raspberry Pi
"""

#==========================================================
#
#  Chris Nelson, Copyright 2026
#
#==========================================================

import logging
from .shared import I2C_ERROR


# Configs / Constants
CONVERSION_RSLT_REG_PTR =       0x00
ALERT_STATUS_REG_PTR =          0X01
CONFIG_REG_PTR =                0x02
LOW_LIMIT_REG_PTR =             0x03
HIGH_LIMIT_REG_PTR =            0x04
HYSTERESIS_REG_PTR =            0x05
LOWEST_CONVERSION_REG_PTR =     0x06
HIGHEST_CONVERSION_REG_PTR =    0x07

ADC121_ADDRS =                  [0x50, 0x51, 0x52, 0x54, 0x55, 0x56, 0x58, 0x59, 0x5a]

adc121c_logger =                logging.getLogger('cjn_PiTools.ADC121C')


# ADC121C I2C operation:
#     The first data byte of every write operation is stored in the address pointer register.
#     This value selects the register that the following data byte(s) will be written to or read from.
#     Write a register send sequence:
#       1) ADC address, write Address Pointer Register byte, write 1 or 2 bytes of target register data (same sequence)
#     Read a register send sequence:
#       1) ADC address, write Address Pointer Register byte
#       2) ADC address, read 1 or 2 byte register data
#       If the Address Pointer is preset to the desired register, a read operation can occur without first writing 
#       the Address Pointer Register (skip step 1)


#=====================================================================================
#=====================================================================================
#  C l a s s   A D C 1 2 1 C
#=====================================================================================
#=====================================================================================

class ADC121C:
    """
## Class ADC121C (device_name, device_addr, pi_i2c_bus_handle, Vref, config_byte=None, cycle_time=0b000, alert_hold=0, alert_flag_en=0, alert_pin_en=0, polarity=0) - ADC121C* 12-bit ADC library for Raspberry Pi

Create an ADC121C family device instance

### Args
`device_name` (str)
- User defined name for this instance, e.g., 'My_ADC121C'

`device_addr` (int)
- I2C bus address for this instance, e.g., 0x50
- Allowed addresses: [0x50, 0x51, 0x52, 0x54, 0x55, 0x56, 0x58, 0x59, 0x5a]

`pi_i2c_bus_handle` (cjn_PiTools.shared.pi_i2c instance)
- Get a `pi_i2c` instance handle in the tools script code and pass it to this device instantiation

`Vref` (float)
- ADC reference (and supply) voltage
- `read_conversion_result()`'s returned 12-bit code is scaled by this value to return the measured voltage

`config_byte` (int, default None)
- If `config_byte` is an int:
  - Explicitly set the configuration register to the `config_byte` value during instantiation
  - Must be in range 0x00 to 0xFF
  - Bit 1 (Reserved) is always forced to `0`, per the specification
  - The field values within the `config_byte` are saved to the respective class instance variables, and used as the default
  values in later `write_config()` calls
  - `config_byte` takes precedent over the following individual field settings, if both are given at instantiation
- If `config_byte` is None then the following individual field settings are used

`cycle_time` (int, default 0b000)
- Value for the 3-bit Cycle Time field in the configuration register
- Must be in range 0b000 to 0b111
- Default 0b000 is Normal Mode (automatic conversion mode disabled)
- This value (or the field bits within `config_byte`, if specified) is used as the default value in later `write_config()` calls

`alert_hold` (int, default 0)
- Value for the Alert Hold field in the configuration register
- Must be 0 or 1
- Default 0 is Alert Hold disabled - alerts will self-clear
- This value (or the field bit within `config_byte`, if specified) is used as the default value in later `write_config()` calls

`alert_flag_en` (int, default 0)
- Value for the Alert Flag Enable field in the configuration register
- Must be 0 or 1
- Default 0 is Alert Flag disabled - disable alert status bit [D15] in the Conversion Result register
- This value (or the field bit within `config_byte`, if specified) is used as the default value in later `write_config()` calls

`alert_pin_en` (int, default 0)
- Value for the Alert Pin Enable field in the configuration register
- Must be 0 or 1
- Default 0 is Alert Pin disabled - disable the ALERT output pin
- This value (or the field bit within `config_byte`, if specified) is used as the default value in later `write_config()` calls
- NOTE:  The Alert Pin function is not tested - I'm using the ADC121C027 (no alert pin)

`polarity` (int, default 0)
- Value for the alert pin Polarity field in the configuration register
- Must be 0 or 1
- Default 0 - the ALERT pin is active low
- This value (or the field bit within `config_byte`, if specified) is used as the default value in later `write_config()` calls
- NOTE:  The Alert Pin function is not tested. (I'm using the ADC121C027 (no alert pin))


### Returns
- Handle to the ADC121C instance on success
- Raises ValueError if args checks fail


### Class instance variables - as passed in at instantiation
- `device_name` (str)
- `device_addr` (int)
- `Vref` (float)
- `cycle_time` (int)
- `alert_hold` (int)
- `alert_flag_en` (int)
- `alert_pin_en` (int)
- `polarity` (int)


### Behaviors and rules
- All configuration register fields default to `0`:
  - `cycle_time` defaults to 0b000 - Normal mode (automatic conversion mode disabled)
  - `alert_hold`, `alert_flag_en`, and `alert_pin_en` each default to 0 - Disabled
  - `polarity` defaults to 0 - the alert pin is active low if `alert_pin_en` is set to 1
- Debug logging may be enabled in the tool script code by setting this module's logging level:

        logging.getLogger('cjn_PiTools.ADC121C').setLevel(logging.DEBUG)
"""

    def __init__(self, device_name, device_addr, pi_i2c_bus_handle, Vref, config_byte=None,
                 cycle_time=0b000, alert_hold=0, alert_flag_en=0, alert_pin_en=0, polarity=0):

        self.device_name =          device_name
        self.device_addr =          device_addr
        self.pi_i2c_bus_handle =    pi_i2c_bus_handle
        self.Vref =                 Vref
        self.cycle_time =           cycle_time
        self.alert_hold =           alert_hold
        self.alert_flag_en =        alert_flag_en
        self.alert_pin_en =         alert_pin_en
        self.polarity =             polarity

        if not isinstance(device_name, str):
            raise ValueError (f"ADC121C device_name must be str - received <{device_name}>")

        if self.device_addr not in ADC121_ADDRS:
            xx = ", ".join(f"0x{v:02x}" for v in ADC121_ADDRS)
            yy = f"0x{device_addr:0>2x}"  if isinstance(device_addr, int)  else device_addr
            raise ValueError (f"<{self.device_name}> device address must be one of <{xx}> - received <{yy}>")

        if config_byte:
            if  not isinstance(config_byte, int)  or  config_byte < 0x00  or  config_byte > 0xFF:
                raise ValueError (f"<{self.device_name}> config_byte must be int in range 0x00 to 0xFF - received <{config_byte}>")
            self.cycle_time, self.alert_hold, self.alert_flag_en, self.alert_pin_en, self.polarity = decode_config_byte(config_byte)

        self.conv_rslt_reg_addressed = False    # Flag indicating that the conv_rslt_reg was last accessed, so skip setting the address pointer

        ADC121C.write_config(self,                              # Use base class implementation when this class is inherited
                             config_byte=   None,
                             cycle_time=    self.cycle_time,
                             alert_hold=    self.alert_hold,
                             alert_flag_en= self.alert_flag_en,
                             alert_pin_en=  self.alert_pin_en,
                             polarity=      self.polarity)

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


### Returns
- Tuple (Alert Flag bit, Measured Voltage (float))
- Tuple (I2C_ERROR, I2C_ERROR) on I2C IO error

### Behaviors and rules
- The 12-bit code read from the device is scaled by Vref and returned as the measured voltage
- Setting the register Address Pointer to the Conversion Result register is skipped on consecutive calls
to `read_conversion_result()`
"""
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
- 1 indicates respective over-range or under-range alert
- Tuple (I2C_ERROR, I2C_ERROR) on I2C IO error
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
- I2C_ERROR on I2C IO error
- Raises ValueError if args checks fail
"""
        if clear_over not in [0, 1]  or  clear_under not in [0, 1]:
            raise ValueError (f"<{self.device_name}> clear_over and clear_under must be ints 0 or 1 - received <{clear_over}, {clear_under}>")

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
        """
## write_config (config_byte=None, cycle_time=None, alert_hold=None, alert_flag_en=None, alert_pin_en=None, polarity=None) - Set operating modes

***ADC121C class member function***

The config register may be written entirely using `config_byte` or by individual field settings,
with their default values set at instantiation


### Args
`config_byte` (int, default None)
- If `config_byte` is an int:
  - Explicitly set the configuration register to the `config_byte` value
  - Must be in range 0x00 to 0xFF
  - Bit 1 (Reserved) is always forced to `0`, per the specification
  - The entire configuration register byte is written using this value, and the following args are ignored
- If `config_byte` is None then the following individual field settings are used

`cycle_time` (int, default None)
- Value for the 3-bit Cycle Time field in the configuration register
- If an int (and `config_byte` is None) then the 3-bit Cycle Time field is set to this value - must be in range 0b000 to 0b111
- If None (and `config_byte` is None), then the default value set at instantiation is used

`alert_hold` (int, default None)
- Value for the Alert Hold field in the configuration register
- If an int (and `config_byte` is None) then the field is set to this value - must be 0 or 1
- If None (and `config_byte` is None), then the default value set at instantiation is used

`alert_flag_en` (int, default None)
- Value for the Alert Flag Enable field in the configuration register
- If an int (and `config_byte` is None) then the field is set to this value - must be 0 or 1
- If None (and `config_byte` is None), then the default value set at instantiation is used

`alert_pin_en` (int, default None)
- Value for the Alert Pin Enable field in the configuration register
- If an int (and `config_byte` is None) then the field is set to this value - must be 0 or 1
- If None (and `config_byte` is None), then the default value set at instantiation is used

`polarity` (int, default None)
- Value for the Polarity field in the configuration register
- If an int (and `config_byte` is None) then the field is set to this value - must be 0 or 1
- If None (and `config_byte` is None), then the default value set at instantiation is used


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
- Raises ValueError if args checks fail


### Behaviors and rules
- If `config_byte` is an int (not None), then the configuration register will be written with this value.  This 
feature gives the tool script explicit control over the configuration register.
- If `config_byte` is None then the individual field args passed in on this call are overlaid on the field value defaults established at instantiation
to construct the configuration byte.  For example:
  - At instantiation, `cycle_time=0b100`, `alert_flag_en=1`, `alert_pin_en=1` and other fields default to 0
  - On this call, `cycle_time=0b001`, `alert_hold=1`, `alert_pin_en=0`, and `polarity=1`
  - The resultant configuration byte is 0b00111001 - `cycle_time=0b001`, `alert_hold=1`, `alert_flag_en=1`, `alert_pin_en=0`, and `polarity=1`
"""

        if config_byte:
            if not isinstance(config_byte, int)  or  config_byte < 0x00  or config_byte > 0xff:
                raise ValueError (f"<{self.device_name}> config_byte must be int between 0x00 and 0xff - received <{config_byte}>")
            config_reg_value = config_byte & 0b11111101     # Bit 1 must be 0
        else:
            config_reg_value = 0x00

            _cycle_time = cycle_time  if cycle_time is not None  else self.cycle_time
            if not isinstance(_cycle_time, int)  or  _cycle_time < 0b000  or _cycle_time > 0b111:
                raise ValueError (f"<{self.device_name}> cycle_time must be int between 0b000 and 0b111 - received <{_cycle_time}>")
            config_reg_value |= _cycle_time << 5

            _alert_hold = alert_hold  if alert_hold is not None  else self.alert_hold
            if _alert_hold not in [0, 1]:
                raise ValueError (f"<{self.device_name}> alert_hold must be int 0 or 1 - received <{_alert_hold}>")
            config_reg_value |= _alert_hold << 4

            _alert_flag_en = alert_flag_en  if alert_flag_en is not None  else self.alert_flag_en
            if _alert_flag_en not in [0, 1]:
                raise ValueError (f"<{self.device_name}> alert_flag_en must be int 0 or 1 - received <{_alert_flag_en}>")
            config_reg_value |= _alert_flag_en << 3

            _alert_pin_en = alert_pin_en  if alert_pin_en is not None  else self.alert_pin_en
            if _alert_pin_en not in [0, 1]:
                raise ValueError (f"<{self.device_name}> alert_pin_en must be int 0 or 1 - received <{_alert_pin_en}>")
            config_reg_value |= _alert_pin_en << 2

            _polarity = polarity  if polarity is not None  else self.polarity
            if _polarity not in [0, 1]:
                raise ValueError (f"<{self.device_name}> polarity must be int 0 or 1 - received <{_polarity}>")
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
        """
## read_config () - Return the contents of the configuration register 

***ADC121C class member function***


### Returns
- Configuration register byte on success
- I2C_ERROR on I2C IO error



### Behaviors and rules
- If debug logging is enabled for this module then the configuration register value is decoded, e.g.,

        ADC121C.read_config     -    DEBUG:  <ADC_xx> configuration register <0b00111000> settings:
        cycle_time:     <0b001>
        alert_hold:     <1>
        alert_flag_en:  <1>
        alert_pin_en:   <0>
        polarity:       <0>
"""
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
            ct, ah, af_en, ap_en, pol = decode_config_byte(config_reg_value)

            xx = f"<{self.device_name}> configuration register <0b{config_reg_value:0>8b}> settings:\n"
            xx += f"  cycle_time:     <0b{ct:0>3b}>\n"
            xx += f"  alert_hold:     <{ah}>\n"
            xx += f"  alert_flag_en:  <{af_en}>\n"
            xx += f"  alert_pin_en:   <{ap_en}>\n"
            xx += f"  polarity:       <{pol}>"
            adc121c_logger.debug (xx)

        return config_reg_value


    #=====================================================================================
    #=====================================================================================
    #  w r i t e _ v l o w _ a l e r t _ l i m i t
    #=====================================================================================
    #=====================================================================================

    def write_vlow_alert_limit(self, vlow):
        """
## write_vlow_alert_limit (vlow) - Set the Vlow alert register voltage level

***ADC121C class member function***


### Arg
`vlow` (float or int)
- Allowed range 0 to Vref (no 'V' units)


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
- Raises ValueError if arg checks fail
"""
        # returns 0 on success, or I2C_ERROR

        if not isinstance(vlow, (int, float))  or  vlow < 0.0  or  vlow > self.Vref:
            raise ValueError (f"<{self.device_name}> vlow out of range 0.0V to VRef ({self.Vref:5.3f}) - received <{vlow}>")
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
        """
## read_vlow_alert_limit () - Return the Vlow alert register voltage level

***ADC121C class member function***

The register value is converted to a voltage based on Vref


### Returns
- Vlow alert level voltage (float) on success
- I2C_ERROR on I2C IO error
"""
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
        """
## write_vhigh_alert_limit (vhigh) - Set the Vhigh alert register voltage level

***ADC121C class member function***


### Arg
`vhigh` (float or int)
- Allowed range 0 to Vref (no 'V' units)


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
- Raises ValueError if arg checks fail
"""
        if not isinstance(vhigh, (int, float))  or  vhigh < 0.0  or  vhigh > self.Vref:
            raise ValueError (f"<{self.device_name}> vhigh out of range 0.0V to VRef ({self.Vref:5.3f}) - received <{vhigh}>")
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
        """
## read_vhigh_alert_limit () - Return the Vhigh alert register voltage level

***ADC121C class member function***

The register value is converted to a voltage based on Vref


### Returns
- Vhigh alert level voltage (float) on success
- I2C_ERROR on I2C IO error
"""
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
        """
## write_alert_hysteresis (vhyst) - Set the Vhyst alert register voltage level

***ADC121C class member function***


### Arg
`vhyst` (float or int)
- Allowed range 0 to Vref (no 'V' units)


### Returns
- 0 on success
- I2C_ERROR on I2C IO error
- Raises ValueError if arg checks fail
"""
        if not isinstance(vhyst, (int, float))  or  vhyst < 0.0  or  vhyst > self.Vref:
            raise ValueError (f"<{self.device_name}> vhyst out of range 0.0V to VRef ({self.Vref:5.3f}) - received <{vhyst}>")
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
        """
## read_alert_hysteresis () - Return the Vhyst alert register voltage level

***ADC121C class member function***

The register value is converted to a voltage based on Vref


### Returns
- Vhyst alert level voltage on success
- I2C_ERROR on I2C IO error
"""
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
        """
## write_lowest_conversion () - Reset the lowest conversion capture register

***ADC121C class member function***

The reset state is 0x0FFF (maximum count value, effectively Vref).


### Returns
- 0 on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- See notes on `read_lowest_conversion()`
"""
        msB = 0x0f          # It doesn't seem to matter what value is written to the register.  A write results in register value 0x0FFF.
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
        """
## read_lowest_conversion () - Return the lowest conversion register voltage level

***ADC121C class member function***

The register value is converted to a voltage based on Vref


### Returns
- The lowest measured/captured voltage (float) on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- The datasheet says that the capture lowest/highest conversion results only works with Automatic Conversion modes (Cycle Time codes 0b001 thru 0b111).
I find that the capture lowest/highest feature also works in Normal mode (Cycle Time code 0b000).
- If switching from an Automatic Conversion mode to Normal mode note that the lowest conversion register may capture code 0x0000 (0.0V).
If using the capture lowest/highest conversion feature it is best to read these registers before stopping the Automatic Conversion
mode (switching to Normal mode).
"""
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

    def write_highest_conversion(self):
        """
## write_highest_conversion () - Reset the highest conversion capture register

***ADC121C class member function***

The reset state is 0x0000 (minimum count value, effectively 0.0V).


### Returns
- 0 on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- See notes on `read_lowest_conversion()`
"""
        msB = 0x00          # It doesn't seem to matter what value is written to the register.  A write results in register value 0x0000.
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
        """
## read_highest_conversion () - Return the highest conversion register voltage level

***ADC121C class member function***

The register value is converted to a voltage based on Vref


### Returns
- The highest measured/captured voltage (float) on success
- I2C_ERROR on I2C IO error


### Behaviors and rules
- See notes on `read_lowest_conversion()`
"""
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

def decode_config_byte (config_byte):
    ct =    config_byte >> 5
    ah =    (config_byte & 0b00010000) >> 4
    af_en = (config_byte & 0b00001000) >> 3
    ap_en = (config_byte & 0b00000100) >> 2
    pol =   config_byte & 0b00000001
    return ct, ah, af_en, ap_en, pol
