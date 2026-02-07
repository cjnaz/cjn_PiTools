# initW1buses - Initialize the W1 buses and set write permission on found therm_bulk_read file(s)

Why?  On a fresh boot the kernel will scan for W1 devices on the buses defined in /`boot/config.txt`.  This leaves two problems:
  1. If the power to the W1 devices was not yet turned on at boot then no devices will be found, and
  2. In the case of the D18B20 temp sensors, the `bulk_convert_trigger` function cannot be used because the `therm_bulk_read` file is write protected.

The initW1buses module addresses these two problems by:
  1. Optionally setting a specified GPIO pin to output mode, logic 1 (this may be used to enable a relay that powers up W1 devices), and
  2. Enabling world-write permission on the `therm_bulk_read` file(s).



<br>

## Setup / Installation

If (and only if) you wish to use the DS18B20 bulk read trigger capability then install `initW1buses.service`, as follows:

1. After installing the cjn_PiTools package...

1. Run the initial user setup:  `initW1buses --setup-user`.  This will extract `/home/<me>/.config/initW1buses/initW1buses.service` from the package distribution.

1. Adjust `initW1buses.service` for the path to initW1buses stub/alias (per `which initW1buses`).  Also optionally specify a GPIO pin to be driven to logic 1 using the `--GPIO` switch, and optionally change the delay time to allow all W1 devices to be found by the kernel.

1. Install `initW1buses.service` into systemd:
   - `sudo cp initW1buses.service /etc/systemd/system; sudo systemctl daemon-reload; sudo systemctl enable --now initW1buses.service`


<br>

## CLI

```
$ initW1buses --help
usage: initW1buses [-h] [-g GPIO] [-d DELAY] [--setup-user] [-V]

initW1busses

1. Optionally enable power to the W1 bus(es) by setting a GPIO,
2. Delay to allow the kernel to scan for W1 devices, and 
3. Set user write permissions on therm_bulk_read for each found bus.

Run at boot via systemd.
1.0

optional arguments:
  -h, --help            show this help message and exit
  -g GPIO, --GPIO GPIO  Optional GPIO pin number to be set to output 1 before the delay time
  -d DELAY, --delay DELAY
                        Delay time in seconds before setting therm_bulk_read permission (default 20)
  --setup-user          Install starter files in user space
  -V, --version         Print version number and exit
```
