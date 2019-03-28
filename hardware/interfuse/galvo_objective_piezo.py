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
from core.module import ConfigOption
from interface.confocal_scanner_interface import ConfocalScannerInterface

# Library modules
import os
import numpy
from pipython import GCSDevice
from pipython import pitools

# %% Class definition


class GalvoObjectivePiezo(Base, ConfocalScannerInterface):

    _modtype = 'GalvoObjectivePiezo'
    _modclass = 'hardware.interfuse'

    # Connectors
    galvo = Connector(interface='ConfocalScannerInterface')

    # Piezo
    _piezoSerial = ConfigOption('piezo_serial', missing='error')
    _piezoModel = 'E709'
    _piezoDllPath = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 "GCSTranslator",
                                                 "PI_GCS2_DLL_x64.dll"))

    _piezo_voltage_ranges = ConfigOption('piezo_voltage_ranges', missing='error')
    _piezo_position_ranges = ConfigOption('piezo_position_ranges', missing='error')

    def on_activate(self):
        """Initialisation performed during activation of the module."""

        self._galvo = self.galvo()
        self._piezo = GCSDevice(devname=self._piezoModel,
                                gcsdll=self._piezoDllPath)
        self._piezo.ConnectUSB(self._piezoSerial)
        self._piezo_axis = self._piezo.axes[0]

    def on_deactivate(self):
        """Deactivate the module."""

        self.reset_hardware()

    def reset_hardware(self):
        """Resets the hardware, so the connection is lost and other programs
        can access it.

        @return int: error code (0:OK, -1:error)
        """

        galvoReturn = self._galvo.reset_hardware()
        self._piezo.CloseConnection()

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
        self._set_piezo_position(z)

        return galvoReturn

    def get_scanner_position(self):
        """Get the current position of the scanner hardware.

        @return list(float): current position in [x, y, z] in meters
        """

        galvoPos = self._galvo.get_scanner_position()

        piezoAxis = self._piezo.axes[0]
        piezoPos = self._piezo.qPOS()[piezoAxis]
        
        qudi_piezo_pos = self._piezo_pi_position_to_qudi_position(piezoPos)

        return galvoPos + [qudi_piezo_pos]

    def scan_line(self, line_path=None, pixel_clock=False):
        """Scans a line and returns the counts on that line.

        @param numpy.ndarray(float) line_path: k x n array defining the
            pixel positions, k is number of pixels, n is number of axes
        @param bool pixel_clock: whether we need to output
            a pixel clock for this line

        @return numpy.ndarray(float): k x m, the photon counts per second for
            k pixels with m channels
        """

        if line_path is None:
            self.log.error('line_path must be specified.')
            return -1

        # Figure out what axes we're scanning.
        # We support xy scans and z scans.

        # Assume we're scanning in x and y rather than z
        zScan = False

        # Get the values for each axis
        galvo_path = line_path[0:2, :]
        xVals = galvo_path[0, :].tolist()
        yVals = galvo_path[1, :].tolist()
        
        piezo_path = line_path[2, :]
        zVals = piezo_path.tolist()

        # Get the first value for each axis
        firstX = xVals[0]
        firstY = yVals[0]
        firstZ = zVals[0]

        # Check if the scan is constant along a given axis. If all the
        # values along the axis are the same, then it is constant.
        constantX = xVals.count(firstX) == len(xVals)
        constantY = yVals.count(firstY) == len(yVals)
        constantZ = zVals.count(firstZ) == len(zVals)

        # If this looks like a z scan, then x and y better be constant
        if not constantZ:
            if constantX and constantY:
                zScan = True
            else:
                self.log.error('This module only supports scans in xy or z.')
                return -1

        if zScan:
            counts = self._scan_z_line(firstX, firstY, zVals, pixel_clock)
        else:
            counts = self._galvo.scan_line(galvo_path, pixel_clock)

        return counts

    def _scan_z_line(self, x, y, z_path, pixel_clock=False):
        """Scans a line in z and returns the counts along the line.

        @param numpy.ndarray(float) line_path: k x n list defining the
            pixel positions, k is number of pixels, n is number of axes
        @param bool pixel_clock: whether we need to output
            a pixel clock for this line

        @return numpy.ndarray(float): k x m, the photon counts per second for
            k pixels with m channels
        """
        
        # Based on the sample clock, the AO write task expects more than one
        # sample per channel. We only really want to write one sample
        # per channel, but since all the samples are the same it doesn't
        # matter if we write two. 
        galvo_vals = numpy.vstack(([x, x], [y, y]))

        for z_index in range(len(z_path)):

            z_pos = z_path[z_index]
            self._set_piezo_position(z_pos)

            # Take just the first sample since we actually collected two. 
            new_count = [self._galvo.scan_line(galvo_vals, pixel_clock)[0, :]]

            if z_index == 0:
                counts = new_count
            else:
                counts = numpy.vstack((counts, new_count))

    def close_scanner(self):
        """Closes the scanner and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """

        galvoReturn = self._galvo.close_scanner()

        return galvoReturn

    def close_scanner_clock(self):
        """Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """

        return self._galvo.close_scanner_clock()

    def _set_piezo_position(self, position):
        """Write a z voltage to the piezo.
        
        @param float position: The position according to qudi (meters)
        """
        
        # The piezo range is 0-100 um according to PI,
        # but qudi expects ranges centered about 0
        voltage = self._piezo_qudi_position_to_pi_voltage(position)

        piezo_vol_min = self._piezo_position_ranges[0]
        piezo_vol_max = self._piezo_position_ranges[1]

        if (voltage < piezo_vol_min) or (voltage > piezo_vol_max):
            return

        # Turn off closed loop feedback
        self._piezo.SVO(self._piezo_axis, False)

        # Write the value
        self._piezo.SVA(self._piezo_axis, voltage)
        
    def _piezo_qudi_position_to_pi_voltage(self, qudi_position):
        """Map the qudi position to the instrument voltage.
        
        @param float position: The position according to qudi (meters)
        
        @return float: The corresponding physical voltage of the piezo
        """
        
        # Qudi passes the position in meters.
        micron_qudi_position = qudi_position * (10**6)
        
        # The piezo range is 0-100 um according to PI,
        # but qudi expects ranges centered about 0.
        # Besides this offset, the micron: voltage mapping is 1:1.
        voltage = micron_qudi_position + 50
        
        return voltage
    
    def _piezo_pi_position_to_qudi_position(self, pi_position):
        """Map the pi position to the qudi position.
        
        @param float position: The position according to qudi (um)
        
        @return float: The corresponding position in qudi (meters)
        """
        
        # The piezo range is 0-100 um according to PI,
        # but qudi expects ranges centered about 0
        qudi_micron_position = pi_position - 50  
        
        # Qudi expects meters
        qudi_position = qudi_micron_position * (10**-6)  
        
        return qudi_position
