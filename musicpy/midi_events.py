"""
MIDI event classes extracted from structures.py.

Contains tempo, pitch_bend, pan, volume, and event classes.
These are imported back into structures.py to maintain backward compatibility.
"""

from copy import deepcopy as copy


class tempo:
    '''
    This is a class to change tempo for the notes after it when it is read,
    it can be inserted into a chord, and if the chord is in a piece,
    then it also works for the piece.
    '''

    def __init__(self, bpm, start_time=0, channel=None, track=None):
        self.bpm = bpm
        self.start_time = start_time
        self.channel = channel
        self.track = track

    def __repr__(self):
        attributes = ['bpm', 'start_time', 'channel', 'track']
        result = f'tempo({", ".join([f"{i}={j}" for i, j in self.__dict__.items() if i in attributes])})'
        return result

    def set_volume(self, vol):
        vol = int(vol)
        self.volume = vol

    def set_channel(self, channel):
        self.channel = channel

    def with_channel(self, channel):
        temp = copy(self)
        temp.channel = channel
        return temp


class pitch_bend:
    '''
    This class represents a pitch bend event in midi.
    '''

    def __init__(self,
                 value,
                 start_time=0,
                 mode='cents',
                 channel=None,
                 track=None):
        '''
        general midi pitch bend values could be taken from -8192 to 8192,
        and the default pitch bend range is -2 semitones to 2 semitones,
        which is -200 cents to 200 cents, which means 1 cent equals to
        8192/200 = 40.96, about 41 values, and 1 semitone equals to
        8192/2 = 4096 values.
        if mode == 'cents', convert value as cents to midi pitch bend values,
        if mode == 'semitones', convert value as semitones to midi pitch bend values,
        if mode == other values, use value as midi pitch bend values
        '''
        self.value = value
        self.start_time = start_time
        self.channel = channel
        self.track = track
        self.mode = mode
        if self.mode == 'cents':
            self.value = int(self.value * 40.96)
        elif self.mode == 'semitones':
            self.value = int(self.value * 4096)

    def __repr__(self):
        attributes = ['value', 'start_time', 'channel', 'track']
        current_cents = self.value / 40.96
        if isinstance(current_cents, float) and current_cents.is_integer():
            current_cents = int(current_cents)
        current_dict = {
            i: j
            for i, j in self.__dict__.items() if i in attributes
        }
        current_dict['cents'] = current_cents
        result = f'pitch_bend({", ".join([f"{i}={j}" for i, j in current_dict.items()])})'
        return result

    def set_volume(self, vol):
        vol = int(vol)
        self.volume = vol

    def set_channel(self, channel):
        self.channel = channel

    def with_channel(self, channel):
        temp = copy(self)
        temp.channel = channel
        return temp


class pan:
    '''
    This is a class to set the pan position for a midi channel,
    it only works in piece class or track class, and must be set as one of the elements
    of the pan list of a piece.
    '''

    def __init__(self,
                 value,
                 start_time=0,
                 mode='percentage',
                 channel=None,
                 track=None):
        # when mode == 'percentage', percentage ranges from 0% to 100%,
        # value takes an integer or float number from 0 to 100 (inclusive),
        # 0% means pan left most, 100% means pan right most, 50% means pan middle
        # when mode == 'value', value takes an integer from 0 to 127 (inclusive),
        # and corresponds to the pan positions same as percentage mode
        self.mode = mode
        if self.mode == 'percentage':
            self.value = int(127 * value / 100)
            self.value_percentage = value
        elif self.mode == 'value':
            self.value = value
            self.value_percentage = (self.value / 127) * 100
        self.start_time = start_time
        self.channel = channel
        self.track = track

    def __repr__(self):
        current_dict = {
            i: j
            for i, j in self.__dict__.items()
            if i in ['value_percentage', 'start_time', 'channel', 'track']
        }
        current_dict['percentage'] = round(
            current_dict.pop('value_percentage'), 3)
        attributes = ['percentage', 'start_time', 'channel', 'track']
        result = f'pan({", ".join([f"{i}={current_dict[i]}" for i in attributes])})'
        return result

    def get_pan_value(self):
        return -((50 - self.value_percentage) /
                 50) if self.value_percentage <= 50 else (
                     self.value_percentage - 50) / 50


class volume:
    '''
    This is a class to set the volume for a midi channel,
    it only works in piece class or track class, and must be set as one of the elements
    of the volume list of a piece.
    '''

    def __init__(self,
                 value,
                 start_time=0,
                 mode='percentage',
                 channel=None,
                 track=None):
        # when mode == 'percentage', percentage ranges from 0% to 100%,
        # value takes an integer or float number from 0 to 100 (inclusive),
        # when mode == 'value', value takes an integer from 0 to 127 (inclusive)
        self.mode = mode
        if self.mode == 'percentage':
            self.value = int(127 * value / 100)
            self.value_percentage = value
        elif self.mode == 'value':
            self.value = value
            self.value_percentage = (self.value / 127) * 100
        self.start_time = start_time
        self.channel = channel
        self.track = track

    def __repr__(self):
        current_dict = {
            i: j
            for i, j in self.__dict__.items()
            if i in ['value_percentage', 'start_time', 'channel', 'track']
        }
        current_dict['percentage'] = round(
            current_dict.pop('value_percentage'), 3)
        attributes = ['percentage', 'start_time', 'channel', 'track']
        result = f'volume({", ".join([f"{i}={current_dict[i]}" for i in attributes])})'
        return result


class event:

    def __init__(self, type, track=0, start_time=0, is_meta=False, **kwargs):
        self.type = type
        self.track = track
        self.start_time = start_time
        self.is_meta = is_meta
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f'event({", ".join([f"{i}={j}" for i, j in self.__dict__.items()])})'