# -*- coding: utf-8 -*-
"""
Use Swabian Instruments PulseStreamer8/2 as a pulse generator.

Created on Mon Mar 25 13:23:33 2019

@author: mccambria
"""


# %% Imports


# User modules
from core.module import Base, ConfigOption
from core.util.modules import get_home_dir
from interface.kolkowitz.pulser_interface import PulserInterface
from interface.pulser_interface import PulserConstraints
from collections import OrderedDict

# Library modules
import os
from pulsestreamer import PulseStreamer
from pulsestreamer import TriggerRearm
from pulsestreamer import TriggerStart
from pulsestreamer import OutputState


# %% Class definition


class Pulser(Base, PulserInterface):
    """ Methods to control PulseStreamer.

    Example config for copy-paste:

    pulser:
        module.Class: 'kolkowitz.pulse_streamer.Pulser'
        pulsestreamer_ip: '128.104.160.11'
        clock_channel: 0
        counter_gate_channel: 2
        aom_channel: 3
        rf_channel: 4

    """
    _modclass = 'pulserinterface'
    _modtype = 'hardware'

    _low = 0
    _high = 1

    _pulsestreamer_ip = ConfigOption('pulsestreamer_ip', '128.104.160.11', missing='warn')
    _clock_channel = ConfigOption('clock_channel', 0, missing='warn')
    _counter_gate_channel = ConfigOption('counter_gate_channel', 2, missing='warn')
    _green_aom_channel = ConfigOption('green_aom_channel', 3, missing='warn')
    _uw_gate_channel = ConfigOption('uw_gate_channel', 4, missing='warn')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        if 'pulsed_file_dir' in config.keys():
            self.pulsed_file_dir = config['pulsed_file_dir']

            if not os.path.exists(self.pulsed_file_dir):
                homedir = get_home_dir()
                self.pulsed_file_dir = os.path.join(homedir, 'pulsed_files')
                self.log.warning('The directory defined in parameter '
                            '"pulsed_file_dir" in the config for '
                            'PulseStreamer does not exist!\n'
                            'The default home directory\n{0}\n will be taken '
                            'instead.'.format(self.pulsed_file_dir))
        else:
            homedir = get_home_dir()
            self.pulsed_file_dir = os.path.join(homedir, 'pulsed_files')
            self.log.warning('No parameter "pulsed_file_dir" was specified in the config for '
                             'PulseStreamer as directory for the pulsed files!\nThe default home '
                             'directory\n{0}\nwill be taken instead.'.format(self.pulsed_file_dir))

        self.current_status = -1
        self.sample_rate = 1e9
        self.current_loaded_asset = None

    def get_constraints(self):
        """
        Retrieve the hardware constrains from the Pulsing device.

        @return PulserConstraints: dict with constraints for the sequence
            generation and GUI
        """
        constraints = PulserConstraints()

        # The file formats are hardware specific.
        constraints.waveform_format = ['pstream']
        constraints.sequence_format = []

        constraints.sample_rate.min = 1e9
        constraints.sample_rate.max = 1e9
        constraints.sample_rate.step = 0
        constraints.sample_rate.default = 1e9

        constraints.d_ch_low.min = 0.0
        constraints.d_ch_low.max = 0.0
        constraints.d_ch_low.step = 0.0
        constraints.d_ch_low.default = 0.0

        constraints.d_ch_high.min = 3.3
        constraints.d_ch_high.max = 3.3
        constraints.d_ch_high.step = 0.0
        constraints.d_ch_high.default = 3.3

        # Sample file length max is not well-defined for PulseStreamer,
        # which collates sequential identical pulses into one.
        # Total number of not-sequentially-identical pulses which
        # can be stored is 10^6.
        constraints.waveform_length.min = 1
        constraints.waveform_length.max = 134217728
        constraints.waveform_length.step = 1
        constraints.waveform_length.default = 1

        # the name a_ch<num> and d_ch<num> are generic names, which describe UNAMBIGUOUSLY the
        # channels. Here all possible channel configurations are stated, where only the generic
        # names should be used. The names for the different configurations can be customary chosen.
        activation_config = OrderedDict()
        activation_config['all'] = ['d_ch1', 'd_ch2', 'd_ch3', 'd_ch4', 'd_ch5', 'd_ch6', 'd_ch7',
                                    'd_ch8']
        constraints.activation_config = activation_config

        return constraints

    def on_activate(self):
        """
        Establish connection to pulse streamer and tell it to
        cancel all operations
        """
        self.pulse_streamer = PulseStreamer(self._pulsestreamer_ip)
        self.pulser_off()
        self.current_status = 0

    def on_deactivate(self):
        """
        Break the connection to the pulse streamer.
        """
        del self.pulse_streamer

    def pulser_on(self):
        """
        Switches the pulsing device on.

        @return int: error code (0:OK, -1:error)
        """

        # start the pulse sequence
        self.pulse_streamer.startNow()
        self.current_status = 1
        return 0

    def pulser_off(self):
        """
        Switches the pulsing device off.

        @return int: error code (0:OK, -1:error)
        """

        # stop the pulse sequence
        #channels = self._convert_to_bitmask([self._laser_channel, self._uw_x_channel])
        self.pulse_streamer.constant(state=OutputState.ZERO())
        self.current_status = 0
        return 0

    def write_sequence(self, sequence, numRepeat):
        """
        Streams a sequence. It'll start when you call pulser_on.

        @param Sequence sequence: The sequence to stream
        @param int numRepeat: Number of times to stream the sequence, -1 for infinite

        @return int: error code (0:OK, -1:error)
        """

        self._sequence = sequence
        self._num_repeat = numRepeat

        # Set the PulseStreamer to start as soon as it receives the stream from
        # from the computer
        self.pulse_streamer.setTrigger(start=TriggerStart.SOFTWARE,
                                       rearm=TriggerRearm.AUTO)

        # Run the stream
        self.pulse_streamer.stream(self._sequence, self._num_repeat)
        self.log.info('Asset uploaded to PulseStreamer')

        return 0

    def load_asset(self, asset_name, load_dict=None):
        """ Loads a sequence or waveform to the specified channel of the pulsing
            device.

        @param str asset_name: The name of the asset to be loaded

        @param dict load_dict:  a dictionary with keys being one of the
                                available channel numbers and items being the
                                name of the already sampled
                                waveform/sequence files.
                                Examples:   {1: rabi_Ch1, 2: rabi_Ch2}
                                            {1: rabi_Ch2, 2: rabi_Ch1}
                                This parameter is optional. If none is given
                                then the channel association is invoked from
                                the sequence generation,
                                i.e. the filename appendix (_Ch1, _Ch2 etc.)

        @return int: error code (0:OK, -1:error)
        """

        self.log.error('Reading from files is not yet implemented with the latest client lib.')
        return -1

#        # ignore if no asset_name is given
#        if asset_name is None:
#            self.log.warning('"load_asset" called with asset_name = None.')
#            return 0
#
#        # check if asset exists
#        saved_assets = self.get_saved_asset_names()
#        if asset_name not in saved_assets:
#            self.log.error('No asset with name "{0}" found for PulseStreamer.\n'
#                           '"load_asset" call ignored.'.format(asset_name))
#            return -1
#
#        # get samples from file
#        filepath = os.path.join(self.host_waveform_directory, asset_name + '.pstream')
#        pulse_sequence_raw = dill.load(open(filepath, 'rb'))
#
#        pulse_sequence = []
#        for pulse in pulse_sequence_raw:
#            pulse_sequence.append(pulse_streamer_pb2.PulseMessage(ticks=pulse[0], digi=pulse[1], ao0=0, ao1=1))
#
#        blank_pulse = pulse_streamer_pb2.PulseMessage(ticks=0, digi=0, ao0=0, ao1=0)
#        laser_on = pulse_streamer_pb2.PulseMessage(ticks=0, digi=self._convert_to_bitmask([self._laser_channel]), ao0=0, ao1=0)
#        laser_and_uw_channels = self._convert_to_bitmask([self._laser_channel, self._uw_x_channel])
#        laser_and_uw_on = pulse_streamer_pb2.PulseMessage(ticks=0, digi=laser_and_uw_channels, ao0=0, ao1=0)
#        self._sequence = pulse_streamer_pb2.SequenceMessage(pulse=pulse_sequence, n_runs=0, initial=laser_on,
#            final=laser_and_uw_on, underflow=blank_pulse, start=1)
#
#        self.current_loaded_asset = asset_name
#        return 0
