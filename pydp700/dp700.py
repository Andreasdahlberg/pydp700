#!/usr/bin/env python3
# -*- coding: utf-8 -*
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import serial

__author__ = 'andreas.dahlberg90@gmail.com (Andreas Dahlberg)'
__version__ = '0.1.0'


MODEL_PARAMETERS = {
    'DP711': {'max_voltage': 30.0, 'max_current': 5.0},
    'DP712':{'max_voltage': 50.0, 'max_current': 3.0},
}


class PowerSupply(object):
    """ A remote programmable DP700 series power supply."""
    def __init__(self, port, baudrate=9600, timeout=0.2):
        self._serial_port = serial.Serial(port, baudrate, timeout=timeout)
        self._get_device_identification()

        self._id = '{} {} {}'.format(self._manufacturer, self._model, self._software_version)

        try:
            self._max_voltage = MODEL_PARAMETERS[self._model]['max_voltage']
            self._max_current = MODEL_PARAMETERS[self._model]['max_current']
        except KeyError:
            print('<WARNING> {} is unsupported!'.format(self._model))
            self._max_voltage = None
            self._max_current = None


    def __str__(self):
        return '<PowerSupply> {}'.format(self.get_identification())


    def __enter__(self):
        return self


    def __exit__(self, type, value, traceback):
        # Return back to local control before exiting
        command_str = ':SYST:LOC\n'
        command = command_str.encode("utf-8")
        self._execute_command(command)
        self._serial_port.close()


    def _execute_command(self, command):
        self._serial_port.write(command)
        data = self._serial_port.readline()

        # Remove trailing line feed.
        return self._decode_response(data[:-1])


    def _decode_response(self, response):
        # Try to convert to float. If this fails, assume the response is a string.
        try:
            value = float(response)
        except ValueError:
            value = response.decode("utf-8")

        return value


    def set_baud_rate(self, baud_rate):
        """Set the baud rate used for communication."""
        command_str = ':SYST:COMM:RS232:BAUD {}\n'.format(baud_rate)
        command = command_str.encode("utf-8")
        self._execute_command(command)

        # Wait for all data to be sent and then change the baud rate to match
        # the new value.
        self._serial_port.flush()
        self._serial_port.baudrate = baud_rate


    def set_output_voltage(self, voltage):
        """Set the maximum output voltage."""

        if self._max_voltage is None or voltage <= self._max_voltage:
            command_str = ':VOLT {}\n'.format(voltage)
            command = command_str.encode("utf-8")
            self._execute_command(command)


    def get_requested_output_voltage(self):
        """Get the requested output voltage."""

        command = ':VOLT?\n'.encode("utf-8")
        return self._execute_command(command)


    def get_output_voltage(self):
        """Get the actual output voltage."""

        command = ':MEAS:VOLT? CH1\n'.encode("utf-8")
        return self._execute_command(command)


    def set_output_current(self, current):
        """Set the maximum output current."""

        if self._max_current is None or current <= self._max_current:
            command_str = ':CURR {}\n'.format(current)
            command = command_str.encode("utf-8")
            self._execute_command(command)


    def get_requested_output_current(self):
        """Get the requested output current."""

        command = ':CURR?\n'.encode("utf-8")
        return self._execute_command(command)


    def get_output_current(self):
        """Get the actual output current."""

        command = ':MEAS:CURR? CH1\n'.encode("utf-8")
        return self._execute_command(command)


    def get_output_power(self):
        """Get the actual output power."""

        command = ':MEAS:POWE? CH1\n'.encode("utf-8")
        return self._execute_command(command)


    def recall_from_memory(self, index):
        """Recalls voltage and current limits from memory."""

        if index >= 1 or index <= 10:
            command_str = ':MEM:LOAD RSF,{}\n'.format(index)
            command = command_str.encode("utf-8")
            self._execute_command(command)


    def save_to_memory(self, index):
        """Saves voltage and current limits to memory."""

        if index >= 1 or index <= 10:
            command_str = ':MEM:STOR RSF,{}\n'.format(index)
            command = command_str.encode("utf-8")
            self._execute_command(command)


    def enable_output(self, enable):
        """Enable/Disable the power output."""
        if enable:
            command_str = ':OUTP:STAT CH1, ON\n'
        else:
            command_str = ':OUTP:STAT CH1, OFF\n'

        command = command_str.encode("utf-8")
        self._execute_command(command)


    def is_output_enabled(self):
        """Check if the power output is enabled."""

        command_str = ':OUTP:STAT? CH1 \n'
        command = command_str.encode("utf-8")
        return self._execute_command(command) == 'ON'


    def _get_device_identification(self):
        command = '*IDN?\n'.encode("utf-8")
        identification_string = self._execute_command(command)
        identification_values = identification_string.split(',')

        self._manufacturer = identification_values[0]
        self._model = identification_values[1]
        self._serial = identification_values[2]
        self._software_version = identification_values[3]


    def get_identification(self):
        """Get the device identification string."""

        return self._id
