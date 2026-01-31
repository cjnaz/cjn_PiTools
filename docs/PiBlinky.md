# piblinky - A multiple LED driver for Raspberry Pi

Why?  To run an LED on a RaspberryPi is done simply by turning a GPIO pin on and off.  Often, that's just fine, but if you want more scheduling capability and features, then this driver may be what you're looking for.

Features

- Multiple concurrent LEDs supported, each with their own independent on/off sequences and timing.
- A flashing sequence can be set once, rather than your main code having to turn the LED on and off repeatedly.
- Supports both RPi.GPIO and pigpio driver libraries.  pigpio supports running LEDs on remote systems.
- LED flashing sequences are completely user defined, including the bit-sequence, bit-time, and number of times to repeat (or indefinitely).
- Advanced features include saving the currently running sequence, then applying a new sequence, and later restoring the saved sequence.  Useful if two different operations need to share an LED.
- Setup and usage in your code is simple.  No external dependencies, other than the RPi.GPIO or pigpio driver. Supported on Python 3.9+ (an probably works on 3.x).

For example, one of my apps flashes a yellow LED for 50ms once per loop of the measurement thread (1s loop time) to indicate that the thread is still alive, flashes a blue LED 0.5s on / 0.5s off continuously while watering is running, and turns a red LED on solid if there are any detected problems, or on exit of the app.  Normally, I should see the yellow LED flash once per seconds, see the blue LED flash while watering, and never see the red LED.

<br>

## Setup / Installation

If using the RPi.GPIO driver:

    pip install piblinky[GPIO]

If using the pigpio driver:

    pip install piblinky[pigpio]

You will also need to install the `pigpiod` daemon and start it manually or at boot:

<br>

## Coding usage

- Once set up, piblinky commands are passed through a queue to the support thread
- Command list structure:

        cmd[0]: Bittime (period in milliseconds for each bit), EG, 0.5s is 500.
        cmd[1]: Bitstream - First bit is on the left, 1=On, 0=Off.
            Spaces may be used in the bitstream for readability.
            Bitstream is minimally checked for errors.
        cmd[2]: Repeat count - Number of times to play the bitstream.
            -1 will repeat forever, until another command is queued.
        cmd[3]: Options flag (optional)
                    piblinky.CMD_SAVE:     Save prior command for later restore.  
                    piblinky.CMD_RESTORE:  Restore prior command.  (fields 0-2 are ignored)
                        The restore stack is 1 deep.  Once saved, a command may be restored more than once.
                    piblinky.CMD_EXIT:     Execute current command and exit the thread.

- A new command entered into the queue will interrupt/replace any currently being executed command.
- Repeat count not supported with CMD_EXIT.  The bitstream is executed once.
- On any error, piblinky logs a warning message and returns.  No exception raised.
- Debug level logging may be enabled to trace execution within a piblinky operation by adding `logging.getLogger('piblinky').setLevel(logging.DEBUG)` in your tool script code.

<br/>

## Usage example - This `README_ex.py` code example is in the tests directory in the github repo

The LED is connected from GPIO pin 4 to ground through an appropriate current limiting resistor.

```
#!/usr/bin/env python3

# Set up a piblinky instance
from piblinky.piblinky import piblinky, CMD_EXIT, CMD_SAVE, CMD_RESTORE
import queue
import time

BLU_LED_GPIO    = 4
BLU_LED_q       = queue.Queue()
BLU_LED_inst    = piblinky("BLU", 'GPIO', BLU_LED_GPIO, BLU_LED_q)
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

## demo-piblinky.py

This demo runs three LEDs concurrently.  See the github repo tests directory for this demo program:

```
$ ./demo-piblinky.py -h
usage: demo-piblinky.py [-h] [-t TEST] [--host HOST] [--port PORT] [-v]

Demo/test for piblinky
1.1.1

optional arguments:
  -h, --help            show this help message and exit
  -t TEST, --test TEST  Test number to run (default 0 runs most all tests (those without untrapped errors))
  --host HOST           Hostname for pigpio, or 'GPIO' for RPi.GPIO usage (Default <localhost>)
  --port PORT           Port number for pigpio (Default <8888>)
  -v, --verbose         Print status and activity messages
```
<br/>

## Notable changes since prior release
First release to PyPI

<br/>

## Version history
- 1.1.1 260106 - Added named logger, release packagized version to PyPI
- 1.1 240929 - named the threads, changed run to start
- 0.1 230226 - New
