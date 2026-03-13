# shared library for cjn_PiTools

Skip to [API documentation](#links)

This module contains a collection of classes and functions that are shared across the cjn_PiTools package.  These functions will remain stable and are supported for use in user code.

- The `pi_i2c` class provides a wrapper on top of the smbus and pigpio APIs. These methods should support most any I2C bus transaction needed.  Note that there are redundancies in the underlying apis, so `pi_i2c` offers a trimmed down set of methods.
  - The tool script will create one `pi_i2c` instance, which is an I2C bus handle for a specified bus number and which api to use.

- Temperature related functions: CtoF(), FtoC(), and calculate_dew_point()


## Testing board configurations

Validation testing is done on a set of boards with the following configuration.  Consider this an FYI.

    Board_1 (connected directly to RPi I2C bus 1)
      PCA9548 address 0x71
          Channel 0:  Connected to Board_2 PCA9548
          Channel 1:  Connected to SHT3x at address 0x44
          Channel 2:  Connected to SHT3x at address 0x45
          Channel 6:  Connected to HTU21D at address 0x40

    Board_2 (connected to Board_1 PCA9548 Channel 0)
      PCA9548 address 0x75
          Channel 0:  Jack I2C1 with SHT3x at address 0x44
          Channel 1:  Jack I2C2
          Channel 2:  Jack I2C3
          Channel 3:  ADC121C ADC1 at address 0x50, Jack SOIL 1
              ADC121C chips use 4.2V reference
          Channel 3:  ADC121C ADC2 at address 0x51, Jack SOIL 2 - ADC test pullup/pulldown ckt
          Channel 4:  MCP23008_IO_ADDR at address 0x70 
              Bit 0: OUT 1
              Bit 1: OUT 2 - ADC test pulldown
              Bit 2: OUT 3 - ADC test pullup
              Bit 3: OUT 4
              Bit 4: S1 input with weak pullup
              Bit 5: S2 input with weak pullup
              Bit 6: S3 input with weak pullup
              Bit 7: NC
          Channel 4:  MCP23008_7SEG_ADDR at address 0x71
              All bits as outputs serving as pulldowns on common anode 7-segment display
              Segment selects in DIG_2_SEG are inverted when written to MCP23008_7SEG_ADDR
          Channel 5:  ADC121C ADC3 at address 0x52, Jack SOIL 3
          Channel 5:  ADC121C ADC4 at address 0x50, Jack SOIL 4
          Channels 6 and 7: No connect


<a id="links"></a>
         
<br>

---

# Links to classes, methods, and functions

- [pi_i2c](#pi_i2c)
- [i2c_write_device](#i2c_write_device)
- [i2c_read_device](#i2c_read_device)
- [i2c_write_byte](#i2c_write_byte)
- [i2c_read_byte](#i2c_read_byte)



<br/>

<a id="pi_i2c"></a>

---

# Class pi_i2c - Support both smbus and pigpio APIs for I2C


### Args
`api` (pigpio handle or str 'smbus')
- pigpio handle is value returned from pigpio.pi()
- If not 'smbus' then `api` is assumed to be a valid pigpio handle (not validity checked)

`i2c_bus_num` (int 0 or 1, default 1)
- Bus 1 is the typical user I2C bus
- Bus 0 is often reserved for comm with HAT boards, but may be used as well
- `i2c_bus_num` is not validity checked


### Returns
- pi_i2c handle associated with I2C comm using the specified api and bus
    
<br/>

<a id="i2c_write_device"></a>

---

# i2c_write_device (addr, bytes_list) - Write a list of bytes to the target

***pi_i2c class member function***


### Args
`addr` (int)
- i2c address of target - range 0x00 to 0x7F
- No validity checks - caller should confirm address validity

`bytes_list` (list of bytes)
- Data to be written to the device
- Minimal data validity checking - some invalid data results in write failure


### Returns
- On success, returns length of `bytes_list` (number of bytes written)
- Raises ValueError if bytes_list is not a list or is an empty list.
- On fail, raises exception (actually raised by `api` call, e.g., I2C IO error, or invalid data in `bytes_list`)


### Behaviors and rules
- Commonly, the first byte in the `bytes_list` is taken as a register address to which the following bytes are written. 
  Note that this behavior is device-type specific.  The contents of `bytes_list` will simply be sent out after 
  the device at `addr` has been addressed for writing.
- Uses pigpio i2c_write_device() and smbus write_i2c_block_data()
- transaction sequence...
        
<br/>

<a id="i2c_read_device"></a>

---

# i2c_read_device (addr, read_byte_count) - Read a number of bytes from the target

***pi_i2c class member function***


### Args
`addr` (int)
- i2c address of target - range 0x00 to 0x7F
- No validity checks - caller should confirm address validity

`read_byte_count` (int)
- Number of bytes to read from the target
- No validity checking


### Returns
- On success, returns tuple (actual read count, [data]).  Note that data is returned as a list of bytes.
- On fail, raises exception (actually raised by `api` call, e.g., I2C IO error, OSError, etc.).
- If using the pigpio api, if the returned byte count is negative this error code is passed within a raised OSError exception.


### Behaviors and rules
- Uses pigpio i2c_read_device() and smbus i2c_msg() / i2c_rdwr
- transaction sequence...
        
<br/>

<a id="i2c_write_byte"></a>

---

# i2c_write_byte (addr, byte_value) - Write one byte to the target

***pi_i2c class member function***


### Args
`addr` (int)
- i2c address of target - range 0x00 to 0x7F
- No validity checks - caller should confirm address validity

`byte_value` (int)
- Data to be written to the device
- The value is check to be an int the range of 0x00 to 0xFF


### Returns
- On success, returns 1 (meaning one byte written)
- Raises ValueError if `byte_value` is not an int in the range of 0x00 to 0xFF
- On fail, raises exception (actually raised by `api` call, e.g., I2C IO error, OSError, etc.).


### Behaviors and rules
- Uses pigpio i2c_write_byte() and smbus write_byte()
- transaction sequence...
        
<br/>

<a id="i2c_read_byte"></a>

---

# i2c_read_byte (addr) - Read one byte from the target

***pi_i2c class member function***


### Args
`addr` (int)
- i2c address of target - range 0x00 to 0x7F
- No validity checks - caller should confirm address validity


### Returns
- On success, returns one byte read from the target
- On fail, raises exception (actually raised by `api` call, e.g., I2C IO error, OSError, etc.).


### Behaviors and rules
- Uses pigpio i2c_read_byte() and smbus read_byte()
- transaction sequence...
        