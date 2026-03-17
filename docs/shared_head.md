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
          Channel 4:  MCP23008_IO_ADDR at address 0x20 
              Bit 0: OUT 1
              Bit 1: OUT 2 - ADC test pulldown
              Bit 2: OUT 3 - ADC test pullup
              Bit 3: OUT 4
              Bit 4: S1 input with weak pullup
              Bit 5: S2 input with weak pullup
              Bit 6: S3 input with weak pullup
              Bit 7: NC
          Channel 4:  MCP23008_7SEG_ADDR at address 0x21
              All bits as outputs serving as pulldowns on common anode 7-segment display
              Segment selects in DIG_2_SEG are inverted when written to MCP23008_7SEG_ADDR
          Channel 5:  ADC121C ADC3 at address 0x52, Jack SOIL 3
          Channel 5:  ADC121C ADC4 at address 0x50, Jack SOIL 4
          Channels 6 and 7: No connect
