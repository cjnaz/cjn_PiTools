# shared library for cjn_PiTools

Skip to [API documentation](#links)

This module contains a collection of classes and functions that are shared across the cjn_PiTools package.  These functions will remain stable and are supported for use in user code.

- The `pi_i2c` class provides a wrapper on top of the smbus and pigpio APIs. These methods should support most any I2C bus transaction needed.  Note that there are redundancies in the underlying apis, so `pi_i2c` offers a trimmed down set of methods.
  - The tool script will create one `pi_i2c` instance, which is an I2C bus handle for a specified bus number and which api to use.

- Temperature related functions: CtoF(), FtoC(), and calculate_dew_point()