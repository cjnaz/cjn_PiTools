#!/usr/bin/env python3
"""Demo/test for MCP23008

Produce / compare to golden results:
    ./MCP23008-demo.py > testrun.log

    Expected differences:
        During init, GPIO may read 0b11110000 due to floating input pins pulled high in prior testing
        pi_i2c object addresses in test 13
"""

#==========================================================
#
#  Chris Nelson, Copyright 2026
#
# 1.0 260401 - New
#
#==========================================================

__version__ =   '1.0'
TOOLNAME =      'MCP23008_demo'

import argparse
import re
import time
import pigpio

from cjnfuncs.core              import set_toolname, setuplogging, logging, set_logging_level
from cjn_PiTools.shared         import pi_i2c
from cjn_PiTools.PCA9548        import PCA9548
from cjn_PiTools.MCP23008       import MCP23008


PCA9548_RESBD =         {'addr': 0x71, 'name': 'PCA9548_Res'}
PCA9548_IRRBD =         {'addr': 0x75, 'name': 'PCA9548_Irr'}
PCA_IRRBD_MCP_IO_CH=    '4'
MCP23008_IO_ADDR =      0x20
RESET_GPIO =            25
RELAY_3V3_GPIO =        21
RELAY_5V0_GPIO =        26


set_toolname(TOOLNAME)
setuplogging(ConsoleLogFormat="{module:>35}.{funcName:30} - {levelname:>8}:  {message}")
set_logging_level(logging.DEBUG)
logging.getLogger('cjn_PiTools.shared').setLevel(logging.DEBUG)
logging.getLogger('cjn_PiTools.PCA9548').setLevel(logging.DEBUG)
logging.getLogger('cjn_PiTools.MCP23008').setLevel(logging.DEBUG)


parser = argparse.ArgumentParser(description=__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-t', '--test', default='0',
                    help="Test number to run (default 0) - 0 runs all tests")
parser.add_argument('-x', '--expand-exception', action='store_true',
                    help="Expand exceptions with trace stack for test debug")
cli_args = parser.parse_args()


logging.warning (f"\n\n---- Test Init ------------------------------------------------------")

# Get i2c bus and device handles
pio =                   pigpio.pi()
i2c_bus_handle_pigpio = pi_i2c(pio)
i2c_bus_handle_smbus =  pi_i2c('smbus')

# Turn on power control relays which power devices plugged into the Board_1 I2C jacks
pio.write(RELAY_3V3_GPIO, 1)
pio.write(RELAY_5V0_GPIO, 1)
time.sleep(0.1)
pio.write(RESET_GPIO, 1)            # De-assert reset on Board_1 pca9548
time.sleep(0.1)

# Instantiate and configure I2C bus switches
pca9548_resBd_handle_pigpio =   PCA9548(PCA9548_RESBD['name'], PCA9548_RESBD['addr'], i2c_bus_handle_pigpio)
pca9548_resBd_handle_pigpio.write_control_reg ('0')
pca9548_irrBd_handle_pigpio =   PCA9548(PCA9548_IRRBD['name'], PCA9548_IRRBD['addr'], i2c_bus_handle_pigpio)

# Instantiate and configure MCP IO
pca9548_irrBd_handle_pigpio.write_control_reg (PCA_IRRBD_MCP_IO_CH)
MCP23008_IO_inst_pigpio =       MCP23008('IO_device', MCP23008_IO_ADDR, i2c_bus_handle_pigpio)
MCP23008_IO_inst_smbus =        MCP23008('IO_device', MCP23008_IO_ADDR, i2c_bus_handle_smbus)

unique_value_per_register = {
            'IODIR':    1,
            'IPOL':     2,
            'GPINTEN':  3,
            'DEFVAL':   4,
            'INTCON':   5,
            'IOCON':    6,
            'GPPU':     7,
            'INTF':     8,
            'INTCAP':   9,
            'GPIO':     10,
            'OLAT':     11
            }


def dotest (desc, expect, func, *args, **kwargs):
    logging.warning (f"\n\n==============================================================================================\n" +
                     f"Test {tnum} - {desc}\n" +
                     f"  GIVEN:      {args}, {kwargs}\n" +
                     f"  EXPECT:     {expect}")
    try:
        result = func(*args, **kwargs)
        logging.warning (f"\n  RETURNED:   {result}")
        return result
    except Exception as e:
        if cli_args.expand_exception:
            logging.exception (f"\n  RAISED:     {type(e).__name__}: {e}")
        else:
            logging.error (f"\n  RAISED:     {type(e).__name__}: {e}")
        return e


tnum_parse = re.compile(r"([\d]+)([\w]*)")
def check_tnum(tnum_in, include0='0'):
    global tnum
    tnum = tnum_in
    if cli_args.test == include0  or  cli_args.test == tnum_in:  return True
    try:
        if int(cli_args.test) == int(tnum_parse.match(tnum_in).group(1)):  return True
    except:  pass
    return False


#===============================================================================================
if __name__ == '__main__':

    #-------------------------------------------------------------------------
    # Basic demo read temp/RH pass cases
    if check_tnum('1a'):
        def func():
            logging.info (f"\nSet unique value in each register")
            MCP23008_IO_inst_smbus.set_registers(unique_value_per_register)
            logging.info (f"\nRegisters with unique values:{MCP23008_IO_inst_smbus.registers_dump()}")
            logging.info (f"\nReinitialize")
            MCP23008_IO_inst_smbus.initialize()
            logging.info (f"\nRegisters after reinitialize:{MCP23008_IO_inst_smbus.registers_dump()}")
            logging.info (f"\nSet bits in IODIR reg - Expect 11001111")
            MCP23008_IO_inst_smbus.set_bits('IODIR', bits=0b11001100, mask= 0b00111100)
            logging.info (f"\nRead IODIR reg: 0b{MCP23008_IO_inst_smbus.read_reg('IODIR'):8>0b}")
        dotest ("Do all with smbus api", "None", func)

    if check_tnum('1b'):
        def func():
            logging.info (f"\nSet unique value in each register")
            MCP23008_IO_inst_pigpio.set_registers(unique_value_per_register)
            logging.info (f"\nRegisters with unique values:{MCP23008_IO_inst_pigpio.registers_dump()}")
            logging.info (f"\nReinitialize")
            MCP23008_IO_inst_pigpio.initialize()
            logging.info (f"\nRegisters after reinitialize:{MCP23008_IO_inst_pigpio.registers_dump()}")
            logging.info (f"\nSet bits in IODIR reg - Expect 11001111")
            MCP23008_IO_inst_pigpio.set_bits('IODIR', bits=0b11001100, mask= 0b00111100)
            logging.info (f"\nRead IODIR reg: 0b{MCP23008_IO_inst_pigpio.read_reg('IODIR'):8>0b}")
        dotest ("Do all with pigpio api", "None", func)

    
    #-------------------------------------------------------------------------
    # Instantiation test cases
    if check_tnum('2a'):
        def func():
            xx = MCP23008('MyXX', 0x20, i2c_bus_handle_smbus, init_settings=unique_value_per_register)
            logging.info (f"Instance name:  {xx.device_name}")
            logging.info (f"Instance addr:  0x{xx.device_addr:2>0x}")
            logging.info (f"DEFVAL addr:    0x{xx.registers['DEFVAL']['addr']:0>2x},  init: 0b{xx.registers['DEFVAL']['init']:0>8b},  cached: 0b{xx.registers['DEFVAL']['cached']:0>8b}")

        dotest ("Instantiation with unique values per reg", "<cjn_PiTools.MCP23008.MCP23008 object at 0x762f5b20>", func)


    #-------------------------------------------------------------------------
    # Instantiation error cases
    if check_tnum('13a'):
        dotest ("Instantiation with illegal device name", "ValueError: device_name must be str - Received <{'whatever': 5}>",
                MCP23008, {'whatever':5}, 0x20, i2c_bus_handle_smbus)

    if check_tnum('13b'):
        dotest ("Instantiation with illegal device addr", "ValueError: <MyXX> Device address must be in range of 0x20 to 0x27.  Received <48>",
                MCP23008, 'MyXX', 0x30, i2c_bus_handle_smbus)

    if check_tnum('13c'):
        dotest ("Instantiation with malformed init_settings", "ValueError: <MyXX> Malformed init_settings - received <whatever>",
                MCP23008, 'MyXX', 0x20, i2c_bus_handle_smbus, init_settings='whatever')

    if check_tnum('13d'):
        dotest ("Instantiation with invalid register name", "ValueError: <MyXX> Invalid register name - Received <IODIRx>",
                MCP23008, 'MyXX', 0x20, i2c_bus_handle_smbus, init_settings={'IODIRx': 0x1FF})

    if check_tnum('13e'):
        dotest ("Instantiation with illegal register value", "ValueError: <MyXX> <IODIR> init_settings illegal value - received <511>",
                MCP23008, 'MyXX', 0x20, i2c_bus_handle_smbus, init_settings={'IODIR': 0x1FF})

    if check_tnum('13f'):
        dotest ("Instantiation with illegal register value", "ValueError: <MyXX> <IODIR> init_settings illegal value - Received <[5]>",
                MCP23008, 'MyXX', 0x20, i2c_bus_handle_smbus, init_settings={'IODIR': [5]})

    if check_tnum('13g'):
        pca9548_irrBd_handle_pigpio.write_control_reg('0')
        dotest ("Instantiate unavailable device - smbus", "OSError: <MyXX> I2C communication error",
                MCP23008, 'MyXX', 0x20, i2c_bus_handle_smbus)
        pca9548_irrBd_handle_pigpio.write_control_reg(PCA_IRRBD_MCP_IO_CH)
        
    if check_tnum('13h'):
        pca9548_irrBd_handle_pigpio.write_control_reg('0')
        dotest ("Instantiate unavailable device - pigpio", "OSError: <MyXX> I2C communication error",
                MCP23008, 'MyXX', 0x20, i2c_bus_handle_pigpio)
        pca9548_irrBd_handle_pigpio.write_control_reg(PCA_IRRBD_MCP_IO_CH)
        

    #-------------------------------------------------------------------------
    # set_registers error cases
    if check_tnum('14a'):
        dotest ("Malformed reg_dict", "ValueError: <IO_device> Malformed reg_dict - Received <whatever>",
                MCP23008_IO_inst_smbus.set_registers, reg_dict='whatever')

    if check_tnum('14b'):
        dotest ("Invalid register name", "ValueError: <IO_device> Invalid register name - Received <IODIRx>",
                MCP23008_IO_inst_smbus.set_registers, reg_dict={'IODIRx': 0x1FF})

    if check_tnum('14c'):
        dotest ("Illegal register value", "ValueError: <IO_device> <IODIR> Illegal value - Received <511>",
                MCP23008_IO_inst_smbus.set_registers, reg_dict={'IODIR': 0x1FF})

    if check_tnum('14d'):
        dotest ("Illegal register value", "ValueError: <IO_device> <IODIR> Illegal value - Received <[5]>",
                MCP23008_IO_inst_smbus.set_registers, reg_dict={'IODIR': [5]})

    if check_tnum('14e'):
        pca9548_irrBd_handle_pigpio.write_control_reg('0')
        dotest ("Unavailable device - smbus", "-256",
                MCP23008_IO_inst_smbus.set_registers, reg_dict={'IODIR': 0x55})
        pca9548_irrBd_handle_pigpio.write_control_reg(PCA_IRRBD_MCP_IO_CH)
        
    if check_tnum('14f'):
        pca9548_irrBd_handle_pigpio.write_control_reg('0')
        dotest ("Unavailable device - pigpio", "-256",
                MCP23008_IO_inst_pigpio.set_registers, reg_dict={'IODIR': 0x55})
        pca9548_irrBd_handle_pigpio.write_control_reg(PCA_IRRBD_MCP_IO_CH)
        


    #-------------------------------------------------------------------------
    # set_bits error cases
    if check_tnum('15a'):
        dotest ("Invalid register name", "ValueError: <IO_device> Invalid register name - Received <IODIRx>",
                MCP23008_IO_inst_smbus.set_bits, reg_name='IODIRx', bits=0x1FF, mask=0x1FF)

    if check_tnum('15b'):
        dotest ("Illegal bits value", "ValueError: <IO_device> Invalid bits value - Received <511>",
                MCP23008_IO_inst_smbus.set_bits, reg_name='IODIR', bits=0x1FF, mask=0x1FF)

    if check_tnum('15c'):
        dotest ("Illegal mask value", "ValueError: <IO_device> Invalid mask value - Received <511>",
                MCP23008_IO_inst_smbus.set_bits, reg_name='IODIR', bits=0xFF, mask=0x1FF)

    if check_tnum('15d'):
        pca9548_irrBd_handle_pigpio.write_control_reg('0')
        dotest ("Unavailable device - smbus", "-256",
                MCP23008_IO_inst_smbus.set_bits, reg_name='IODIR', bits=0xFF, mask=0xFF)
                # MCP23008_IO_inst_smbus.set_registers, reg_dict={'IODIR': 0x55})
        pca9548_irrBd_handle_pigpio.write_control_reg(PCA_IRRBD_MCP_IO_CH)
        
    if check_tnum('15e'):
        pca9548_irrBd_handle_pigpio.write_control_reg('0')
        dotest ("Unavailable device - pigpio", "-256",
                MCP23008_IO_inst_pigpio.set_bits, reg_name='IODIR', bits=0xFF, mask=0xFF)
                # MCP23008_IO_inst_pigpio.set_registers, reg_dict={'IODIR': 0x55})
        pca9548_irrBd_handle_pigpio.write_control_reg(PCA_IRRBD_MCP_IO_CH)
        

    #-------------------------------------------------------------------------
    # registers_dump I2C error cases
    if check_tnum('16a'):
        pca9548_irrBd_handle_pigpio.write_control_reg('0')
        dotest ("registers_dump() Unavailable device - smbus", "-256",
                MCP23008_IO_inst_smbus.registers_dump)
        pca9548_irrBd_handle_pigpio.write_control_reg(PCA_IRRBD_MCP_IO_CH)

    if check_tnum('16b'):
        pca9548_irrBd_handle_pigpio.write_control_reg('0')
        dotest ("registers_dump() Unavailable device - pigpio", "-256",
                MCP23008_IO_inst_pigpio.registers_dump)
        pca9548_irrBd_handle_pigpio.write_control_reg(PCA_IRRBD_MCP_IO_CH)


    #-------------------------------------------------------------------------
    # read_reg I2C error cases
    if check_tnum('17a'):
        dotest ("Invalid register name", "ValueError: <IO_device> Invalid register name - Received <IODIRx>",
                MCP23008_IO_inst_smbus.read_reg, reg_name='IODIRx')

    if check_tnum('17b'):
        pca9548_irrBd_handle_pigpio.write_control_reg('0')
        dotest ("read_reg() Unavailable device - smbus", "-256",
                MCP23008_IO_inst_smbus.read_reg, reg_name='IODIR')
        pca9548_irrBd_handle_pigpio.write_control_reg(PCA_IRRBD_MCP_IO_CH)

    if check_tnum('17c'):
        pca9548_irrBd_handle_pigpio.write_control_reg('0')
        dotest ("registers_dump() Unavailable device - pigpio", "-256",
                MCP23008_IO_inst_pigpio.read_reg, reg_name='IODIR')
        pca9548_irrBd_handle_pigpio.write_control_reg(PCA_IRRBD_MCP_IO_CH)



    #-------------------------------------------------------------------------
    # Development/testing/debug
    if check_tnum('50', include0=False):
        def func():
            xx = MCP23008('My_MCP23008', 0x20, i2c_bus_handle_smbus,
                          init_settings={'IODIR': 0b11110000, 'GPPU': 0b11110000, 'OLAT': 0b00000110})
        dotest ("Module documentation", "None", func)



    logging.warning (f"\n\n---- Cleanup --------------------------------------------------------")

    i2c_bus_handle_pigpio.close()
    pio.stop()

    i2c_bus_handle_smbus.close()
