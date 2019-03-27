# -*- coding: utf-8 -*-

"""
This file contains the Qudi hardware interface for pulsing devices.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at
<https://github.com/Ulm-IQO/qudi/>
"""


import abc
from core.util.interfaces import InterfaceMetaclass, ScalarConstraint


class PulserInterface(metaclass=InterfaceMetaclass):
    """ Interface class to define the abstract controls and
    communication with all pulsing devices.
    """

    _modtype = 'PulserInterface'
    _modclass = 'interface'

    @abc.abstractmethod
    def get_constraints(self):
        """
        Retrieve the hardware constrains from the Pulsing device.

        @return PulserConstraints: object with pulser constraints
            as attributes.
        """
        pass

    @abc.abstractmethod
    def pulser_on(self):
        """ Switches the pulsing device on.

        @return int: error code (0:OK, -1:error)
        """
        pass

    @abc.abstractmethod
    def pulser_off(self):
        """ Switches the pulsing device off.

        @return int: error code (0:OK, -1:error)
        """
        pass

    @abc.abstractmethod
    def write_sequence(self, sequence, numRepeat):
        """
        Write a new sequence to the device memory. Designed for Swabian's
        Sequence class.

        @param func sequence: Function from pulse_sequence_library
        @param int numRepeat: Number of times to run the sequence per start,
            -1 for infinite

        @return int: error code (0:OK, -1:error)
        """
        pass


class PulserConstraints:
    def __init__(self):
        # sample rate, i.e. the time base of the pulser
        self.sample_rate = ScalarConstraint(unit='Hz')
        # The peak-to-peak amplitude and voltage offset of the analog channels
        self.a_ch_amplitude = ScalarConstraint(unit='Vpp')
        self.a_ch_offset = ScalarConstraint(unit='V')
        # Low and high voltage level of the digital channels
        self.d_ch_low = ScalarConstraint(unit='V')
        self.d_ch_high = ScalarConstraint(unit='V')
        # length of the created waveform in samples
        self.waveform_length = ScalarConstraint(unit='Samples')
        # number of waveforms/sequences to put in a single asset (sequence mode)
        self.waveform_num = ScalarConstraint(unit='#')
        self.sequence_num = ScalarConstraint(unit='#')
        self.subsequence_num = ScalarConstraint(unit='#')
        # Sequence parameters
        self.sequence_steps = ScalarConstraint(unit='#', min=0)
        self.repetitions = ScalarConstraint(unit='#')
        self.event_triggers = list()
        self.flags = list()
        self.activation_config = dict()
