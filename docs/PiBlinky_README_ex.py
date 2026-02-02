#!/usr/bin/env python3

# Set up a piblinky instance
from cjn_PiFuncs.PiBlinky import piblinky, CMD_EXIT, CMD_SAVE, CMD_RESTORE
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