# -*- coding: utf-8 -*-
"""
Interfuse for adding depth scanning via an objective piezo to an
otherwise 2d scanner.

Created on Tue Mar 26 21:16:45 2019

@author: mccambria
"""

# %% Imports

# User modules
from core.module import Base
from core.module import Connector
from interface.confocal_scanner_interface import ConfocalScannerInterface

# Library modules
import os
from pipython import GCSDevice
from pipython import pitools

# %% Class definition


class GalvoObjectivePiezo(Base, ConfocalScannerInterface):

    _modtype = 'GalvoObjectivePiezo'
    _modclass = 'hardware.interfuse'

    # Connectors
    galvo = Connector(interface='NationalInstrumentsXSeries')

    # Piezo
    _piezoSerial = ConfigOption('piezo_serial', missing='error')
    _piezoModel = 'E709'
    _piezoDllPath = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 "GCSTranslator",
                                                 "PI_GCS2_DLL_x64.dll"))

    def on_activate(self):
        """Initialisation performed during activation of the module."""

        self._galvo = self.galvo()
        self._piezo = GCSDevice(devname=_piezoModel, gcsdll=_piezoDllPath)
        self._piezo.ConnectUSB(piezoSerial)

    def on_deactivate(self):
        """Deactivate the module."""

        self.reset_hardware()

    def reset_hardware(self):
        """Resets the hardware, so the connection is lost and other programs
        can access it.

        @return int: error code (0:OK, -1:error)
        """

        galvoReturn = self._galvo.reset_hardware()
        this._piezo.close()

        return galvoReturn

    def get_position_range(self):
        """Returns the physical range of the scanner.

        @return list(float): 3x2 list with low and high limits for x, y, z
        """

        galvoRanges = self._galvo.get_position_range()
        piezoRanges = self._piezo_position_ranges

        return galvoRanges + piezoRanges

    def set_position_range(self, posRange=None):
        """Sets the physical range of the scanner.

        @param list(float) posRange: 3x2 list with low and high limits
            for x, y, z

        @return int: error code (0:OK, -1:error)
        """

        galvoReturn = self._galvo.set_position_range(posRange[0:2][:])
        self._piezo_position_ranges = posRange[2:3][:]

        return galvoReturn

    def set_voltage_range(self, volRange=None):
        """Sets the voltage range of the scanner.

        @param list(float) volRange: 3x2 list with low and high limits
            for x, y, z

        @return int: error code (0:OK, -1:error)
        """

        galvoReturn = self._galvo.set_voltage_range(volRange[0:2][:])
        self._piezo_voltage_ranges = volRange[2:3][:]

        return galvoReturn

    def get_scanner_axes(self):
        """Return the scan axes.

        @return list(str): list of axis names
        """

        return ['x', 'y', 'z']

    def get_scanner_count_channels(self):
        """Returns the list of counter channels for the scan.

        @return list(str): channel names
        """

        return self._galvo.get_scanner_count_channels()

    def set_up_scanner_clock(self, clock_frequency=None, clock_channel=None):
        """Configures the hardware clock of the NiDAQ card to give the timing.

        @param float clock_frequency: if defined, this sets the frequency
            of the clock
        @param str clock_channel: if defined, this is the physical channel of
            the clock

        @return int: error code (0:OK, -1:error)
        """

        return self._galvo.set_up_scanner_clock(clock_frequency, clock_channel)

    def set_up_scanner(self,
                       counter_channels=None,
                       sources=None,
                       clock_channel=None,
                       scanner_ao_channels=None):
        """Configures the actual scanner with a given clock.

        @param str counter_channels: if defined, these are the physical
            counting devices
        @param str sources: if defined, these are the physical channels where
            the photons are to count from
        @param str clock_channel: if defined, this specifies the clock for
            the counter
        @param str scanner_ao_channels: if defined, this specifies the analog
            output channels

        @return int: error code (0:OK, -1:error)
        """

        return self._galvo.set_up_scanner(counter_channels=None,
                                          sources=None,
                                          clock_channel=None,
                                          scanner_ao_channels=None)

    def scanner_set_position(self, x, y, z):
        """Move stage to x, y, z, a (where a is the fourth voltage channel).

        @param float x: postion in x-direction (volts)
        @param float y: postion in y-direction (volts)
        @param float z: postion in z-direction (volts)

        @return int: error code (0:OK, -1:error)
        """

        # Set the galvo
        galvoReturn = self._galvo.scanner_set_position(x, y)

        # Set the piezo
        axis = self._piezo.axes()[0]  # Just one axis for this device
        self._piezo.SVO(axis, True) # Turn on closed loop feedback
        self._piezo.MOV(axis, z)
        pitools.waitontarget(self._piezo) # Wait until we get to the position

        return galvoReturn

    def get_scanner_position(self):
        """Get the current position of the scanner hardware.

        @return list(float): current position in [x, y, z].
        """

        galvoPos = self._galvo.get_scanner_position()

        piezoAxis = piezo.axes()[0]
        piezoPos = [piezo.qPOS(piezoAxis)]

        return galvoPos + piezoPos

    def scan_line(self, line_path=None, pixel_clock=False):
        """Scans a line and returns the counts on that line.

        @param float[k][n] line_path: array k of n-part tuples
            defining the pixel positions
        @param bool pixel_clock: whether we need to output
            a pixel clock for this line

        @return float[k][m]: the photon counts per second for
            k pixels with m channels
        """
        pass

    def close_scanner(self):
        """Closes the scanner and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """

        galvoReturn = self._galvo.close_scanner()

        return galvoReturn

    def close_scanner_clock(self, power=0):
        """Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """

        return self._galvo.close_scanner_clock(power)
