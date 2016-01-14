from collections import deque
import time
import os
import glob
import subprocess
import asyncio

import RPi.GPIO as GPIO


class HeaterController(object):
    def __init__(self, target_temp=1, max_track_length=50, debug=True, loop=None):
        GPIO.setup(10, GPIO.OUT)
        self.loop = loop
        self.debug = debug
        if not debug:
            os.system('modprobe w1-gpio')
            os.system('modprobe w1-therm')
        self.target_temp = target_temp
        self.heater_on = False
        self.heater_enabled = True
        self.creation_time = time.time()
        self.max_track_length = 50
        if debug:
            self.temp_sensor_file = 'sample_sensor_output.txt'
        else:
            self.temp_sensor_file = glob.glob('/sys/bus/w1/devices/28*')[0] + '/w1_slave'

        self.targets = deque(maxlen=max_track_length)
        self.times = deque(maxlen=max_track_length)
        self.values = deque(maxlen=max_track_length)

    def set_target(self, target):
        # TODO: validate value
        self.target_temp = target

    def get_status(self):
        return {
            'targets': list(self.targets),
            'times': list(range(-self.max_track_length + 1, 1)),  # list(self.times),
            'heater_on': self.heater_on,
            'heater_enabled': self.heater_enabled,
            'values': list(self.values)
        }

    async def update_state(self):
        try:
            if self.values[-1] > self.target_temp:
                self.turn_heater_off()
            else:
                if self.heater_enabled:
                    self.turn_heater_on()
        except IndexError:
            pass

    async def read_state(self):
        try:
            temp = await self.read_temp()
            if temp is None:
                temp = self.values[-1]
            self.values.append(temp)
            self.targets.append(self.target_temp)
            self.times.append(int(time.time() - self.creation_time))
        except IndexError:
            pass

    def turn_heater_on(self):
        GPIO.output(10, True)
        self.heater_on = True

    def turn_heater_off(self):
        GPIO.output(10, False)
        self.heater_on = False

    def enable_heater(self):
        self.heater_enabled = True

    def disable_heater(self):
        self.turn_heater_off()
        self.heater_enabled = False

    async def read_temp_sensor_file(self):
        catdata = await asyncio.create_subprocess_exec('cat', self.temp_sensor_file,
                                                       stdout=subprocess.PIPE,
                                                       stderr=subprocess.PIPE,
                                                       loop=self.loop)
        output, _ = await catdata.communicate()
        return bytes(output).decode('utf-8').split('\n')

    async def read_temp(self):
        lines = await self.read_temp_sensor_file()
        while lines[0].strip()[-3:] != 'YES':
            await asyncio.sleep(0.2, loop=self.loop)
            lines = await self.read_temp_sensor_file()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            return float(temp_string) / 1000.0
