from copy import deepcopy as copy
from fractions import Fraction
from dataclasses import dataclass
import functools

if __name__ == 'musicpy.primitives':
    from . import database
else:
    import database


class note:
    '''
    This class represents a single note.
    '''

    def __init__(self,
                 name,
                 num=4,
                 duration=1 / 4,
                 volume=100,
                 channel=None,
                 accidental=None):
        if not name:
            raise ValueError('note name is empty')
        if name[0] not in database.standard:
            raise ValueError(f"Invalid note name '{name}'")
        if accidental is not None:
            self.base_name = name
            self.accidental = accidental
        else:
            self.base_name = name[0]
            accidental = name[1:]
            if not accidental:
                accidental = None
            self.accidental = accidental
        self.num = num
        self.duration = duration
        volume = int(volume)
        self.volume = volume
        self.channel = channel

    @property
    def name(self):
        return f'{self.base_name}{self.accidental if self.accidental is not None else ""}'

    @name.setter
    def name(self, value):
        self.base_name = value[0]
        accidental = value[1:]
        if not accidental:
            accidental = None
        self.accidental = accidental

    @property
    def degree(self):
        return database.standard.get(
            self.name, database.standard.get(
                self.standard_name())) + 12 * (self.num + 1)

    @degree.setter
    def degree(self, value):
        self.name = database.standard_reverse[value % 12]
        self.num = (value // 12) - 1

    def __repr__(self):
        return f'{self.name}{self.num}'

    def __eq__(self, other):
        return type(other) is note and self.same_note(
            other) and self.duration == other.duration

    def __lt__(self, other):
        return self.degree < other.degree

    def __le__(self, other):
        return self.degree <= other.degree

    def to_standard(self):
        temp = copy(self)
        temp.name = mp.standardize_note(temp.name)
        return temp

    def standard_name(self):
        return mp.standardize_note(self.name)

    def get_number(self):
        return database.standard.get(
            self.name, database.standard.get(self.standard_name()))

    def same_note_name(self, other):
        return self.get_number() == other.get_number()

    def same_note(self, other):
        return self.same_note_name(other) and self.num == other.num

    def __matmul__(self, other):
        if isinstance(other, rhythm):
            return self.from_rhythm(other)

    def set_volume(self, vol):
        vol = int(vol)
        self.volume = vol

    def set(self, duration=None, volume=None, channel=None):
        if duration is None:
            duration = copy(self.duration)
        if volume is None:
            volume = copy(self.volume)
        if channel is None:
            channel = copy(self.channel)
        return note(self.name, self.num, duration, volume, channel)

    def __mod__(self, obj):
        return self.set(*obj)

    def accidental(self):
        result = ''
        if self.name in database.standard:
            if '#' in self.name:
                result = '#'
            elif 'b' in self.name:
                result = 'b'
        return result

    def join(self, other, ind, interval):
        if isinstance(other, str):
            other = mp.to_note(other)
        if isinstance(other, note):
            return chord([copy(self), copy(other)], interval=interval)
        if isinstance(other, chord):
            temp = copy(other)
            temp.insert(ind, copy(self))
            temp.interval.insert(ind, interval)
            return temp

    def up(self, unit=1):
        if isinstance(unit, database.Interval):
            return self + unit
        else:
            if unit == 0:
                return copy(self)
            return mp.degree_to_note(self.degree + unit, self.duration,
                                     self.volume, self.channel)

    def down(self, unit=1):
        return self.up(-unit)

    def sharp(self, unit=1):
        temp = self
        for i in range(unit):
            temp += database.A1
        return temp

    def flat(self, unit=1):
        temp = self
        for i in range(unit):
            temp -= database.A1
        return temp

    def __pos__(self):
        return self.up()

    def __neg__(self):
        return self.down()

    def __invert__(self):
        name = self.name
        if name in database.standard_dict:
            if '#' in name:
                return self.reset(name=database.reverse_standard_dict[name])
            else:
                return self.reset(name=database.standard_dict[name])
        elif name in database.reverse_standard_dict:
            return self.reset(name=database.reverse_standard_dict[name])
        else:
            return self.reset(name=name)

    def flip_accidental(self):
        return ~self

    def __add__(self, obj):
        if isinstance(obj, int):
            return self.up(obj)
        elif isinstance(obj, database.Interval):
            return obj + self
        if not isinstance(obj, note):
            obj = mp.to_note(obj)
        return chord([copy(self), copy(obj)])

    def __sub__(self, obj):
        if isinstance(obj, int):
            return self.down(obj)
        elif isinstance(obj, database.Interval):
            return obj.__rsub__(self)

    def __call__(self, obj=''):
        return mp.C(self.name + obj, self.num)

    def with_interval(self, interval):
        result = chord([copy(self), self + interval])
        return result

    def get_chord_by_interval(start,
                              interval1,
                              duration=1 / 4,
                              interval=0,
                              cumulative=True):
        return mp.get_chord_by_interval(start, interval1, duration, interval,
                                        cumulative)

    def dotted(self, num=1):
        temp = copy(self)
        if num == 0:
            return temp
        temp.duration = temp.duration * sum([(1 / 2)**i
                                             for i in range(num + 1)])
        return temp

    def reset_octave(self, num):
        temp = copy(self)
        temp.num = num
        return temp

    def reset_pitch(self, name):
        temp = copy(self)
        temp.name = name
        return temp

    def reset_name(self, name):
        temp = mp.to_note(name)
        temp.duration = self.duration
        temp.volume = self.volume
        temp.channel = self.channel
        return temp

    def set_channel(self, channel):
        self.channel = channel

    def with_channel(self, channel):
        temp = copy(self)
        temp.channel = channel
        return temp

    def from_rhythm(self, current_rhythm, set_duration=True):
        return mp.get_chords_from_rhythm(chords=self,
                                         current_rhythm=current_rhythm,
                                         set_duration=set_duration)


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


class beat:
    '''
    This class represents a single beat.
    '''

    def __init__(self, duration=1 / 4, dotted=None):
        self.rhythm_name = 'beat'
        self.duration = duration
        self.dotted = dotted

    def __repr__(self):
        current_duration = Fraction(self.duration).limit_denominator()
        dotted_part = "." * (self.dotted if self.dotted is not None else 0)
        return f'{self.rhythm_name}({current_duration}{dotted_part})'

    def get_duration(self):
        if self.dotted is not None and self.dotted != 0:
            duration = self.duration * sum([(1 / 2)**i
                                            for i in range(self.dotted + 1)])
        else:
            duration = self.duration
        return duration


class rest_symbol(beat):
    '''
    This class represents a single rest.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rhythm_name = 'rest'


class continue_symbol(beat):
    '''
    This class represents a single continuation of previous note.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rhythm_name = 'continue'


class rest(rest_symbol):
    pass


if __name__ == 'musicpy.primitives':
    from .chord_class import chord, chord_type
    from .piece_class import rhythm
else:
    from chord_class import chord, chord_type
    from piece_class import rhythm

import musicpy as mp
