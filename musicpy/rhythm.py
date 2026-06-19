"""
Rhythm classes extracted from structures.py.

Contains beat, rest_symbol, continue_symbol, rest, and rhythm classes.
These are imported back into structures.py to maintain backward compatibility.
"""

from copy import deepcopy as copy
from fractions import Fraction

# Lazy import helper to avoid circular dependency with musicpy module
_mp = None


def _get_mp():
    global _mp
    if _mp is None:
        import musicpy as _m
        _mp = _m
    return _mp


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


class rhythm(list):
    '''
    This class represents a rhythm, which consists of beats, rest symbols and continue symbols.
    '''

    def __init__(self,
                 beat_list,
                 total_bar_length=None,
                 beats=None,
                 time_signature=None,
                 separator=' ',
                 unit=None):
        from musicpy.parsing import _process_note, copy_list
        is_str = False
        settings_list = []
        if isinstance(beat_list, str):
            is_str = True
            beat_list, settings_list = self._convert_to_rhythm(
                beat_list, separator)
        if time_signature is None:
            self.time_signature = [4, 4]
        else:
            self.time_signature = time_signature
        current_duration = None
        if total_bar_length is not None:
            if beat_list:
                current_time_signature_ratio = self.time_signature[
                    0] / self.time_signature[1]
                current_duration = total_bar_length * current_time_signature_ratio / (
                    self.get_length(beat_list) if beats is None else beats)
        elif unit is not None:
            current_duration = unit
        if not is_str:
            if current_duration is not None:
                for each in beat_list:
                    each.duration = current_duration
        else:
            new_beat_list = []
            for i, each in enumerate(beat_list):
                current_beat = [each]
                current_repeat_times, current_beats_num, current_after_repeat_times = settings_list[
                    i]
                current_beat_duration = current_duration if current_duration is not None else each.duration
                current_new_duration = current_beat_duration * current_beats_num / current_repeat_times
                if current_repeat_times > 1:
                    current_beat = [
                        copy(each) for j in range(current_repeat_times)
                    ]
                for k in current_beat:
                    k.duration = current_new_duration
                if current_after_repeat_times > 1:
                    current_beat = copy_list(current_beat,
                                             current_after_repeat_times)
                new_beat_list.extend(current_beat)
            beat_list = new_beat_list

        super().__init__(beat_list)

    @property
    def total_bar_length(self):
        return self.get_total_duration(apply_time_signature=True)

    def __repr__(self):
        current_total_bar_length = Fraction(
            self.total_bar_length).limit_denominator()
        current_rhythm = ', '.join([str(i) for i in self])
        return f'[rhythm]\nrhythm: {current_rhythm}\ntotal bar length: {current_total_bar_length}\ntime signature: {self.time_signature[0]} / {self.time_signature[1]}'

    def _convert_to_rhythm(self, current_rhythm, separator=' '):
        from musicpy.parsing import _process_note
        settings_list = []
        current_beat_list = current_rhythm.split(separator)
        current_beat_list = [i.strip() for i in current_beat_list if i]
        for i, each in enumerate(current_beat_list):
            current_settings = None
            if '[' in each and ']' in each:
                each, current_settings = each.split('[')
            if ':' in each:
                current, duration = each.split(':')
                duration = _process_note(duration)
            else:
                current, duration = each, 1 / 4
            current_beat = None
            if current.startswith('b') and all(j == '.' for j in current[1:]):
                dotted_num = len(current[1:])
                current_beat = beat(
                    duration=duration,
                    dotted=dotted_num if dotted_num != 0 else None)
            elif current.startswith('-') and all(j == '.'
                                                 for j in current[1:]):
                dotted_num = len(current[1:])
                current_beat = continue_symbol(
                    duration=duration,
                    dotted=dotted_num if dotted_num != 0 else None)
            elif current.startswith('0') and all(j == '.'
                                                 for j in current[1:]):
                dotted_num = len(current[1:])
                current_beat = rest_symbol(
                    duration=duration,
                    dotted=dotted_num if dotted_num != 0 else None)
            if current_beat is not None:
                current_repeat_times = 1
                current_after_repeat_times = 1
                current_beats = 1
                if current_settings is not None:
                    current_settings = [
                        j.strip().split(':')
                        for j in current_settings[:-1].split(';')
                    ]
                    for k in current_settings:
                        current_keyword, current_content = k
                        if current_keyword == 'r':
                            current_repeat_times = int(current_content)
                        elif current_keyword == 'R':
                            current_after_repeat_times = int(current_content)
                        if current_keyword == 'b':
                            current_beats = _process_note(current_content)
                current_beat_list[i] = current_beat
                settings_list.append([
                    current_repeat_times, current_beats,
                    current_after_repeat_times
                ])
        return current_beat_list, settings_list

    def __add__(self, *args, **kwargs):
        return rhythm(super().__add__(*args, **kwargs))

    def __mul__(self, *args, **kwargs):
        return rhythm(super().__mul__(*args, **kwargs))

    def get_length(self, beat_list=None):
        mp = _get_mp()
        return sum([
            1 if i.dotted is None else mp.dotted(1, i.dotted)
            for i in (beat_list if beat_list is not None else self)
        ])

    def get_beat_num(self, beat_list=None):
        return len([
            i for i in (beat_list if beat_list is not None else self)
            if type(i) is beat
        ])

    def get_total_duration(self, beat_list=None, apply_time_signature=False):
        result = sum([
            i.get_duration()
            for i in (beat_list if beat_list is not None else self)
        ])
        if apply_time_signature:
            result /= (self.time_signature[0] / self.time_signature[1])
        return result

    def play(self, *args, notes='C4', **kwargs):
        mp = _get_mp()
        result = mp.chord([copy(notes) for i in range(self.get_beat_num())
                           ]).apply_rhythm(self)
        result.play(*args, **kwargs)

    def convert_time_signature(self, time_signature, mode=0):
        temp = copy(self)
        ratio = (time_signature[0] / time_signature[1]) / (
            self.time_signature[0] / self.time_signature[1])
        temp.time_signature = time_signature
        if mode == 1:
            for each in temp:
                each.duration *= ratio
        return temp
