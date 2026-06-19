from copy import deepcopy as copy
from fractions import Fraction
from dataclasses import dataclass
import functools

if __name__ == 'musicpy.scale_class':
    from . import database
    from .primitives import note, tempo, pitch_bend, pan, volume, event, beat, rest_symbol, continue_symbol, rest
    from .chord_class import chord, chord_type
else:
    import database
    from primitives import note, tempo, pitch_bend, pan, volume, event, beat, rest_symbol, continue_symbol, rest
    from chord_class import chord, chord_type


class scale:
    '''
    This class represents a scale.
    '''

    def __init__(self,
                 start=None,
                 mode=None,
                 interval=None,
                 notes=None,
                 standard_interval=True):
        self.interval = interval
        self.notes = None
        if notes is not None:
            notes = [mp.to_note(i) if isinstance(i, str) else i for i in notes]
            self.notes = notes
            self.start = notes[0]
            self.mode = mode
        else:
            if isinstance(start, str):
                start = mp.trans_note(start)
            self.start = start
            if mode is not None:
                self.mode = mode.lower()
            else:
                self.mode = mode
            self.notes = self.get_scale().notes

        if interval is None:
            self.interval = self.get_interval(
                standard_interval=standard_interval)
        if mode is None:
            current_mode = mp.alg.detect_scale_type(self.interval,
                                                    mode='interval')
            if current_mode is not None:
                self.mode = current_mode

    def set_mode_name(self, name):
        self.mode = name

    def change_interval(self, interval):
        self.interval = interval

    def __repr__(self):
        return f'[scale]\nscale name: {self.start} {self.mode} scale\nscale intervals: {self.get_interval()}\nscale notes: {self.get_scale().notes}'

    def __eq__(self, other):
        return type(other) is scale and self.notes == other.notes

    def get_scale_name(self, with_octave=True):
        return f'{self.start if with_octave else self.start.name} {self.mode} scale'

    def standard(self):
        if len(self) == 8:
            standard_notes = [i.name for i in copy(self.notes)[:-1]]
            compare_notes = [i.name for i in scale('C', 'major').notes[:-1]]
            inds = compare_notes.index(standard_notes[0][0])
            compare_notes = compare_notes[inds:] + compare_notes[:inds]
            standard_notes = [
                mp.relative_note(standard_notes[i], compare_notes[i])
                for i in range(7)
            ]
            return standard_notes
        else:
            return self.names()

    def __contains__(self, note1):
        names = self.names()
        names = [
            database.standard_dict[i] if i in database.standard_dict else i
            for i in names
        ]
        if isinstance(note1, chord):
            chord_names = note1.names()
            chord_names = [
                database.standard_dict[i] if i in database.standard_dict else i
                for i in chord_names
            ]
            return all(i in names for i in chord_names)
        else:
            if isinstance(note1, note):
                note1 = note1.name
            else:
                note1 = mp.trans_note(note1).name
            return (database.standard_dict[note1]
                    if note1 in database.standard_dict else note1) in names

    def __getitem__(self, ind):
        return self.notes[ind]

    def __iter__(self):
        for i in self.notes:
            yield i

    def __call__(self, n, duration=1 / 4, interval=0, num=3, step=2):
        if isinstance(n, int):
            return self.pick_chord_by_degree(n, duration, interval, num, step)
        elif isinstance(n, str):
            altered_notes = n.replace(' ', '').split(',')
            notes = copy(self.notes)
            for each in altered_notes:
                if each.startswith('#'):
                    current_ind = int(each.split('#')[1]) - 1
                    notes[current_ind] = notes[current_ind].sharp()
                elif each.startswith('b'):
                    current_ind = int(each.split('b')[1]) - 1
                    notes[current_ind] = notes[current_ind].flat()
            return scale(notes=notes)

    def get_interval(self, standard_interval=True):
        if self.mode is None:
            if self.interval is None:
                if self.notes is None:
                    raise ValueError(
                        'a mode or interval or notes list should be settled')
                else:
                    notes = self.notes
                    if not standard_interval:
                        root_degree = notes[0].degree
                        return [
                            notes[i].degree - notes[i - 1].degree
                            for i in range(1, len(notes))
                        ]
                    else:
                        start = notes[0]
                        return [
                            mp.get_pitch_interval(notes[i - 1], notes[i])
                            for i in range(1, len(notes))
                        ]
            else:
                return self.interval
        else:
            if self.interval is not None:
                return self.interval
            mode = self.mode.lower()
            if mode in database.scaleTypes:
                return database.scaleTypes[mode]
            else:
                if self.notes is None:
                    raise ValueError(f'could not find scale {self.mode}')
                else:
                    notes = self.notes
                    if not standard_interval:
                        root_degree = notes[0].degree
                        return [
                            notes[i].degree - notes[i - 1].degree
                            for i in range(1, len(notes))
                        ]
                    else:
                        start = notes[0]
                        return [
                            mp.get_pitch_interval(notes[i - 1], notes[i])
                            for i in range(1, len(notes))
                        ]

    def get_scale(self, intervals=1 / 4, durations=None):
        if self.mode is None:
            if self.interval is None:
                raise ValueError(
                    'at least one of mode or interval in the scale should be settled'
                )
            else:
                result = [self.start]
                start = copy(self.start)
                for t in self.interval:
                    start += t
                    result.append(start)
                if (result[-1].degree - result[0].degree) % 12 == 0:
                    result[-1].name = result[0].name
                return chord(result, duration=durations, interval=intervals)
        else:
            result = [self.start]
            start = copy(self.start)
            interval1 = self.get_interval()
            for t in interval1:
                start += t
                result.append(start)
            if (result[-1].degree - result[0].degree) % 12 == 0:
                result[-1].name = result[0].name
            return chord(result, duration=durations, interval=intervals)

    def __len__(self):
        return len(self.notes)

    def names(self, standardize_note=False):
        temp = [x.name for x in self.notes]
        result = []
        for i in temp:
            if i not in result:
                result.append(i)
        if standardize_note:
            result = [mp.standardize_note(i) for i in result]
        return result

    def pick_chord_by_degree(self,
                             degree1,
                             duration=1 / 4,
                             interval=0,
                             num=3,
                             step=2,
                             standardize=False):
        result = []
        high = False
        if degree1 == 7:
            degree1 = 0
            high = True
        temp = copy(self)
        scale_notes = temp.notes[:-1]
        for i in range(degree1, degree1 + step * num, step):
            result.append(scale_notes[i % 7].name)
        result_chord = chord(result,
                             rootpitch=temp[0].num,
                             interval=interval,
                             duration=duration)
        if standardize:
            result_chord = result_chord.standardize()
        if high:
            result_chord = result_chord + database.octave
        return result_chord

    def pattern(self, indlist, duration=1 / 4, interval=0, num=3, step=2):
        if isinstance(indlist, str):
            indlist = [int(i) for i in indlist]
        elif isinstance(indlist, int):
            indlist = [int(i) for i in str(indlist)]
        return [
            self(n - 1, num=num, step=step).set(duration, interval)
            for n in indlist
        ]

    def __mod__(self, x):
        if isinstance(x, (int, str)):
            x = [x]
        return self.pattern(*x)

    def dom(self):
        return self[4]

    def dom_mode(self):
        if self.mode is not None:
            return scale(self[4], mode=self.mode)
        else:
            return scale(self[4], interval=self.get_interval())

    def fifth(self, step=1, inner=False):
        # move the scale on the circle of fifths by number of steps,
        # if the step is > 0, then move clockwise,
        # if the step is < 0, then move counterclockwise,
        # if inner is True: pick the inner scales from the circle of fifths,
        # i.e. those minor scales.
        return circle_of_fifths().rotate_get_scale(self[0].name,
                                                   step,
                                                   pitch=self[0].num,
                                                   inner=inner)

    def fourth(self, step=1, inner=False):
        # same as fifth but instead of circle of fourths
        # Maybe someone would notice that circle of fourths is just
        # the reverse of circle of fifths.
        return circle_of_fourths().rotate_get_scale(self[0].name,
                                                    step,
                                                    pitch=self[0].num,
                                                    inner=inner)

    def tonic(self):
        return self[0]

    def supertonic(self):
        return self[1]

    def mediant(self):
        return self[2]

    def subdominant(self):
        return self[3]

    def dominant(self):
        return self[4]

    def submediant(self):
        return self[5]

    def leading_tone(self):
        return self[0].up(database.major_seventh)

    def subtonic(self):
        return self[0].up(database.minor_seventh)

    def tonic_chord(self):
        return self(0)

    def subdom(self):
        return self[3]

    def subdom_chord(self):
        return self(3)

    def dom_chord(self):
        return self(4)

    def dom7_chord(self):
        return self(4) + self[3].up(12)

    def leading_chord(self):
        return chord([self[6].down(database.octave), self[1], self[3]])

    def leading7_chord(self):
        return chord(
            [self[6].down(database.octave), self[1], self[3], self[5]])

    def scale_from(self, degree=4, mode=None, interval=None):
        # default is pick the dominant mode of the scale
        if mode is None and interval is None:
            mode, interval = self.mode, self.interval
        return scale(self[degree], mode, interval)

    def secondary_dom(self, degree=4):
        newscale = self.scale_from(degree, 'major')
        return newscale.dom_chord()

    def secondary_dom7(self, degree=4):
        return self.scale_from(degree, 'major').dom7_chord()

    def secondary_leading(self, degree=4):
        return self.scale_from(degree, 'major').leading_chord()

    def secondary_leading7(self, degree=4):
        return self.scale_from(degree, 'major').leading7_chord()

    def pick_chord_by_index(self, indlist):
        return chord([self[i] for i in indlist])

    def detect(self):
        return mp.alg.detect_scale_type(self)

    def get_all_chord(self, duration=None, interval=0, num=3, step=2):
        return [
            self.pick_chord_by_degree(i,
                                      duration=duration,
                                      interval=interval,
                                      num=num,
                                      step=step)
            for i in range(len(self.get_interval()) + 1)
        ]

    def relative_key(self):
        if self.mode == 'major':
            return scale(self[5].reset_octave(self[0].num), 'minor')
        elif self.mode == 'minor':
            return scale(self[2].reset_octave(self[0].num), 'major')
        else:
            raise ValueError(
                'this function only applies to major and minor scales')

    def parallel_key(self):
        if self.mode == 'major':
            return scale(self[0], 'minor')
        elif self.mode == 'minor':
            return scale(self[0], 'major')
        else:
            raise ValueError(
                'this function only applies to major and minor scales')

    def get_note_from_degree(self, degree, pitch=None):
        if degree < 1:
            raise ValueError('scale degree starts from 1')
        extra_num, current_degree = divmod(degree - 1, 7)
        result = self[current_degree]
        if pitch is not None:
            result = result.reset_octave(pitch)
        result += extra_num * database.octave
        return result

    def get_chord(self, degree, chord_type=None, natural=False):
        current_accidental = None
        original_degree = degree
        if degree.startswith('#') or degree.startswith('b'):
            current_accidental = degree[0]
            degree = degree[1:]
        if not chord_type:
            current_keys = list(database.roman_numerals_dict.keys())
            current_keys.sort(key=lambda s: len(s[0]), reverse=True)
            found = False
            for each in current_keys:
                for i in each:
                    if degree.startswith(i):
                        found = True
                        chord_type = degree[len(i):]
                        degree = i
                        break
                if found:
                    break
            if not found:
                raise ValueError(
                    f'{original_degree} is not a valid roman numerals chord representation'
                )
        if degree not in database.roman_numerals_dict:
            raise ValueError(
                f'{original_degree} is not a valid roman numerals chord representation'
            )
        current_degree = database.roman_numerals_dict[degree] - 1
        current_note = self[current_degree].name
        if natural:
            temp = mp.C(current_note + chord_type)
            if not isinstance(temp, chord):
                raise ValueError(f'{chord_type} is not a valid chord type')
            length = len(temp)
            return self.pick_chord_by_degree(current_degree, num=length)
        if degree.islower():
            try:
                result = mp.C(current_note + 'm' + chord_type)
            except:
                result = mp.C(current_note + chord_type)
        else:
            result = mp.C(current_note + chord_type)
        if current_accidental is not None:
            if current_accidental == '#':
                result += 1
            elif current_accidental == 'b':
                result -= 1
        return result

    def up(self, unit=1, ind=None, ind2=None):
        if ind2 is not None:
            notes = copy(self.notes)
            return scale(notes=[
                notes[i].up(unit) if ind <= i < ind2 else notes[i]
                for i in range(len(notes))
            ])
        if ind is None:
            return scale(self[0].up(unit), self.mode, self.interval)
        else:
            notes = copy(self.notes)
            if isinstance(ind, int):
                notes[ind] = notes[ind].up(unit)
            else:
                notes = [
                    notes[i].up(unit) if i in ind else notes[i]
                    for i in range(len(notes))
                ]
            result = scale(notes=notes)
            return result

    def down(self, unit=1, ind=None, ind2=None):
        return self.up(-unit, ind, ind2)

    def sharp(self, unit=1):
        return scale(self[0].sharp(unit), self.mode, self.interval)

    def flat(self, unit=1):
        return scale(self[0].flat(unit), self.mode, self.interval)

    def __pos__(self):
        return self.up()

    def __neg__(self):
        return self.down()

    def __invert__(self):
        return scale(self[0], interval=list(reversed(self.interval)))

    def reverse(self):
        return ~self

    def move(self, x):
        notes = copy(self.get_scale())
        return scale(notes=notes.move(x))

    def inversion(self, ind, parallel=False, start=None):
        # return the inversion of a scale with the beginning note of a given index
        if ind < 1:
            raise ValueError('inversion of scale starts from 1')
        ind -= 1
        interval1 = self.get_interval()
        new_interval = interval1[ind:] + interval1[:ind]
        if parallel:
            start1 = self.start
        else:
            if start is not None:
                start1 = start
            else:
                start1 = self.get_scale().notes[ind]
        result = scale(start=start1, interval=new_interval)
        result.mode = result.detect()
        return result

    def play(self, intervals=1 / 4, durations=None, *args, **kwargs):
        mp.play(self.get_scale(intervals, durations), *args, **kwargs)

    def __add__(self, obj):
        if isinstance(obj, (int, database.Interval)):
            return self.up(obj)
        elif isinstance(obj, tuple):
            return self.up(*obj)

    def __sub__(self, obj):
        if isinstance(obj, (int, database.Interval)):
            return self.down(obj)
        elif isinstance(obj, tuple):
            return self.down(*obj)

    def chord_progression(self,
                          chords,
                          durations=1 / 4,
                          intervals=0,
                          volumes=None,
                          chords_interval=None,
                          merge=True):
        current_keys = list(database.roman_numerals_dict.keys())
        current_keys.sort(key=lambda s: len(s[0]), reverse=True)
        for k in range(len(chords)):
            current_chord = chords[k]
            if isinstance(current_chord, (tuple, list)):
                current_degree_name = current_chord[0]
                current_accidental = None
                if current_degree_name.startswith(
                        '#') or current_degree_name.startswith('b'):
                    current_accidental = current_degree_name[0]
                    current_degree_name = current_degree_name[1:]
                if current_degree_name not in database.roman_numerals_dict:
                    raise ValueError(
                        f'{"".join(current_chord)} is not a valid roman numerals chord representation'
                    )
                current_degree = database.roman_numerals_dict[
                    current_degree_name] - 1
                current_note = self[current_degree]
                if current_accidental is not None:
                    if current_accidental == '#':
                        current_note += 1
                    elif current_accidental == 'b':
                        current_note -= 1
                if current_degree_name.islower():
                    try:
                        current_chord_name = current_note.name + 'm' + current_chord[
                            1]
                        temp = mp.C(current_chord_name)
                    except:
                        current_chord_name = current_note.name + current_chord[
                            1]
                else:
                    current_chord_name = current_note.name + current_chord[1]
                chords[k] = current_chord_name
            else:
                found = False
                current_degree = None
                current_accidental = None
                original_current_chord = current_chord
                if current_chord.startswith('#') or current_chord.startswith(
                        'b'):
                    current_accidental = current_chord[0]
                    current_chord = current_chord[1:]
                for each in current_keys:
                    for i in each:
                        if current_chord.startswith(i):
                            found = True
                            current_degree_name = i
                            current_degree = database.roman_numerals_dict[i] - 1
                            current_note = self[current_degree]
                            if current_accidental is not None:
                                if current_accidental == '#':
                                    current_note += 1
                                elif current_accidental == 'b':
                                    current_note -= 1
                            if current_degree_name.islower():
                                try:
                                    current_chord_name = current_note.name + 'm' + current_chord[
                                        len(i):]
                                    temp = mp.C(current_chord_name)
                                except:
                                    current_chord_name = current_note.name + current_chord[
                                        len(i):]
                            else:
                                current_chord_name = current_note.name + current_chord[
                                    len(i):]
                            chords[k] = current_chord_name
                            break
                    if found:
                        break
                if not found:
                    raise ValueError(
                        f'{original_current_chord} is not a valid roman numerals chord representation'
                    )
        return mp.chord_progression(chords, durations, intervals, volumes,
                                    chords_interval, merge)

    def reset_octave(self, num):
        return scale(self.start.reset_octave(num), self.mode, self.interval)

    def reset_pitch(self, name):
        return scale(self.start.reset_pitch(name), self.mode, self.interval)

    def reset_mode(self, mode):
        return scale(self.start, mode=mode)

    def reset_interval(self, interval):
        return scale(self.start, interval=interval)

    def set(self, start=None, num=None, mode=None, interval=None):
        temp = copy(self)
        if start is None:
            start = temp.start
        else:
            if isinstance(start, str):
                start = mp.trans_note(start)
        if num is not None:
            start.num = num
        if mode is None and interval is None:
            mode = temp.mode
            interval = temp.interval
        return scale(start, mode, interval)

    def __truediv__(self, n):
        if isinstance(n, tuple):
            return self.inversion(*n)
        else:
            return self.inversion(n)

    def _parse_scale_text(self, text, rootpitch, pitch_mode=0):
        octaves = None
        if '.' in text:
            text, octaves = text.split('.', 1)
        if text.endswith('#'):
            current_degree = int(text[:-1])
            if pitch_mode == 0:
                result = self.get_note_from_degree(current_degree,
                                                   pitch=rootpitch) + 1
            elif pitch_mode == 1:
                extra_num, current_degree_in_scale = divmod(
                    current_degree - 1, 7)
                diff = self[current_degree_in_scale].degree - self[0].degree
                result = self.get_note_from_degree(
                    1,
                    pitch=rootpitch) + 1 + diff + extra_num * database.octave
        elif text.endswith('b'):
            current_degree = int(text[:-1])
            if pitch_mode == 0:
                result = self.get_note_from_degree(current_degree,
                                                   pitch=rootpitch) - 1
            elif pitch_mode == 1:
                extra_num, current_degree_in_scale = divmod(
                    current_degree - 1, 7)
                diff = self[current_degree_in_scale].degree - self[0].degree
                result = self.get_note_from_degree(
                    1,
                    pitch=rootpitch) - 1 + diff + extra_num * database.octave
        else:
            current_degree = int(text)
            if pitch_mode == 0:
                result = self.get_note_from_degree(current_degree,
                                                   pitch=rootpitch)
            elif pitch_mode == 1:
                extra_num, current_degree_in_scale = divmod(
                    current_degree - 1, 7)
                diff = self[current_degree_in_scale].degree - self[0].degree
                result = self.get_note_from_degree(
                    1, pitch=rootpitch) + diff + extra_num * database.octave
        if octaves:
            octaves = int(octaves) * database.octave
            result += octaves
        return result

    def get(self,
            current_ind,
            default_duration=1 / 8,
            default_interval=1 / 8,
            default_volume=100,
            pitch_mode=0):
        if isinstance(current_ind, list):
            current_ind = ','.join([str(i) for i in current_ind])
        current = current_ind.replace(' ', '').split(',')
        notes_result = []
        intervals = []
        start_time = 0
        rootpitch = self[0].num
        for each in current:
            if each == '':
                continue
            if each.startswith('o'):
                rootpitch = int(each.split('o', 1)[1])
            else:
                has_settings = False
                duration = default_duration
                interval = default_interval
                volume = default_volume
                if '[' in each and ']' in each:
                    has_settings = True
                    each, current_settings = each.split('[', 1)
                    current_settings = current_settings[:-1].split(';')
                    current_settings_len = len(current_settings)
                    if current_settings_len == 1:
                        duration = _process_note(current_settings[0])
                    else:
                        if current_settings_len == 2:
                            duration, interval = current_settings
                        else:
                            duration, interval, volume = current_settings
                            volume = mp.parse_num(volume)
                        duration = _process_note(duration)
                        interval = _process_note(
                            interval) if interval != '.' else duration
                current_notes = each.split(';')
                current_length = len(current_notes)
                for i, each_note in enumerate(current_notes):
                    has_same_time = True
                    if i == current_length - 1:
                        has_same_time = False
                    notes_result, intervals, start_time = self._read_single_note(
                        each_note,
                        rootpitch,
                        duration,
                        interval,
                        volume,
                        notes_result,
                        intervals,
                        start_time,
                        has_settings=has_settings,
                        has_same_time=has_same_time,
                        pitch_mode=pitch_mode)
        current_chord = chord(notes_result,
                              interval=intervals,
                              start_time=start_time)
        return current_chord

    def _read_single_note(self,
                          each,
                          rootpitch,
                          duration,
                          interval,
                          volume,
                          notes_result,
                          intervals,
                          start_time,
                          has_settings=False,
                          has_same_time=False,
                          pitch_mode=0):
        dotted_num = 0
        if each.endswith('.'):
            for k in range(len(each) - 1, -1, -1):
                if each[k] != '.':
                    each = each[:k + 1]
                    break
                else:
                    dotted_num += 1
        if each == 'r':
            current_interval = duration if has_settings else (
                mp.dotted(interval, dotted_num) if interval != 0 else 1 / 4)
            if not notes_result:
                start_time += current_interval
            elif intervals:
                intervals[-1] += current_interval
        elif each == '-':
            current_interval = duration if has_settings else (
                mp.dotted(interval, dotted_num) if interval != 0 else 1 / 4)
            if notes_result:
                notes_result[-1].duration += current_interval
            if intervals:
                intervals[-1] += current_interval
        else:
            current_note = self._parse_scale_text(each,
                                                  rootpitch,
                                                  pitch_mode=pitch_mode)
            current_note.duration = duration
            current_note.volume = volume
            if has_same_time:
                current_interval = 0
                if not has_settings:
                    current_note.duration = mp.dotted(current_note.duration,
                                                      dotted_num)
            else:
                if has_settings:
                    current_interval = interval
                else:
                    current_interval = mp.dotted(interval, dotted_num)
                    current_note.duration = mp.dotted(current_note.duration,
                                                      dotted_num)
            notes_result.append(current_note)
            intervals.append(current_interval)
        return notes_result, intervals, start_time

    def index(self, current_note):
        if isinstance(current_note, note):
            current_note = current_note.name
        else:
            current_note = mp.N(mp.standardize_note(current_note)).name
        current_note = mp.standardize_note(current_note)
        current_names = [mp.standardize_note(i) for i in self.names()]
        if current_note not in current_names:
            raise ValueError(
                f'{current_note} is not in {self.get_scale_name(with_octave=False)}'
            )
        result = current_names.index(current_note)
        return result

    def get_scale_degree(self, current_note):
        return self.index(current_note) + 1

    def get_note_with_interval(self, current_note, interval, standard=False):
        current_scale_degree = self.get_scale_degree(current_note)
        current_num = current_note.num if isinstance(
            current_note, note) else mp.get_note_num(current_note)
        if not current_num:
            current_num = 4
        if interval < 0:
            start_note = self.get_note_from_degree(current_scale_degree,
                                                   pitch=current_num)
            current_degree = current_scale_degree
            for i in range(abs(interval) - 1):
                current_degree -= 1
                if current_degree < 1:
                    current_degree = 7
                start_note -= self.interval[current_degree - 1]
            result = start_note
        else:
            current_scale_degree += (interval - 1)
            result = self.get_note_from_degree(current_scale_degree,
                                               pitch=current_num)
        if standard:
            result_scale_degree = self.get_scale_degree(result.name) - 1
            current_name = self.standard()[result_scale_degree]
            if current_name not in database.standard:
                current_name = mp.standardize_note(current_name)
            result.name = current_name
        return result

    def get_standard_notation(self, current_note):
        current_scale_degree = self.get_scale_degree(current_note)
        result = self.standard()[current_scale_degree - 1]
        return result


class circle_of_fifths:
    '''
    This class represents the circle of fifths.
    '''
    outer = ['C', 'G', 'D', 'A', 'E', 'B', 'Gb', 'Db', 'Ab', 'Eb', 'Bb', 'F']
    inner = [
        'Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'Ebm', 'Bbm', 'Fm', 'Cm', 'Gm',
        'Dm'
    ]

    def __init__(self):
        pass

    def __getitem__(self, ind):
        if isinstance(ind, int):
            if not (0 <= ind < 12):
                ind = ind % 12
            return self.outer[ind]
        elif isinstance(ind, tuple):
            ind = ind[0]
            if not (0 <= ind < 12):
                ind = ind % 12
            return self.inner[ind]

    def get(self, ind, mode=0):
        if mode == 0:
            return self[ind]
        else:
            return self[
                ind,
            ]

    def rotate(self, start, step=1, direction='cw', inner=False):
        if direction == 'ccw':
            step = -step
        if isinstance(start, note):
            startind = self.outer.index(start.name)
        elif isinstance(start, str):
            startind = self.outer.index(start)
        else:
            startind = start
        return self[startind + step] if not inner else self[
            startind + step,
        ]

    def rotate_get_scale(self,
                         start,
                         step=1,
                         direction='cw',
                         pitch=4,
                         inner=False):
        if not inner:
            return scale(note(self.rotate(start, step, direction), pitch),
                         'major')
        else:
            return scale(
                note(self.rotate(start, step, direction, True)[:-1], pitch),
                'minor')

    def get_scale(self, ind, pitch, inner=False):
        return scale(note(self[ind], pitch), 'major') if not inner else scale(
            note(self[
                ind,
            ][:-1], pitch), 'minor')

    def __repr__(self):
        return f'[circle of fifths]\nouter circle: {self.outer}\ninner circle: {self.inner}\ndirection: clockwise'


class circle_of_fourths(circle_of_fifths):
    '''
    This class represents the circle of fourths.
    '''
    outer = list(reversed(circle_of_fifths.outer))
    outer.insert(0, outer.pop())
    inner = list(reversed(circle_of_fifths.inner))
    inner.insert(0, inner.pop())

    def __init__(self):
        pass

    def __repr__(self):
        return f'[circle of fourths]\nouter circle: {self.outer}\ninner circle: {self.inner}\ndirection: clockwise'


import musicpy as mp
