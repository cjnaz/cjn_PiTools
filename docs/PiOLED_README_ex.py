#!/usr/bin/env python3
# PiOLED_README_ex.py available in the docs directory in the github repo

import queue
from cjn_PiTools.PiOLED import pioled_display_driver, PIOLED_TH_EXIT

# Configure the server interface settings
DISPLAY_FILE =      '/mnt/RAMDRIVE/pioled_display.txt'

# Instantiate the local queue and thread
pioled_q =          queue.Queue()
pioled =            pioled_display_driver(pioled_q, display_file=DISPLAY_FILE)
pioled_th =         pioled.start()

# Display a message and exit
pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[0, 0, 12, 'Hello my name is Marvin'],[10, 20, 12, "I'm so depressed..."]]]})

# Exit cleanup code
pioled_th.join()