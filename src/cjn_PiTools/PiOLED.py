#!/usr/bin/env python3
"""PiOLED display service and driver
"""

import importlib.metadata
__version__ = importlib.metadata.version(__package__ or __name__)

#==========================================================
#
#  Chris Nelson, Copyright 2024-2026
#
#==========================================================

import time
import datetime
import argparse
import sys
import os
import signal
import ast
from pathlib import Path
from types import SimpleNamespace
from threading import Thread
from importlib_resources import files as ir_files
import collections


from luma.core import cmdline
from luma.core.render import canvas
from PIL import ImageFont

from cjnfuncs.core          import set_toolname, logging, set_logging_level, periodic_log, setuplogging
from cjnfuncs.configman     import config_item
from cjnfuncs.mungePath     import mungePath
from cjnfuncs.resourcelock  import resource_lock
from cjnfuncs.deployfiles   import deploy_files
import cjnfuncs.core as core


# Configs / Constants
TOOLNAME =                      'PiOLED'
CONFIG_FILE =                   'PiOLED_server.cfg'       # Abs, or relative to the core.tool.config_dir
PIOLED_GO_FLAG =                'PiOLED_go_flag'
PIOLED_SHM_LOCK =               'PiOLED_shm_lock'
PIOLED_SHM =                    'PiOLED_shm'
PRINT_LOG_LENGTH_DEFAULT =      50

SERVER_FILE_LOGGING_FORMAT =    '{asctime} {module:>15}.{funcName:20} * {levelname:>8}:  {message}'
SERVER_CONS_LOGGING_FORMAT =              '{module:>15}.{funcName:20} * {levelname:>8}:  {message}'
CLI_CONSOLE_LOGGING_FORMAT =              '{module:>15}.{funcName:20} - {levelname:>8}:  {message}'

DISPLAY_DRIVER_FONT =           'C&C Red Alert [INET].ttf'  # Default font for _oneliner    # TODO configurable, size and color
DISPLAY_DRIVER_SIZE =           12
DISPLAY_DRIVER_COLOR =          'white'
PIOLED_TH_EXIT =                -99
PIOLED_TH_PAUSE =               -98
PIOLED_NEWMSG =                 -1
PIOLED_SAVE =                   -2
PIOLED_RESTORE =                -3

PIOLED_PAGE_TIME =              7
PIOLED_INTER_PAGE_TIME =        0.3
PIOLED_INTER_MESSAGE_SET_TIME = 1

pioled_logger = logging.getLogger('cjn_PiTools.PiOLED')


set_toolname (TOOLNAME)
# print (core.tool)

pioled_go_flag =                resource_lock(PIOLED_GO_FLAG)
pioled_shm_lock =               resource_lock(PIOLED_SHM_LOCK)
pioled_shm =                    resource_lock(PIOLED_SHM)



#=====================================================================================
#=====================================================================================
#   c l i e n t - s i d e   p i o l e d _ d i s p l a y _ d r i v e r
#=====================================================================================
#=====================================================================================

class pioled_display_driver:
    """Driver for sending messages on the OLED display via shared memory
    This driver/handler is instantiated within the client/tool script/app.
    The config file is not used (used only by the server).
    """
    def __init__(self, queue,
                 name =                 'pioled_driver',
                 page_time =            PIOLED_PAGE_TIME,
                 inter_page_time =      PIOLED_INTER_PAGE_TIME,
                 inter_message_set_time=PIOLED_INTER_MESSAGE_SET_TIME,
                 toolname =             'toolname not set'
                 ):
        global pioled_logger
        global pioled_go_flag, pioled_shm_lock, pioled_shm

        self.queue =                    queue
        self.name =                     name
        self.page_time =                page_time
        self.inter_page_time =          inter_page_time
        self.inter_message_set_time =   inter_message_set_time
        self.toolname =                 toolname
        self.saved_message_set =        {'cmd:':None, 'cnt':None, 'pages':[[{'x':0,  'y':0,  'size':18, 'text':"Warning"},
                                                                            {'x':10, 'y':20, 'size':12, 'text':"Message set Restored"},
                                                                            {'x':10, 'y':32, 'size':12, 'text':"before Saved"}]]}


    def start(self):
        self.this_thread = Thread(target=self.message_loop, name=self.name, daemon=True)    # daemon so that if the main thread errors this thread is auto-killed, avoiding hang
        self.this_thread.start()
        pioled_logger.debug (f"pioled message_loop thread created")
        return self.this_thread


    def blank(self):
        pioled_logger.debug ("pioled_blank")
        self.message_page([[0, 0, 12, '']])     # Not sent thru the queue as the blank would be saved and restored
        time.sleep (0.01)                       # Allow time for blank to be processed


    def oneliner(self, x, y, size, text, message_time=0, font=None, color=None, cmd=None):
        # message_time is blocking to the main code.  Alternately send thru the queue with a second blank page.
        pioled_logger.debug (f"pioled_message - <{text}>")
        self.queue.put ({'cmd':cmd, 'pages':[[{'x':x, 'y':y, 'size':size, 'text':text, 'font':font, 'color':color}]]})
        if message_time:
            time.sleep (message_time)
            self.blank()
        else:
            time.sleep (0.01)                   # Allow time for queue to be processed


    def message_loop(self):
        """Run this functions in a thread, sending a full set of message pages thru the queue
        per the `cmd` and `cnt` settings.

        New message is displayed in < 0.15 sec
        """

        message_set = {'cmd:':None, 'cnt':None, 'pages':[]}
        while True:                                                 # "Top-level Loop While"
            prior_message_set = message_set
            message_set = self.queue.get()
            pioled_logger.debug (f"Received message_set: <{message_set}>")

            try:
                cmd = message_set.get('cmd', PIOLED_NEWMSG)
                if cmd == PIOLED_SAVE:
                    self.saved_message_set = prior_message_set
                    pioled_logger.debug ("Prior pioled message_set saved")
                if cmd == PIOLED_RESTORE:
                    message_set = self.saved_message_set
                    pioled_logger.debug ("Prior pioled message_set restored")

                cnt = message_set.get('cnt', -1)                    # Default loop endlessly
                pages = message_set.get('pages', None)

                if cmd == PIOLED_TH_EXIT:
                    if pages is not None:
                        self.message_page(pages[0])
                    else:
                        self.blank()
                    time.sleep (0.01)                               # Allow time for queue to be processed
                    pioled_logger.debug ("pioled message_loop() exiting")
                    sys.exit()                                      # On exit the locks are still set, cleared by the server
                
                elif cmd == PIOLED_TH_PAUSE:
                    if pages is not None:
                        self.message_page(pages[0])
                    else:
                        self.blank()
                    pioled_logger.debug ("pioled message_loop() paused")

                elif pages is None:
                    pioled_logger.debug ("Empty pages - blanking display")
                    self.blank()

                else:                                               # PIOLED_NEWMSG, PIOLED_SAVE, PIOLED_RESTORE
                    page_time =                 message_set.get('page_time', self.page_time)
                    inter_page_time =           message_set.get('inter_page_time', self.inter_page_time)
                    inter_message_set_time =    message_set.get('inter_message_set_time', self.inter_message_set_time)
                    pioled_logger.debug (f"Timings:  page_time={page_time}, inter_page_time={inter_page_time}, inter_message_set_time={inter_message_set_time}")
                    len_pages = len(pages)
                    while cnt != 0:                                 # "Iterate Pages While"
                        for index in range(len_pages):              # "For Pages"
                            self.message_page(pages[index])
                            wait_until = datetime.datetime.now() + datetime.timedelta(seconds=page_time)
                            while datetime.datetime.now() < wait_until:
                                if not self.queue.empty():          # Break wait if new message in queue
                                    break
                                time.sleep (0.1)

                            if not self.queue.empty():              # Break "For Pages" loop if new message in queue
                                break

                            if len_pages == 1:                      # If just single page, then leave it up and break out of "For Pages"
                                break


                            # Blank between individual pages or between full pages list repeat
                            wait_time = inter_page_time  if index < len_pages -1  else  inter_message_set_time
                            if wait_time > 0:                       # NOTE - inter_message_set_time = 0 leaves last page on display
                                self.blank()
                                wait_until = datetime.datetime.now() + datetime.timedelta(seconds=wait_time)
                                while datetime.datetime.now() < wait_until:
                                    if not self.queue.empty():      # Break wait if new message in queue
                                        break
                                    time.sleep (0.1)

                            if not self.queue.empty():              # Break "For Pages" loop if new message in queue
                                break

                        else:                                       # Code run on non-break "For Pages" exit
                            if cnt != -1:
                                cnt -= 1
                            continue                                # Continue "Iterate Pages While"

                        self.queue.task_done()                      # Code run on "For Pages" break
                        break                                       # Break "Iterate Pages While"
            except Exception as e:
                pioled_logger.warning (f"Failed to parse/display pioled message <{message_set}> - Skipping\n  {type(e).__name__}: {e}")
                self.queue.task_done()


    def message_page(self, message_list, message_time=0):
        # message_time is blocking to the main code if not sent thru a queue to pioled message_loop
        # returns 0 on success, 1 on failure
        xx = ""
        for line in message_list:
            if isinstance(line, list):
                xx += f"{{'x':{line[0]}, 'y':{line[1]}, 'size':{line[2]}, 'text':'''{line[3]}'''}}\n"
            elif isinstance(line, dict):
                xx += str(line) + '\n'
            else:
                pioled_logger.warning (f"Expecting list or dict, found type {type(line)}: <{line}> - Skipping\n  {message_list}")
                return 1

        if not pioled_shm_lock.get_lock(lock_info=self.toolname + ' - message_page'):
            periodic_log(f"Failed to get pioled_shm_lock. Current lock owner: <{pioled_shm_lock.get_lock_info()}> - Skipping",
                         category='get pioled_shm_lock', logger_name='pioled_logger', log_interval='1h', log_level=logging.WARNING)
            return 1

        pioled_logger.debug (f"Writing to shared memory block:\n{xx[:-1]}")      # trim off final \n

        try:
            pioled_shm.set_lock_info(xx)
        except Exception as e:
            periodic_log(f"Unable to access shared memory block - Skipping\n  {type(e).__name__}: {e}",
                         category='write pioled_shm', logger_name='pioled_logger', log_interval='1h', log_level=logging.WARNING)
            pioled_shm_lock.unget_lock(where_called='message_page failed to write the display file')
            return 1

        pioled_go_flag.get_lock(lock_info=self.toolname + ' - message_page')

        if message_time > 0:
            time.sleep(message_time)
            self.blank()

        return 0




#=====================================================================================
#=====================================================================================
#   S E R V E R
#=====================================================================================
#=====================================================================================

def service():
    """ Display content of shared memory pioled_shm
    """

    global pioled_disp                                      # Used in _oneliner() service_int_handler()
    global pioled_go_flag, pioled_shm_lock, pioled_shm

    signal.signal(signal.SIGINT,  service_int_handler)      # Ctrl-C
    signal.signal(signal.SIGTERM, service_int_handler)      # kill <pid>

    pioled_disp = pioled()
    _oneliner("PiOLED service started")
    time.sleep(2)
    _oneliner("")
    logging.debug (pioled_disp)

    pioled_shm_lock.unget_lock (where_called="PiOLED service startup", force=True)  # Restarting the server will force unget the locks
    pioled_go_flag.unget_lock  (where_called="PiOLED service startup", force=True)

    while 1:
        if pioled_go_flag.is_locked():
            try:
                contents = pioled_shm.get_lock_info()[:-1]          # drop final \n
                logging.debug (f"PiOLED Server received at {datetime.datetime.now()}\n{contents}")

                with canvas(pioled_disp.device) as draw:
                    for line in contents.split('\n'):
                        _line = ast.literal_eval(line)              # convert text to dict
                        x =     _line['x']
                        y =     _line['y']
                        size =  _line['size']
                        text =  _line['text']

                        try:
                            font_size = known_fonts.get_font(_line['font'], size)
                        except:
                            font_size = known_fonts.get_font(config.getcfg('Default_font', DISPLAY_DRIVER_FONT), size)  # TODO rework defaults
                        color = _line['color']  if ('color' in _line  and  _line['color'] is not None)  else config.getcfg('Default_color', DISPLAY_DRIVER_COLOR)

                        draw.text((x, y), text, font=font_size, fill=color)

            except Exception as e:
                logging.warning (f"Error processing contents: {contents}\n  {type(e).__name__}: {e}")

            pioled_go_flag.unget_lock  (where_called='service loop end', force=True)
            pioled_shm_lock.unget_lock (where_called='service loop end', force=True)

        time.sleep(0.01)


def _oneliner(text, color='white'):
    """Private version used in service and service_int_handler"""
    logging.debug (f"<{text}>")
    with canvas(pioled_disp.device) as draw:
        draw.text((0, 0), text, font=known_fonts.get_font(DISPLAY_DRIVER_FONT, 12), fill=color)


def service_int_handler(signal, frame):
    logging.warning(f"Signal {signal} received.  Exiting.")
    _oneliner("PiOLED service exiting")
    time.sleep(2)
    pioled_shm_lock.unget_lock (where_called='service_int_handler', force=True)
    pioled_go_flag.unget_lock  (where_called='service_int_handler', force=True)
    sys.exit(0)     # Display is cleared by luma when the service process terminates


#=====================================================================================
#=====================================================================================
#   c l a s s   p i o l e d
#=====================================================================================
#=====================================================================================

class pioled:
    """ Interact with the luma.oled driver
    """

    def __init__(self):
        global known_fonts
        # Import luma config and instantiate self.device
        if 'create_device args' not in config.sections():
            logging.error (f"Missing section 'create_device args' in the config file - Aborting")
            sys.exit(1)

        self.device_args = SimpleNamespace()
        for key in config.cfg['create_device args']:
            setattr(self.device_args, key, config.cfg['create_device args'][key])

        logging.debug (f"self.device_args: <{self.device_args}>")
        self.device = cmdline.create_device(self.device_args)

        known_fonts = pioled_font_manager()


    def __repr__(self):
        iface = ''
        display_types = cmdline.get_display_types()
        if self.device_args.display not in display_types['emulator']:
            iface = f"Interface: {self.device_args.interface}\n"

        lib_name = cmdline.get_library_for_display_type(self.device_args.display)
        if lib_name is not None:
            lib_version = cmdline.get_library_version(lib_name)
        else:
            lib_name = lib_version = 'unknown'

        import luma.core
        version = f"luma.{lib_name} {lib_version} (luma.core {luma.core.__version__})"
        
        return f"Version: {version}\nDisplay: {self.device_args.display}\n{iface}Dimensions: {self.device.width} x {self.device.height}\n"


#=====================================================================================
#=====================================================================================
#   c l a s s   p i o l e d _ f o n t _ m a n a g e r
#=====================================================================================
#=====================================================================================

class pioled_font_manager:
    """ Create and provide unique combinations of fonts and sizes
    """
    def __init__(self):
        self.known_fonts =  {}
        self.fonts_path =   Path (ir_files(core.tool.main_module)) / "fonts"
        self.default_font = self.fonts_path / config.getcfg('Default_font', DISPLAY_DRIVER_FONT)
        self.default_size = config.getcfg('Default_size', DISPLAY_DRIVER_SIZE)

        if not self.default_font.exists():
            logging.error (f"Default font <{self.default_font} not found - Aborting.")
            sys.exit(1)
        

    def get_font (self, font_name, size):
        font_name_size = font_name + '_' + str(size)
        if not font_name_size in self.known_fonts:
            try:
                self.known_fonts[font_name_size] = ImageFont.truetype(self.fonts_path / font_name, size)
                logging.debug (f"Created known_font <{font_name_size}>")
            except Exception as e:
                logging.warning (f"Failed creating known_font <{font_name_size}> - Using default font and size\n  {type(e).__name__}: {e}")
                self.known_fonts[font_name_size] = ImageFont.truetype(self.fonts_path / self.default_font, self.default_size)
                # TODO any chance of failure?
        
        return self.known_fonts[font_name_size]


#=====================================================================================
#=====================================================================================
#   c l i
#=====================================================================================
#=====================================================================================

def cli():
    """**** PiOLED's interactive commands ****

    status      Display the state of the server process, and the ipc semaphores
    unlock      Release the ipc semaphores, which are normally released by the server process
    taillog     Print the tail (last 50 lines) of the server log file
    blank       Clear the display
    message     Display a multi-line message on the display, supporting list and dictionary formats - Example:
            PiOLED message "[0, 0, 18, 'Wherever you go...'], {'x':10, 'y':20, 'size':20, 'text':'there you are.', 'font':'ProggyTiny.ttf'}"
"""

    global config, args
    global logging
    global pioled_logger
    global pioled_go_flag, pioled_shm_lock, pioled_shm


    commands = ['message', 'blank', 'status', 'unlock', 'taillog']
    parser = argparse.ArgumentParser(description=cli.__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('Command', nargs='?', choices=commands,
                        help=f"Interactive mode Command")
    parser.add_argument('Message', nargs='?',
                        help=f"Message content for Command 'message' - see PiOLED.md for format")

    parser.add_argument('--service', action='store_true',
                        help="Start PiOLED server")
    parser.add_argument('--config-file', '-c', type=str, default=CONFIG_FILE,
                        help=f"Path to the server config file (Default <{CONFIG_FILE}> in user config directory)")
    parser.add_argument('--log-console', '-z', action='store_true',
                        help="Force server logging to the console, overriding config LogFile param")
    parser.add_argument('--val-logfile', default=None,
                        help=f"Path to server log file (abs or rel to core.tool.log_dir_base) used for validation testing (overrides LogFile in config file, default <{None}>)")
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help="Log status and activity messages (-vv for debug logging)")

    parser.add_argument('--setup-user', action='store_true',
                        help="Install starter files in user space")
    parser.add_argument('--version', '-V', action='version', version=f"{core.tool.toolname} {__version__}",
                        help="Return version number and exit")
    args = parser.parse_args()

    if args.Command is None  and  not args.service  and  not args.setup_user:
        parser.print_help()
        sys.exit()


    # Deploy starter files
    if args.setup_user:
        logging.getLogger('cjnfuncs.deployfiles').setLevel(logging.INFO)
        deploy_files([
            { 'source': CONFIG_FILE,             'target_dir': 'USER_CONFIG_DIR', 'file_stat': 0o644, 'dir_stat': 0o755},
            { 'source': 'PiOLED_server.service', 'target_dir': 'USER_CONFIG_DIR', 'file_stat': 0o644},
            ]) #, overwrite=True)
        sys.exit()


    # Load config file and setup logging
    call_logfile_override = True  if (not args.service  or  args.log_console  or  args.val_logfile)  else False
    try:
        config = config_item(args.config_file)
        config.loadconfig(call_logfile_wins=call_logfile_override, call_logfile=args.val_logfile)
    except Exception as e:
        logging.exception(f"Failed loading config file <{args.config_file}> - Aborting\n  {type(e).__name__}: {e}")
        sys.exit(1)


    logging.warning (f"========== {core.tool.toolname} ({__version__}), pid {os.getpid()} ==========")


    # ----------- S e r v i c e / S e r v e r   m o d e -----------
    if args.service:
        ll = [config.getcfg('LogLevel', logging.WARNING), logging.INFO, logging.DEBUG][args.verbose]
        set_logging_level (ll)                                          # Set root logger level for the server process
        set_logging_level (ll, logger_name='cjnfuncs.resourcelock')     # info level logs pioled_go_flag and pioled_file_lock handles

        if args.val_logfile:
            # setuplogging (call_logfile=args.val_logfile, call_logfile_wins=True, FileLogFormat=SERVER_CONS_LOGGING_FORMAT)
            setuplogging (call_logfile=args.val_logfile, call_logfile_wins=True, FileLogFormat=SERVER_FILE_LOGGING_FORMAT)
        service()                                                                           # service never returns


    # ----------- Interactive Commands setups  -----------
    setuplogging(ConsoleLogFormat=CLI_CONSOLE_LOGGING_FORMAT)
    ll = [logging.WARNING, logging.INFO, logging.DEBUG][args.verbose]
    set_logging_level (ll, logger_name='cjn_PiTools.PiOLED')
    set_logging_level (ll, logger_name='cjnfuncs.resourcelock')
    

    # ----------- S T A T U S -----------
    if args.Command == 'status':
        import subprocess
        print ("-----------------------------")
        print (f"\n{subprocess.run(['systemctl', 'status', 'PiOLED_server'],  capture_output=True, text=True).stdout}")
        print ("-----------------------------")
        print (f"\nPiOLED_go_flag is currently set?   <{pioled_go_flag.is_locked()}>,  last locked by: <{pioled_go_flag.get_lock_info()}>")
        print (f"\npioled_shm_lock is currently set?  <{pioled_shm_lock.is_locked()}>,  last locked by: <{pioled_shm_lock.get_lock_info()}>")
        print ("-----------------------------")
        sys.exit()


    # ----------- U N L O C K -----------
    if args.Command == 'unlock':
        print (f"Before forced unlock:  PiOLED_go_flag is currently set?      <{pioled_go_flag.is_locked()}>")
        pioled_go_flag.unget_lock(force=True, where_called='PiOLED.main - UNLOCK forced unlock')
        print (f"After  forced unlock:  PiOLED_go_flag is currently set?      <{pioled_go_flag.is_locked()}>")
        print (f"Before forced unlock:  pioled_shm_lock is currently locked? <{pioled_shm_lock.is_locked()}>")
        pioled_shm_lock.unget_lock(force=True, where_called='PiOLED.main - UNLOCK forced unlock')
        print (f"After  forced unlock:  pioled_shm_lock is currently locked? <{pioled_shm_lock.is_locked()}>")
        sys.exit()


    # ----------- T A I L L O G -----------
    if args.Command == 'taillog':

        try:
            logfile = mungePath(config.getcfg('LogFile'), core.tool.log_dir_base).full_path
            nlines = config.getcfg("PrintLogLength", PRINT_LOG_LENGTH_DEFAULT)
            print (f"Tail of  <{logfile}>:")
            _xx = collections.deque(logfile.open(), nlines)
            for line in _xx:
                print (line, end="")
        except Exception as e:
            print (f"Couldn't print the log file.  LogFile defined in the config file?\n  {type(e).__name__}: {e}")
        sys.exit()


    import queue
    pioled_q =  queue.Queue()
    pioled =    pioled_display_driver(pioled_q, toolname=TOOLNAME)
    pioled.start()

    # ----------- B L A N K -----------
    if args.Command == 'blank':
        pioled.blank()


    # ----------- M E S S A G E -----------
    if args.Command == 'message':
        try:
            message = args.Message.strip()
            if not (message.startswith('[')  or  message.startswith('{')):      # 0, 0, 12, 'Wherever you go...'
                message = '[' + message + ']'                                   # [0, 0, 12, 'Wherever you go...']
            message = '[' + message + ']'                                       # [[0, 0, 12, 'Wherever you go...']]
            message = ast.literal_eval(message)                                 # <class 'list'> - [[0, 0, 12, 'Wherever you go...']]
            pioled.message_page(message)
        except Exception as e:
            logging.error (f"Failed to process message <{args.Message}>:\n  {type(e).__name__}: {e}")


if __name__ == '__main__':
    sys.exit(cli())
