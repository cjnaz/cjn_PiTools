#!/usr/bin/env python3
"""piblinky - A threaded multiple LED driver for Raspberry Pi

Commands to a LED piblinky instance are passed thru a queue to the thread managing
the given LED.  One thread and queue per LED.  Command list structure:

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

Debug logging can be enabled with this statement in the main script code:
    logging.getLogger('piblinky').setLevel(logging.DEBUG)
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

piblinky_logger = logging.getLogger('piblinky')
piblinky_logger.setLevel(logging.WARNING)

class piblinky:

    def __init__(self, name, daemon, gpio_num, queue):
        global GPIO
        self.name = name
        self.daemon = daemon
        self.gpio_num = gpio_num
        self.queue = queue

        if daemon == 'GPIO':
            piblinky_logger.debug (f"Setting up piblinky instance <{self.name}> using RPi.GPIO, pin# <{self.gpio_num}>")
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.gpio_num, GPIO.OUT)
            GPIO.output(self.gpio_num, 0)
        else:       # pigpio mode
            piblinky_logger.debug (f"Setting up piblinky instance <{self.name}> using pigpio, pin# <{self.gpio_num}>")
            import pigpio
            self.daemon.set_mode(self.gpio_num, pigpio.OUTPUT)
            self.daemon.write(self.gpio_num, 0)


    def start(self):
        self.this_thread = Thread(target=self.piblinky, daemon=True, name='piblinky_' + self.name)   # daemon so that if the main thread errors this thread is auto-killed, avoiding hang
        self.this_thread.start()
        piblinky_logger.debug (f"{self.name} thread on GPIO {self.gpio_num:>2} created")
        return self.this_thread


    def piblinky(self):
        cmd = None
        cmd_save = None
        do_exit = False
        while True:
            cmd_prior = cmd
            cmd = self.queue.get()
            piblinky_logger.debug (f"{self.name} Command:  <{cmd}>")

            if len(cmd) == 4:
                if cmd[3] == CMD_SAVE:
                    piblinky_logger.debug (f"{self.name} Saving prior piblinky command")
                    cmd_save = cmd_prior
                elif cmd[3] == CMD_RESTORE:
                    if cmd_save != None:
                        piblinky_logger.debug (f"{self.name} Restoring prior piblinky command")
                        cmd = cmd_save
                    else:
                        piblinky_logger.warning (f"{self.name} Attempted command restore with no prior save - <{cmd}>.  Skipped.")
                        continue
                elif cmd[3] == CMD_EXIT:
                    do_exit = True
                else:
                    piblinky_logger.warning (f"{self.name} Invalid option flag received - <{cmd}>.  Skipped.")
                    continue
            if len(cmd) == 3  or  len(cmd) == 4:
                try:
                    period    = float(cmd[0]) / 1000
                    bitstream = list(cmd[1].replace(' ', ''))   # Drop any spaces in the bitstream
                    rptcnt    = int(cmd[2])
                except Exception as e:
                    piblinky_logger.warning (f"{self.name} Invalid command received - <{cmd}>.  Skipped.")
                    continue
            else:
                piblinky_logger.warning (f"{self.name} Invalid command received - <{cmd}>.  Skipped.")
                continue
            
            piblinky_logger.debug (f"{self.name} Stream:   Period {period}s, bitstream {bitstream}, repeat {rptcnt}")

            quit = False
            while True:
                if not self.queue.empty()  or  quit:
                    break
                for bit in bitstream:
                    if not self.queue.empty():
                        break
                    try:
                        if self.daemon == 'GPIO':
                            GPIO.output(self.gpio_num, int(bit))
                        else:
                            self.daemon.write(self.gpio_num, int(bit))
                    except Exception as e:
                        piblinky_logger.warning (f"{self.name} Error writing <{bit}>.  Skipped.:\n  {e}")
                        quit = True
                        break
                    time.sleep(period)
                if do_exit:
                    piblinky_logger.debug (f"{self.name} Thread exiting")
                    sys.exit()
                if rptcnt > 0:
                    rptcnt -= 1
                    if rptcnt == 0:
                        break
