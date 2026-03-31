# initW1buses - Initialize the W1 bus(es) and set write permission on found therm_bulk_read file(s)

Why?  On a fresh boot the kernel will scan for W1 devices on the buses defined in /`boot/config.txt`.  This leaves two problems:
  1. If the power to the W1 devices was not yet turned on at boot then no devices will be found, and
  2. In the case of the DS18B20 temp sensors, the `bulk_convert_trigger` function cannot be used because the `therm_bulk_read` file is write protected.

The initW1buses module addresses these two problems by:
  1. Optionally setting a specified GPIO pin to output mode, logic 0 or 1 (this may be used to enable a relay that powers up W1 devices), and
  2. Setting world-write permission on the `therm_bulk_read` file(s).



<br>

## Setup / Installation

If (and only if) you wish to use the DS18B20 bulk read trigger capability as a non-privileged user, then install `initW1buses.service`, as follows:

1. Run the initial user setup:  `initW1buses --setup-user`.  This will extract `/home/<me>/.config/initW1buses/initW1buses.service` from the package distribution.

1. Adjust `initW1buses.service` for the path to the initW1buses file stub/alias (per `which initW1buses`).  Also optionally specify a GPIO pin to be driven high or low using the `--GPIO` switch (`--HiLo` defaults to 1), and optionally change the `--delay` time to allow all W1 devices to be found by the kernel.

1. Install `initW1buses.service` into systemd:
   - `sudo cp initW1buses.service /etc/systemd/system; sudo systemctl daemon-reload; sudo systemctl enable --now initW1buses.service`


<br>

## CLI

The default operation of initW1buses is to do the initialization steps listed below.  NOTE that initialization requires root privilege in order to modify permission on the therm_bulk_read file.  Alternately, `--status` and `--setup-user`
may be run - these bypass initialization and do not require root privilege.

```
$ initW1buses --help
usage: initW1buses [-h] [-G GPIO] [-S HILO] [-d DELAY] [-s] [--setup-user] [-V]

initW1busses

1. Optionally enable power to the W1 bus(es) by setting a GPIO to 1 or 0
2. Delay to allow the kernel to scan for W1 devices, and 
3. Set user write permissions on therm_bulk_read for each found bus.

Run at boot via systemd.
1.1

optional arguments:
  -h, --help            show this help message and exit
  -G GPIO, --GPIO GPIO  Optional GPIO pin number to be set to drive --HiLo before the delay time
  -S HILO, --HiLo HILO  Set the --GPIO pin drive state to 0 or 1 (default 1)
  -d DELAY, --delay DELAY
                        Delay time in seconds before setting therm_bulk_read permission (default 20)
  -s, --status          Display status of W1 buses initialization
  --setup-user          Install starter files in user space
  -V, --version         Print version number and exit
```

The status output should look like this:

```
$ initW1buses --status
--------- Service status --------------------

● initW1buses.service - Initialize W1 busses therm_bulk_read permission
     Loaded: loaded (/etc/systemd/system/initW1buses.service; enabled; vendor preset: enabled)
     Active: active (exited) since Sun 2026-03-29 07:34:01 MST; 1 day 4h ago
    Process: 352 ExecStart=/home/<me>/devel/venvs/pydev-3.9/bin/initW1buses --GPIO 21 (code=exited, status=0/SUCCESS)
   Main PID: 352 (code=exited, status=0/SUCCESS)
        CPU: 1.057s

Mar 29 07:33:39 testhost systemd[1]: Starting Initialize W1 busses therm_bulk_read permission...
Mar 29 07:33:41 testhost initW1buses[352]:     initW1buses.cli                  -  WARNING:  Set GPIO <21> to drive <1>
Mar 29 07:33:41 testhost initW1buses[352]:     initW1buses.cli                  -  WARNING:  Waiting 20 seconds for W1 devices discovery
Mar 29 07:34:01 testhost initW1buses[352]:     initW1buses.cli                  -  WARNING:  Found and enabled write access to </sys/devices/w1_bus_master1/therm_bulk_read>
Mar 29 07:34:01 testhost systemd[1]: Finished Initialize W1 busses therm_bulk_read permission.

--------- Found buses and sensors --------------------
/sys/devices/w1_bus_master1
    /sys/devices/w1_bus_master1/therm_bulk_read:   <-rw-rw-rw->
    Sensors
        /sys/devices/w1_bus_master1/28-0b228004203c
        /sys/devices/w1_bus_master1/28-0b2280337113
```