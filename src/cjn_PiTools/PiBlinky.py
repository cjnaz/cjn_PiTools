#!/usr/bin/env python3
"""PiBlinky - A threaded multiple LED driver for Raspberry Pi
"""

import importlib.metadata
__version__ = importlib.metadata.version(__package__ or __name__)

#==========================================================
#
#  Chris Nelson, Copyright 2022-2026
#
#==========================================================

import time
import sys
import logging
from threading import Thread

# Configs / Constants
CMD_SAVE    = 1
CMD_RESTORE = 2
CMD_EXIT    = -99
GPIO_NUMBERS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]

piblinky_logger = logging.getLogger('cjn_PiTools.PiBlinky')

class PiBlinky:
    """
## Class PiBlinky (LED_name, api, gpio_num, queue, inverted=False) - A threaded, multiple LED driver for Raspberry Pi


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
"""

    def __init__(self, LED_name, api, gpio_num, queue, inverted=0):
        global GPIO
        self.LED_name = LED_name
        self.api = api
        self.gpio_num = gpio_num
        self.queue = queue
        self.inverted = inverted

        if not isinstance(LED_name, str):
            raise ValueError (f"LED_name must be str - received <{LED_name}> - {type(LED_name)}")

        if gpio_num not in GPIO_NUMBERS:
            raise ValueError (f"<{self.LED_name}> gpio_num must be a valid GPIO Broadcom SOC channel number - received <{gpio_num}> - {type(gpio_num)}")

        if not inverted in [0, 1]:
            raise ValueError (f"<{self.LED_name}> inverted must be int 0 or 1 - received <{inverted}> - {type(inverted)}")


        if api == 'GPIO':
            piblinky_logger.debug (f"<{self.LED_name}> - Setting up PiBlinky instance using RPi.GPIO, ch# <{self.gpio_num}>")
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.gpio_num, GPIO.OUT)
            GPIO.output(self.gpio_num, self.inverted ^ 0)
        else:       # pigpio mode
            piblinky_logger.debug (f"<{self.LED_name}> - Setting up PiBlinky instance using pigpio, ch# <{self.gpio_num}>")
            import pigpio
            self.api.set_mode(self.gpio_num, pigpio.OUTPUT)
            self.api.write(self.gpio_num, self.inverted ^ 0)


    def start(self):
        self.this_thread = Thread(target=self.piblinky, daemon=True, name='piblinky_' + self.LED_name)   # daemon so that if the main thread errors this thread is auto-killed, avoiding hang
        self.this_thread.start()
        piblinky_logger.debug (f"<{self.LED_name}> thread on GPIO {self.gpio_num:>2} created")
        return self.this_thread


    def piblinky(self):
        cmd = None
        cmd_save = None
        do_exit = False
        while True:
            cmd_prior = cmd
            cmd = self.queue.get()
            piblinky_logger.debug (f"<{self.LED_name}> Command:  <{cmd}>")

            if len(cmd) == 4:
                if cmd[3] == CMD_SAVE:
                    piblinky_logger.debug (f"<{self.LED_name}> Saving prior PiBlinky command")
                    cmd_save = cmd_prior
                elif cmd[3] == CMD_RESTORE:
                    if cmd_save != None:
                        piblinky_logger.debug (f"<{self.LED_name}> Restoring prior PiBlinky command")
                        cmd = cmd_save
                    else:
                        piblinky_logger.warning (f"<{self.LED_name}> Attempted command restore with no prior save - <{cmd}> - Skipped")
                        continue
                elif cmd[3] == CMD_EXIT:
                    do_exit = True
                else:
                    piblinky_logger.warning (f"<{self.LED_name}> Invalid option flag received - <{cmd}> - Skipped")
                    continue
            if len(cmd) == 3  or  len(cmd) == 4:
                try:
                    period    = float(cmd[0]) / 1000
                    bitstream = list(cmd[1].replace(' ', ''))   # Drop any spaces in the bitstream
                    if set(bitstream) - {'0', '1'}:
                        piblinky_logger.warning (f"<{self.LED_name}> Invalid bitstream <{bitstream}> - Skipped")
                        continue
                    play_cnt    = int(cmd[2])
                except Exception as e:
                    piblinky_logger.warning (f"<{self.LED_name}> Invalid command received - <{cmd}> - Skipped")
                    continue
            else:
                piblinky_logger.warning (f"<{self.LED_name}> Invalid command received - <{cmd}> - Skipped")
                continue
            
            piblinky_logger.debug (f"<{self.LED_name}> Stream:   period {period}s, bitstream {bitstream}, play_cnt {play_cnt}")

            quit = False
            while True:
                if not self.queue.empty()  or  quit:
                    break
                for bit in bitstream:
                    if not self.queue.empty():
                        break
                    try:
                        if self.api == 'GPIO':
                            GPIO.output(self.gpio_num, self.inverted ^ int(bit))
                        else:
                            self.api.write(self.gpio_num, self.inverted ^ int(bit))
                    except Exception as e:
                        piblinky_logger.warning (f"<{self.LED_name}> Error writing <{bit}> - Skipped:\n  {type(e).__name__}: {e}")
                        quit = True
                        break
                    time.sleep(period)
                if do_exit:
                    piblinky_logger.debug (f"<{self.LED_name}> Thread exiting")
                    sys.exit()
                if play_cnt > 0:
                    play_cnt -= 1
                if play_cnt == 0:
                    break
