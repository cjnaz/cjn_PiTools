# PiBlinky - A threaded, multiple LED driver for Raspberry Pi

Skip to [API documentation](#links)

Why?  To run an LED on a RaspberryPi is done simply by turning a GPIO pin on and off.  Often, that's just fine, but if you want more scheduling capability and features, then this driver may be what you're looking for.

Features

- Multiple concurrent LEDs supported, each with their own independent on/off sequences and timing.
- A flashing sequence can be set once, rather than your main code having to turn the LED on and off on a schedule.
- Supports both RPi.GPIO and pigpio driver libraries.  pigpio supports running LEDs on remote systems.
- LED flashing sequences are completely user defined, including the bit-sequence, bit-time, and number of times to repeat (or indefinitely).
- Advanced features include saving the currently running sequence, then applying a new sequence, and later restoring the saved sequence.  Useful if two different operations need to share an LED.
- Setup and usage in your code is simple.  No external dependencies, other than the RPi.GPIO or pigpio driver.

For example, one of my apps flashes a yellow LED for 50ms once per loop of the measurement thread (1s loop time) to indicate that the thread is still alive, flashes a blue LED 0.5s on / 0.5s off continuously while watering is running, and turns a red LED on solid if there are any detected problems, or on exit of the app.  Normally, I should see the yellow LED flash once per seconds, see the blue LED flash while watering, and never see the red LED.

<br>

## Command interface

Commands to a PiBlinky instance are passed (as a list) thru a queue to the thread managing the given LED - one thread and queue per LED.  See the API documentation, below, for details of the command structure.

<br/>

## Usage example

The LED is connected from GPIO pin 4 to ground through an appropriate current limiting resistor. When the output is high the LED is on.

```
#!/usr/bin/env python3
# PiBlinky_README_ex.py available in the docs directory in the github repo

# Set up a PiBlinky instance
from cjn_PiTools.PiBlinky import PiBlinky, CMD_EXIT, CMD_SAVE, CMD_RESTORE
import queue
import time

BLU_LED_GPIO    = 4
BLU_LED_q       = queue.Queue()
BLU_LED_inst    = PiBlinky("BLU", 'GPIO', BLU_LED_GPIO, BLU_LED_q)
BLU_LED_th      = BLU_LED_inst.start()

print ("Produce the bit stream <1000> with a period of 50ms for each bit, repeated 3 times")
BLU_LED_q.put ([50, "1000", 3])                 # Conclude with the LED off.
time.sleep (2)

# Save a blink pattern, apply a new one, then restore the prior one:
print ("1s x2 blinks (2 blinks with on and off times = 500ms)")
BLU_LED_q.put ([500, "10", 2])
time.sleep (3)

print ("A 50ms blink over 400ms, repeated 2 times, while saving above 1s blinks")
BLU_LED_q.put ([50, "1000 0000", 2, CMD_SAVE])
time.sleep (3)

print ("Re-execute the prior saved 1s x2 blinks")
BLU_LED_q.put ([0,"0",0, CMD_RESTORE])
time.sleep (3)

print ("Re-execute the prior saved 1s x2 blinks again")
BLU_LED_q.put ([0,"0",0, CMD_RESTORE])
time.sleep (3)

# Terminate gracefully
print ("Off solid (no blink)")
BLU_LED_q.put ([0, "0", 1, CMD_EXIT])
BLU_LED_th.join()
```

<br>

## PiBlinky-demo.py

PiBlinky-demo.py is ths validation testing script for PiBlinky.  Test '1a' runs three LEDs concurrently.  See the github repo tests directory for this demo program.

    /<path to tests dir>/PiBlinky-demo.py --test 1a

<br>

## Enabling debug logging

To enabled debug logging from this module's classes/functions, add this to your tool script code:

     logging.getLogger('cjn_PiTools.PiBlinky').setLevel(logging.DEBUG)


<a id="links"></a>
         
<br>

---

# Links to classes, methods, and functions

- [PiBlinky](#PiBlinky)



<br/>

<a id="PiBlinky"></a>

---

# Class PiBlinky (LED_name, api, gpio_num, queue, inverted=False) - A threaded, multiple LED driver for Raspberry Pi

Create an PiBlinky device instance

### Args
`LED_name` (str)
- User defined name for this LED instance, e.g., 'BLU'

`api` (str or pigpio.pi instance handle)
- 'GPIO' if using the RPi.GPIO api
- As returned from `pigpio.pi()` if using the pigpio api
- If not 'GPIO' then `api` is taken as a valid pigpio.pi handle - no error checking

`gpio_num` (int)
- GPIO channel number using "Broadcom SOC channel" numbering (e.g., int 22 refers to GPIO22 which is on header pin 15)
- Checked to be a valid GPIO channel number for Raspberry Pi versions Model B+ and later (40 pin header, values 0 to 27)

`queue` (queue handle)
- As returned from `queue.Queue()`
- No error checking

`inverted` (int, default 0)
- If 0 the GPIO channel will be driven to logic high when outputting a bit '1'
- If 1 the GPIO channel will be driven to logic low when outputting a bit '1'


### Class instance variables - as passed in at instantiation
- `LED_name` (str)
- `api` ('GPIO' or pigpio.pi instance handle)
- `gpio_num` (int)
- `queue` (queue handle)
- `inverted` (int)


### Returns
- PiBlinky instance handle on success
- Raises ValueError on args errors during instantiation, where checked


### Behaviors and rules
- Commands to a LED PiBlinky instance are passed (as a list) thru a queue to the thread managing the given 
LED - one thread and queue per LED.  
  - Command list structure:

        cmd[0]: Bittime (int or float) - Period in milliseconds for each bit
            EG, <500> is 0.5s per bit
        cmd[1]: Bitstream (str) - First bit is on the left, 1=On, 0=Off
            Spaces may be used in the bitstream for readability
            The bitstream is checked to contain only '0' and '1'
            If bitstream is an empty string then the LED is unchanged and bittime is skipped
        cmd[2]: Play count (int) - Number of times to play the bitstream
            -1 will repeat forever, until another command is queued
            0 or 1 means play the bitstream once
            2 = two times, etc
        cmd[3]: Option flag (optional enum (int))
            PiBlinky.CMD_SAVE:     Save prior command for later restore, and play the new command
            PiBlinky.CMD_RESTORE:  Restore prior command (fields 0-2 are ignored)
                The restore stack is 1 deep.  Once saved, a command may be restored more than once.
            PiBlinky.CMD_EXIT:     Play the bitstream once then exit the thread

  - A new command entered into the queue will interrupt/replace any command currently being executed.
  - On any command error, PiBlinky logs a warning message and returns.  No exception is raised.

- Debug logging may be enabled in the tool script code by setting this module's logging level:

        logging.getLogger('cjn_PiTools.PiBlinky').setLevel(logging.DEBUG)
