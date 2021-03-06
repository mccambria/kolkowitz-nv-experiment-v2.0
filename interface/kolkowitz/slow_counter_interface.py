# -*- coding: utf-8 -*-

"""
This file contains the Qudi Interface for slow counter.

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
from core.util.interfaces import InterfaceMetaclass


class SlowCounterInterface(metaclass=InterfaceMetaclass):
    """
    Define the controls for a slow counter.
    """

    _modtype = 'SlowCounterInterface'
    _modclass = 'interface'

    @abc.abstractmethod
    def get_constraints(self):
        """
        Retrieve the hardware constrains from the counter device.

        @return SlowCounterConstraints: object with constraints for the counter
        """
        pass

    @abc.abstractmethod
    def set_up_counter(self,
                       counter_channels=None,
                       sources=None,
                       counter_buffer=None):
        """ Configures the actual counter with a given clock.

        @param list(str) counter_channels: optional, physical channel
            of the counter
        @param list(str) sources: optional, physical channel where the photons
            photons are to count from
        @param int counter_buffer: optional, a buffer of specified integer
            length, where in each bin the count numbers are saved.

        @return int: error code (0:OK, -1:error)
        """
        pass

    @abc.abstractmethod
    def get_counter(self):
        """
        Returns the current counts in the buffer.

        @return numpy.array((n, uint32)): the photon counts per second for n channels
        """
        pass

    @abc.abstractmethod
    def get_counter_channels(self):
        """
        Returns the list of counter channel names.

        @return list(str): channel names

        Most methods calling this might just care about the number of
        channels, though.
        """
        pass

    @abc.abstractmethod
    def close_counter(self):
        """
        Closes the counter and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        pass


class SlowCounterConstraints:

    def __init__(self):
        # maximum numer of possible detectors for slow counter
        self.max_detectors = 0
        # frequencies in Hz
        self.min_count_frequency = 5e-5
        self.max_count_frequency = 5e5
        # add CountingMode enums to this list in instances
        self.counting_mode = []
