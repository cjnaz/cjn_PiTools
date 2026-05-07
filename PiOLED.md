# PiOLED - Display multi-line messages on a shared OLED display on Raspberry Pi

PiOLED utilizes the luma.oled package.  A notable limitation of luma.oled is that only one process
can talk to the display.  PiOLED solves this limitation by setting up a client-sever configuration, where the server is started at boot and various clients may send display messages to the server.

Notable features (and limitations):
- Designed and tested (and supported) on Raspberry Pi devices with SPI and I2C connected OLED displays supported by luma.oled (see https://luma-oled.readthedocs.io/en/latest/index.html).
- Displays 'pages' of text (no graphics) using TrueType fonts at user-specified locations and sizes.
- Multiple pages may be defined and are automatically cycled through without blocking the tool script code (using a background thread).


### My usage, as an example

I have a handful of tools that I run on Raspberry Pis...  Garden Watering System, Temperature Monitor for freezers, Power Monitor (tracks backup battery status and power outage notifications), PoolSolar (thermostat pump control), and a 'PiControl' tool that acts as the system administration interface.  My main circuit board (I2C Switch Bd) has a connector for the SPI port and three buttons for selecting which tool sends messages to the shared OLED display.  Here's a picture of my development/debug setup with a Pi Zero 2W (pardon the defective display, the blown out fuzzy text (picture artifact), and dust & clutter):

![pic](https://github.com/cjnaz/cjn_PiTools/blob/main/docs/Development_board_with_OLED.jpg)


Coordination between tool scripts for which has display access is beyond the scope of this documentation, but hints...  When activated by a button push PiControl sets a resourcelock semaphore that all other running tool scripts respect, and which tool script normally has the display is also controlled by button pushes.

<br/>

---

## PiOLED big picture architecture

PiOLED has three distinct modes/functions:

1. Your tool script imports the _pioled_display_driver_ class.  Using this class, the tool script creates a queue and starts a 
background thread to service the queued messages.  This thread, in turn, sets a _PiOLED_shm_lock_ IPC semaphore, writes a message page to shared memory and then
sets a _PiOLED_go_flag_ IPC semaphore (see `cjnfuncs.resourcelock`) to notify the server of a new page to display.

1. The _PiOLED display server_ is started at Raspberry Pi system boot.  The server monitors for the IPC semaphores and displays the message page found in shared memory, then clears the semaphores.

1. PiOLED also supports a _commmand line interface_, using the alias 'PiOLED', which can display a message page, blank the display, 
check status of the server and semaphores, and clear the semaphores.


<br>

---

## Setup / Installation

1. After installing the cjn_PiTools package...

1. Run the initial user setup:  `PiOLED --setup-user`.  This will create `/home/<me>/.config/PiOLED`, with two files:
   - `PiOLED_server.cfg` - Defines parameters for the PiOLED display server
   - `PiOLED_server.service` - A systemd service file for starting the PiOLED display server at boot

1. Customize `PiOLED_server.cfg` for your display specifics and specify the `LogFile` path.

1. Customize `PiOLED_server.service` for the installed path of the `PiOLED` command (shown by `which PiOLED`) and your User and Group settings, and install this file into systemd (`sudo cp PiOLED_server.service /etc/systemd/system; sudo systemctl daemon-reload; sudo systemctl enable --now PiOLED_server.service`).  This gets the server up and running.  Check server status with `PiOLED status`.

1. In your tool script import the driver class and instantiate it, then send page display messages through the queue:

      ```
      #!/usr/bin/env python3
      # PiOLED_README_ex.py available in the docs directory in the github repo

      import queue
      from cjn_PiTools.PiOLED import pioled_display_driver, PIOLED_TH_EXIT


      # Instantiate the local queue and thread
      pioled_q =          queue.Queue()
      pioled =            pioled_display_driver(pioled_q)
      pioled_th =         pioled.start()

      # Display a message and exit
      pioled_q.put ({'cmd':PIOLED_TH_EXIT, 'pages':[[[0, 0, 12, 'Hello my name is Marvin'],[10, 20, 12, "I'm so depressed..."]]]})

      # Exit cleanup code
      pioled_th.join()
      ```

<br>

---

## The _Message_set_ format

A _message_set_ is a dictionary of settings that are passed to the `pioled_display_driver` handler via the `pioled_q`.  This section lays out the details of the message_set format.  NOTE that this dictionary is parsed by the Python ast.literal_eval() library, and thus follows exactly Python's dictionary, list, string, int, float syntax rules.

Consider this message_set passed thru the queue:

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


<br>

### The keys in the message_set dictionary are:

Key | Purpose | Default
--- | --- | ---
'cmd' | Special operations, in addition to displaying 'pages' | None (only display pages)
'cnt' | How many times to loop display 'pages'. `'cnt':1` shows the pages once, then blanks the display. | -1 (loop endlessly until new queued message_set)
'pages' | Content to be displayed (see below) | None (blank the display)
'page_time' | Sets display time for each page in pages for just this message_set | See below
'inter_page_time' | Sets the blank time between each page for just this message_set | See below
'inter_message_set_time' | Sets the blank time between repeating all pages for just this message_set | See below

<br>

### The supported 'cmd' commands (names imported from cjn_PiTools.PiOLED):

'cmd' | Function
--- | ---
(no 'cmd') | Just display the 'pages' data
PIOLED_SAVE | Save the previous message_set for later restoration, and apply the new message_set content.
PIOLED_RESTORE | Restore the previously saved message_set.  All the other keys for the new message_set (that has 'cmd':PIOLED_RESTORE) are ignored.
PIOLED_PAUSE | Terminate any looping from the previous message_set and display _only the first page_ in the new 'pages' list (or blank the display if no 'pages' passed).
PIOLED_TH_EXIT | After displaying the _only the first page_ in the 'pages' list, then exit the pioled_th thread.  Do this for a clean exit at the end of your code.

<br>

### 'pages' formats

- The 'pages' key defines a **list** of pages to be sequentially displayed
- Each page is a **list** of text lines
- Each text line is a **list** of x, y, size, and text, or a **dict** with the same fields plus more options

For each text line, either the list or dict format may be used.  The list format uses default values for the font and color, while the dict format allows font and color to be specified.

term | Description | list format | dict format
--- | --- | --- | ---
x | x offset from top left corner | element [0] in the list, int value, required | `'x':0` int value, required
y | y offset from top left corner | element [1] in the list, int value, required | `'y':20` int value, required
size | size, as determined by the selected font | element [2] in the list, int value, required | `'size':15` int value, required
text | text string | element [3] in the list, str value, required | `'text':"string text"` str value, required
font | Name of TrueType font file | N/A - use the server config `Default_font` | `'font':"font file name"`, optional, default to server config `Default_font`
color | str [Common HTML color names](https://htmlcolorcodes.com/color-names/) | N/A - use the server config `Default_color` | `'color':"color name"`, optional, default to server config `Default_color`

Font files provided with cjn_PiTools:
- C&C Red Alert [INET].ttf
- code2000.ttf
- fontawesome-webfont.ttf
- GLECB.TTF
- pixelmix.ttf
- Volter__28Goldfish_29.ttf
- ChiKareGo.ttf
- FreePixel.ttf
- miscfs_.ttf
- ProggyTiny.ttf
- tiny.ttf

<br>

### Page timing controls

When `pioled_display_driver` is instantiated the default timings may be specified.  Also, the timings may be specified on each individual queued message_set.

Order of precedence:
1. A value specified on the queued message_set is the highest precedent, and overrides any value specified on the pioled_display_driver instantiation, or the Default value.
2. A value specified on the pioled_display_driver instantiation overrides the Default value.
3. The Default value is used.

term | Default value | Description 
--- | --- | ---
page_time | 7 seconds | How long to display each individual page before blanking or proceeding to the next page in the pages list 
inter_page_time | 0.3 seconds | How long blank before proceeding to the next page in the pages list
inter_message_set_time  | 1 second| When repeating the full pages sequence, how long to blank before displaying the first page in the pages list

Note that if there is only one page it is displayed without blanking, and the 'cnt' key is ignored.


<br/>

---

## Command Line Interface

```
$ PiOLED -h
usage: PiOLED [-h] [--service] [--config-file CONFIG_FILE] [--log-console] [--val-logfile VAL_LOGFILE] [--verbose] [--setup-user] [--version]
              [{message,blank,status,unlock,taillog}] [Message]

**** PiOLED's interactive commands ****

    status      Display the state of the server process, and the ipc semaphores
    unlock      Release the ipc semaphores, which are normally released by the server process
    taillog     Print the tail (last 50 lines) of the server log file
    blank       Clear the display
    message     Display a multi-line message on the display, supporting list and dictionary formats - Example:
            PiOLED message "[0, 0, 18, 'Wherever you go...'], {'x':10, 'y':20, 'size':20, 'text':'there you are.', 'font':'ProggyTiny.ttf'}"
1.2

positional arguments:
  {message,blank,status,unlock,taillog}
                        Interactive mode Command
  Message               Message content for Command 'message' - see PiOLED.md for format

optional arguments:
  -h, --help            show this help message and exit
  --service             Start PiOLED server
  --config-file CONFIG_FILE, -c CONFIG_FILE
                        Path to the server config file (Default <PiOLED_server.cfg> in user config directory)
  --log-console, -z     Force server logging to the console, overriding config LogFile param
  --val-logfile VAL_LOGFILE
                        Path to server log file (abs or rel to core.tool.log_dir_base) used for validation testing (overrides LogFile in config file, default <None>)
  --verbose, -v         Log status and activity messages (-vv for debug logging)
  --setup-user          Install starter files in user space
  --version, -V         Return version number and exit
```

`PiOLED message` supports only a single page display, with these format variations...
  - Minimally, `PiOLED message "0, 0, 18, 'Wherever you go...'"`, without `[]` around the message definition.
    - Note the the surrounding quotes `"..."` are required to avoid the shell trying to decipher the message.  Watch out shell special characters, such as `!`.
  
  - `[]` around the message definition is also accepted:  `PiOLED message "[0, 0, 18, 'Wherever you go...']"`
  
  - A multi-line page looks like:  `PiOLED message "[0, 0, 18, 'Wherever you go...'], [0, 20, 15, 'there you are.']"`
  
  - Dictionary format (and a mix with list format) is supported:  `PiOLED message "[0, 0, 18, 'Wherever you go...'], {'x':0, 'y':20, 'size':24, 'text':'there you are.', 'font':'ProggyTiny.ttf'}"`

<br/>

---

## Lower level details
- Three IPC hooks are used between the pioled_display_driver (instantiated in the tool script) and the PiOLED display server:
  - `PiOLED_shm` is created by resourcelock, but only the companion shared memory block is used.  This shared memory 
  block is used to send new display page data from the pioled_display_driver to the PiOLED display server.
  - `PiOLED_shm_lock` is requested by the tool script (within pioled_display_driver) before writing the new display page to PiOLED_shm.
  - `PiOLED_go_flag` is set by the tool script (within pioled_display_driver) to tell the PiOLED server to process the new display page.
  - After being displayed, the server releases first the `PiOLED_shm_lock` and then the `PiOLED_go_flag`.

These locks may be cleared by the PiOLED CLI command:

      PiOLED unlock, or within code:

or using the resourcelock CLI commands:

      resourcelock PiOLED_shm_lock unget
      resourcelock PiOLED_go_flag unget

- Errors in message_sets that are flagged by the PiOLED server, such as can't find the font file, or bad font size, are logged to the server log file as warnings, not to the tool script log file.

<br/>

---

## Debug logging

Debug logging may be enabled for both the server and the client-side code into a combined stream to the console.  Logging to a file may also be done (see the `tests/PiOLED-demo.py` doc string).

1. Run the server with debug logging and output to the console:

        $ PiOLED --service --log-console -vv &

2. Within the tool-script, enable debug logging from the pioled_display_driver code:

        logging.getLogger('cjn_PiTools.PiOLED').setLevel(logging.DEBUG)

3. Debug logging of the cjnfuncs.resourcelock transactions may also be enabled:

        logging.getLogger('cjnfuncs.resourcelock').setLevel(logging.DEBUG)

Note that the server logs use a '*' separator, while the client-side code uses a '-' separator.  Some log lines may shift in sequence due to combining the logging streams of two separate processes.

This example shows server startup (before Test Init) and shutdown (Cleanup section), pioled_display_driver thread startup (Test Init section), and the sequence to display a message page (Test number 52 section):

```
$ PiOLED --service --log-console -vv &
[1] 4894
(pydev-3.9) cjn@testhost:~/devel/cjn_PiTools $          PiOLED.cli                  *  WARNING:  ========== PiOLED (1.2), pid 4894 ==========
         PiOLED.__init__             *    DEBUG:  self.device_args: <namespace(config=None, display='ssd1309', width=128, height=64, rotate=2, interface='spi', i2c_port=1, i2c_address='0x3C', spi_port=0, spi_device=1, spi_bus_speed=8000000, spi_mode=0, spi_transfer_size=4096, spi_cs_high=False, ftdi_device='ftdi://::/1', framebuffer_device='/dev/fd0', gpio=None, gpio_mode=None, gpio_data_command=6, gpio_chip_select=24, gpio_reset=5, gpio_backlight=18, gpio_reset_hold_time=0, gpio_reset_release_time=0, block_orientation=0, mode='RGB', framebuffer='diff_to_previous', num_segments=4, bgr=False, inverse=False, h_offset=0, v_offset=0, backlight_active='low', debug=False, transform='scale2x', scale=2, duration=0.01, loop=0, max_frames=None)>
         PiOLED._oneliner            *    DEBUG:  <PiOLED service started>
         PiOLED.get_font             *    DEBUG:  Created known_font <C&C Red Alert [INET].ttf_12>
         PiOLED._oneliner            *    DEBUG:  <>
         PiOLED.service              *    DEBUG:  Version: luma.oled 3.15.0 (luma.core 2.5.3)
Display: ssd1309
Interface: spi
Dimensions: 128 x 64

   resourcelock.unget_lock           *    DEBUG:  <PiOLED_shm_lock> Extraneous lock unget request ignored  <PiOLED service startup>
   resourcelock.unget_lock           *    DEBUG:  <PiOLED_go_flag> Extraneous lock unget request ignored  <PiOLED service startup>


$ ./PiOLED-demo.py -t 52 -vv
2026-05-06 22:05:19,678          PiOLED.start                -    DEBUG:  pioled message_loop thread created
2026-05-06 22:05:19,679     PiOLED-demo.print_test_header    -  WARNING:  

======================================================================================================
***** Test number 52: Demo single message via queue - dict format *****

2026-05-06 22:05:19,680          PiOLED.message_loop         -    DEBUG:  Received message_set: <{'pages': [[{'x': 0, 'y': 0, 'size': 20, 'text': "Hello'"}, [100, 50, 12, '52']]]}>
2026-05-06 22:05:19,680          PiOLED.message_loop         -    DEBUG:  Timings:  page_time=1, inter_page_time=0.2, inter_message_set_time=2
2026-05-06 22:05:19,681    resourcelock.get_lock             -    DEBUG:  <PiOLED_shm_lock> lock request successful - Granted         <2026-05-06 22:05:19.681272 - PiOLED_demo - message_page>
2026-05-06 22:05:19,681          PiOLED.message_page         -    DEBUG:  Writing to shared memory block:
{'x': 0, 'y': 0, 'size': 20, 'text': "Hello'"}
{'x':100, 'y':50, 'size':12, 'text':'''52'''}
2026-05-06 22:05:19,682    resourcelock.get_lock             -    DEBUG:  <PiOLED_go_flag> lock request successful - Granted         <2026-05-06 22:05:19.682528 - PiOLED_demo - message_page>
         PiOLED.service              *    DEBUG:  PiOLED Server received at 2026-05-06 22:05:19.688670
{'x': 0, 'y': 0, 'size': 20, 'text': "Hello'"}
{'x':100, 'y':50, 'size':12, 'text':'''52'''}
         PiOLED.get_font             *    DEBUG:  Created known_font <C&C Red Alert [INET].ttf_20>
   resourcelock.unget_lock           *    DEBUG:  <PiOLED_go_flag> lock force released  <service loop end>
   resourcelock.unget_lock           *    DEBUG:  <PiOLED_shm_lock> lock force released  <service loop end>
2026-05-06 22:05:21,681          PiOLED.message_loop         -    DEBUG:  Received message_set: <{'cmd': -99, 'pages': [[{'x': 20, 'y': 20, 'size': 18, 'text': 'Exited'}, [100, 50, 12, '52']]]}>
2026-05-06 22:05:21,682    resourcelock.get_lock             -    DEBUG:  <PiOLED_shm_lock> lock request successful - Granted         <2026-05-06 22:05:21.682273 - PiOLED_demo - message_page>
2026-05-06 22:05:21,683          PiOLED.message_page         -    DEBUG:  Writing to shared memory block:
{'x': 20, 'y': 20, 'size': 18, 'text': 'Exited'}
{'x':100, 'y':50, 'size':12, 'text':'''52'''}
2026-05-06 22:05:21,685    resourcelock.get_lock             -    DEBUG:  <PiOLED_go_flag> lock request successful - Granted         <2026-05-06 22:05:21.684962 - PiOLED_demo - message_page>
         PiOLED.service              *    DEBUG:  PiOLED Server received at 2026-05-06 22:05:21.694609
{'x': 20, 'y': 20, 'size': 18, 'text': 'Exited'}
{'x':100, 'y':50, 'size':12, 'text':'''52'''}
2026-05-06 22:05:21,697          PiOLED.message_loop         -    DEBUG:  pioled message_loop() exiting
2026-05-06 22:05:21,698     PiOLED-demo.<module>             -  WARNING:  

---- Cleanup --------------------------------------------------------
         PiOLED.get_font             *    DEBUG:  Created known_font <C&C Red Alert [INET].ttf_18>
   resourcelock.unget_lock           *    DEBUG:  <PiOLED_go_flag> lock force released  <service loop end>
   resourcelock.unget_lock           *    DEBUG:  <PiOLED_shm_lock> lock force released  <service loop end>
(pydev-3.9) cjn@testhost:/mnt/share/dev/packages/cjn_PiTools/tests $ fg
PiOLED --service --log-console -vv	(wd: ~/devel/cjn_PiTools)
^C         PiOLED.service_int_handler  *  WARNING:  Signal 2 received.  Exiting.
         PiOLED._oneliner            *    DEBUG:  <PiOLED service exiting>
   resourcelock.unget_lock           *    DEBUG:  <PiOLED_shm_lock> Extraneous lock unget request ignored  <service_int_handler>
   resourcelock.unget_lock           *    DEBUG:  <PiOLED_go_flag> Extraneous lock unget request ignored  <service_int_handler>
```