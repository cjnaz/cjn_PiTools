#!/usr/bin/env python3
# DS18B20_README_ex.py available in the docs directory in the github repo

import logging
from cjn_PiTools.DS18B20 import DS18B20

logging.basicConfig()
logging.getLogger('cjn_PiTools.DS18B20').setLevel(logging.DEBUG)


sensor = DS18B20('28-0b2280337113', 'My_DS18B20')
logging.warning (f"Current temperature for sensor {sensor.device_name} / {sensor.device_id}:  {sensor.read_temperature(tempunits='F'):7.3f} F")
