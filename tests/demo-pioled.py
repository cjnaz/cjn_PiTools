#!/usr/bin/env python3
"""Demo/test for PiOLED multi-message display system

Produce / compare to golden results:
    # Note:  Logs from the server use a '*' separator, while logs from the demo/test file use a '-' separator.
    cd to test directory
    pioled --service --val-logfile ./testrun.log -vv &
    ./demo-pioled.py -vv >> testrun.log
    killall pioled
    diff testrun.log to the golden file
    
    Expected differences:
        timestamps
        Minor reordering of server vs. demo/test logs
"""

#==========================================================
#
#  Chris Nelson, 2024-2026
#
#==========================================================

__version__ = "1.0"

import argparse
import time
import datetime
import logging
import re
from pathlib import Path

from cjnfuncs.resourcelock  import resource_lock

import queue
from cjn_PiFuncs.PiOLED import pioled_display_driver, PIOLED_TH_EXIT, PIOLED_TH_PAUSE, PIOLED_SAVE, PIOLED_RESTORE

DISPLAY_FILE =      '/mnt/RAMDRIVE/pioled_display.txt'
PIOLED_GO_FLAG =    'PiOLED_go_flag'
PIOLED_FILE_LOCK=   'PiOLED_file_lock'

pioled_go_flag =    resource_lock(PIOLED_GO_FLAG)
pioled_file_lock=   resource_lock(PIOLED_FILE_LOCK)

logging.basicConfig()

parser = argparse.ArgumentParser(description=__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-t', '--test', default='0',
                    help="Test number to run (default 0) - 0 runs all tests")
parser.add_argument('-v', '--verbose', action='store_true',
                    help="Print status and activity messages")
args = parser.parse_args()

if args.verbose:
    logging.getLogger('pioled').setLevel(logging.DEBUG)
    logging.getLogger('cjnfuncs.resourcelock').setLevel(logging.DEBUG)


# --------------------------------------------------------------------

def print_test_header(header):
    print ("\n======================================================================================================")
    print (f"***** Test number {tnum}: {header} *****")
    print ("======================================================================================================\n")


tnum_parse = re.compile(r"([\d]+)([\w]*)")
def check_tnum(tnum_in, include0='0'):      # include0=False to disable in '0' run
    global tnum
    tnum = tnum_in
    if args.test == include0  or  args.test == tnum_in:  return True
    try:
        if int(args.test) == int(tnum_parse.match(tnum_in).group(1)):  return True
    except:  pass
    return False

def do_setup(page_time=1, inter_page_time=0.2, inter_message_set_time=2):
    # Returns tuple:  queue handle, pioled class instance, and pioled thread handle
    pioled_q =    queue.Queue()
    pioled =      pioled_display_driver(pioled_q, display_file=DISPLAY_FILE,
                    page_time=page_time, inter_page_time=inter_page_time, inter_message_set_time=inter_message_set_time)
    return pioled_q, pioled, pioled.start()


#===============================================================================================
if check_tnum('1a'):
    print_test_header ("Demo single message via queue - list format")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [[0, 0, 20, "Hello"]]
    msg_set = [m1]
    pioled_q.put ({'pages':msg_set})
    time.sleep (2)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()
    time.sleep (0.5)


#===============================================================================================
if check_tnum('1b'):
    print_test_header ("Demo single message via queue - dict format")

    pioled_q, pioled, pioled_th = do_setup()
    # logging.getLogger('cjnfuncs.resourcelock').setLevel(logging.DEBUG)

    m1 = [{'x':0, 'y':0, 'size':20, 'text':"Hello'"}]
    msg_set = [m1]
    pioled_q.put ({'pages':msg_set})
    time.sleep (2)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[{'x':20, 'y':20, 'size':18, 'text':"Exited"}]]})
    pioled_th.join()
    # logging.getLogger('cjnfuncs.resourcelock').setLevel(logging.WARNING)


#===============================================================================================
if check_tnum('2a'):
    print_test_header ("Demo message queue")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [[0, 0, 20, "Message1.1"], [5, 30, 12, "To be, or not to be"]]
    m2 = [[0, 0, 20, "Message1.2"], [5, 30, 12, "This is the question"]]
    m3 = [[0, 0, 20, "Message1.3"], [5, 30, 12, datetime.datetime(2021, 2, 3, 4, 5, 6)]]
    msg_set = [m1, m2, m3]
    pioled_q.put ({'pages':msg_set})
    time.sleep (12)

    m1 = [[0, 0, 20, "Message2.1"], [5, 30, 12, "New msg interrupted"]]
    m2 = [[0, 0, 20, "Message2.2"], [5, 30, 12, "Ha, clobbered it !"]]
    msg_set = [m1, m2]
    pioled_q.put ({'pages':msg_set})
    time.sleep (7)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('2b'):
    print_test_header ("Demo message queue with dict defined lines")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [{'x':0, 'y':0, 'size':20, 'text':"Message1.1"}, {'x':5, 'y':30, 'size':12, 'text':"To be, or not to be"}]
    m2 = [{'x':0, 'y':0, 'size':20, 'text':"Message1.2"}, {'x':5, 'y':30, 'size':12, 'text':"This is the question"}]
    m3 = [{'x':0, 'y':0, 'size':20, 'text':"Message1.3"}, {'x':5, 'y':30, 'size':12, 'text':f"{datetime.datetime(2021, 2, 3, 4, 5, 6)}"}]

    msg_set = [m1, m2, m3]
    pioled_q.put ({'pages':msg_set})
    time.sleep (12)

    m1 = [{'x':0, 'y':0, 'size':20, 'text':"Message2.1"}, {'x':5, 'y':30, 'size':12, 'text':"New msg interrupted"}]
    m2 = [{'x':0, 'y':0, 'size':20, 'text':"Message2.2"}, {'x':5, 'y':30, 'size':12, 'text':"Ha, clobbered it !"}]
    msg_set = [m1, m2]
    pioled_q.put ({'pages':msg_set})
    time.sleep (7)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[{'x':20, 'y':20, 'size':18, 'text':"Exited"}]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('3a'):
    font = 'C&C Red Alert [INET].ttf'
    size = 12
    print_test_header (f"Font <{font}>")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [
          {'x':0, 'y':0,  'size':size, 'font':font, 'text':f"{font} - {size}"},
          {'x':0, 'y':15, 'size':size, 'font':font, 'text':"ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
          {'x':0, 'y':30, 'size':size, 'font':font, 'text':"abcdefghijklmnopqrstuvwxyz"},
          {'x':0, 'y':45, 'size':size, 'font':font, 'text':"1234567890 !@#$%^&*()_-+="},
          ]
    
    msg_set = [m1]
    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':msg_set})
    if args.test == '3':
        time.sleep (4)      # Show long enough to view
    else:
        time.sleep (1)      # Show long enough to confirm
    pioled_th.join()


#===============================================================================================
if check_tnum('3b'):
    font = 'ChiKareGo.ttf'
    size = 14
    print_test_header (f"Font <{font}>")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [
          {'x':0, 'y':0,  'size':size, 'font':font, 'text':f"{font} - {size}"},
          {'x':0, 'y':15, 'size':size, 'font':font, 'text':"ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
          {'x':0, 'y':30, 'size':size, 'font':font, 'text':"abcdefghijklmnopqrstuvwxyz"},
          {'x':0, 'y':45, 'size':size, 'font':font, 'text':"1234567890 !@#$%^&*()_-+="},
          ]
    
    msg_set = [m1]
    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':msg_set})
    if args.test == '3':
        time.sleep (4)
    else:
        time.sleep (1)
    pioled_th.join()


#===============================================================================================
if check_tnum('3c'):
    font = 'code2000.ttf'
    size = 12
    print_test_header (f"Font <{font}>")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [
          {'x':0, 'y':0,  'size':size, 'font':font, 'text':f"{font} - {size}"},
          {'x':0, 'y':15, 'size':size, 'font':font, 'text':"ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
          {'x':0, 'y':30, 'size':size, 'font':font, 'text':"abcdefghijklmnopqrstuvwxyz"},
          {'x':0, 'y':45, 'size':size, 'font':font, 'text':"1234567890 !@#$%^&*()_-+="},
          ]
    
    msg_set = [m1]
    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':msg_set})
    if args.test == '3':
        time.sleep (4)
    else:
        time.sleep (1)
    pioled_th.join()


#===============================================================================================
if check_tnum('3d'):
    font = 'GLECB.TTF'
    size = 12
    print_test_header (f"Font <{font}>")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [
          {'x':0, 'y':0,  'size':size, 'font':font, 'text':f"{font} - {size}"},
          {'x':0, 'y':15, 'size':size, 'font':font, 'text':"ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
          {'x':0, 'y':30, 'size':size, 'font':font, 'text':"abcdefghijklmnopqrstuvwxyz"},
          {'x':0, 'y':45, 'size':size, 'font':font, 'text':"1234567890 !@#$%^&*()_-+="},
          ]
    
    msg_set = [m1]
    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':msg_set})
    if args.test == '3':
        time.sleep (4)
    else:
        time.sleep (1)
    pioled_th.join()


#===============================================================================================
if check_tnum('3e'):
    font = 'FreePixel.ttf'
    size = 12
    print_test_header (f"Font <{font}>")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [
          {'x':0, 'y':0,  'size':size, 'font':font, 'text':f"{font} - {size}"},
          {'x':0, 'y':15, 'size':size, 'font':font, 'text':"ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
          {'x':0, 'y':30, 'size':size, 'font':font, 'text':"abcdefghijklmnopqrstuvwxyz"},
          {'x':0, 'y':45, 'size':size, 'font':font, 'text':"1234567890 !@#$%^&*()_-+="},
          ]
    
    msg_set = [m1]
    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':msg_set})
    if args.test == '3':
        time.sleep (4)
    else:
        time.sleep (1)
    pioled_th.join()


#===============================================================================================
if check_tnum('3f'):
    font = 'miscfs_.ttf'
    size = 12
    print_test_header (f"Font <{font}>")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [
          {'x':0, 'y':0,  'size':size, 'font':font, 'text':f"{font} - {size}"},
          {'x':0, 'y':15, 'size':size, 'font':font, 'text':"ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
          {'x':0, 'y':30, 'size':size, 'font':font, 'text':"abcdefghijklmnopqrstuvwxyz"},
          {'x':0, 'y':45, 'size':size, 'font':font, 'text':"1234567890 !@#$%^&*()_-+="},
          ]
    
    msg_set = [m1]
    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':msg_set})
    if args.test == '3':
        time.sleep (4)
    else:
        time.sleep (1)
    pioled_th.join()


#===============================================================================================
if check_tnum('3g'):
    font = 'pixelmix.ttf'
    size = 10
    print_test_header (f"Font <{font}>")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [
          {'x':0, 'y':0,  'size':size, 'font':font, 'text':f"{font} - {size}"},
          {'x':0, 'y':15, 'size':size, 'font':font, 'text':"ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
          {'x':0, 'y':30, 'size':size, 'font':font, 'text':"abcdefghijklmnopqrstuvwxyz"},
          {'x':0, 'y':45, 'size':size, 'font':font, 'text':"1234567890 !@#$%^&*()_-+="},
          ]
    
    msg_set = [m1]
    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':msg_set})
    if args.test == '3':
        time.sleep (4)
    else:
        time.sleep (1)
    pioled_th.join()


#===============================================================================================
if check_tnum('3h'):
    font = 'ProggyTiny.ttf'
    size = 16
    print_test_header (f"Font <{font}>")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [
          {'x':0, 'y':0,  'size':size, 'font':font, 'text':f"{font} - {size}"},
          {'x':0, 'y':15, 'size':size, 'font':font, 'text':"ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
          {'x':0, 'y':30, 'size':size, 'font':font, 'text':"abcdefghijklmnopqrstuvwxyz"},
          {'x':0, 'y':45, 'size':size, 'font':font, 'text':"1234567890 !@#$%^&*()_-+="},
          ]
    
    msg_set = [m1]
    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':msg_set})
    if args.test == '3':
        time.sleep (4)
    else:
        time.sleep (1)
    pioled_th.join()


#===============================================================================================
if check_tnum('3i'):
    font = 'tiny.ttf'
    size = 12
    print_test_header (f"Font <{font}>")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [
          {'x':0, 'y':0,  'size':size, 'font':font, 'text':f"{font} - {size}"},
          {'x':0, 'y':15, 'size':size, 'font':font, 'text':"ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
          {'x':0, 'y':30, 'size':size, 'font':font, 'text':"abcdefghijklmnopqrstuvwxyz"},
          {'x':0, 'y':45, 'size':size, 'font':font, 'text':"1234567890 !@#$%^&*()_-+="},
          ]
    
    msg_set = [m1]
    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':msg_set})
    if args.test == '3':
        time.sleep (4)
    else:
        time.sleep (1)
    pioled_th.join()


#===============================================================================================
if check_tnum('3j'):
    font = 'Volter__28Goldfish_29.ttf'
    size = 9
    print_test_header (f"Font <{font}>")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [
          {'x':0, 'y':0,  'size':size, 'font':font, 'text':f"{font} - {size}"},
          {'x':0, 'y':15, 'size':size, 'font':font, 'text':"ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
          {'x':0, 'y':30, 'size':size, 'font':font, 'text':"abcdefghijklmnopqrstuvwxyz"},
          {'x':0, 'y':45, 'size':size, 'font':font, 'text':"1234567890 !@#$%^&*()_-+="},
          ]
    
    msg_set = [m1]
    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':msg_set})
    if args.test == '3':
        time.sleep (4)
    else:
        time.sleep (1)
    pioled_th.join()


#===============================================================================================
if check_tnum('3k'):
    print_test_header (f"Mix it up")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [
          {'x':0,  'y':0,  'size':12, 'text':'code2000.ttf', 'font':'code2000.ttf'},
          {'x':90, 'y':0,  'size':12, 'text':'Aa1Tt9', 'font':'code2000.ttf'},
          {'x':0,  'y':15, 'size':12, 'text':'FreePixel.ttf', 'font':'FreePixel.ttf'},
          {'x':90, 'y':15, 'size':12, 'text':'Aa1Tt9', 'font':'FreePixel.ttf'},
          {'x':0,  'y':30, 'size':15, 'text':'ProggyTiny.ttf', 'font':'ProggyTiny.ttf'},
          {'x':90, 'y':30, 'size':15, 'text':'Aa1Tt9', 'font':'ProggyTiny.ttf'},
          {'x':0,  'y':45, 'size':9,  'text':'Volter__28Goldfi', 'font':'Volter__28Goldfish_29.ttf'},
          {'x':90, 'y':45, 'size':9,  'text':'Aa1Tt9', 'font':'Volter__28Goldfish_29.ttf'},
          ]

    msg_set = [m1]
    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':msg_set})
    if args.test == '3':
        time.sleep (4)
    else:
        time.sleep (1)
    pioled_th.join()


#===============================================================================================
if check_tnum('4'):
    print_test_header ("One-liners with timeout and permanent")

    pioled_q, pioled, pioled_th = do_setup()

    pioled.oneliner(5, 5, 18, "Hi there", message_time=1, font='GLECB.TTF')   # Blank after 1 second, then return
    time.sleep(1)                                                           # Wait an additional time before the next message
    pioled.oneliner(5, 5, 18, "Another page", cmd=PIOLED_TH_EXIT)               # Permanent page, remains after exit

    pioled_th.join()


#===============================================================================================
if check_tnum('5'):
    print_test_header ("Message pages with timeout and permanent - message_time is blocking to the calling code")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [[0, 0, 20, "Message 1"], [20, 30, 12, "with timeout"]]
    m2 = [[0, 0, 20, "Message 2"], [20, 30, 12, "Permanent"]]

    pioled.message_page(m1, message_time=2)                   # Timed page
    time.sleep(1)
    pioled.message_page(m2)                                   # Permanent page, remains after exit
    time.sleep(2)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT})                       # Does a Blank on exit
    pioled_th.join()


#===============================================================================================
if check_tnum('6'):
    
    print_test_header ("Run thru a range of font sizes")

    pioled_q, pioled, pioled_th = do_setup()

    runlist = range(9, 31) 

    for size in runlist:
        pioled.oneliner(0, 0, size, f"Font size {size}", message_time=1)
        time.sleep (0.1)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT})
    pioled_th.join()


#===============================================================================================
if check_tnum('7'):
    print_test_header ("pioled multi_message with pause and exit messages")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [[0, 0, 20, "Message1.1"], [5, 30, 12, "To be, or not to be"]]
    m2 = [[0, 0, 20, "Message1.2"], [5, 30, 12, "This is the question"]]
    m3 = [[0, 0, 20, "Message1.3"], [5, 30, 12, datetime.datetime(2021, 2, 3, 4, 5, 6)]]
    msg_set = [m1, m2, m3]
    pioled_q.put ({'pages':msg_set})
    time.sleep (12)

    pioled_q.put ({'cmd':PIOLED_TH_PAUSE, 'pages':[[[20, 20, 18, 'Paused']]]})
    time.sleep(3)

    m1 = [[0, 0, 20, "Message2.1"], [5, 30, 12, "New multi-message"]]
    m2 = [[0, 0, 20, "Message2.2"], [5, 30, 18, "Page 2"]]
    msg_set = [m1, m2]
    pioled_q.put ({'pages':msg_set})
    time.sleep (7)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('8a'):
    print_test_header ("save and restore")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [[0, 0, 20, "Message1.1"], [5, 30, 12, "To be, or not to be"]]
    m2 = [[0, 0, 20, "Message1.2"], [5, 30, 12, "This is the question"]]
    m3 = [[0, 0, 20, "Message1.3"], [5, 30, 12, datetime.datetime(2021, 2, 3, 4, 5, 6)]] # datetime.datetime(2026, 1, 21, 22, 9, 12)
    msg_set = [m1, m2, m3]
    pioled_q.put ({'pages':msg_set})
    time.sleep (7)

    m1 = [[0, 0, 20, "Message2.1"], [5, 30, 12, "Saved Message1"]]
    m2 = [[0, 0, 20, "Message2.2"], [5, 30, 18, "Page 2"]]
    msg_set = [m1, m2]
    pioled_q.put ({'cmd':PIOLED_SAVE, 'pages':msg_set})
    time.sleep (7)

    pioled_q.put ({'cmd':PIOLED_RESTORE})
    time.sleep (7)

    pioled_q.put ({'cmd':PIOLED_TH_PAUSE, 'pages':[[[20, 20, 18, 'Paused']]]})
    time.sleep (5)

    pioled_q.put ({'cmd':PIOLED_RESTORE})
    time.sleep (7)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('8b'):
    print_test_header ("Restore before save")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [[0, 0, 20, "Message1.1"], [5, 30, 12, "To be, or not to be"]]
    m2 = [[0, 0, 20, "Message1.2"], [5, 30, 12, "This is the question"]]
    m3 = [[0, 0, 20, "Message1.3"], [5, 30, 12, datetime.datetime(2021, 2, 3, 4, 5, 6)]] # datetime.datetime(2026, 1, 21, 22, 9, 12)
    msg_set = [m1, m2, m3]
    pioled_q.put ({'cmd':PIOLED_RESTORE})
    time.sleep (2)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('9'):
    print_test_header ("No provided pages = blank")

    pioled_q, pioled, pioled_th = do_setup()

    pioled.oneliner (0, 0, 18, 'Something')
    time.sleep (3)

    pioled_q.put ({})
    time.sleep (3)

    pioled.oneliner (0, 0, 18, 'Again')
    time.sleep (3)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('10'):
    print_test_header ("Loop messages N times")

    pioled_q, pioled, pioled_th = do_setup()

    pioled.oneliner (0, 0, 18, 'Msg 1 looped 1x')
    time.sleep (2)

    m1 = [[0, 0, 20, "Message1.1"], [5, 30, 12, "Looped 1x"]]
    m2 = [[0, 0, 20, "Message1.2"], [5, 30, 12, "This is the question"]]
    m3 = [[0, 0, 20, "Message1.3"], [5, 30, 12, datetime.datetime(2021, 2, 3, 4, 5, 6)]]
    msg_set = [m1, m2, m3]
    pioled_q.put ({'cnt':1, 'pages':msg_set})
    time.sleep (7)

    pioled.oneliner (0, 0, 18, 'Msg 2 looped 2x')
    time.sleep (2)

    m1 = [[0, 0, 20, "Message2.1"], [5, 30, 12, "Looped 2x"]]
    m2 = [[0, 0, 20, "Message2.2"], [5, 30, 12, "This is the question"]]
    m3 = [[0, 0, 20, "Message2.3"], [5, 30, 12, datetime.datetime(2021, 2, 3, 4, 5, 6)]]
    msg_set = [m1, m2, m3]
    pioled_q.put ({'cnt':2, 'pages':msg_set})
    time.sleep (12)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()

    time.sleep(1)
    pioled.blank()


#===============================================================================================
if check_tnum('11'):
    print_test_header ("Zero blank time between pages and loops")

    pioled_q, pioled, pioled_th = do_setup(page_time=1, inter_page_time=0, inter_message_set_time=0)

    m1 = [[0, 0, 20, "Message1.1"], [5, 30, 12, "To be, or not to be"]]
    m2 = [[0, 0, 20, "Message1.2"], [5, 30, 12, "This is the question"]]
    m3 = [[0, 0, 20, "Message1.3"], [5, 30, 12, datetime.datetime(2021, 2, 3, 4, 5, 6)]]
    msg_set = [m1, m2, m3]
    pioled_q.put ({'pages':msg_set})
    time.sleep (10)

    m1 = [[0, 0, 20, "Message2.1"]]
    m2 = [[0, 0, 20, "Message2.2"], [5, 30, 12, "No final wait leaves"], [5, 45, 12, "last page displayed."]]
    msg_set = [m1, m2]
    pioled_q.put ({'cnt':2, 'pages':msg_set})
    time.sleep (10)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('11a'):
    print_test_header ("Page/blank timing set via pioled_q.put(), overriding defaults set at thread instantiation")


    pioled_q, pioled, pioled_th = do_setup(page_time=1, inter_page_time=2, inter_message_set_time=2)

    m1 = [[0, 0, 20, "Message1.1"], [5, 30, 12, "To be, or not to be"]]
    m2 = [[0, 0, 20, "Message1.2"], [5, 30, 12, "This is the question"]]
    m3 = [[0, 0, 20, "Message1.3"], [5, 30, 12, datetime.datetime(2021, 2, 3, 4, 5, 6)]]
    msg_set = [m1, m2, m3]
    pioled_q.put ({'pages':msg_set, 'page_time':0.5, 'inter_page_time':0.5, 'inter_message_set_time':0.5})
    time.sleep (10)

    m1 = [[0, 0, 20, "Message2.1"]]
    m2 = [[0, 0, 20, "Message2.2"], [5, 30, 12, "No final wait leaves"], [5, 45, 12, "last page displayed."]]
    msg_set = [m1, m2]
    pioled_q.put ({'cnt':2, 'pages':msg_set, 'inter_page_time':0.2})
    time.sleep (10)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('12'):
    print_test_header ("Single page message in queue")

    pioled_q, pioled, pioled_th = do_setup()

    m1 = [[0, 0, 20, "Message1.1"], [5, 30, 12, "To be, or not to be"]]
    m2 = [[0, 0, 20, "Message1.2"], [5, 30, 12, "This is the question"]]
    m3 = [[0, 0, 20, "Message1.3"], [5, 30, 12, datetime.datetime(2021, 2, 3, 4, 5, 6)]]

    pioled_q.put ({'pages':[m1]})
    time.sleep (3)

    pioled_q.put ({'pages':[m2]})
    time.sleep (3)

    pioled_q.put ({'pages':[m3]})
    time.sleep (3)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('13a'):
    print_test_header ("Can't find the display file")

    pioled_q, pioled, pioled_th = do_setup()

    try:
        Path(DISPLAY_FILE).unlink()
    except:
        pass

    pioled_go_flag.get_lock(lock_info='Test 13a')

    time.sleep (0.1)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('13b'):
    print_test_header ("Missing list nest level in pages")

    pioled_q, pioled, pioled_th = do_setup()

    pioled_q.put ({'pages':[[0, 0, 20, "Missing list nest level"]]})

    time.sleep (0.1)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('13c'):
    print_test_header ("Missing two list nest levels in pages")

    pioled_q, pioled, pioled_th = do_setup()

    pioled_q.put ({'pages':[0, 0, 20, "Missing two list nest levels"]})

    time.sleep (0.1)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('13d'):
    print_test_header ("Missing wrapper dictionary")

    pioled_q, pioled, pioled_th = do_setup()

    pioled_q.put ([0, 0, 20, "Missing wrapper dictionary"])

    time.sleep (0.1)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('13e'):
    print_test_header ("Bad x coordinate - Flagged by server")

    pioled_q, pioled, pioled_th = do_setup()

    pioled_q.put ({'pages':[[["Hello", 0, 20, "Bad x coordinate - string"]]]})

    time.sleep (0.1)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('13f'):
    print_test_header ("Bad size - Flagged by server")

    pioled_q, pioled, pioled_th = do_setup()

    pioled_q.put ({'pages':[[[0, 0, -1, "Bad size"]]]})

    time.sleep (0.1)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('13g'):
    print_test_header ("Unknown font name - Flagged by server")

    pioled_q, pioled, pioled_th = do_setup()

    pioled_q.put ({'pages':[[{'x':0, 'y':0, 'size':10, 'font':'xyz', 'text':"Bad fontname"}]]})

    time.sleep (1)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('13m'):
    print_test_header ("display file is locked")

    pioled_q, pioled, pioled_th = do_setup()

    pioled_file_lock.get_lock(lock_info='Test 13d')

    pioled_q.put ({'pages':[[[0, 0, 20, "display file is locked"]]]})

    time.sleep (0.1)

    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()


#===============================================================================================
if check_tnum('50', include0=False):
    print_test_header ("Dev/debug")

    pioled_q, pioled, pioled_th = do_setup()

    pioled_q.put({'cmd':PIOLED_SAVE,
                  'cnt':2,
                  'page_time':2,
                  'inter_page_time':0.5,
                  'inter_message_set_time':1.5,
                  'pages':[
                      [[0, 0, 15, "Page 1"],[0, 20, 15, "Page 1 2nd line"]],
                      [[0, 0, 15, "Page 2"],[0, 20, 15, "Page 2 2nd line"]],
                      ]})
    time.sleep(12)
    
    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()

#===============================================================================================
if check_tnum('51', include0=False):
    print_test_header ("Dev/debug")

    pioled_q, pioled, pioled_th = do_setup()

    pioled_q.put(  {
        'cmd':PIOLED_SAVE,
        'cnt':2,
        'page_time':1,
        'inter_page_time':0.5,
        'inter_message_set_time':1.5,
        'pages': [
            [ [0, 0, 15, "Page 1"], [0, 20, 15, "Page 1 2nd line"] ],
            [ {'x':0, 'y':0,  'size':15, 'text':"Page 2"},
              {'x':0, 'y':20, 'size':12, 'text':"Page 2 2nd line", 'font':'FreePixel.ttf', 'color':'PapayaWhip'} ]
            ]
        }  )
    time.sleep(10)
    pioled_q.put({})    # Effectively terminate the above looping and blank the display

    time.sleep (4)
    
    pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[20, 20, 18, 'Exited']]]})
    pioled_th.join()
