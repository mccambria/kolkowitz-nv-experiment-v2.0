# -*- coding: utf-8 -*-
"""
Library of pulse sequences. Each function returns an instance of Swabian's
Sequence class.

Created on Tue Mar 26 17:47:57 2019

@author: mccambria
"""


# %% Imports

# Library modules
from pulsestreamer import Sequence

# %% Constants

_LOW = 0
_HIGH = 1

# %% Sequences


def cont_illum_clock(self, channelDict, period, readout=None):
    """
    Ungate the AOM and run a clock. Ungate the counter for readout.
    Leave the counter ungated if readout is None.

    @param dict channelDict: Dictionary of channels
    @param int period: Period of the clock in ns
    @param int readout: Time to ungate the counter at the end of a period
        in ns. None leaves the counter ungated.

    @return Sequence: The sequence
    """

    clockChannel, counterGateChannel, aomChannel,

    seq = Sequence()

    train = [(100, _HIGH), (period - 100, _LOW)]
    seq.setDigital(clockChannel, train)

    if readout is not None:
        train = [(period - readout, _LOW), (readout, _HIGH)]
        seq.setDigital(counterGateChannel, train)

    train = [(period, _HIGH)]
    seq.setDigital(aomChannel, train)

    return seq
