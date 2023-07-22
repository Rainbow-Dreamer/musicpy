from copy import deepcopy as copy
from fractions import Fraction
from dataclasses import dataclass
import functools

if __name__ == 'musicpy.structures':
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
        return type(other) is note and self.same_note_name(
            other) and self.num == other.num

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


class chord:
    '''
    This class represents a collection of notes with relative distances.
    '''

    def __init__(self,
                 notes,
                 duration=None,
                 interval=None,
                 volume=None,
                 rootpitch=4,
                 other_messages=[],
                 start_time=None,
                 default_duration=1 / 4,
                 default_interval=0,
                 default_volume=100,
                 tempos=None,
                 pitch_bends=None):
        standardize_msg = False
        if isinstance(notes, str):
            notes = notes.replace(' ', '').split(',')
            if all(not any(i.isdigit() for i in j) for j in notes):
                standardize_msg = True
        elif isinstance(notes, list) and all(
                not isinstance(i, note)
                for i in notes) and all(not any(j.isdigit() for j in i)
                                        for i in notes if isinstance(i, str)):
            standardize_msg = True
        notes_msg = _read_notes(note_ls=notes,
                                rootpitch=rootpitch,
                                default_duration=default_duration,
                                default_interval=default_interval,
                                default_volume=default_volume)
        notes, current_intervals, current_start_time = notes_msg
        if current_intervals and not interval:
            interval = current_intervals
        if standardize_msg and notes:
            root = notes[0]
            notels = [root]
            for i in range(1, len(notes)):
                last_note = notels[i - 1]
                current_note = notes[i]
                if isinstance(current_note, note):
                    current = note(name=current_note.name,
                                   num=last_note.num,
                                   duration=current_note.duration,
                                   volume=current_note.volume,
                                   channel=current_note.channel)
                    if current.get_number() <= last_note.get_number():
                        current.num += 1
                    notels.append(current)
                else:
                    notels.append(current_note)
            notes = notels
        self.notes = notes
        # interval between each two notes one-by-one
        self.interval = [0 for i in range(len(notes))]
        if interval is not None:
            self.change_interval(interval)
        if duration is not None:
            if isinstance(duration, (int, float)):
                for t in self.notes:
                    t.duration = duration
            else:
                for k in range(len(duration)):
                    self.notes[k].duration = duration[k]
        if volume is not None:
            self.set_volume(volume)
        if start_time is None:
            self.start_time = current_start_time
        else:
            self.start_time = start_time
        self.other_messages = other_messages
        self.tempos = tempos if tempos is not None else []
        self.pitch_bends = pitch_bends if pitch_bends is not None else []

    def get_duration(self):
        return [i.duration for i in self.notes]

    def get_volume(self):
        return [i.volume for i in self.notes]

    def get_degree(self):
        return [i.degree for i in self]

    def names(self, standardize_note=False):
        result = [i.name for i in self]
        if standardize_note:
            result = [mp.standardize_note(i) for i in result]
        return result

    def __eq__(self, other):
        return type(other) is chord and self.notes == other.notes

    def get_msg(self, types):
        return [i for i in self.other_messages if i.type == types]

    def cut(self,
            ind1=0,
            ind2=None,
            start_time=0,
            cut_extra_duration=False,
            cut_extra_interval=False,
            round_duration=False,
            round_cut_interval=False):
        # get parts of notes between two bars
        temp = copy(self)
        find_start = False
        if ind1 <= start_time:
            find_start = True
            actual_start_time = start_time - ind1
        else:
            actual_start_time = 0
        if ind2 is None:
            ind2 = temp.bars(mode=0, start_time=start_time)

        new_tempos = []
        new_pitch_bends = []
        new_other_messages = []
        adjust_time = ind1
        cut_bar_length = ind2 - ind1
        for each in temp.tempos:
            each.start_time -= adjust_time
            if 0 <= each.start_time < cut_bar_length:
                new_tempos.append(each)
        for each in temp.pitch_bends:
            each.start_time -= adjust_time
            if 0 <= each.start_time < cut_bar_length:
                new_pitch_bends.append(each)
        for each in temp.other_messages:
            each.start_time -= adjust_time
            if 0 <= each.start_time < cut_bar_length:
                new_other_messages.append(each)

        if ind2 <= start_time:
            result = chord([], start_time=ind2 - ind1)
            result.tempos = new_tempos
            result.pitch_bends = new_pitch_bends
            result.other_messages = new_other_messages
            return result

        current_bar = start_time
        notes = temp.notes
        intervals = temp.interval
        length = len(notes)
        start_ind = 0
        to_ind = length
        for i in range(length):
            current_bar += intervals[i]
            if round_cut_interval:
                current_bar = float(Fraction(current_bar).limit_denominator())
            if (not find_start) and current_bar >= ind1:
                start_ind = i + 1
                find_start = True
                actual_start_time = current_bar - ind1
            elif current_bar >= ind2:
                to_ind = i + 1
                break
        if not find_start:
            start_ind = to_ind
        result = temp[start_ind:to_ind]
        result.tempos = new_tempos
        result.pitch_bends = new_pitch_bends
        result.other_messages = new_other_messages
        result.start_time = actual_start_time
        if cut_extra_duration:
            current_bar = result.start_time
            new_notes = []
            new_intervals = []
            for i in range(len(result.notes)):
                current_note = result.notes[i]
                current_interval = result.interval[i]
                current_duration = current_note.duration
                new_bar_with_duration = current_bar + current_duration
                if new_bar_with_duration > cut_bar_length:
                    current_note.duration -= (new_bar_with_duration -
                                              cut_bar_length)
                    if round_duration:
                        current_note.duration = float(
                            Fraction(
                                current_note.duration).limit_denominator())
                    if current_note.duration > 0:
                        new_notes.append(current_note)
                        new_intervals.append(current_interval)
                    else:
                        if new_intervals:
                            new_intervals[-1] += current_interval
                else:
                    new_notes.append(current_note)
                    new_intervals.append(current_interval)
                current_bar += current_interval
            result.notes = new_notes
            result.interval = new_intervals
        if cut_extra_interval:
            if result.interval:
                current_bar = result.bars(mode=0, start_time=result.start_time)
                if current_bar > cut_bar_length:
                    result.interval[-1] -= (current_bar - cut_bar_length)
        return result

    def cut_time(self,
                 bpm,
                 time1=0,
                 time2=None,
                 start_time=0,
                 normalize_tempo=False,
                 cut_extra_duration=False,
                 cut_extra_interval=False,
                 round_duration=False,
                 round_cut_interval=False):
        if normalize_tempo:
            temp = copy(self)
            temp.normalize_tempo(bpm)
            return temp.cut_time(bpm=bpm,
                                 time1=time1,
                                 time2=time2,
                                 start_time=start_time,
                                 normalize_tempo=False,
                                 cut_extra_duration=cut_extra_duration,
                                 cut_extra_interval=cut_extra_interval,
                                 round_duration=round_duration,
                                 round_cut_interval=round_cut_interval)
        bar_left = time1 / ((60 / bpm) * 4)
        bar_right = time2 / ((60 / bpm) * 4) if time2 is not None else None
        result = self.cut(ind1=bar_left,
                          ind2=bar_right,
                          start_time=start_time,
                          cut_extra_duration=cut_extra_duration,
                          cut_extra_interval=cut_extra_interval,
                          round_duration=round_duration,
                          round_cut_interval=round_cut_interval)
        return result

    def last_note_standardize(self):
        self.interval[-1] = self.notes[-1].duration

    def bars(self, start_time=0, mode=1, audio_mode=0, bpm=None):
        if mode == 0:
            max_length = sum(self.interval)
        elif mode == 1:
            temp = self.only_notes()
            if audio_mode == 1:
                from pydub import AudioSegment
                temp = temp.set(duration=[
                    mp.real_time_to_bar(len(i), bpm) if isinstance(
                        i, AudioSegment) else i.duration for i in temp.notes
                ])
            current_durations = temp.get_duration()
            if not current_durations:
                return 0
            current_intervals = temp.interval
            max_length = current_durations[0]
            current_length = 0
            for i in range(1, len(temp)):
                current_duration = current_durations[i]
                last_interval = current_intervals[i - 1]
                current_length += last_interval + current_duration
                if current_length > max_length:
                    max_length = current_length
                current_length -= current_duration
        elif mode == 2:
            result = self.bars(start_time=start_time,
                               mode=1,
                               audio_mode=audio_mode,
                               bpm=bpm)
            last_extra_interval = self.interval[-1] - self.notes[-1].duration
            if last_extra_interval > 0:
                result += last_extra_interval
            return result
        return start_time + max_length

    def firstnbars(self, n, start_time=0):
        return self.cut(0, n, start_time)

    def get_bar(self, n, start_time=0):
        return self.cut(n, n + 1, start_time)

    def split_bars(self, start_time=0):
        bars_length = int(self.bars(start_time))
        result = []
        for i in range(bars_length):
            result.append(self.cut(i, i + 1, start_time))
        return result

    def count(self, note1, mode='name'):
        if isinstance(note1, str):
            if any(i.isdigit() for i in note1):
                mode = 'note'
            note1 = mp.to_note(note1)
        if mode == 'name':
            return self.names().count(note1.name)
        elif mode == 'note':
            return self.notes.count(note1)

    def standard_notation(self):
        temp = copy(self)
        for each in temp.notes:
            if each.name in database.standard_dict:
                each.name = database.standard_dict[each.name]
        return temp

    def most_appear(self, choices=None, mode='name', as_standard=False):
        test_obj = self
        if as_standard:
            test_obj = self.standard_notation()
        if not choices:
            return max([i for i in database.standard2],
                       key=lambda s: test_obj.count(s))
        else:
            choices = [
                mp.to_note(i) if isinstance(i, str) else i for i in choices
            ]
            if mode == 'name':
                return max([i.name for i in choices],
                           key=lambda s: test_obj.count(s))
            elif mode == 'note':
                return max(choices,
                           key=lambda s: test_obj.count(s, mode='note'))

    def count_appear(self, choices=None, as_standard=True, sort=False):
        test_obj = self
        if as_standard:
            test_obj = self.standard_notation()
        if not choices:
            choices = copy(database.standard2) if as_standard else copy(
                database.standard)
        else:
            choices = [
                mp.to_note(i).name if isinstance(i, str) else i.name
                for i in choices
            ]
        result = {i: test_obj.count(i) for i in choices}
        if sort:
            result = [[i, result[i]] for i in result]
            result.sort(key=lambda s: s[1], reverse=True)
        return result

    def eval_time(self,
                  bpm,
                  ind1=None,
                  ind2=None,
                  mode='seconds',
                  start_time=0,
                  normalize_tempo=False,
                  audio_mode=0):
        if normalize_tempo:
            temp = copy(self)
            temp.normalize_tempo(bpm)
            return temp.eval_time(bpm,
                                  ind1,
                                  ind2,
                                  start_time,
                                  mode=mode,
                                  audio_mode=audio_mode)
        if ind1 is None:
            whole_bars = self.bars(start_time, audio_mode=audio_mode, bpm=bpm)
        else:
            if ind2 is None:
                ind2 = self.bars(start_time, audio_mode=audio_mode, bpm=bpm)
            whole_bars = ind2 - ind1
        result = (60 / bpm) * whole_bars * 4
        if mode == 'seconds':
            result = round(result, 3)
            return f'{result}s'
        elif mode == 'hms':
            hours = int(result / 3600)
            minutes = int((result - 3600 * hours) / 60)
            seconds = round(result - 3600 * hours - 60 * minutes, 3)
            if hours:
                return f'{hours} hours, {minutes} minutes, {seconds} seconds'
            else:
                return f'{minutes} minutes, {seconds} seconds'
        elif mode == 'number':
            return result

    def count_bars(self, ind1, ind2, bars_range=True):
        bars_length = self[ind1:ind2].bars()
        if bars_range:
            start = self[:ind1].bars(mode=0)
            return [start, start + bars_length]
        else:
            return bars_length

    def clear_pitch_bend(self, value='all', cond=None):
        pitch_bends = self.pitch_bends
        length = len(pitch_bends)
        if cond is None:
            if value == 'all':
                self.pitch_bends.clear()
                return
            else:
                inds = [
                    i for i in range(length) if pitch_bends[i].value != value
                ]
        else:
            inds = [i for i in range(length) if not cond(pitch_bends[i])]
        self.pitch_bends = [pitch_bends[k] for k in inds]

    def clear_tempo(self, cond=None):
        if cond is None:
            self.tempos.clear()
        else:
            tempos = self.tempos
            length = len(tempos)
            inds = [i for i in range(length) if not cond(tempos[i])]
            self.tempos = [tempos[k] for k in inds]

    def only_notes(self):
        temp = copy(self)
        temp.clear_tempo()
        temp.clear_pitch_bend()
        return temp

    def __mod__(self, alist):
        if isinstance(alist, (list, tuple)):
            return self.set(*alist)
        elif isinstance(alist, (str, note)):
            return self.on(alist)

    def standardize(self, standardize_note=True):
        temp = self.only_notes()
        notenames = temp.names()
        intervals = temp.interval
        durations = temp.get_duration()
        if standardize_note:
            names_standard = [mp.standardize_note(i) for i in notenames]
        else:
            names_standard = notenames
        names_offrep = []
        new_duration = []
        new_interval = []
        for i in range(len(names_standard)):
            current = names_standard[i]
            if current not in names_offrep:
                if current is not None:
                    names_offrep.append(current)
                else:
                    names_offrep.append(temp.notes[i])
                new_interval.append(intervals[i])
                new_duration.append(durations[i])
        temp.notes = chord(names_offrep,
                           rootpitch=temp[0].num,
                           duration=new_duration).notes
        temp.interval = new_interval
        return temp

    def standardize_note(self):
        temp = copy(self)
        for i in temp:
            i.name = mp.standardize_note(i.name)
        return temp

    def sortchord(self):
        temp = self.copy()
        temp.notes.sort(key=lambda x: x.degree)
        return temp

    def set(self, duration=None, interval=None, volume=None, ind='all'):
        if interval is None:
            interval = copy(self.interval)
        result = chord(copy(self.notes),
                       duration,
                       interval,
                       start_time=copy(self.start_time))
        if volume is not None:
            result.set_volume(volume, ind)
        return result

    def special_set(self,
                    duration=None,
                    interval=None,
                    volume=None,
                    ind='all'):
        if interval is None:
            interval = copy(self.interval)
        result = chord(copy(self.notes),
                       duration,
                       interval,
                       start_time=copy(self.start_time))
        result.interval = [
            0 if hasattr(self.notes[i], 'keep_same_time')
            and self.notes[i].keep_same_time else result.interval[i]
            for i in range(len(self))
        ]
        result.set_volume(volume)
        if volume is not None:
            result.set_volume(volume, ind)
        return result

    def change_interval(self, newinterval):
        if isinstance(newinterval, (int, float)):
            self.interval = [newinterval for i in range(len(self.notes))]
        else:
            if len(newinterval) == len(self.interval):
                self.interval = newinterval
            else:
                raise ValueError(
                    'please ensure the intervals between notes has the same numbers of the notes'
                )

    def __repr__(self):
        return self.show()

    def show(self, limit=10):
        if limit is None:
            limit = len(self.notes)
        current_notes_str = ', '.join([str(i) for i in self.notes[:limit]])
        if len(self.notes) > limit:
            current_notes_str += ', ...'
        current_interval_str = ', '.join([
            str(Fraction(i).limit_denominator()) for i in self.interval[:limit]
        ])
        if len(self.interval) > limit:
            current_interval_str += ', ...'
        result = f'chord(notes=[{current_notes_str}], interval=[{current_interval_str}], start_time={self.start_time})'
        return result

    def __contains__(self, note1):
        if not isinstance(note1, note):
            note1 = mp.to_note(note1)
            if note1.name in database.standard_dict:
                note1.name = database.standard_dict[note1.name]
        return note1 in self.same_accidentals().notes

    def __add__(self, obj):
        if isinstance(obj, (int, list, database.Interval)):
            return self.up(obj)
        elif isinstance(obj, tuple):
            if isinstance(obj[0], chord):
                return self | obj
            else:
                return self.up(*obj)
        elif isinstance(obj, rest):
            return self.rest(obj.get_duration())
        temp = copy(self)
        if isinstance(obj, note):
            temp.notes.append(copy(obj))
            temp.interval.append(temp.interval[-1])
        elif isinstance(obj, str):
            return temp + mp.to_note(obj)
        elif isinstance(obj, chord):
            temp |= obj
        return temp

    def __radd__(self, obj):
        if isinstance(obj, (rest, float)):
            temp = copy(self)
            temp.start_time += (obj if not isinstance(obj, rest) else
                                obj.get_duration())
            return temp
        elif isinstance(obj, (int, database.Interval)):
            return self + obj

    def __ror__(self, obj):
        if isinstance(obj, (int, float, rest)):
            temp = copy(self)
            temp.start_time += (obj if not isinstance(obj, rest) else
                                obj.get_duration())
            return temp

    def __pos__(self):
        return self.up()

    def __neg__(self):
        return self.down()

    def __invert__(self):
        return self.reverse()

    def __or__(self, obj):
        if isinstance(obj, (int, float)):
            return self.rest(obj)
        elif isinstance(obj, str):
            obj = mp.trans(obj)
        elif isinstance(obj, tuple):
            first = obj[0]
            start = obj[1] if len(obj) == 2 else 0
            if isinstance(first, int):
                temp = copy(self)
                for k in range(first - 1):
                    temp |= (self, start)
                return temp
            elif isinstance(first, rest):
                return self.rest(first.get_duration(),
                                 ind=obj[1] if len(obj) == 2 else None)
            else:
                return self.add(first, start=start, mode='after')
        elif isinstance(obj, list):
            return self.rest(*obj)
        elif isinstance(obj, rest):
            return self.rest(obj.get_duration())
        return self.add(obj, mode='after')

    def __xor__(self, obj):
        if isinstance(obj, int):
            return self.inversion_highest(obj)
        if isinstance(obj, note):
            name = obj.name
        else:
            name = obj
        notenames = self.names()
        if name in notenames and name != notenames[-1]:
            return self.inversion_highest(notenames.index(name))
        else:
            return self + obj

    def __truediv__(self, obj):
        if isinstance(obj, int):
            if obj > 0:
                return self.inversion(obj)
            else:
                return self.inversion_highest(-obj)
        elif isinstance(obj, list):
            return self.sort(obj)
        else:
            if not isinstance(obj, chord):
                if isinstance(obj, str):
                    obj = mp.trans_note(obj)
                notenames = self.names()
                if obj.name not in database.standard2:
                    obj.name = database.standard_dict[obj.name]
                if obj.name in notenames and obj.name != notenames[0]:
                    return self.inversion(notenames.index(obj.name))
            return self.on(obj)

    def __and__(self, obj):
        if isinstance(obj, tuple):
            if len(obj) == 2:
                first = obj[0]
                if isinstance(first, int):
                    temp = copy(self)
                    for k in range(first - 1):
                        temp &= (self, (k + 1) * obj[1])
                    return temp
                else:
                    return self.add(obj[0], start=obj[1], mode='head')
            else:
                return
        elif isinstance(obj, int):
            return self & (obj, 0)
        else:
            return self.add(obj, mode='head')

    def __matmul__(self, obj):
        if type(obj) is list:
            return self.get(obj)
        elif isinstance(obj, int):
            return self.inv(obj)
        elif isinstance(obj, str):
            return self.inv(self.names().index(
                database.standard_dict.get(obj, obj)))
        elif isinstance(obj, rhythm):
            return self.from_rhythm(obj)
        else:
            if isinstance(obj, tuple):
                return mp.alg.negative_harmony(obj[0], self, *obj[1:])
            else:
                return mp.alg.negative_harmony(obj, self)

    def negative_harmony(self, *args, **kwargs):
        return mp.alg.negative_harmony(current_chord=self, *args, **kwargs)

    def __call__(self, obj):
        # deal with the chord's sharp or flat notes, or to omit some notes
        # of the chord
        temp = copy(self)
        commands = obj.split(',')
        for each in commands:
            each = each.replace(' ', '')
            first = each[0]
            if first in ['#', 'b']:
                degree = each[1:]
                if degree in database.degree_match:
                    degree_ls = database.degree_match[degree]
                    found = False
                    for i in degree_ls:
                        current_note = temp[0] + i
                        if current_note in temp:
                            ind = temp.notes.index(current_note)
                            temp.notes[ind] = temp.notes[ind].sharp(
                            ) if first == '#' else temp.notes[ind].flat()
                            found = True
                            break
                    if not found:
                        if first == '#':
                            new_note = (temp[0] + degree_ls[0]).sharp()
                        else:
                            new_note = (temp[0] + degree_ls[0]).flat()
                        temp += new_note
                else:
                    self_names = temp.names()
                    if degree in self_names:
                        ind = temp.names().index(degree)
                        temp.notes[ind] = temp.notes[ind].sharp(
                        ) if first == '#' else temp.notes[ind].flat()
            elif each.startswith('omit') or each.startswith('no'):
                degree = each[4:] if each.startswith('omit') else each[2:]
                if degree in database.degree_match:
                    degree_ls = database.degree_match[degree]
                    for i in degree_ls:
                        current_note = temp[0] + i
                        if current_note in temp:
                            ind = temp.notes.index(current_note)
                            del temp.notes[ind]
                            del temp.interval[ind]
                            break
                else:
                    self_names = temp.names()
                    if degree in self_names:
                        temp = temp.omit(degree)
            elif each.startswith('sus'):
                num = each[3:]
                if num.isdigit():
                    num = int(num)
                else:
                    num = 4
                temp.notes = temp.sus(num).notes
            elif each.startswith('add'):
                degree = each[3:]
                if degree in database.degree_match:
                    degree_ls = database.degree_match[degree]
                    temp += (temp[0] + degree_ls[0])
            else:
                raise ValueError(f'{obj} is not a valid chord alternation')
        return temp

    def get(self, ls):
        temp = copy(self)
        result = []
        result_interval = []
        for each in ls:
            if isinstance(each, int):
                result.append(temp[each - 1])
                result_interval.append(temp.interval[each - 1])
            elif isinstance(each, float):
                num, pitch = [int(j) for j in str(each).split('.')]
                if num > 0:
                    current_note = temp[num - 1] + pitch * database.octave
                else:
                    current_note = temp[-num - 1] - pitch * database.octave
                result.append(current_note)
                result_interval.append(temp.interval[abs(num) - 1])
        return chord(result,
                     interval=result_interval,
                     start_time=temp.start_time)

    def pop(self, ind=None):
        if ind is None:
            result = self.notes.pop()
            self.interval.pop()
        else:
            result = self.notes.pop(ind)
            self.interval.pop(ind)
        return result

    def __sub__(self, obj):
        if isinstance(obj, (int, list, database.Interval)):
            return self.down(obj)
        elif isinstance(obj, tuple):
            return self.down(*obj)
        if not isinstance(obj, note):
            obj = mp.to_note(obj)
        temp = copy(self)
        if obj in temp:
            ind = temp.notes.index(obj)
            del temp.notes[ind]
            del temp.interval[ind]
        return temp

    def __mul__(self, num):
        if isinstance(num, tuple):
            return self | num
        else:
            temp = copy(self)
            for i in range(num - 1):
                temp |= self
            return temp

    def __rmul__(self, num):
        return self * num

    def reverse(self, start=None, end=None, cut=False, start_time=0):
        temp = copy(self)
        if start is None:
            temp2 = temp.only_notes()
            length = len(temp2)
            bar_length = temp2.bars()
            tempos = []
            pitch_bends = []
            for each in temp.tempos:
                each.start_time -= start_time
                each.start_time = bar_length - each.start_time
                tempos.append(each)
            for each in temp.pitch_bends:
                each.start_time -= start_time
                each.start_time = bar_length - each.start_time
                pitch_bends.append(each)
            if temp2.notes:
                last_interval = temp2.interval[-1]
                end_events = []
                current_start_time = 0
                for i in range(len(temp2.notes)):
                    current_note = temp2.notes[i]
                    current_end_time = current_start_time + current_note.duration
                    current_end_event = (current_note, current_end_time, i)
                    end_events.append(current_end_event)
                    current_start_time += temp2.interval[i]
                end_events.sort(key=lambda s: (s[1], s[2]), reverse=True)
                new_notes = [i[0] for i in end_events]
                new_interval = [
                    end_events[j][1] - end_events[j + 1][1]
                    for j in range(len(end_events) - 1)
                ]
                new_interval.append(last_interval)
                temp2.notes = new_notes
                temp2.interval = new_interval
            temp2.tempos = tempos
            temp2.pitch_bends = pitch_bends
            return temp2
        else:
            if end is None:
                result = temp[:start] + temp[start:].reverse(
                    start_time=start_time)
                return result[start:] if cut else result
            else:
                result = temp[:start] + temp[start:end].reverse(
                    start_time=start_time) + temp[end:]
                return result[start:end] if cut else result

    def reverse_chord(self, start_time=0):
        temp = copy(self)
        bar_length = temp.bars()
        temp.notes = temp.notes[::-1]
        temp.interval = temp.interval[::-1]
        if temp.interval:
            temp.interval.append(temp.interval.pop(0))
        for each in temp.tempos:
            each.start_time -= start_time
            each.start_time = bar_length - each.start_time
        for each in temp.pitch_bends:
            each.start_time -= start_time
            each.start_time = bar_length - each.start_time
        return temp

    def intervalof(self, cumulative=True, translate=False):
        degrees = self.get_degree()
        N = len(degrees)
        if not cumulative:
            if not translate:
                result = [degrees[i] - degrees[i - 1] for i in range(1, N)]
            else:
                result = [
                    mp.get_pitch_interval(self.notes[i - 1], self.notes[i])
                    for i in range(1, N)
                ]
        else:
            if not translate:
                root = degrees[0]
                others = degrees[1:]
                result = [i - root for i in others]
            else:
                result = [
                    mp.get_pitch_interval(self.notes[0], i)
                    for i in self.notes[1:]
                ]
        return result

    def add(self,
            note1=None,
            mode='after',
            start=0,
            duration=1 / 4,
            adjust_msg=True):
        if self.is_empty():
            result = copy(note1)
            shift = start
            if mode == 'after':
                shift += self.start_time
            elif mode == 'head':
                if result.interval:
                    last_note_diff = self.start_time - (
                        result.start_time + shift + sum(result.interval[:-1]))
                    result.interval[-1] = max(result.interval[-1],
                                              last_note_diff)
            result.start_time += shift
            if adjust_msg:
                result.apply_start_time_to_changes(shift, msg=True)
            if not result.notes:
                result.start_time = max(result.start_time, self.start_time)
            return result
        temp = copy(self)
        if note1.is_empty():
            if mode == 'after':
                if note1.start_time > 0:
                    temp = temp.rest(note1.start_time)
            elif mode == 'head':
                if temp.interval:
                    last_note_diff = (note1.start_time + start) - (
                        temp.start_time + sum(temp.interval[:-1]))
                    temp.interval[-1] = max(temp.interval[-1], last_note_diff)
                else:
                    temp.start_time = max(temp.start_time,
                                          note1.start_time + start)
            return temp
        if mode == 'tail':
            note1 = copy(note1)
            adjust_interval = sum(temp.interval)
            temp.notes += note1.notes
            temp.interval += note1.interval
            if adjust_msg:
                note1.apply_start_time_to_changes(adjust_interval, msg=True)
            temp.other_messages += note1.other_messages
            temp.tempos += note1.tempos
            temp.pitch_bends += note1.pitch_bends
            return temp
        elif mode == 'head':
            note1 = copy(note1)
            if isinstance(note1, str):
                note1 = chord([mp.to_note(note1, duration=duration)])
            elif isinstance(note1, note):
                note1 = chord([note1])
            elif isinstance(note1, list):
                note1 = chord(note1)
            # calculate the absolute distances of all of the notes of the chord to add and self,
            # and then sort them, make differences between each two distances
            apply_msg_chord = note1
            if temp.notes:
                note1_start_time = note1.start_time + start
                if note1_start_time < 0:
                    current_add_start_time = temp.start_time - note1_start_time
                    note1.start_time = temp.start_time + note1_start_time
                    temp, note1 = note1, temp
                    apply_msg_chord = temp
                else:
                    if note1_start_time < temp.start_time:
                        current_add_start_time = temp.start_time - note1_start_time
                        note1.start_time = note1_start_time
                        temp, note1 = note1, temp
                        apply_msg_chord = temp
                    else:
                        current_add_start_time = note1_start_time - temp.start_time

                if not temp.notes:
                    new_notes = note1.notes
                    new_interval = note1.interval
                    current_start_time = note1.start_time
                else:
                    distance = []
                    intervals1 = temp.interval
                    intervals2 = note1.interval
                    current_start_time = temp.start_time

                    if current_add_start_time != 0:
                        note1.notes.insert(0, temp.notes[0])
                        intervals2.insert(0, current_add_start_time)
                    counter = 0
                    for i in range(len(intervals1)):
                        distance.append([counter, temp.notes[i]])
                        counter += intervals1[i]
                    counter = 0
                    for j in range(len(intervals2)):
                        if not (j == 0 and current_add_start_time != 0):
                            distance.append([counter, note1.notes[j]])
                        counter += intervals2[j]
                    distance.sort(key=lambda s: s[0])
                    new_notes = [each[1] for each in distance]
                    new_interval = [each[0] for each in distance]
                    new_interval = [
                        new_interval[i] - new_interval[i - 1]
                        for i in range(1, len(new_interval))
                    ] + [distance[-1][1].duration]
            else:
                new_notes = note1.notes
                new_interval = note1.interval
                current_start_time = note1.start_time + start
            if adjust_msg:
                apply_msg_chord.apply_start_time_to_changes(start, msg=True)
            return chord(new_notes,
                         interval=new_interval,
                         start_time=current_start_time,
                         other_messages=temp.other_messages +
                         note1.other_messages,
                         tempos=temp.tempos + note1.tempos,
                         pitch_bends=temp.pitch_bends + note1.pitch_bends)
        elif mode == 'after':
            return self.rest(start + note1.start_time).add(note1, mode='tail')

    def inversion(self, num=1):
        if not 1 <= num < len(self.notes):
            raise ValueError(
                'the number of inversion is out of range of the notes in this chord'
            )
        else:
            temp = copy(self)
            for i in range(num):
                temp.notes.append(temp.notes.pop(0) + database.octave)
            return temp

    def inv(self, num=1, interval=None):
        temp = self.copy()
        if isinstance(num, str):
            return self @ num
        if not 1 <= num < len(self.notes):
            raise ValueError(
                'the number of inversion is out of range of the notes in this chord'
            )
        while temp[num].degree >= temp[num - 1].degree:
            temp[num] = temp[num].down(database.octave)
        current_interval = copy(temp.interval)
        temp.insert(0, temp.pop(num))
        temp.interval = current_interval
        return temp

    def sort(self, indlist, rootpitch=None):
        temp = self.copy()
        names = [temp[i - 1].name for i in indlist]
        if rootpitch is None:
            rootpitch = temp[indlist[0] - 1].num
        elif rootpitch == 'same':
            rootpitch = temp[0].num
        new_interval = [temp.interval[i - 1] for i in indlist]
        return chord(names,
                     rootpitch=rootpitch,
                     interval=new_interval,
                     start_time=temp.start_time)

    def voicing(self, rootpitch=None):
        if rootpitch is None:
            rootpitch = self[0].num
        duration, interval = [i.duration for i in self.notes], self.interval
        notenames = self.names()
        return [
            chord(i,
                  rootpitch=rootpitch).standardize().set(duration, interval)
            for i in mp.alg.perm(notenames)
        ]

    def inversion_highest(self, ind):
        if not 1 <= ind < len(self):
            raise ValueError(
                'the number of inversion is out of range of the notes in this chord'
            )
        temp = self.copy()
        ind -= 1
        while temp[ind].degree < temp[-1].degree:
            temp[ind] = temp[ind].up(database.octave)
        temp.notes.append(temp.notes.pop(ind))
        return temp

    def inoctave(self):
        temp = self.copy()
        root = self[0].degree
        for i in range(1, len(temp)):
            while temp[i].degree - root > database.octave:
                temp[i] = temp[i].down(database.octave)
        temp.notes.sort(key=lambda x: x.degree)
        return temp

    def on(self, root, duration=1 / 4, interval=None, each=0):
        temp = copy(self)
        if each == 0:
            if isinstance(root, chord):
                return root & self
            if isinstance(root, str):
                root = mp.to_note(root)
                root.duration = duration
            temp.notes.insert(0, root)
            if interval is not None:
                temp.interval.insert(0, interval)
            else:
                temp.interval.insert(0, self.interval[0])
            return temp
        else:
            if isinstance(root, chord):
                root = list(root)
            else:
                root = [mp.to_note(i) for i in root]
            return [self.on(x, duration, interval) for x in root]

    def up(self, unit=1, ind=None, ind2=None):
        temp = copy(self)
        if not isinstance(unit, (int, database.Interval)):
            temp.notes = [temp.notes[k].up(unit[k]) for k in range(len(unit))]
            return temp
        if not isinstance(ind, (int, database.Interval)) and ind is not None:
            temp.notes = [
                temp.notes[i].up(unit) if i in ind else temp.notes[i]
                for i in range(len(temp.notes))
            ]
            return temp
        if ind2 is None:
            if ind is None:
                temp.notes = [each.up(unit) for each in temp.notes]
            else:
                temp[ind] = temp[ind].up(unit)
        else:
            temp.notes = temp.notes[:ind] + [
                each.up(unit) for each in temp.notes[ind:ind2]
            ] + temp.notes[ind2:]
        return temp

    def down(self, unit=1, ind=None, ind2=None):
        if not isinstance(unit, (int, database.Interval)):
            unit = [-i for i in unit]
            return self.up(unit, ind, ind2)
        return self.up(-unit, ind, ind2)

    def sharp(self, unit=1):
        temp = copy(self)
        temp.notes = [i.sharp(unit=unit) for i in temp.notes]
        return temp

    def flat(self, unit=1):
        temp = copy(self)
        temp.notes = [i.flat(unit=unit) for i in temp.notes]
        return temp

    def omit(self, ind, mode=0):
        '''
        mode == 0: omit note as pitch interval with the first note
        mode == 1: omit note as number of semitones with the first note
        mode == 2: omit note as index of current chord
        '''
        if not isinstance(ind, list):
            ind = [ind]
        if mode == 0:
            ind = [self.interval_note(i) for i in ind]
        elif mode == 1:
            ind = [self.notes[0] + i for i in ind]
        if ind:
            if isinstance(ind[0], int):
                temp = copy(self)
                length = len(temp)
                temp.notes = [
                    temp.notes[k] for k in range(length) if k not in ind
                ]
                temp.interval = [
                    temp.interval[k] for k in range(length) if k not in ind
                ]
                return temp
            elif isinstance(ind[0], note) or (isinstance(ind[0], str) and any(
                    i for i in ind[0] if i.isdigit())):
                temp = self.same_accidentals()
                ind = chord(ind).same_accidentals().notes
                current_ind = [
                    k for k in range(len(temp)) if temp.notes[k] in ind
                ]
                return self.omit(current_ind, mode=2)
            elif isinstance(ind[0],
                            str) and not any(i for i in ind[0] if i.isdigit()):
                temp = self.standardize_note()
                self_notenames = temp.names()
                ind = chord(ind).standardize_note().names()
                current_ind = [
                    k for k in range(len(self_notenames))
                    if self_notenames[k] in ind
                ]
                return self.omit(current_ind, mode=2)
            else:
                return self
        else:
            return self

    def sus(self, num=4):
        temp = self.copy()
        first_note = temp[0]
        if num == 4:
            temp.notes = [
                temp.notes[0] +
                database.P4 if abs(i.degree - first_note.degree) %
                database.octave
                in [database.major_third, database.minor_third] else i
                for i in temp.notes
            ]
        elif num == 2:
            temp.notes = [
                temp.notes[0] +
                database.M2 if abs(i.degree - first_note.degree) %
                database.octave
                in [database.major_third, database.minor_third] else i
                for i in temp.notes
            ]
        return temp

    def __setitem__(self, ind, value):
        if isinstance(value, str):
            value = mp.to_note(value)
        self.notes[ind] = value
        if isinstance(value, chord):
            self.interval[ind] = value.interval

    def __delitem__(self, ind):
        del self.notes[ind]
        del self.interval[ind]

    def index(self, value):
        if isinstance(value, str):
            if value not in database.standard:
                value = mp.to_note(value)
                if value not in self:
                    return -1
                return self.notes.index(value)
            else:
                note_names = self.names()
                if value not in note_names:
                    return -1
                return note_names.index(value)
        else:
            return self.index(str(value))

    def remove(self, note1):
        if isinstance(note1, str):
            note1 = mp.to_note(note1)
        if note1 in self:
            inds = self.notes.index(note1)
            self.notes.remove(note1)
            del self.interval[inds]

    def append(self, value, interval=0):
        if isinstance(value, str):
            value = mp.to_note(value)
        self.notes.append(value)
        self.interval.append(interval)

    def extend(self, values, intervals=0):
        if isinstance(values, chord):
            self.notes.extend(values.notes)
            self.interval.extend(values.interval)
        else:
            values = [
                mp.to_note(value) if isinstance(value, str) else value
                for value in values
            ]
            if isinstance(intervals, int):
                intervals = [intervals for i in range(len(values))]
            self.notes.extend(values)
            self.interval.extend(intervals)

    def delete(self, ind):
        del self.notes[ind]
        del self.interval[ind]

    def insert(self, ind, value, interval=0):
        if isinstance(value, chord):
            self.notes[ind:ind] = value.notes
            self.interval[ind:ind] = value.interval
        else:
            if isinstance(value, str):
                value = mp.to_note(value)
            self.notes.insert(ind, value)
            self.interval.insert(ind, interval)

    def replace_chord(self, ind1, ind2=None, value=None, mode=0):
        if not isinstance(value, chord):
            value = chord(value)
        if ind2 is None:
            ind2 = ind1 + len(value)
        if mode == 0:
            self.notes[ind1:ind2] = value.notes
            self.interval[ind1:ind2] = value.interval
        elif mode == 1:
            N = len(self.notes)
            for i in range(ind1, ind2):
                current_value = value.notes[i - ind1]
                if i < N:
                    current = self.notes[i]
                    current.name = current_value.name
                    current.num = current_value.num
                else:
                    self.notes[i:i] = [current_value]
                    self.interval[i:i] = [value.interval[i - ind1]]

    def drops(self, ind):
        temp = self.copy()
        dropnote = temp.notes.pop(-ind).down(database.octave)
        dropinterval = temp.interval.pop(-ind)
        temp.notes.insert(0, dropnote)
        temp.interval.insert(0, dropinterval)
        return temp

    def rest(self, length, dotted=None, ind=None):
        temp = copy(self)
        if dotted is not None:
            length = length * sum([(1 / 2)**i for i in range(dotted + 1)])
        if not temp.notes:
            temp.start_time += length
            return temp
        if ind is None:
            last_interval = temp.interval[-1]
            if last_interval != 0:
                temp.interval[-1] += length
            else:
                temp.interval[-1] += (temp.notes[-1].duration + length)
        else:
            if ind == len(temp) - 1:
                last_interval = temp.interval[-1]
                if last_interval != 0:
                    temp.interval[-1] += length
                else:
                    temp.interval[-1] += (temp.notes[-1].duration + length)
            else:
                temp.interval[ind] += length
        return temp

    def modulation(self, old_scale, new_scale):
        # change notes (including both of melody and chords) in the given piece
        # of music from a given scale to another given scale, and return
        # the new changing piece of music

        # this modulation function only supports modulate from a scale with equal or more notes to another scale
        temp = copy(self)
        old_scale_names = [
            i if i not in database.standard_dict else database.standard_dict[i]
            for i in old_scale.names()
        ]
        new_scale_names = [
            i if i not in database.standard_dict else database.standard_dict[i]
            for i in new_scale.names()
        ]
        old_scale_names_len = len(old_scale_names)
        new_scale_names_len = len(new_scale_names)
        if new_scale_names_len < old_scale_names_len:
            new_scale_names += new_scale_names[-(old_scale_names_len -
                                                 new_scale_names_len):]
            new_scale_names.sort(key=lambda s: database.standard[s])
        number = len(new_scale_names)
        transdict = {
            old_scale_names[i]: new_scale_names[i]
            for i in range(number)
        }
        for k in range(len(temp)):
            current = temp.notes[k]
            if current.name in database.standard_dict:
                current_name = database.standard_dict[current.name]
            else:
                current_name = current.name
            if current_name in transdict:
                current_note = mp.closest_note(transdict[current_name],
                                               current)
                temp.notes[k] = current.reset(name=current_note.name,
                                              num=current_note.num)
        return temp

    def __getitem__(self, ind):
        if isinstance(ind, slice):
            return self.__getslice__(ind.start, ind.stop)
        return self.notes[ind]

    def __iter__(self):
        for i in self.notes:
            yield i

    def __getslice__(self, i, j):
        temp = copy(self)
        temp.notes = temp.notes[i:j]
        temp.interval = temp.interval[i:j]
        return temp

    def __len__(self):
        return len(self.notes)

    def set_volume(self, vol, ind='all'):
        if isinstance(ind, int):
            each = self.notes[ind]
            each.set_volume(vol)
        elif isinstance(ind, list):
            if isinstance(vol, list):
                for i in range(len(ind)):
                    current = ind[i]
                    each = self.notes[current]
                    each.set_volume(vol[i])
            elif isinstance(vol, (int, float)):
                vol = int(vol)
                for i in range(len(ind)):
                    current = ind[i]
                    each = self.notes[current]
                    each.set_volume(vol)
        elif ind == 'all':
            if isinstance(vol, list):
                for i in range(len(vol)):
                    current = self.notes[i]
                    current.set_volume(vol[i])
            elif isinstance(vol, (int, float)):
                vol = int(vol)
                for each in self.notes:
                    each.set_volume(vol)

    def move(self, x):
        # x could be a dict or list of (index, move_steps)
        temp = self.copy()
        if isinstance(x, dict):
            for i in x:
                temp.notes[i] = temp.notes[i].up(x[i])
            return temp
        if isinstance(x, list):
            for i in x:
                temp.notes[i[0]] = temp.notes[i[0]].up(i[1])
            return temp

    def clear_at(self, duration=0, interval=None, volume=None):
        temp = copy(self)
        i = 0
        while i < len(temp):
            current = temp[i]
            if duration is not None:
                if current.duration <= duration:
                    temp.delete(i)
                    continue
            if interval is not None:
                if temp.interval[i] <= interval:
                    temp.delete(i)
                    continue
            if volume is not None:
                if current.volume <= volume:
                    temp.delete(i)
                    continue
            i += 1
        return temp

    def retrograde(self):
        temp = self.copy()
        tempo_changes = temp.tempos
        if tempo_changes:
            temp.normalize_tempo(tempo_changes[0].bpm)
        result = temp.reverse()
        return result

    def pitch_inversion(self):
        pitch_bend_changes = self.pitch_bends
        temp = self.copy()
        temp.clear_pitch_bend()
        tempo_changes = temp.tempos
        if tempo_changes:
            temp.normalize_tempo(tempo_changes[0].bpm)
        volumes = temp.get_volume()
        pitch_intervals = temp.intervalof(cumulative=False)
        result = mp.get_chord_by_interval(temp[0],
                                          [-i for i in pitch_intervals],
                                          temp.get_duration(), temp.interval,
                                          False)
        result.set_volume(volumes)
        result += pitch_bend_changes
        return result

    def normalize_tempo(self,
                        bpm,
                        start_time=0,
                        pan_msg=None,
                        volume_msg=None,
                        original_bpm=None):
        # choose a bpm and apply to all of the notes, if there are tempo
        # changes, use relative ratios of the chosen bpms and changes bpms
        # to re-calculate the notes durations and intervals
        if original_bpm is not None:
            self.tempos.append(tempo(bpm=original_bpm, start_time=0))
        if all(i.bpm == bpm for i in self.tempos):
            self.clear_tempo()
            return
        if start_time > 0:
            self.notes.insert(0, note('C', 5, duration=0))
            self.interval.insert(0, start_time)
        tempo_changes = copy(self.tempos)
        tempo_changes.insert(0, tempo(bpm=bpm, start_time=0))
        self.clear_tempo()
        tempo_changes.sort(key=lambda s: s.start_time)
        new_tempo_changes = [tempo_changes[0]]
        for i in range(len(tempo_changes) - 1):
            current_tempo = tempo_changes[i]
            next_tempo = tempo_changes[i + 1]
            if next_tempo.start_time == current_tempo.start_time:
                new_tempo_changes[-1] = next_tempo
            else:
                new_tempo_changes.append(next_tempo)
        tempo_changes_ranges = [
            (new_tempo_changes[i].start_time,
             new_tempo_changes[i + 1].start_time, new_tempo_changes[i].bpm)
            for i in range(len(new_tempo_changes) - 1)
        ]
        tempo_changes_ranges.append(
            (new_tempo_changes[-1].start_time, self.bars(mode=1),
             new_tempo_changes[-1].bpm))
        pitch_bend_msg = copy(self.pitch_bends)
        self.clear_pitch_bend()
        _process_normalize_tempo(self, tempo_changes_ranges, bpm)
        other_types = pitch_bend_msg + self.other_messages
        if pan_msg:
            other_types += pan_msg
        if volume_msg:
            other_types += volume_msg
        other_types.sort(key=lambda s: s.start_time)
        other_types.insert(0, pitch_bend(value=0, start_time=0))
        other_types_interval = [
            other_types[i + 1].start_time - other_types[i].start_time
            for i in range(len(other_types) - 1)
        ]
        other_types_interval.append(0)
        other_types_chord = chord([])
        other_types_chord.notes = other_types
        other_types_chord.interval = other_types_interval
        _process_normalize_tempo(other_types_chord,
                                 tempo_changes_ranges,
                                 bpm,
                                 mode=1)
        new_pitch_bends = []
        new_pan = []
        new_volume = []
        new_other_messages = []
        for i in range(len(other_types_chord.notes)):
            each = other_types_chord.notes[i]
            current_start_time = sum(other_types_chord.interval[:i])
            each.start_time = current_start_time
        del other_types_chord[0]
        for each in other_types_chord.notes:
            if isinstance(each, pitch_bend):
                new_pitch_bends.append(each)
            elif isinstance(each, pan):
                new_pan.append(each)
            elif isinstance(each, volume):
                new_volume.append(each)
            else:
                new_other_messages.append(each)
        self.pitch_bends.extend(new_pitch_bends)
        result = [new_other_messages]
        if new_pan or new_volume:
            result += [new_pan, new_volume]
        if start_time > 0:
            start_time = self.interval[0]
            del self.notes[0]
            del self.interval[0]
        return result, start_time

    def place_shift(self, time=0, pan_msg=None, volume_msg=None):
        temp = copy(self)
        for i in temp.tempos:
            i.start_time += time
            if i.start_time < 0:
                i.start_time = 0
        for i in temp.pitch_bends:
            i.start_time += time
            if i.start_time < 0:
                i.start_time = 0
        if pan_msg:
            for each in pan_msg:
                each.start_time += time
                if each.start_time < 0:
                    each.start_time = 0
        if volume_msg:
            for each in volume_msg:
                each.start_time += time
                if each.start_time < 0:
                    each.start_time = 0
        for each in temp.other_messages:
            each.start_time += time
            if each.start_time < 0:
                each.start_time = 0
        if pan_msg or volume_msg:
            return temp, pan_msg, volume_msg
        else:
            return temp

    def info(self, **detect_args):
        chord_type = self.detect(get_chord_type=True, **detect_args)
        return chord_type

    def same_accidentals(self, mode='#'):
        temp = copy(self)
        for each in temp.notes:
            each.name = mp.standardize_note(each.name)
            if mode == '#':
                if len(each.name) > 1 and each.name[-1] == 'b':
                    each.name = database.standard_dict[each.name]
            elif mode == 'b':
                if each.name[-1] == '#':
                    each.name = database.reverse_standard_dict[each.name]
        return temp

    def filter(self, cond, action=None, mode=0, action_mode=0):
        temp = self.copy()
        available_inds = [k for k in range(len(temp)) if cond(temp.notes[k])]
        if mode == 1:
            return available_inds
        if action is None:
            if available_inds:
                new_interval = []
                N = len(available_inds) - 1
                for i in range(N):
                    new_interval.append(
                        sum(temp.
                            interval[available_inds[i]:available_inds[i + 1]]))
                new_interval.append(sum(temp.interval[available_inds[-1]:]))
                new_notes = [temp.notes[j] for j in available_inds]
                result = chord(new_notes, interval=new_interval)
                start_time = sum(temp.interval[:available_inds[0]])
            else:
                result = chord([])
                start_time = 0
            return result, start_time
        else:
            if action_mode == 0:
                for each in available_inds:
                    temp.notes[each] = action(temp.notes[each])
            elif action_mode == 1:
                for each in available_inds:
                    action(temp.notes[each])
            return temp

    def pitch_filter(self, x='A0', y='C8'):
        if isinstance(x, str):
            x = mp.trans_note(x)
        if isinstance(y, str):
            y = mp.trans_note(y)
        if all(x.degree <= i.degree <= y.degree for i in self.notes):
            return self, 0
        temp = self.copy()
        available_inds = [
            k for k in range(len(temp))
            if x.degree <= temp.notes[k].degree <= y.degree
        ]
        if available_inds:
            new_interval = []
            N = len(available_inds) - 1
            for i in range(N):
                new_interval.append(
                    sum(temp.interval[available_inds[i]:available_inds[i +
                                                                       1]]))
            new_interval.append(sum(temp.interval[available_inds[-1]:]))
            new_notes = [temp.notes[j] for j in available_inds]
            start_time = sum(temp.interval[:available_inds[0]])
            temp.notes = new_notes
            temp.interval = new_interval

        else:
            temp.notes.clear()
            temp.interval.clear()
            start_time = 0
        return temp, start_time

    def interval_note(self, interval, mode=0):
        if mode == 0:
            interval = str(interval)
            if interval in database.degree_match:
                self_notes = self.same_accidentals().notes
                degrees = database.degree_match[interval]
                for each in degrees:
                    current_note = self_notes[0] + each
                    if current_note in self_notes:
                        return current_note
            if interval in database.precise_degree_match:
                self_notes = self.same_accidentals().notes
                degrees = database.precise_degree_match[interval]
                current_note = self_notes[0] + degrees
                if current_note in self_notes:
                    return current_note
        elif mode == 1:
            if interval in database.precise_degree_match:
                interval = database.precise_degree_match[interval]
            return self[0] + interval

    def note_interval(self, current_note, mode=0):
        if isinstance(current_note, str):
            if not any(i.isdigit() for i in current_note):
                current_note = mp.to_note(current_note)
                if database.standard[self[0].name] == database.standard[
                        current_note.name]:
                    current_interval = 0
                else:
                    current_chord = chord([self[0].name, current_note.name])
                    current_interval = current_chord[1].degree - current_chord[
                        0].degree
            else:
                current_note = mp.to_note(current_note)
                current_interval = current_note.degree - self[0].degree
        else:
            current_interval = current_note.degree - self[0].degree
        if mode == 0:
            if current_interval in database.reverse_precise_degree_match:
                return database.reverse_precise_degree_match[current_interval]
        elif mode == 1:
            return database.INTERVAL[current_interval]

    def get_voicing(self, voicing):
        notes = [self.interval_note(i).name for i in voicing]
        pitch = self.notes[self.names().index(notes[0])].num
        return chord(notes,
                     interval=copy(self.interval),
                     rootpitch=pitch,
                     start_time=copy(self.start_time))

    def near_voicing(self,
                     other,
                     keep_root=True,
                     standardize=True,
                     choose_nearest=False,
                     get_distance=False):
        if choose_nearest:
            result1, distance1 = self.near_voicing(other,
                                                   keep_root=True,
                                                   standardize=standardize,
                                                   choose_nearest=False,
                                                   get_distance=True)
            result2, distance2 = self.near_voicing(other,
                                                   keep_root=False,
                                                   standardize=standardize,
                                                   choose_nearest=False,
                                                   get_distance=True)
            result = result2 if distance2 < distance1 else result1
            return result if not get_distance else (result,
                                                    min(distance1, distance2))
        if standardize:
            temp = self.standardize()
            other = other.standardize()
        else:
            temp = copy(self)
        original_duration = temp.get_duration()
        original_volume = temp.get_volume()
        if keep_root:
            root_note = temp.notes[0]
            other_root_note = other.notes[0]
            new_root_note, current_distance = mp.closest_note(
                root_note, other_root_note, get_distance=True)
            remain_notes = []
            current_other_notes = other.notes[1:]
            total_distance = current_distance
            for each in temp.notes[1:]:
                current_closest_note, current_distance = mp.closest_note_from_chord(
                    each, current_other_notes, get_distance=True)
                total_distance += current_distance
                current_other_notes.remove(current_closest_note)
                new_note = mp.closest_note(each, current_closest_note)
                remain_notes.append(new_note)
            remain_notes.insert(0, new_root_note)
        else:
            remain_notes = []
            current_other_notes = other.notes
            total_distance = 0
            for each in temp.notes:
                current_closest_note, current_distance = mp.closest_note_from_chord(
                    each, current_other_notes, get_distance=True)
                total_distance += current_distance
                current_other_notes.remove(current_closest_note)
                new_note = mp.closest_note(each, current_closest_note)
                remain_notes.append(new_note)
        temp.notes = remain_notes
        temp = temp.sortchord()
        temp = temp.set(duration=original_duration, volume=original_volume)
        return temp if not get_distance else (temp, total_distance)

    def reset_octave(self, num):
        diff = num - self[0].num
        return self + diff * database.octave

    def reset_pitch(self, pitch):
        if isinstance(pitch, str):
            pitch = mp.to_note(pitch)
        return self + (pitch.degree - self[0].degree)

    def reset_same_octave(self, octave):
        temp = copy(self)
        for each in temp.notes:
            each.num = octave
        return temp

    def reset_same_channel(self, channel=None):
        for each in self.notes:
            each.channel = channel

    def with_same_channel(self, channel=None):
        temp = copy(self)
        temp.reset_same_channel(channel)
        return temp

    def with_other_messages(self, other_messages):
        temp = copy(self)
        temp.other_messages = other_messages
        return temp

    def clear_program_change(self):
        self.other_messages = [
            i for i in self.other_messages if i.type != 'program_change'
        ]

    def clear_other_messages(self, types=None):
        if types is None:
            self.other_messages.clear()
        else:
            self.other_messages = [
                i for i in self.other_messages if i.type != types
            ]

    def dotted(self, ind=-1, num=1, duration=True, interval=False):
        temp = copy(self)
        if duration:
            if isinstance(ind, list):
                for each in ind:
                    temp.notes[
                        each].duration = temp.notes[each].duration * sum(
                            [(1 / 2)**i for i in range(num + 1)])
            elif ind == 'all':
                for each in range(len(temp.notes)):
                    temp.notes[
                        each].duration = temp.notes[each].duration * sum(
                            [(1 / 2)**i for i in range(num + 1)])
            else:
                temp.notes[ind].duration = temp.notes[ind].duration * sum(
                    [(1 / 2)**i for i in range(num + 1)])
        if interval:
            if isinstance(ind, list):
                for each in ind:
                    temp.interval[each] = temp.interval[each] * sum(
                        [(1 / 2)**i for i in range(num + 1)])
            elif ind == 'all':
                for each in range(len(temp.notes)):
                    temp.interval[each] = temp.interval[each] * sum(
                        [(1 / 2)**i for i in range(num + 1)])
            else:
                temp.interval[ind] = temp.interval[ind] * sum(
                    [(1 / 2)**i for i in range(num + 1)])
        return temp

    def apply_start_time_to_changes(self, start_time, msg=False):
        for each in self.tempos:
            each.start_time += start_time
            if each.start_time < 0:
                each.start_time = 0
        for each in self.pitch_bends:
            each.start_time += start_time
            if each.start_time < 0:
                each.start_time = 0
        if msg:
            for each in self.other_messages:
                each.start_time += start_time
                if each.start_time < 0:
                    each.start_time = 0

    def with_start(self, start_time):
        temp = copy(self)
        temp.start_time = start_time
        return temp

    def reset_channel(self,
                      channel,
                      reset_msg=True,
                      reset_pitch_bend=True,
                      reset_note=True):
        if reset_msg:
            for i in self.other_messages:
                if hasattr(i, 'channel'):
                    i.channel = channel
        if reset_note:
            for i in self.notes:
                i.channel = channel
        if reset_pitch_bend:
            for i in self.pitch_bends:
                i.channel = channel

    def reset_track(self, track, reset_msg=True, reset_pitch_bend=True):
        if reset_msg:
            for i in self.other_messages:
                i.track = track
        if reset_pitch_bend:
            for i in self.pitch_bends:
                i.track = track

    def pick(self, indlist):
        temp = copy(self)
        whole_notes = temp.notes
        new_interval = []
        whole_interval = temp.interval
        M = len(indlist) - 1
        for i in range(M):
            new_interval.append(sum(whole_interval[indlist[i]:indlist[i + 1]]))
        new_interval.append(sum(whole_interval[indlist[-1]:]))
        start_time = temp[:indlist[0]].bars(mode=0)
        return chord([whole_notes[j] for j in indlist],
                     interval=new_interval,
                     start_time=start_time,
                     other_messages=temp.other_messages)

    def remove_duplicates(self):
        temp = copy(self)
        inds = []
        degrees = []
        notes = []
        intervals = []
        for i, each in enumerate(temp.notes):
            if each.degree not in degrees:
                degrees.append(each.degree)
                notes.append(each)
                intervals.append(temp.interval[i])
        temp.notes = notes
        temp.interval = intervals
        return temp

    def delete_track(self, current_ind):
        self.tempos = [i for i in self.tempos if i.track != current_ind]
        self.pitch_bends = [
            i for i in self.pitch_bends if i.track != current_ind
        ]
        for i in self.tempos:
            if i.track is not None and i.track > current_ind:
                i.track -= 1
        for i in self.pitch_bends:
            if i.track is not None and i.track > current_ind:
                i.track -= 1
        self.other_messages = [
            i for i in self.other_messages if i.track != current_ind
        ]
        for i in self.other_messages:
            if i.track > current_ind:
                i.track -= 1

    def delete_channel(self, current_ind):
        available_inds = [
            i for i, each in enumerate(self.notes)
            if each.channel != current_ind
        ]
        self.notes = [self.notes[i] for i in available_inds]
        self.interval = [self.interval[i] for i in available_inds]
        self.tempos = [i for i in self.tempos if i.channel != current_ind]
        self.pitch_bends = [
            i for i in self.pitch_bends if i.channel != current_ind
        ]
        self.other_messages = [
            i for i in self.other_messages
            if not (hasattr(i, 'channel') and i.channel == current_ind)
        ]

    def to_piece(self, *args, **kwargs):
        return mp.chord_to_piece(self, *args, **kwargs)

    def apply_rhythm(self, current_rhythm, set_duration=True):
        temp = copy(self)
        length = len(temp)
        counter = -1
        has_beat = False
        current_start_time = 0
        for i, each in enumerate(current_rhythm):
            current_duration = each.get_duration()
            if type(each) is beat:
                has_beat = True
                counter += 1
                if counter >= length:
                    break
                temp.interval[counter] = current_duration
                if set_duration:
                    if current_duration != 0:
                        temp.notes[counter].duration = current_duration
            elif type(each) is rest_symbol:
                if not has_beat:
                    current_start_time += current_duration
                else:
                    temp.interval[counter] += current_duration
            elif type(each) is continue_symbol:
                if not has_beat:
                    current_start_time += current_duration
                else:
                    temp.interval[counter] += current_duration
                    temp.notes[counter].duration += current_duration
        temp.start_time = current_start_time
        return temp

    def from_rhythm(self, current_rhythm, set_duration=True):
        return mp.get_chords_from_rhythm(chords=self,
                                         current_rhythm=current_rhythm,
                                         set_duration=set_duration)

    def fix_length(self, n, round_duration=False, round_cut_interval=False):
        current_bar = self.bars(mode=2, start_time=self.start_time)
        if current_bar < n:
            extra = n - current_bar
            result = self | extra
        elif current_bar > n:
            result = self.cut(0,
                              n,
                              start_time=self.start_time,
                              cut_extra_duration=True,
                              cut_extra_interval=True,
                              round_duration=round_duration,
                              round_cut_interval=round_cut_interval)
        else:
            result = copy(self)
        return result

    def is_empty(self):
        return not self.notes and not self.tempos and not self.pitch_bends and not self.other_messages


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
            return self[ind, ]

    def rotate(self, start, step=1, direction='cw', inner=False):
        if direction == 'ccw':
            step = -step
        if isinstance(start, note):
            startind = self.outer.index(start.name)
        elif isinstance(start, str):
            startind = self.outer.index(start)
        else:
            startind = start
        return self[startind + step] if not inner else self[startind + step, ]

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
            note(self[ind, ][:-1], pitch), 'minor')

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


class piece:
    '''
    This class represents a piece which contains multiple tracks.
    '''

    def __init__(self,
                 tracks,
                 instruments=None,
                 bpm=120,
                 start_times=None,
                 track_names=None,
                 channels=None,
                 name=None,
                 pan=None,
                 volume=None,
                 other_messages=[],
                 daw_channels=None):
        self.tracks = tracks
        if instruments is None:
            self.instruments = [1 for i in range(len(self.tracks))]
        else:
            self.instruments = [
                database.INSTRUMENTS[i] if isinstance(i, str) else i
                for i in instruments
            ]
        self.bpm = bpm
        self.start_times = start_times
        if self.start_times is None:
            self.start_times = [0 for i in range(self.track_number)]
        self.track_names = track_names
        self.channels = channels
        self.name = name
        self.pan = pan
        self.volume = volume
        if not self.pan:
            self.pan = [[] for i in range(self.track_number)]
        if not self.volume:
            self.volume = [[] for i in range(self.track_number)]
        self.other_messages = other_messages
        self.daw_channels = daw_channels
        self.ticks_per_beat = None

    @property
    def track_number(self):
        return len(self.tracks)

    def __repr__(self):
        return self.show()

    def show(self, limit=10):
        result = (
            f'[piece] {self.name if self.name is not None else ""}\n'
        ) + f'BPM: {round(self.bpm, 3)}\n' + '\n'.join([
            f'track {i} | channel: {self.channels[i] if self.channels is not None else None} | track name: {self.track_names[i] if self.track_names is not None and self.track_names[i] is not None else None} | instrument: {database.reverse_instruments[self.instruments[i]]} | start time: {self.start_times[i]} | content: {self.tracks[i].show(limit=limit)}'
            for i in range(len(self.tracks))
        ])
        return result

    def __eq__(self, other):
        return type(other) is piece and self.__dict__ == other.__dict__

    def __iter__(self):
        for i in self.tracks:
            yield i

    def __getitem__(self, i):
        return track(
            content=self.tracks[i],
            instrument=self.instruments[i],
            start_time=self.start_times[i],
            channel=self.channels[i] if self.channels is not None else None,
            track_name=self.track_names[i]
            if self.track_names is not None else None,
            pan=self.pan[i],
            volume=self.volume[i],
            bpm=self.bpm,
            name=self.name,
            daw_channel=self.daw_channels[i]
            if self.daw_channels is not None else None)

    def __delitem__(self, i):
        del self.tracks[i]
        del self.instruments[i]
        del self.start_times[i]
        if self.track_names is not None:
            del self.track_names[i]
        if self.channels is not None:
            del self.channels[i]
        del self.pan[i]
        del self.volume[i]
        if self.daw_channels is not None:
            del self.daw_channels[i]

    def __setitem__(self, i, new_track):
        self.tracks[i] = new_track.content
        self.instruments[i] = new_track.instrument
        self.start_times[i] = new_track.start_time
        if self.track_names is not None and new_track.track_name is not None:
            self.track_names[i] = new_track.track_name
        if self.channels is not None and new_track.channel is not None:
            self.channels[i] = new_track.channel
        if new_track.pan is not None:
            self.pan[i] = new_track.pan
        if new_track.volume is not None:
            self.volume[i] = new_track.volume
        if self.daw_channels is not None and new_track.daw_channel is not None:
            self.daw_channels[i] = new_track.daw_channel

    def __len__(self):
        return len(self.tracks)

    def get_instrument_names(self):
        return [database.reverse_instruments[i] for i in self.instruments]

    def mute(self, i=None):
        if not hasattr(self, 'muted_msg'):
            self.muted_msg = [each.get_volume() for each in self.tracks]
        if i is None:
            for k in range(len(self.tracks)):
                self.tracks[k].set_volume(0)
        else:
            self.tracks[i].set_volume(0)

    def unmute(self, i=None):
        if not hasattr(self, 'muted_msg'):
            return
        if i is None:
            for k in range(len(self.tracks)):
                self.tracks[k].set_volume(self.muted_msg[k])
        else:
            self.tracks[i].set_volume(self.muted_msg[i])

    def update_msg(self):
        self.other_messages = mp.concat(
            [i.other_messages for i in self.tracks], start=[])

    def append(self, new_track):
        if not isinstance(new_track, track):
            raise ValueError('must be a track type to be appended')
        new_track = copy(new_track)
        self.tracks.append(new_track.content)
        self.instruments.append(new_track.instrument)
        self.start_times.append(new_track.start_time)
        if self.channels is not None:
            if new_track.channel is not None:
                self.channels.append(new_track.channel)
            else:
                self.channels.append(
                    max(self.channels) + 1 if self.channels else 0)
        if self.track_names is not None:
            if new_track.track_name is not None:
                self.track_names.append(new_track.track_name)
            else:
                self.track_names.append(
                    new_track.name if new_track.
                    name is not None else f'track {self.track_number}')
        self.pan.append(new_track.pan if new_track.pan is not None else [])
        self.volume.append(
            new_track.volume if new_track.volume is not None else [])
        if self.daw_channels is not None:
            if new_track.daw_channel is not None:
                self.daw_channels.append(new_track.daw_channel)
            else:
                self.daw_channels.append(0)
        self.tracks[-1].reset_track(len(self.tracks) - 1)
        self.update_msg()

    def insert(self, ind, new_track):
        if not isinstance(new_track, track):
            raise ValueError('must be a track type to be inserted')
        new_track = copy(new_track)
        self.tracks.insert(ind, new_track.content)
        self.instruments.insert(ind, new_track.instrument)
        self.start_times.insert(ind, new_track.start_time)
        if self.channels is not None:
            if new_track.channel is not None:
                self.channels.insert(ind, new_track.channel)
            else:
                self.channels.insert(
                    ind,
                    max(self.channels) + 1 if self.channels else 0)
        if self.track_names is not None:
            if new_track.track_name is not None:
                self.track_names.insert(ind, new_track.track_name)
            else:
                self.track_names.insert(
                    ind, new_track.name if new_track.name is not None else
                    f'track {self.track_number}')
        self.pan.insert(ind,
                        new_track.pan if new_track.pan is not None else [])
        self.volume.insert(
            ind, new_track.volume if new_track.volume is not None else [])
        if self.daw_channels is not None:
            if new_track.daw_channel is not None:
                self.daw_channels.insert(ind, new_track.daw_channel)
            else:
                self.daw_channels.insert(ind, 0)
        for k in range(ind, len(self.tracks)):
            self.tracks[k].reset_track(k)
        self.update_msg()

    def up(self, n=1, mode=0):
        temp = copy(self)
        for i in range(temp.track_number):
            if mode == 0 or (mode == 1 and not (temp.channels is not None
                                                and temp.channels[i] == 9)):
                temp.tracks[i] += n
        return temp

    def down(self, n=1, mode=0):
        temp = copy(self)
        for i in range(temp.track_number):
            if mode == 0 or (mode == 1 and not (temp.channels is not None
                                                and temp.channels[i] == 9)):
                temp.tracks[i] -= n
        return temp

    def __mul__(self, n):
        temp = copy(self)
        whole_length = temp.bars()
        for i in range(temp.track_number):
            current = temp.tracks[i]
            current.interval[-1] = current.notes[-1].duration
            current_start_time = temp.start_times[i]
            current.interval[-1] += (whole_length - current.bars() -
                                     current_start_time)
            unit = copy(current)
            for k in range(n - 1):
                if current_start_time:
                    current.interval[-1] += current_start_time
                extra = (k + 1) * whole_length
                for each in unit.tempos:
                    each.start_time += extra
                for each in unit.pitch_bends:
                    each.start_time += extra
                current.notes += unit.notes
                current.interval += unit.interval
            temp.tracks[i] = current
        return temp

    def __or__(self, n):
        if isinstance(n, piece):
            return self + n
        elif isinstance(n, (int, float)):
            return self.rest(n)

    def __and__(self, n):
        if isinstance(n, tuple):
            n, start_time = n
        else:
            start_time = 0
        return self.merge_track(n, mode='head', start_time=start_time)

    def __add__(self, n):
        if isinstance(n, (int, database.Interval)):
            return self.up(n)
        elif isinstance(n, piece):
            return self.merge_track(n, mode='after')
        elif isinstance(n, tuple):
            return self.up(*n)

    def __sub__(self, n):
        if isinstance(n, (int, database.Interval)):
            return self.down(n)
        elif isinstance(n, tuple):
            return self.down(*n)

    def __neg__(self):
        return self.down()

    def __pos__(self):
        return self.up()

    def __call__(self, ind):
        return self.tracks[ind]

    def merge_track(self,
                    n,
                    mode='after',
                    start_time=0,
                    ind_mode=0,
                    include_last_interval=False):
        temp = copy(self)
        temp2 = copy(n)
        if temp.channels is not None:
            free_channel_numbers = [
                i for i in range(16) if i not in temp.channels
            ]
            counter = 0
        if mode == 'after':
            start_time = temp.bars(mode=1 if not include_last_interval else 2)
        for i in range(len(temp2)):
            current_instrument_number = temp2.instruments[i]
            if current_instrument_number in temp.instruments:
                if ind_mode == 0:
                    current_ind = temp.instruments.index(
                        current_instrument_number)
                elif ind_mode == 1:
                    current_ind = i
                    if current_ind > len(temp.tracks) - 1:
                        temp.append(
                            track(content=chord([]), start_time=start_time))
                current_track = temp2.tracks[i]
                for each in current_track.tempos:
                    each.start_time += start_time
                for each in current_track.pitch_bends:
                    each.start_time += start_time
                current_start_time = temp2.start_times[
                    i] + start_time - temp.start_times[current_ind]
                temp.tracks[current_ind] = temp.tracks[current_ind].add(
                    current_track,
                    start=current_start_time,
                    mode='head',
                    adjust_msg=False)
                if current_start_time < 0:
                    temp.start_times[current_ind] += current_start_time
            else:
                temp.instruments.append(current_instrument_number)
                current_start_time = temp2.start_times[i]
                current_start_time += start_time
                current_track = temp2.tracks[i]
                for each in current_track.tempos:
                    each.start_time += start_time
                for each in current_track.pitch_bends:
                    each.start_time += start_time
                temp.tracks.append(current_track)
                temp.start_times.append(current_start_time)
                if temp.channels is not None:
                    if temp2.channels is not None:
                        current_channel_number = temp2.channels[i]
                        if current_channel_number in temp.channels:
                            current_channel_number = free_channel_numbers[
                                counter]
                            counter += 1
                        else:
                            if current_channel_number in free_channel_numbers:
                                del free_channel_numbers[
                                    free_channel_numbers.index(
                                        current_channel_number)]
                    else:
                        current_channel_number = free_channel_numbers[counter]
                        counter += 1
                    temp.channels.append(current_channel_number)
                if temp.track_names is not None:
                    temp.track_names.append(temp2.track_names[i])
        return temp

    def align(self, extra=0):
        temp = copy(self)
        track_lens = [
            temp.start_times[i] + temp.tracks[i].bars()
            for i in range(len(temp.tracks))
        ]
        for each in temp.tracks:
            each.interval[-1] = each.notes[-1].duration
        max_len = max(track_lens) + extra
        for i in range(len(temp.tracks)):
            extra_lens = max_len - track_lens[i]
            if extra_lens > 0:
                temp.tracks[i] |= extra_lens
        return temp

    def rest(self, n):
        return self.align(n)

    def add_pitch_bend(self,
                       value,
                       start_time,
                       channel='all',
                       track=0,
                       mode='cents'):
        if channel == 'all':
            for i in range(len(self.tracks)):
                current_channel = self.channels[
                    i] if self.channels is not None else i
                current_pitch_bend = pitch_bend(value=value,
                                                start_time=start_time,
                                                mode=mode,
                                                channel=current_channel,
                                                track=track)
                self.tracks[i].pitch_bends.append(current_pitch_bend)
        else:
            current_channel = self.channels[
                channel] if self.channels is not None else channel
            self.tracks[channel].pitch_bends.append(
                pitch_bend(value=value,
                           start_time=start_time,
                           mode=mode,
                           channel=current_channel,
                           track=track))

    def add_tempo_change(self, bpm, start_time, track_ind=0):
        self.tracks[track_ind].tempos.append(
            tempo(bpm=bpm, start_time=start_time))

    def clear_pitch_bend(self, ind='all', value='all', cond=None):
        if ind == 'all':
            for each in self.tracks:
                each.clear_pitch_bend(value, cond)
        else:
            self.tracks[ind].clear_pitch_bend(value, cond)

    def clear_tempo(self, ind='all', cond=None):
        if ind == 'all':
            for each in self.tracks:
                each.clear_tempo(cond)
        else:
            self.tracks[ind].clear_tempo(cond)

    def normalize_tempo(self, bpm=None, reset_bpm=False):
        if bpm is None:
            bpm = self.bpm
        if bpm == self.bpm and all(i.bpm == bpm for each in self.tracks
                                   for i in each.tempos):
            self.clear_tempo()
            return
        temp = copy(self)
        original_bpm = None
        if bpm != self.bpm and all(not each.tempos for each in self.tracks):
            original_bpm = self.bpm
        _piece_process_normalize_tempo(temp,
                                       bpm,
                                       min(temp.start_times),
                                       original_bpm=original_bpm)
        self.start_times = temp.start_times
        self.other_messages = temp.other_messages
        self.pan = temp.pan
        self.volume = temp.volume
        for i in range(len(self.tracks)):
            self.tracks[i] = temp.tracks[i]
        if reset_bpm:
            self.bpm = bpm

    def get_tempo_changes(self, ind=None):
        tempo_changes = [i.tempos for i in self.tracks
                         ] if ind is None else self.tracks[ind].tempos
        return tempo_changes

    def get_pitch_bend(self, ind=None):
        pitch_bend_changes = [
            i.pitch_bends for i in self.tracks
        ] if ind is None else self.tracks[ind].pitch_bends
        return pitch_bend_changes

    def get_msg(self, types, ind=None):
        if ind is None:
            return [i for i in self.other_messages if i.type == types]
        else:
            return [
                i for i in self.tracks[ind].other_messages if i.type == types
            ]

    def add_pan(self,
                value,
                ind,
                start_time=0,
                mode='percentage',
                channel=None,
                track=None):
        self.pan[ind].append(pan(value, start_time, mode, channel, track))

    def add_volume(self,
                   value,
                   ind,
                   start_time=0,
                   mode='percentage',
                   channel=None,
                   track=None):
        self.volume[ind].append(volume(value, start_time, mode, channel,
                                       track))

    def clear_pan(self, ind='all'):
        if ind == 'all':
            for each in self.pan:
                each.clear()
        else:
            self.pan[ind].clear()

    def clear_volume(self, ind='all'):
        if ind == 'all':
            for each in self.volume:
                each.clear()
        else:
            self.volume[ind].clear()

    def reassign_channels(self, start=0):
        new_channels_numbers = [start + i for i in range(len(self.tracks))]
        self.channels = new_channels_numbers

    def delete_track(self, current_ind, only_clear_msg=False):
        if not only_clear_msg:
            del self[current_ind]
        self.other_messages = [
            i for i in self.other_messages if i.track != current_ind
        ]
        for each in self.tracks:
            each.delete_track(current_ind)
        self.pan = [[i for i in each if i.track != current_ind]
                    for each in self.pan]
        for each in self.pan:
            for i in each:
                if i.track is not None and i.track > current_ind:
                    i.track -= 1
        self.volume = [[i for i in each if i.track != current_ind]
                       for each in self.volume]
        for each in self.volume:
            for i in each:
                if i.track is not None and i.track > current_ind:
                    i.track -= 1

    def delete_channel(self, current_ind):
        for each in self.tracks:
            each.delete_channel(current_ind)
        self.other_messages = [
            i for i in self.other_messages
            if not (hasattr(i, 'channel') and i.channel == current_ind)
        ]
        self.pan = [[i for i in each if i.channel != current_ind]
                    for each in self.pan]
        self.volume = [[i for i in each if i.channel != current_ind]
                       for each in self.volume]

    def get_off_drums(self):
        if self.channels is not None:
            while 9 in self.channels:
                current_ind = self.channels.index(9)
                self.delete_track(current_ind)
        self.delete_channel(9)

    def merge(self,
              add_labels=True,
              add_pan_volume=False,
              get_off_drums=False,
              track_names_add_channel=False):
        temp = copy(self)
        if add_labels:
            temp.add_track_labels()
        if get_off_drums:
            temp.get_off_drums()
        if track_names_add_channel and temp.channels is not None:
            for i, each in enumerate(temp.tracks):
                for j in each.other_messages:
                    if j.type == 'track_name':
                        j.channel = temp.channels[i]
        all_tracks = temp.tracks
        length = len(all_tracks)
        track_map_dict = {}
        if temp.channels is not None:
            merge_channels = list(dict.fromkeys(temp.channels))
            merge_length = len(merge_channels)
            if merge_length < length:
                for i in range(merge_length, length):
                    track_map_dict[i] = temp.channels.index(temp.channels[i])
        start_time_ls = temp.start_times
        sort_tracks_inds = [[i, start_time_ls[i]] for i in range(length)]
        sort_tracks_inds.sort(key=lambda s: s[1])
        first_track_start_time = sort_tracks_inds[0][1]
        first_track_ind = sort_tracks_inds[0][0]
        first_track = all_tracks[first_track_ind]
        for i in sort_tracks_inds[1:]:
            current_track = all_tracks[i[0]]
            current_start_time = i[1]
            current_shift = current_start_time - first_track_start_time
            first_track = first_track.add(current_track,
                                          start=current_shift,
                                          mode='head',
                                          adjust_msg=False)
        first_track.other_messages = temp.other_messages
        if add_pan_volume:
            whole_pan = mp.concat(temp.pan)
            whole_volume = mp.concat(temp.volume)
            pan_msg = [
                event('control_change',
                      channel=i.channel,
                      track=i.track,
                      start_time=i.start_time,
                      control=10,
                      value=i.value) for i in whole_pan
            ]
            volume_msg = [
                event('control_change',
                      channel=i.channel,
                      track=i.track,
                      start_time=i.start_time,
                      control=7,
                      value=i.value) for i in whole_volume
            ]
            first_track.other_messages += pan_msg
            first_track.other_messages += volume_msg
        first_track_start_time += first_track.start_time
        first_track.start_time = 0
        if track_map_dict:
            if add_labels:
                for i in first_track.notes:
                    if i.track_num in track_map_dict:
                        i.track_num = track_map_dict[i.track_num]
            for i in first_track.tempos:
                if i.track in track_map_dict:
                    current_track = track_map_dict[i.track]
                    i.track = current_track
                    if add_labels:
                        i.track_num = current_track
            for i in first_track.pitch_bends:
                if i.track in track_map_dict:
                    current_track = track_map_dict[i.track]
                    i.track = current_track
                    if add_labels:
                        i.track_num = current_track
            for i in first_track.other_messages:
                if i.track in track_map_dict:
                    i.track = track_map_dict[i.track]
        return first_track, temp.bpm, first_track_start_time

    def add_track_labels(self):
        all_tracks = self.tracks
        length = len(all_tracks)
        for k in range(length):
            current_track = all_tracks[k]
            for each in current_track.notes:
                each.track_num = k
            for each in current_track.tempos:
                each.track_num = k
            for each in current_track.pitch_bends:
                each.track_num = k

    def reconstruct(self,
                    track,
                    start_time=0,
                    offset=0,
                    correct=False,
                    include_empty_track=False,
                    get_channels=True):
        first_track, first_track_start_time = track, start_time
        length = len(self.tracks)
        start_times_inds = [[
            i for i in range(len(first_track))
            if first_track.notes[i].track_num == k
        ] for k in range(length)]
        if not include_empty_track:
            available_tracks_inds = [
                k for k in range(length) if start_times_inds[k]
            ]
        else:
            available_tracks_inds = [k for k in range(length)]
        available_tracks_messages = [
            self.tracks[i].other_messages for i in available_tracks_inds
        ]
        if not include_empty_track:
            start_times_inds = [i[0] for i in start_times_inds if i]
        else:
            empty_track_inds = [
                i for i in range(length) if not start_times_inds[i]
            ]
            start_times_inds = [i[0] if i else -1 for i in start_times_inds]
        new_start_times = [
            first_track_start_time +
            first_track[:k].bars(mode=0) if k != -1 else 0
            for k in start_times_inds
        ]
        if correct:
            new_start_times_offset = [
                self.start_times[i] - offset for i in available_tracks_inds
            ]
            start_time_offset = min([
                new_start_times_offset[k] - new_start_times[k]
                for k in range(len(new_start_times))
            ],
                                    key=lambda s: abs(s))
            new_start_times = [i + start_time_offset for i in new_start_times]
            if include_empty_track:
                new_start_times = [
                    new_start_times[i] if i not in empty_track_inds else 0
                    for i in range(length)
                ]
        new_start_times = [i if i >= 0 else 0 for i in new_start_times]
        new_track_notes = [[] for k in range(length)]
        new_track_inds = [[] for k in range(length)]
        new_track_tempos = [[] for k in range(length)]
        new_track_pitch_bends = [[] for k in range(length)]
        whole_length = len(first_track)
        for j in range(whole_length):
            current_note = first_track.notes[j]
            new_track_notes[current_note.track_num].append(current_note)
            new_track_inds[current_note.track_num].append(j)
        for i in first_track.tempos:
            new_track_tempos[i.track_num].append(i)
        for i in first_track.pitch_bends:
            new_track_pitch_bends[i.track_num].append(i)
        whole_interval = first_track.interval
        new_track_intervals = [[
            sum(whole_interval[inds[i]:inds[i + 1]])
            for i in range(len(inds) - 1)
        ] for inds in new_track_inds]
        for i in available_tracks_inds:
            if new_track_inds[i]:
                new_track_intervals[i].append(
                    sum(whole_interval[new_track_inds[i][-1]:]))
        new_tracks = []
        for i in range(len(available_tracks_inds)):
            current_track_ind = available_tracks_inds[i]
            current_track = chord(
                new_track_notes[current_track_ind],
                interval=new_track_intervals[current_track_ind],
                tempos=new_track_tempos[current_track_ind],
                pitch_bends=new_track_pitch_bends[current_track_ind],
                other_messages=available_tracks_messages[i])
            current_track.track_ind = current_track_ind
            current_track.interval = [
                int(i) if isinstance(i, float) and i.is_integer() else i
                for i in current_track.interval
            ]
            new_tracks.append(current_track)
        self.tracks = new_tracks
        self.start_times = [
            int(i) if isinstance(i, float) and i.is_integer() else i
            for i in new_start_times
        ]
        self.instruments = [self.instruments[k] for k in available_tracks_inds]
        if self.track_names is not None:
            self.track_names = [
                self.track_names[k] for k in available_tracks_inds
            ]
        if self.channels is not None:
            self.channels = [self.channels[k] for k in available_tracks_inds]
        else:
            if get_channels:
                from collections import Counter
                current_channels = [
                    Counter([i.channel for i in each
                             if i.channel is not None]).most_common(1)
                    for each in self.tracks
                ]
                if all(i for i in current_channels):
                    self.channels = [i[0][0] for i in current_channels]
        self.pan = [self.pan[k] for k in available_tracks_inds]
        self.volume = [self.volume[k] for k in available_tracks_inds]
        self.reset_track(list(range(self.track_number)))

    def eval_time(self,
                  bpm=None,
                  ind1=None,
                  ind2=None,
                  mode='seconds',
                  normalize_tempo=True,
                  audio_mode=0):
        merged_result, temp_bpm, start_time = self.merge()
        if bpm is not None:
            temp_bpm = bpm
        if normalize_tempo:
            merged_result.normalize_tempo(temp_bpm)
        return merged_result.eval_time(temp_bpm,
                                       ind1,
                                       ind2,
                                       mode,
                                       start_time=start_time,
                                       audio_mode=audio_mode)

    def cut(self,
            ind1=0,
            ind2=None,
            correct=False,
            cut_extra_duration=False,
            cut_extra_interval=False,
            round_duration=False,
            round_cut_interval=False):
        merged_result, temp_bpm, start_time = self.merge()
        if ind1 < 0:
            ind1 = 0
        result = merged_result.cut(ind1,
                                   ind2,
                                   start_time,
                                   cut_extra_duration=cut_extra_duration,
                                   cut_extra_interval=cut_extra_interval,
                                   round_duration=round_duration,
                                   round_cut_interval=round_cut_interval)
        offset = ind1
        temp = copy(self)
        start_time -= ind1
        if start_time < 0:
            start_time = 0
        temp.reconstruct(track=result,
                         start_time=start_time,
                         offset=offset,
                         correct=correct)
        if ind2 is None:
            ind2 = temp.bars()
        for each in temp.pan:
            for i in each:
                i.start_time -= ind1
                if i.start_time < 0:
                    i.start_time = 0
        for each in temp.volume:
            for i in each:
                i.start_time -= ind1
                if i.start_time < 0:
                    i.start_time = 0
        temp.pan = [[i for i in each if i.start_time < ind2]
                    for each in temp.pan]
        temp.volume = [[i for i in each if i.start_time < ind2]
                       for each in temp.volume]
        tempo_changes = mp.concat(temp.get_tempo_changes(), start=[])
        temp.clear_tempo()
        track_inds = [each.track_ind for each in temp.tracks]
        temp.other_messages = [
            i for i in temp.other_messages if ind1 <= i.start_time < ind2
        ]
        temp.other_messages = [
            i for i in temp.other_messages if i.track in track_inds
        ]
        for each in temp.other_messages:
            each.track = track_inds.index(each.track)
        temp.tracks[0].tempos.extend(tempo_changes)
        temp.reset_track([*range(len(temp.tracks))])
        return temp

    def cut_time(self,
                 time1=0,
                 time2=None,
                 bpm=None,
                 start_time=0,
                 cut_extra_duration=False,
                 cut_extra_interval=False,
                 round_duration=False,
                 round_cut_interval=False):
        temp = copy(self)
        temp.normalize_tempo()
        if bpm is not None:
            temp_bpm = bpm
        else:
            temp_bpm = temp.bpm
        bar_left = time1 / ((60 / temp_bpm) * 4)
        bar_right = time2 / (
            (60 / temp_bpm) * 4) if time2 is not None else temp.bars()
        result = temp.cut(bar_left,
                          bar_right,
                          cut_extra_duration=cut_extra_duration,
                          cut_extra_interval=cut_extra_interval,
                          round_duration=round_duration,
                          round_cut_interval=round_cut_interval)
        return result

    def get_bar(self, n):
        start_time = min(self.start_times)
        return self.cut(n + start_time, n + start_time)

    def firstnbars(self, n):
        start_time = min(self.start_times)
        return self.cut(start_time, n + start_time)

    def bars(self, mode=1, audio_mode=0, bpm=None):
        return max([
            self.tracks[i].bars(start_time=self.start_times[i],
                                mode=mode,
                                audio_mode=audio_mode,
                                bpm=bpm) for i in range(len(self.tracks))
        ])

    def total(self):
        return sum([len(i) for i in self.tracks])

    def count(self, note1, mode='name'):
        return sum([each.count(note1, mode) for each in self.tracks])

    def most_appear(self, choices=None, mode='name', as_standard=False):
        return self.quick_merge().most_appear(choices, mode, as_standard)

    def quick_merge(self):
        result = chord([])
        for each in self.tracks:
            result.notes += each.notes
            result.interval += each.interval
            result.other_messages += each.other_messages
            result.tempos += each.tempos
            result.pitch_bends += each.pitch_bends
        return result

    def standard_notation(self):
        temp = copy(self)
        temp.tracks = [each.standard_notation() for each in temp.tracks]
        return temp

    def count_appear(self, choices=None, as_standard=True, sort=False):
        return self.quick_merge().count_appear(choices, as_standard, sort)

    def apply_start_time_to_changes(self,
                                    start_time,
                                    msg=False,
                                    pan_volume=False):
        if isinstance(start_time, (int, float)):
            start_time = [start_time for i in range(len(self.tracks))]
        tracks = self.tracks
        for i in range(len(tracks)):
            current_start_time = start_time[i]
            current_track = tracks[i]
            for each in current_track.tempos:
                each.start_time += current_start_time
                if each.start_time < 0:
                    each.start_time = 0
            for each in current_track.pitch_bends:
                each.start_time += current_start_time
                if each.start_time < 0:
                    each.start_time = 0
            if msg:
                for each in current_track.other_messages:
                    each.start_time += current_start_time
                    if each.start_time < 0:
                        each.start_time = 0
            if pan_volume:
                current_pan = self.pan[i]
                current_volume = self.volume[i]
                for each in current_pan:
                    each.start_time += current_start_time
                    if each.start_time < 0:
                        each.start_time = 0
                for each in current_volume:
                    each.start_time += current_start_time
                    if each.start_time < 0:
                        each.start_time = 0

    def reverse(self):
        temp = copy(self)
        temp.tracks = [
            temp.tracks[i].reverse(start_time=temp.start_times[i])
            for i in range(len(temp.tracks))
        ]
        length = temp.bars()
        start_times = temp.start_times
        tracks = temp.tracks
        track_num = len(temp.tracks)
        first_start_time = min(self.start_times)
        temp.start_times = [
            length - (start_times[i] + tracks[i].bars() - first_start_time)
            for i in range(track_num)
        ]

        temp.apply_start_time_to_changes(temp.start_times)
        for each in temp.pan:
            for i in each:
                i.start_time = length - i.start_time
                if i.start_time < 0:
                    i.start_time = 0
        for each in temp.volume:
            for i in each:
                i.start_time = length - i.start_time
                if i.start_time < 0:
                    i.start_time = 0
        return temp

    def reverse_chord(self):
        temp = copy(self)
        temp.tracks = [
            temp.tracks[i].reverse_chord(start_time=temp.start_times[i])
            for i in range(len(temp.tracks))
        ]
        length = temp.bars()
        start_times = temp.start_times
        tracks = temp.tracks
        track_num = len(temp.tracks)
        first_start_time = min(self.start_times)
        temp.start_times = [
            length - (start_times[i] + tracks[i].bars() - first_start_time)
            for i in range(track_num)
        ]
        temp.apply_start_time_to_changes(temp.start_times)
        for each in temp.pan:
            for i in each:
                i.start_time = length - i.start_time
                if i.start_time < 0:
                    i.start_time = 0
        for each in temp.volume:
            for i in each:
                i.start_time = length - i.start_time
                if i.start_time < 0:
                    i.start_time = 0
        return temp

    def __invert__(self):
        return self.reverse()

    def clear_program_change(self, apply_tracks=True):
        if apply_tracks:
            for each in self.tracks:
                each.clear_program_change()
        self.other_messages = [
            i for i in self.other_messages if i.type != 'program_change'
        ]

    def clear_other_messages(self, types=None, apply_tracks=True, ind=None):
        if ind is None:
            if types is None:
                self.other_messages.clear()
            else:
                self.other_messages = [
                    i for i in self.other_messages if i.type != types
                ]
            if apply_tracks:
                for each in self.tracks:
                    each.clear_other_messages(types)
        else:
            if types is None:
                self.other_messages = [
                    i for i in self.other_messages if i.track != ind
                ]
            else:
                self.other_messages = [
                    i for i in self.other_messages
                    if not (i.track == ind and i.type == types)
                ]
            if apply_tracks:
                self.tracks[ind].clear_other_messages(types)

    def change_instruments(self, instruments, ind=None):
        if ind is None:
            if all(isinstance(i, int) for i in instruments):
                self.instruments = copy(instruments)
            elif all(isinstance(i, str) for i in instruments):
                self.instruments = [
                    database.INSTRUMENTS[i] for i in instruments
                ]
            elif any(
                    isinstance(i, list) and all(isinstance(j, int) for j in i)
                    for i in instruments):
                self.instruments = copy(instruments)
        else:
            if isinstance(instruments, int):
                self.instruments[ind] = instruments
            elif isinstance(instruments, str):
                self.instruments[ind] = database.INSTRUMENTS[instruments]
            elif isinstance(instruments, list) and all(
                    isinstance(j, int) for j in instruments):
                self.instruments[ind] = copy(instruments)

    def move(self, time=0, ind='all'):
        temp = copy(self)
        if ind == 'all':
            temp.start_times = [i + time for i in temp.start_times]
            temp.start_times = [0 if i < 0 else i for i in temp.start_times]
            temp.apply_start_time_to_changes(
                [time for i in range(len(temp.start_times))],
                msg=True,
                pan_volume=True)
        else:
            temp.start_times[ind] += time
            temp.tracks[ind].apply_start_time_to_changes(time, msg=True)
            for each in temp.pan[ind]:
                each.start_time += time
                if each.start_time < 0:
                    each.start_time = 0
            for each in temp.volume[ind]:
                each.start_time += time
                if each.start_time < 0:
                    each.start_time = 0
        return temp

    def modulation(self, old_scale, new_scale, mode=1, inds='all'):
        temp = copy(self)
        if inds == 'all':
            inds = list(range(len(temp)))
        for i in inds:
            if not (mode == 1 and temp.channels is not None
                    and temp.channels[i] == 9):
                temp.tracks[i] = temp.tracks[i].modulation(
                    old_scale, new_scale)
        return temp

    def apply(self, func, inds='all', mode=0, new=True):
        if new:
            temp = copy(self)
            if isinstance(inds, int):
                inds = [inds]
            elif inds == 'all':
                inds = list(range(len(temp)))
            if mode == 0:
                for i in inds:
                    temp.tracks[i] = func(temp.tracks[i])
            elif mode == 1:
                for i in inds:
                    func(temp.tracks[i])
            return temp
        else:
            if isinstance(inds, int):
                inds = [inds]
            elif inds == 'all':
                inds = list(range(len(self)))
            if mode == 0:
                for i in inds:
                    self.tracks[i] = func(self.tracks[i])
            elif mode == 1:
                for i in inds:
                    func(self.tracks[i])

    def reset_channel(self,
                      channels,
                      reset_msg=True,
                      reset_pitch_bend=True,
                      reset_pan_volume=True,
                      reset_note=True):
        if isinstance(channels, (int, float)):
            channels = [channels for i in range(len(self.tracks))]
        self.channels = channels
        for i in range(len(self.tracks)):
            current_channel = channels[i]
            current_track = self.tracks[i]
            if reset_msg:
                current_other_messages = current_track.other_messages
                for each in current_other_messages:
                    if hasattr(each, 'channel'):
                        each.channel = current_channel
            if reset_pitch_bend:
                for each in current_track.pitch_bends:
                    each.channel = current_channel
            if reset_note:
                for each in current_track.notes:
                    each.channel = current_channel
            if reset_pan_volume:
                current_pan = self.pan[i]
                current_volume = self.volume[i]
                for each in current_pan:
                    each.channel = current_channel
                for each in current_volume:
                    each.channel = current_channel

    def reset_track(self,
                    tracks,
                    reset_msg=True,
                    reset_pitch_bend=True,
                    reset_pan_volume=True):
        if isinstance(tracks, (int, float)):
            tracks = [tracks for i in range(len(self.tracks))]
        for i in range(len(self.tracks)):
            current_track_num = tracks[i]
            current_track = self.tracks[i]
            if reset_msg:
                current_other_messages = current_track.other_messages
                for each in current_other_messages:
                    each.track = current_track_num
            if reset_pitch_bend:
                for each in current_track.pitch_bends:
                    each.track = current_track_num
            if reset_pan_volume:
                current_pan = self.pan[i]
                current_volume = self.volume[i]
                for each in current_pan:
                    each.track = current_track_num
                for each in current_volume:
                    each.track = current_track_num


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


class track:
    '''
    This class represents a single track, which content is a chord instance, and has other attributes that define a track.
    '''

    def __init__(self,
                 content,
                 instrument=1,
                 start_time=0,
                 channel=None,
                 track_name=None,
                 pan=None,
                 volume=None,
                 bpm=120,
                 name=None,
                 daw_channel=None):
        self.content = content
        self.instrument = database.INSTRUMENTS[instrument] if isinstance(
            instrument, str) else instrument
        self.bpm = bpm
        self.start_time = start_time
        self.track_name = track_name
        self.channel = channel
        self.name = name
        self.pan = pan
        self.volume = volume
        self.daw_channel = daw_channel
        if self.pan:
            if not isinstance(self.pan, list):
                self.pan = [self.pan]
        else:
            self.pan = []
        if self.volume:
            if not isinstance(self.volume, list):
                self.volume = [self.volume]
        else:
            self.volume = []

    def __repr__(self):
        return self.show()

    def show(self, limit=10):
        return (f'[track] {self.name if self.name is not None else ""}\n') + (
            f'BPM: {round(self.bpm, 3)}\n' if self.bpm is not None else ""
        ) + f'channel: {self.channel} | track name: {self.track_name} | instrument: {database.reverse_instruments[self.instrument]} | start time: {self.start_time} | content: {self.content.show(limit=limit)}'

    def get_instrument_name(self):
        return database.reverse_instruments[self.instrument]

    def add_pan(self,
                value,
                start_time=0,
                mode='percentage',
                channel=None,
                track=None):
        self.pan.append(pan(value, start_time, mode, channel, track))

    def add_volume(self,
                   value,
                   start_time=0,
                   mode='percentage',
                   channel=None,
                   track=None):
        self.volume.append(volume(value, start_time, mode, channel, track))

    def get_interval(self):
        return self.content.interval

    def get_duration(self):
        return self.content.get_duration()

    def get_volume(self):
        return self.content.get_volume()

    def reverse(self, *args, **kwargs):
        temp = copy(self)
        temp.content = temp.content.reverse(*args, **kwargs)
        length = temp.bars()
        for each in temp.pan:
            for i in each:
                i.start_time = length - i.start_time
                if i.start_time < 0:
                    i.start_time = 0
        for each in temp.volume:
            for i in each:
                i.start_time = length - i.start_time
                if i.start_time < 0:
                    i.start_time = 0
        return temp

    def reverse_chord(self, *args, **kwargs):
        temp = copy(self)
        temp.content = temp.content.reverse_chord(*args, **kwargs)
        length = temp.bars()
        for each in temp.pan:
            for i in each:
                i.start_time = length - i.start_time
                if i.start_time < 0:
                    i.start_time = 0
        for each in temp.volume:
            for i in each:
                i.start_time = length - i.start_time
                if i.start_time < 0:
                    i.start_time = 0
        return temp

    def __invert__(self):
        return self.reverse()

    def up(self, n=1):
        temp = copy(self)
        temp.content += n
        return temp

    def down(self, n=1):
        temp = copy(self)
        temp.content -= n
        return temp

    def __mul__(self, n):
        temp = copy(self)
        temp.content *= n
        return temp

    def __pos__(self):
        return self.up()

    def __neg__(self):
        return self.down()

    def __add__(self, i):
        if isinstance(i, (int, database.Interval)):
            return self.up(i)
        else:
            temp = copy(self)
            temp.content += i
            return temp

    def __sub__(self, i):
        if isinstance(i, (int, database.Interval)):
            return self.down(i)

    def __or__(self, i):
        temp = copy(self)
        temp.content |= i
        return temp

    def __and__(self, i):
        temp = copy(self)
        temp.content &= i
        return temp

    def set(self, duration=None, interval=None, volume=None, ind='all'):
        temp = copy(self)
        temp.content = temp.content.set(duration, interval, volume, ind)
        return temp

    def __getitem__(self, i):
        return self.content[i]

    def __setitem__(self, i, value):
        self.content[i] = value

    def __delitem__(self, i):
        del self.content[i]

    def __len__(self):
        return len(self.content)

    def delete_track(self, current_ind):
        self.content.delete_track(current_ind)
        if self.pan:
            self.pan = [i for i in self.pan if i.track != current_ind]
            for i in self.pan:
                if i.track is not None and i.track > current_ind:
                    i.track -= 1
        if self.volume:
            self.volume = [i for i in self.volume if i.track != current_ind]
            for i in self.volume:
                if i.track is not None and i.track > current_ind:
                    i.track -= 1

    def delete_channel(self, current_ind):
        self.content.delete_channel(current_ind)
        self.pan = [i for i in self.pan if i.channel != current_ind]
        self.volume = [i for i in self.volume if i.channel != current_ind]


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


class drum:
    '''
    This class represents a drum beat.
    '''

    def __init__(self,
                 pattern='',
                 mapping=database.drum_mapping,
                 name=None,
                 notes=None,
                 i=1,
                 start_time=None,
                 default_duration=1 / 8,
                 default_interval=1 / 8,
                 default_volume=100,
                 translate_mode=0):
        self.pattern = pattern
        self.mapping = mapping
        self.name = name
        self.default_duration = default_duration
        self.default_interval = default_interval
        self.default_volume = default_volume
        self.translate_mode = translate_mode
        self.last_non_num_note = None
        self.notes = self.translate(
            self.pattern,
            self.mapping,
            default_duration=self.default_duration,
            default_interval=self.default_interval,
            default_volume=self.default_volume,
            translate_mode=self.translate_mode) if not notes else notes
        if start_time is not None:
            self.notes.start_time = start_time
        self.instrument = i if isinstance(
            i, int) else (database.drum_set_dict_reverse[i]
                          if i in database.drum_set_dict_reverse else 1)

    def __repr__(self):
        return f"[drum] {self.name if self.name is not None else ''}\n{self.notes}"

    def translate(self,
                  pattern,
                  mapping,
                  default_duration=1 / 8,
                  default_interval=1 / 8,
                  default_volume=100,
                  translate_mode=0):
        current_rest_symbol = '0'
        current_continue_symbol = '-'
        self.last_non_num_note = None
        if -1 in mapping.values():
            current_rest_symbol = [i for i, j in mapping.items() if j == -1][0]
        if -2 in mapping.values():
            current_continue_symbol = [
                i for i, j in mapping.items() if j == -2
            ][0]
        start_time = 0
        current_has_keyword = False
        whole_parts = []
        whole_keywords = []
        current_keyword = []
        current_part = []
        global_keywords = []
        pattern = pattern.replace(' ', '').replace('\n', '')
        whole_units = [each.split(',') for each in pattern.split('|')]
        repeat_times = 1
        whole_set = False
        for units in whole_units:
            current_has_keyword = False
            for each in units:
                if ':' in each and each[:each.
                                        index(':')] in database.drum_keywords:
                    current_keyword.append(each)
                    if not current_has_keyword:
                        current_has_keyword = True
                        whole_parts.append(current_part)
                        current_part = []
                elif each.startswith('!'):
                    global_keywords.append(each)
                else:
                    current_part.append(each)
                    if current_has_keyword:
                        current_has_keyword = False
                        whole_keywords.append(current_keyword)
                        current_keyword = []
            if not current_has_keyword:
                whole_parts.append(current_part)
                current_part = []
                whole_keywords.append([])
            else:
                whole_keywords.append(current_keyword)
                current_keyword = []
        notes = []
        durations = []
        intervals = []
        volumes = []
        name_dict = {}

        global_default_duration, global_default_interval, global_default_volume, global_repeat_times, global_all_same_duration, global_all_same_interval, global_all_same_volume, global_fix_length, global_fix_beats = self._translate_global_keyword_parser(
            global_keywords)

        for i in range(len(whole_parts)):
            current_part = whole_parts[i]
            current_keyword = whole_keywords[i]
            current_notes = []
            current_durations = []
            current_intervals = []
            current_volumes = []
            current_custom_durations = []
            current_same_times = []
            if current_part:
                current_part_default_duration, current_part_default_interval, current_part_default_volume, current_part_repeat_times, current_part_all_same_duration, current_part_all_same_interval, current_part_all_same_volume, current_part_fix_length, current_part_name, current_part_fix_beats = self._translate_keyword_parser(
                    current_keyword,
                    default_duration if global_default_duration is None else
                    global_default_duration,
                    default_interval if global_default_interval is None else
                    global_default_interval, default_volume if
                    global_default_volume is None else global_default_volume,
                    global_all_same_duration, global_all_same_interval,
                    global_all_same_volume, global_fix_length,
                    global_fix_beats)
                current_part_fix_length_unit = None
                if current_part_fix_length is not None:
                    if current_part_fix_beats is not None:
                        current_part_fix_length_unit = current_part_fix_length / current_part_fix_beats
                    else:
                        current_part_fix_length_unit = current_part_fix_length / self._get_length(
                            current_part)
                for each in current_part:
                    if each.startswith('i:'):
                        current_extra_interval = _process_note(each[2:])
                        if current_intervals:
                            current_intervals[-1][-1] += current_extra_interval
                        else:
                            if intervals:
                                intervals[-1] += current_extra_interval
                            else:
                                start_time = current_extra_interval
                        continue
                    elif each.startswith('u:'):
                        content = each[2:]
                        if content in name_dict:
                            current_append_notes, current_append_durations, current_append_intervals, current_append_volumes = name_dict[
                                content]
                        else:
                            continue
                    elif '[' in each and ']' in each:
                        current_append_notes, current_append_durations, current_append_intervals, current_append_volumes, current_custom_duration, current_same_time = self._translate_setting_parser(
                            each, mapping, current_part_default_duration,
                            current_part_default_interval,
                            current_part_default_volume, current_rest_symbol,
                            current_continue_symbol,
                            current_part_fix_length_unit, translate_mode)
                    else:
                        current_append_notes, current_append_durations, current_append_intervals, current_append_volumes = self._translate_normal_notes_parser(
                            each, mapping, current_part_default_duration,
                            current_part_default_interval,
                            current_part_default_volume, current_rest_symbol,
                            current_continue_symbol,
                            current_part_fix_length_unit, translate_mode)
                        current_custom_duration = False
                        current_same_time = True
                    current_notes.append(current_append_notes)
                    current_durations.append(current_append_durations)
                    current_intervals.append(current_append_intervals)
                    current_volumes.append(current_append_volumes)
                    current_custom_durations.append(current_custom_duration)
                    current_same_times.append(current_same_time)
                if current_part_all_same_duration is not None:
                    current_durations = [[
                        current_part_all_same_duration for k in each_part
                    ] for each_part in current_durations]
                if current_part_all_same_interval is not None:
                    current_intervals = [
                        [current_part_all_same_interval for k in each_part]
                        if not (len(each_part) > 1 and current_same_times[j])
                        else each_part[:-1] + [current_part_all_same_interval]
                        for j, each_part in enumerate(current_intervals)
                    ]
                if current_part_all_same_volume is not None:
                    current_volumes = [[
                        current_part_all_same_volume for k in each_part
                    ] for each_part in current_volumes]
                current_notes, current_durations, current_intervals, current_volumes = self._split_symbol(
                    [
                        current_notes, current_durations, current_intervals,
                        current_volumes
                    ])

                symbol_inds = [
                    j for j, each_note in enumerate(current_notes)
                    if each_note and isinstance(each_note[0], (
                        rest_symbol, continue_symbol))
                ]
                current_part_start_time = 0
                if symbol_inds:
                    last_symbol_ind = None
                    last_symbol_start_ind = None
                    available_symbol_ind = len(symbol_inds)
                    if symbol_inds[0] == 0:
                        for k in range(1, len(symbol_inds)):
                            if symbol_inds[k] - symbol_inds[k - 1] != 1:
                                available_symbol_ind = k
                                break
                        for ind in symbol_inds[:available_symbol_ind]:
                            current_symbol = current_notes[ind][0]
                            if isinstance(current_symbol, rest_symbol):
                                current_symbol_interval = current_intervals[
                                    ind][0]
                                current_part_start_time += current_symbol_interval
                                if i == 0:
                                    start_time += current_symbol_interval
                                else:
                                    if intervals:
                                        intervals[
                                            -1] += current_symbol_interval
                                    else:
                                        start_time += current_symbol_interval
                    else:
                        available_symbol_ind = 0
                    for ind in symbol_inds[available_symbol_ind:]:
                        if last_symbol_ind is None:
                            last_symbol_ind = ind
                            last_symbol_start_ind = ind - 1
                        else:
                            if any(not isinstance(j[0], (rest_symbol,
                                                         continue_symbol))
                                   for j in current_notes[last_symbol_ind +
                                                          1:ind]):
                                last_symbol_ind = ind
                                last_symbol_start_ind = ind - 1
                        current_symbol = current_notes[ind][0]
                        current_symbol_interval = current_intervals[ind][0]
                        current_symbol_duration = current_durations[ind][0]
                        if isinstance(current_symbol, rest_symbol):
                            last_symbol_interval = current_intervals[
                                last_symbol_start_ind]
                            last_symbol_interval[-1] += current_symbol_interval
                        elif isinstance(current_symbol, continue_symbol):
                            last_symbol_interval = current_intervals[
                                last_symbol_start_ind]
                            last_symbol_duration = current_durations[
                                last_symbol_start_ind]
                            last_symbol_interval[-1] += current_symbol_interval
                            if current_symbol.mode is None:
                                if all(k == 0
                                       for k in last_symbol_interval[:-1]):
                                    for j in range(len(last_symbol_duration)):
                                        last_symbol_duration[
                                            j] += current_symbol_duration
                                else:
                                    last_symbol_duration[
                                        -1] += current_symbol_duration
                            elif current_symbol.mode == 0:
                                last_symbol_duration[
                                    -1] += current_symbol_duration
                            elif current_symbol.mode == 1:
                                for j in range(len(last_symbol_duration)):
                                    last_symbol_duration[
                                        j] += current_symbol_duration
                    current_length = len(current_notes)
                    current_notes = [
                        current_notes[j] for j in range(current_length)
                        if j not in symbol_inds
                    ]
                    current_durations = [
                        current_durations[j] for j in range(current_length)
                        if j not in symbol_inds
                    ]
                    current_intervals = [
                        current_intervals[j] for j in range(current_length)
                        if j not in symbol_inds
                    ]
                    current_volumes = [
                        current_volumes[j] for j in range(current_length)
                        if j not in symbol_inds
                    ]
                current_notes = [j for k in current_notes for j in k]
                current_durations = [j for k in current_durations for j in k]
                current_intervals = [j for k in current_intervals for j in k]
                current_volumes = [j for k in current_volumes for j in k]
                if current_part_repeat_times > 1:
                    current_notes = copy_list(current_notes,
                                              current_part_repeat_times)
                    current_durations = copy_list(current_durations,
                                                  current_part_repeat_times)
                    current_intervals = copy_list(
                        current_intervals,
                        current_part_repeat_times,
                        start_time=current_part_start_time)
                    current_volumes = copy_list(current_volumes,
                                                current_part_repeat_times)
                if current_part_name:
                    name_dict[current_part_name] = [
                        current_notes, current_durations, current_intervals,
                        current_volumes
                    ]
            notes.extend(current_notes)
            durations.extend(current_durations)
            intervals.extend(current_intervals)
            volumes.extend(current_volumes)
        if global_repeat_times > 1:
            notes = copy_list(notes, global_repeat_times)
            durations = copy_list(durations, global_repeat_times)
            intervals = copy_list(intervals,
                                  global_repeat_times,
                                  start_time=start_time)
            volumes = copy_list(volumes, global_repeat_times)
        result = chord(notes) % (durations, intervals, volumes)
        result.start_time = start_time
        return result

    def _split_symbol(self, current_list):
        current_notes = current_list[0]
        return_list = [[] for i in range(len(current_list))]
        for k, each_note in enumerate(current_notes):
            if len(each_note) > 1 and any(
                    isinstance(j, (rest_symbol, continue_symbol))
                    for j in each_note):
                current_return_list = [[] for j in range(len(return_list))]
                current_ind = [
                    k1 for k1, k2 in enumerate(each_note)
                    if isinstance(k2, (rest_symbol, continue_symbol))
                ]
                start_part = [
                    each[k][:current_ind[0]] for each in current_list
                ]
                if start_part[0]:
                    for i, each in enumerate(current_return_list):
                        each.append(start_part[i])
                for j in range(len(current_ind) - 1):
                    current_symbol_part = [[each[k][current_ind[j]]]
                                           for each in current_list]
                    for i, each in enumerate(current_return_list):
                        each.append(current_symbol_part[i])
                    middle_part = [
                        each[k][current_ind[j] + 1:current_ind[j + 1]]
                        for each in current_list
                    ]
                    if middle_part[0]:
                        for i, each in enumerate(current_return_list):
                            each.append(middle_part[i])
                current_symbol_part = [[each[k][current_ind[-1]]]
                                       for each in current_list]
                for i, each in enumerate(current_return_list):
                    each.append(current_symbol_part[i])
                end_part = [
                    each[k][current_ind[-1] + 1:] for each in current_list
                ]
                if end_part[0]:
                    for i, each in enumerate(current_return_list):
                        each.append(end_part[i])
                for i, each in enumerate(return_list):
                    each.extend(current_return_list[i])
            else:
                for i, each in enumerate(return_list):
                    each.append(current_list[i][k])
        return return_list

    def _translate_setting_parser(self, each, mapping, default_duration,
                                  default_interval, default_volume,
                                  current_rest_symbol, current_continue_symbol,
                                  current_part_fix_length_unit,
                                  translate_mode):
        left_bracket_inds = [k for k in range(len(each)) if each[k] == '[']
        right_bracket_inds = [k for k in range(len(each)) if each[k] == ']']
        current_brackets = [
            each[left_bracket_inds[k] + 1:right_bracket_inds[k]]
            for k in range(len(left_bracket_inds))
        ]
        current_append_notes = each[:left_bracket_inds[0]]
        if ';' in current_append_notes:
            current_append_notes = current_append_notes.split(';')
        else:
            current_append_notes = [current_append_notes]
        current_same_time = True
        current_chord_same_time = True
        current_repeat_times = 1
        current_after_repeat_times = 1
        current_fix_length = None
        current_fix_beats = None
        current_inner_fix_beats = 1
        current_append_durations = [
            self._apply_dotted_notes(default_duration, self._get_dotted(i))
            for i in current_append_notes
        ]
        current_append_intervals = [
            self._apply_dotted_notes(default_interval, self._get_dotted(i))
            for i in current_append_notes
        ]
        current_append_volumes = [default_volume for i in current_append_notes]
        if translate_mode == 0:
            current_append_notes = [
                self._convert_to_note(each_note, mapping) if all(
                    not each_note.startswith(j)
                    for j in [current_rest_symbol, current_continue_symbol])
                else self._convert_to_symbol(each_note, current_rest_symbol,
                                             current_continue_symbol)
                for each_note in current_append_notes
            ]
        else:
            new_current_append_notes = []
            for each_note in current_append_notes:
                if ':' not in each_note:
                    if all(not each_note.startswith(j) for j in
                           [current_rest_symbol, current_continue_symbol]):
                        current_each_note = self._convert_to_note(each_note,
                                                                  mode=1)
                        new_current_append_notes.append(current_each_note)
                    else:
                        new_current_append_notes.append(
                            self._convert_to_symbol(each_note,
                                                    current_rest_symbol,
                                                    current_continue_symbol))
                else:
                    current_note, current_chord_type = each_note.split(":")
                    if current_note not in [
                            current_rest_symbol, current_continue_symbol
                    ]:
                        current_note = self._convert_to_note(current_note,
                                                             mode=1)
                        current_each_note = mp.C(
                            f'{current_note.name}{current_chord_type}',
                            current_note.num)
                        for i in current_each_note:
                            i.dotted_num = current_note.dotted_num
                        new_current_append_notes.append(current_each_note)
                        self.last_non_num_note = current_each_note.notes[-1]
            current_append_notes = new_current_append_notes
        custom_durations = False
        for j in current_brackets:
            current_bracket_settings = [k.split(':') for k in j.split(';')]
            if all(len(k) == 1 for k in current_bracket_settings):
                current_settings = _process_settings(
                    [k[0] for k in current_bracket_settings])
                current_append_durations, current_append_intervals, current_append_volumes = current_settings
                if current_append_durations is None:
                    current_append_durations = default_duration
                if not isinstance(current_append_durations, list):
                    current_append_durations = [
                        current_append_durations for k in current_append_notes
                    ]
                    custom_durations = True
                if current_append_intervals is None:
                    current_append_intervals = default_interval
                if not isinstance(current_append_intervals, list):
                    current_append_intervals = [
                        current_append_intervals for k in current_append_notes
                    ]
                if current_append_volumes is None:
                    current_append_volumes = default_volume
                if not isinstance(current_append_volumes, list):
                    current_append_volumes = [
                        current_append_volumes for k in current_append_notes
                    ]
            else:
                for each_setting in current_bracket_settings:
                    if len(each_setting) != 2:
                        continue
                    current_setting_keyword, current_content = each_setting
                    if current_setting_keyword == 's':
                        if current_content == 'F':
                            current_same_time = False
                        elif current_content == 'T':
                            current_same_time = True
                    if current_setting_keyword == 'cs':
                        if current_content == 'F':
                            current_chord_same_time = False
                        elif current_content == 'T':
                            current_chord_same_time = True
                    elif current_setting_keyword == 'r':
                        current_repeat_times = int(current_content)
                    elif current_setting_keyword == 'R':
                        current_after_repeat_times = int(current_content)
                    elif current_setting_keyword == 't':
                        current_fix_length = _process_note(current_content)
                    elif current_setting_keyword == 'b':
                        current_fix_beats = _process_note(current_content)
                    elif current_setting_keyword == 'B':
                        current_inner_fix_beats = _process_note(
                            current_content)
                    elif current_setting_keyword == 'i':
                        if current_content == '.':
                            current_append_intervals = _process_note(
                                current_content,
                                mode=1,
                                value2=current_append_durations)
                        else:
                            current_append_intervals = _process_note(
                                current_content)
                        if current_append_intervals is None:
                            current_append_intervals = default_interval
                        if not isinstance(current_append_intervals, list):
                            current_append_intervals = [
                                current_append_intervals
                                for k in current_append_notes
                            ]
                    elif current_setting_keyword == 'l':
                        current_append_durations = _process_note(
                            current_content)
                        if current_append_durations is None:
                            current_append_durations = default_duration
                        if not isinstance(current_append_durations, list):
                            current_append_durations = [
                                current_append_durations
                                for k in current_append_notes
                            ]
                            custom_durations = True
                    elif current_setting_keyword == 'v':
                        current_append_volumes = _process_note(current_content,
                                                               mode=2)
                        if current_append_volumes is None:
                            current_append_volumes = default_volume
                        if not isinstance(current_append_volumes, list):
                            current_append_volumes = [
                                current_append_volumes
                                for k in current_append_notes
                            ]
                    elif current_setting_keyword == 'cm':
                        if len(current_append_notes) == 1 and isinstance(
                                current_append_notes[0], continue_symbol):
                            current_append_notes[0].mode = int(current_content)
        current_fix_length_unit = None
        if current_fix_length is not None:
            if current_same_time:
                current_fix_length_unit = current_fix_length / (
                    current_repeat_times * current_inner_fix_beats)
            else:
                current_fix_length_unit = current_fix_length / (
                    self._get_length(current_append_notes) *
                    current_repeat_times * current_inner_fix_beats)
            if current_fix_beats is not None:
                current_fix_length_unit *= current_fix_beats
        elif current_part_fix_length_unit is not None:
            if current_same_time:
                current_fix_length_unit = current_part_fix_length_unit / current_repeat_times
            else:
                current_fix_length_unit = current_part_fix_length_unit / (
                    self._get_length(current_append_notes) *
                    current_repeat_times)
            if current_fix_beats is not None:
                current_fix_length_unit *= current_fix_beats
        if current_same_time:
            current_append_intervals = [
                0 for k in range(len(current_append_notes) - 1)
            ] + [current_append_intervals[-1]]
        if current_fix_length_unit is not None:
            if current_same_time:
                current_append_intervals = [
                    0 for k in range(len(current_append_notes) - 1)
                ] + [
                    self._apply_dotted_notes(
                        current_fix_length_unit,
                        current_append_notes[-1].dotted_num)
                ]
            else:
                current_append_intervals = [
                    self._apply_dotted_notes(current_fix_length_unit,
                                             k.dotted_num)
                    for k in current_append_notes
                ]
            if not custom_durations:
                current_append_durations = [
                    self._apply_dotted_notes(current_fix_length_unit,
                                             k.dotted_num)
                    for k in current_append_notes
                ]
        if current_repeat_times > 1:
            current_append_notes = copy_list(current_append_notes,
                                             current_repeat_times)
            current_append_durations = copy_list(current_append_durations,
                                                 current_repeat_times)
            current_append_intervals = copy_list(current_append_intervals,
                                                 current_repeat_times)
            current_append_volumes = copy_list(current_append_volumes,
                                               current_repeat_times)

        if current_after_repeat_times > 1:
            current_append_notes = copy_list(current_append_notes,
                                             current_after_repeat_times)
            current_append_durations = copy_list(current_append_durations,
                                                 current_after_repeat_times)
            current_append_intervals = copy_list(current_append_intervals,
                                                 current_after_repeat_times)
            current_append_volumes = copy_list(current_append_volumes,
                                               current_after_repeat_times)

        if translate_mode == 1:
            new_current_append_durations = []
            new_current_append_intervals = []
            new_current_append_volumes = []
            new_current_append_notes = []
            for i, each in enumerate(current_append_notes):
                if isinstance(each, chord):
                    if not current_chord_same_time:
                        current_duration = [
                            current_append_durations[i] / len(each)
                            for k in each.notes
                        ]
                        current_interval = [
                            current_append_intervals[i] / len(each)
                            for k in each.notes
                        ]
                    else:
                        current_duration = [
                            current_append_intervals[i] for k in each.notes
                        ]
                        current_interval = [0 for j in range(len(each) - 1)
                                            ] + [current_append_intervals[i]]
                    new_current_append_durations.extend(current_duration)
                    new_current_append_intervals.extend(current_interval)
                    new_current_append_volumes.extend(
                        [current_append_volumes[i] for k in each.notes])
                    new_current_append_notes.extend(each.notes)
                else:
                    new_current_append_durations.append(
                        current_append_durations[i])
                    new_current_append_intervals.append(
                        current_append_intervals[i])
                    new_current_append_volumes.append(
                        current_append_volumes[i])
                    new_current_append_notes.append(each)
            current_append_durations = new_current_append_durations
            current_append_intervals = new_current_append_intervals
            current_append_volumes = new_current_append_volumes
            current_append_notes = new_current_append_notes
        return current_append_notes, current_append_durations, current_append_intervals, current_append_volumes, custom_durations, current_same_time

    def _translate_normal_notes_parser(self, each, mapping, default_duration,
                                       default_interval, default_volume,
                                       current_rest_symbol,
                                       current_continue_symbol,
                                       current_part_fix_length_unit,
                                       translate_mode):
        current_append_notes = each
        if ';' in current_append_notes:
            current_append_notes = current_append_notes.split(';')
        else:
            current_append_notes = [current_append_notes]
        current_append_notes = [i for i in current_append_notes if i]
        if translate_mode == 0:
            current_append_notes = [
                self._convert_to_note(each_note, mapping) if all(
                    not each_note.startswith(j)
                    for j in [current_rest_symbol, current_continue_symbol])
                else self._convert_to_symbol(each_note, current_rest_symbol,
                                             current_continue_symbol)
                for each_note in current_append_notes
            ]
        else:
            new_current_append_notes = []
            for each_note in current_append_notes:
                if ':' not in each_note:
                    if all(not each_note.startswith(j) for j in
                           [current_rest_symbol, current_continue_symbol]):
                        current_each_note = self._convert_to_note(each_note,
                                                                  mode=1)
                        new_current_append_notes.append(current_each_note)
                    else:
                        new_current_append_notes.append(
                            self._convert_to_symbol(each_note,
                                                    current_rest_symbol,
                                                    current_continue_symbol))
                else:
                    current_note, current_chord_type = each_note.split(":")
                    if current_note not in [
                            current_rest_symbol, current_continue_symbol
                    ]:
                        current_note = self._convert_to_note(current_note,
                                                             mode=1)
                        current_each_note = mp.C(
                            f'{current_note.name}{current_chord_type}',
                            current_note.num)
                        for i in current_each_note:
                            i.dotted_num = current_note.dotted_num
                        new_current_append_notes.extend(
                            current_each_note.notes)
                        self.last_non_num_note = current_each_note.notes[-1]
            current_append_notes = new_current_append_notes

        current_append_durations = [
            self._apply_dotted_notes(default_duration, k.dotted_num)
            if not current_part_fix_length_unit else self._apply_dotted_notes(
                current_part_fix_length_unit, k.dotted_num)
            for k in current_append_notes
        ]
        current_append_intervals = [
            self._apply_dotted_notes(default_interval, k.dotted_num)
            if not current_part_fix_length_unit else self._apply_dotted_notes(
                current_part_fix_length_unit, k.dotted_num)
            for k in current_append_notes
        ]
        current_append_volumes = [default_volume for k in current_append_notes]
        if len(current_append_notes) > 1:
            current_append_intervals = [
                0 for i in range(len(current_append_intervals) - 1)
            ] + [current_append_intervals[-1]]
        return current_append_notes, current_append_durations, current_append_intervals, current_append_volumes

    def _translate_keyword_parser(self, current_keyword, default_duration,
                                  default_interval, default_volume,
                                  default_all_same_duration,
                                  default_all_same_interval,
                                  default_all_same_volume, default_fix_length,
                                  default_fix_beats):
        current_part_default_duration = default_duration
        current_part_default_interval = default_interval
        current_part_default_volume = default_volume
        current_part_repeat_times = 1
        current_part_all_same_duration = default_all_same_duration
        current_part_all_same_interval = default_all_same_interval
        current_part_all_same_volume = default_all_same_volume
        current_part_fix_length = default_fix_length
        current_part_fix_beats = default_fix_beats
        current_part_name = None
        for each in current_keyword:
            keyword, content = each.split(':')
            if keyword == 't':
                current_part_fix_length = _process_note(content)
            elif keyword == 'b':
                current_part_fix_beats = _process_note(content)
            elif keyword == 'r':
                current_part_repeat_times = int(content)
            elif keyword == 'n':
                current_part_name = content
            elif keyword == 'd':
                current_part_default_duration, current_part_default_interval, current_part_default_volume = _process_settings(
                    content.split(';'))
                if current_part_default_duration is None:
                    current_part_default_duration = self.default_duration
                if current_part_default_interval is None:
                    current_part_default_interval = self.default_interval
                if current_part_default_volume is None:
                    current_part_default_volume = self.default_volume
            elif keyword == 'a':
                current_part_all_same_duration, current_part_all_same_interval, current_part_all_same_volume = _process_settings(
                    content.split(';'))
            elif keyword == 'dl':
                current_part_default_duration = _process_note(content)
            elif keyword == 'di':
                current_part_default_interval = _process_note(content)
            elif keyword == 'dv':
                current_part_default_volume = _process_note(content, mode=2)
            elif keyword == 'al':
                current_part_all_same_duration = _process_note(content)
            elif keyword == 'ai':
                current_part_all_same_interval = _process_note(content)
            elif keyword == 'av':
                current_part_all_same_volume = _process_note(content, mode=2)
        return current_part_default_duration, current_part_default_interval, current_part_default_volume, current_part_repeat_times, current_part_all_same_duration, current_part_all_same_interval, current_part_all_same_volume, current_part_fix_length, current_part_name, current_part_fix_beats

    def _translate_global_keyword_parser(self, global_keywords):
        global_default_duration = None
        global_default_interval = None
        global_default_volume = None
        global_repeat_times = 1
        global_all_same_duration = None
        global_all_same_interval = None
        global_all_same_volume = None
        global_fix_length = None
        global_fix_beats = None
        for each in global_keywords:
            keyword, content = each[1:].split(':')
            if keyword == 't':
                global_fix_length = _process_note(content)
            elif keyword == 'b':
                global_fix_beats = _process_note(content)
            elif keyword == 'r':
                global_repeat_times = int(content)
            elif keyword == 'd':
                global_default_duration, global_default_interval, global_default_volume = _process_settings(
                    content.split(';'))
            elif keyword == 'a':
                global_all_same_duration, global_all_same_interval, global_all_same_volume = _process_settings(
                    content.split(';'))
            elif keyword == 'dl':
                global_default_duration = _process_note(content)
            elif keyword == 'di':
                global_default_interval = _process_note(content)
            elif keyword == 'dv':
                global_default_volume = _process_note(content, mode=2)
            elif keyword == 'al':
                global_all_same_duration = _process_note(content)
            elif keyword == 'ai':
                global_all_same_interval = _process_note(content)
            elif keyword == 'av':
                global_all_same_volume = _process_note(content, mode=2)
        return global_default_duration, global_default_interval, global_default_volume, global_repeat_times, global_all_same_duration, global_all_same_interval, global_all_same_volume, global_fix_length, global_fix_beats

    def _convert_to_symbol(self, text, current_rest_symbol,
                           current_continue_symbol):
        dotted_num = 0
        if '.' in text:
            text, dotted = text.split('.', 1)
            dotted_num = len(dotted) + 1
        if text == current_rest_symbol:
            result = rest_symbol()
        elif text == current_continue_symbol:
            result = continue_symbol()
        result.dotted_num = dotted_num
        result.mode = None
        return result

    def _convert_to_note(self, text, mapping=None, mode=0):
        dotted_num = 0
        if text.startswith('+') or text.startswith('-'):
            current_num, current_changed, dotted_num = _parse_change_num(text)
            if self.last_non_num_note is not None:
                result = self.last_non_num_note + current_num
                result.dotted_num = dotted_num
            else:
                raise ValueError(
                    'requires at least a previous non-number note')
            if current_changed:
                self.last_non_num_note = result
        else:
            if '.' in text:
                text, dotted = text.split('.', 1)
                dotted_num = len(dotted) + 1
            if mode == 0:
                result = mp.degree_to_note(mapping[text])
            else:
                result = mp.N(text)
            result.dotted_num = dotted_num
            self.last_non_num_note = result

        return result

    def _get_dotted(self, text):
        result = 0
        if isinstance(text, str):
            if ':' in text:
                text = text.split(':', 1)[0]
            if '.' in text:
                ind = text.index('.')
                ind2 = len(text)
                if '[' in text:
                    ind2 = text.index('[')
                if ind2 > ind:
                    if all(i == '.' for i in text[ind:ind2]):
                        text, dotted = text[:ind2].split('.', 1)
                        dotted += '.'
                        result = len(dotted)
                    else:
                        raise Exception(
                            'for drum notes group, dotted notes syntax should be placed after the last note'
                        )
        else:
            result = text.dotted_num
        return result

    def _get_length(self, notes):
        return sum([
            mp.dotted(1, self._get_dotted(i)) for i in notes
            if not (isinstance(i, str) and i.startswith('i:'))
        ])

    def _apply_dotted_notes(self, current_part_fix_length_unit, dotted_num):
        return mp.dotted(current_part_fix_length_unit, dotted_num)

    def __mul__(self, n):
        temp = copy(self)
        temp.notes *= n
        return temp

    def __add__(self, other):
        temp = copy(self)
        if isinstance(other, tuple) and isinstance(other[0], drum):
            other = (other[0].notes, ) + other[1:]
        temp.notes += (other.notes if isinstance(other, drum) else other)
        return temp

    def __and__(self, other):
        temp = copy(self)
        if isinstance(other, tuple) and isinstance(other[0], drum):
            other = (other[0].notes, ) + other[1:]
        temp.notes &= (other.notes if isinstance(other, drum) else other)
        return temp

    def __or__(self, other):
        temp = copy(self)
        if isinstance(other, tuple) and isinstance(other[0], drum):
            other = (other[0].notes, ) + other[1:]
        temp.notes |= (other.notes if isinstance(other, drum) else other)
        return temp

    def set(self, durations=None, intervals=None, volumes=None):
        return self % (durations, intervals, volumes)

    def with_start(self, start_time):
        temp = copy(self)
        temp.notes.start_time = start_time
        return temp


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
        if self.dotted is not None:
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
        result = chord([copy(notes) for i in range(self.get_beat_num())
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


@dataclass
class chord_type:
    '''
    This class represents a chord type, which defines how a chord is derived precisely.
    '''
    root: str = None
    chord_type: str = None
    chord_speciality: str = 'root position'
    inversion: int = None
    omit: list = None
    altered: list = None
    non_chord_bass_note: str = None
    voicing: list = None
    type: str = 'chord'
    note_name: str = None
    interval_name: str = None
    polychords: list = None
    order: list = None

    def get_root_position(self):
        if self.root is not None and self.chord_type is not None:
            return f'{self.root}{self.chord_type}'
        else:
            return None

    def to_chord(self,
                 root_position=False,
                 apply_voicing=True,
                 apply_omit=True,
                 apply_altered=True,
                 apply_non_chord_bass_note=True,
                 apply_inversion=True,
                 custom_mapping=None,
                 custom_order=None,
                 root_octave=None):
        if self.type == 'note':
            return chord([self.note_name])
        elif self.type == 'interval':
            current_root = mp.N(self.root)
            if root_octave is not None:
                current_root.num = root_octave
            return chord([
                current_root,
                current_root.up(database.NAME_OF_INTERVAL[self.interval_name])
            ])
        elif self.type == 'chord':
            if self.chord_speciality == 'polychord':
                current_chords = [
                    each.to_chord(
                        root_position=root_position,
                        apply_voicing=apply_voicing,
                        apply_omit=apply_omit,
                        apply_altered=apply_altered,
                        apply_non_chord_bass_note=apply_non_chord_bass_note,
                        apply_inversion=apply_inversion,
                        custom_mapping=custom_mapping,
                        custom_order=custom_order)
                    for each in self.polychords[::-1]
                ]
                current = functools.reduce(chord.on, current_chords)
            else:
                if self.root is None or self.chord_type is None:
                    return None
                current = mp.C(self.get_root_position(),
                               custom_mapping=custom_mapping)
                if not root_position:
                    if custom_order is not None:
                        current_order = custom_order
                    else:
                        if self.order is not None:
                            current_order = self.order
                        else:
                            current_order = [0, 1, 2, 3, 4]
                    current_apply = [
                        apply_omit, apply_altered, apply_inversion,
                        apply_voicing, apply_non_chord_bass_note
                    ]
                    for each in current_order:
                        if current_apply[each]:
                            current = self._apply_order(current, each)
            if root_octave is not None:
                current = current.reset_octave(root_octave)
            return current

    def _apply_order(self, current, order):
        '''
        order is an integer that represents a type of chord alternation
        0: omit some notes
        1: alter some notes
        2: inversion
        3: chord voicing
        4: add a non-chord bass note
        '''
        if order == 0:
            if self.omit:
                current = current.omit([
                    database.precise_degree_match.get(i.split('/')[0], i)
                    for i in self.omit
                ],
                                       mode=1)
        elif order == 1:
            if self.altered:
                current = current(','.join(self.altered))
        elif order == 2:
            if self.inversion:
                current = current.inversion(self.inversion)
        elif order == 3:
            if self.voicing:
                current = current @ self.voicing
        elif order == 4:
            if self.non_chord_bass_note:
                current = current.on(self.non_chord_bass_note)
        return current

    def _add_order(self, order):
        if self.order is not None:
            if order in self.order:
                self.order.remove(order)
            self.order.append(order)

    def to_text(self,
                show_degree=True,
                show_voicing=True,
                custom_mapping=None):
        if self.type == 'note':
            return f'note {self.note_name}'
        elif self.type == 'interval':
            return f'{self.root} with {self.interval_name}'
        elif self.type == 'chord':
            if self.chord_speciality == 'polychord':
                return '/'.join([
                    f'[{i.to_text(show_degree=show_degree, show_voicing=show_voicing, custom_mapping=custom_mapping)}]'
                    for i in self.polychords[::-1]
                ])
            else:
                if self.root is None or self.chord_type is None:
                    return None
                current_chord = mp.C(self.get_root_position(),
                                     custom_mapping=custom_mapping)
                if self.altered:
                    if show_degree:
                        altered_msg = ', '.join(self.altered)
                    else:
                        current_alter = []
                        for i in self.altered:
                            if i[1:].isdigit():
                                current_degree = current_chord.interval_note(
                                    i[1:])
                                if current_degree is not None:
                                    current_alter.append(i[0] +
                                                         current_degree.name)
                            else:
                                current_alter.append(i)
                        altered_msg = ', '.join(current_alter)
                else:
                    altered_msg = ''
                if self.omit:
                    if show_degree:
                        omit_msg = f'omit {", ".join([i if not ("/" not in i and (i.startswith("b") or i.startswith("#"))) else i[1:] for i in self.omit])}'
                    else:
                        current_omit = []
                        for i in self.omit:
                            i = i.split('/')[0]
                            if i in database.precise_degree_match:
                                current_degree = current_chord.interval_note(
                                    i, mode=1)
                                if current_degree is not None:
                                    current_omit.append(current_degree.name)
                            else:
                                if i.startswith('b') or i.startswith('#'):
                                    i = i[1:]
                                current_omit.append(i)
                        omit_msg = f'omit {", ".join(current_omit)}'
                else:
                    omit_msg = ''
                voicing_msg = f'sort as {self.voicing}' if self.voicing else ''
                non_chord_bass_note_msg = f'/{self.non_chord_bass_note}' if self.non_chord_bass_note else ''
                if self.inversion:
                    current_new_chord = self.to_chord(
                        custom_mapping=custom_mapping, apply_inversion=False)
                    inversion_msg = f'/{current_new_chord[self.inversion].name}'
                else:
                    inversion_msg = ''
                result = f'{self.root}{self.chord_type}'
                other_msg = [
                    omit_msg, altered_msg, inversion_msg, voicing_msg,
                    non_chord_bass_note_msg
                ]
                if not self.order:
                    current_order = [0, 1, 2, 3, 4]
                else:
                    current_order = self.order
                if not show_voicing and 3 in current_order:
                    current_order.remove(3)
                other_msg = [other_msg[i] for i in current_order]
                other_msg = [i for i in other_msg if i]
                if other_msg:
                    if other_msg[0] != inversion_msg:
                        result += ' '
                    result += ' '.join(other_msg)
                return result

    def clear(self):
        self.root = None
        self.chord_type = None
        self.chord_speciality = 'root position'
        self.inversion = None
        self.omit = None
        self.altered = None
        self.non_chord_bass_note = None
        self.voicing = None
        self.type = 'chord'
        self.note_name = None
        self.interval_name = None
        self.order = []

    def apply_sort_msg(self, msg, change_order=False):
        if isinstance(msg, int):
            self.chord_speciality = 'inverted chord'
            self.inversion = msg
            if change_order and self.order is not None:
                self._add_order(2)
        else:
            self.chord_speciality = 'chord voicings'
            self.voicing = msg
            if change_order and self.order is not None:
                self._add_order(3)

    def simplify(self):
        if self.inversion is not None and self.voicing is not None:
            current_chord1 = self.to_chord()
            current_chord2 = self.to_chord(apply_inversion=False,
                                           apply_voicing=False)
            current_inversion_way = mp.alg.inversion_way(
                current_chord1, current_chord2)
            if isinstance(current_inversion_way, int):
                self.inversion = current_inversion_way
                self.voicing = None
                self.chord_speciality = 'inverted chord'
                self._add_order(2)
            elif isinstance(current_inversion_way, list):
                self.inversion = None
                self.voicing = current_inversion_way
                self.chord_speciality = 'chord voicings'
                self._add_order(3)

    def show(self, **to_text_args):
        current_vars = vars(self)
        if self.type == 'note':
            current = '\n'.join([
                f'{i.replace("_", " ")}: {current_vars[i]}'
                for i in ['type', 'note_name']
            ])
        elif self.type == 'interval':
            current = '\n'.join([
                f'{i.replace("_", " ")}: {current_vars[i]}'
                for i in ['type', 'root', 'interval_name']
            ])
        elif self.type == 'chord':
            current = [f'type: {self.type}'] + [
                f'{i.replace("_", " ")}: {j}'
                for i, j in current_vars.items() if i not in [
                    'type', 'note_name', 'interval_name', 'highest_ratio',
                    'order'
                ]
            ]
            if self.chord_speciality == 'polychord':
                for i, each in enumerate(current):
                    if each.startswith('polychords:'):
                        current[
                            i] = f'polychords: {[i.to_text(**to_text_args) for i in self.polychords]}'
                        break
            current = '\n'.join(current)
        return current

    def get_complexity(self):
        score = 0
        if self.type == 'chord':
            if self.chord_speciality == 'polychord':
                score += 100
            else:
                if self.inversion is not None:
                    score += 10
                if self.omit is not None:
                    score += 10 * len(self.omit)
                if self.altered is not None:
                    score += 30 * len(self.altered)
                if self.non_chord_bass_note is not None:
                    score += 30
                if self.voicing is not None:
                    score += 10
        return score


def _read_notes(note_ls,
                rootpitch=4,
                default_duration=1 / 4,
                default_interval=0,
                default_volume=100):
    intervals = []
    notes_result = []
    start_time = 0
    last_non_num_note = None
    for each in note_ls:
        if each == '':
            continue
        if isinstance(each, note):
            notes_result.append(each)
            intervals.append(default_interval)
            last_non_num_note = notes_result[-1]
        elif isinstance(each, rest):
            if not notes_result:
                start_time += each.get_duration()
            elif intervals:
                intervals[-1] += each.get_duration()
        elif isinstance(each, str):
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
                last_non_num_note, notes_result, intervals, start_time = _read_single_note(
                    each_note,
                    rootpitch,
                    duration,
                    interval,
                    volume,
                    last_non_num_note,
                    notes_result,
                    intervals,
                    start_time,
                    has_settings=has_settings,
                    has_same_time=has_same_time)
        else:
            notes_result.append(each)
            intervals.append(default_interval)
    if len(intervals) != len(notes_result):
        intervals = []
    return notes_result, intervals, start_time


def _read_single_note(each,
                      rootpitch,
                      duration,
                      interval,
                      volume,
                      last_non_num_note,
                      notes_result,
                      intervals,
                      start_time,
                      has_settings=False,
                      has_same_time=False):
    dotted_num = 0
    if '.' in each:
        each, dotted = each.split('.', 1)
        dotted_num = len(dotted) + 1
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
    elif each != '-' and (each.startswith('+') or each.startswith('-')):
        current_num, current_changed, current_dotted_num = _parse_change_num(
            each)
        if last_non_num_note is None:
            raise ValueError('requires at least a previous non-number note')
        current_note = last_non_num_note + current_num
        current_note.duration = duration
        current_note.volume = volume
        current_interval = interval
        if has_same_time:
            current_interval = 0
            if not has_settings:
                current_note.duration = mp.dotted(current_note.duration,
                                                  dotted_num)
        else:
            if has_settings:
                current_interval = interval
            else:
                current_interval = mp.dotted(current_interval, dotted_num)
                current_note.duration = mp.dotted(current_note.duration,
                                                  dotted_num)
        if current_changed:
            last_non_num_note = current_note
        notes_result.append(current_note)
        intervals.append(current_interval)
    else:
        current_note = mp.to_note(each,
                                  duration=duration,
                                  volume=volume,
                                  pitch=rootpitch)
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
        last_non_num_note = current_note
    return last_non_num_note, notes_result, intervals, start_time


def _parse_change_num(each):
    current_changed = False
    dotted_num = 0
    if '.' in each:
        each, dotted = each.split('.', 1)
        dotted_num = len(dotted) + 1
    if each.startswith('++'):
        current_changed = True
        current_content = each.split('++', 1)[1]
        if 'o' in current_content:
            current_octave, current_extra = current_content.split('o', 1)
            current_octave = int(current_octave)
            if current_extra:
                current_extra = int(current_extra)
            else:
                current_extra = 0
            current_num = current_octave * database.octave + current_extra
        else:
            current_num = int(current_content)
    elif each.startswith('--'):
        current_changed = True
        current_content = each.split('--', 1)[1]
        if 'o' in current_content:
            current_octave, current_extra = current_content.split('o', 1)
            current_octave = int(current_octave)
            if current_extra:
                current_extra = int(current_extra)
            else:
                current_extra = 0
            current_num = -(current_octave * database.octave + current_extra)
        else:
            current_num = -int(current_content)
    elif each.startswith('+'):
        current_content = each.split('+', 1)[1]
        if 'o' in current_content:
            current_octave, current_extra = current_content.split('o', 1)
            current_octave = int(current_octave)
            if current_extra:
                current_extra = int(current_extra)
            else:
                current_extra = 0
            current_num = current_octave * database.octave + current_extra
        else:
            current_num = int(current_content)
    elif each.startswith('-'):
        current_content = each.split('-', 1)[1]
        if 'o' in current_content:
            current_octave, current_extra = current_content.split('o', 1)
            current_octave = int(current_octave)
            if current_extra:
                current_extra = int(current_extra)
            else:
                current_extra = 0
            current_num = -(current_octave * database.octave + current_extra)
        else:
            current_num = -int(current_content)
    return current_num, current_changed, dotted_num


def _process_note(value, mode=0, value2=None):
    if mode == 1 and value == '.':
        return value2
    if ';' in value:
        result = [_process_note(i) for i in value.split(';')]
        if mode == 2:
            result = [
                int(i) if isinstance(i, float) and i.is_integer() else i
                for i in result
            ]
        return result
    elif value == 'n':
        return None
    else:
        length = len(value)
        if value[0] != '.':
            num_ind = length - 1
            for k in range(num_ind, -1, -1):
                if value[k] != '.':
                    num_ind = k
                    break
            dotted_notes = value[num_ind + 1:].count('.')
            value = value[:num_ind + 1]
            value = mp.parse_num(value) * sum(
                [(1 / 2)**i for i in range(dotted_notes + 1)])
        elif length > 1:
            num_ind = 0
            for k, each in enumerate(value):
                if each != '.':
                    num_ind = k
                    break
            if value[-1] != '.':
                value = 1 / mp.parse_num(value[num_ind:])
            else:
                dotted_notes_start_ind = length - 1
                for k in range(dotted_notes_start_ind, -1, -1):
                    if value[k] != '.':
                        dotted_notes_start_ind = k + 1
                        break
                dotted_notes = length - dotted_notes_start_ind
                value = (1 / mp.parse_num(
                    value[num_ind:dotted_notes_start_ind])) * sum(
                        [(1 / 2)**i for i in range(dotted_notes + 1)])
        if mode == 2:
            if isinstance(value, float) and value.is_integer():
                value = int(value)
        return value


def _process_settings(settings):
    settings += ['n' for i in range(3 - len(settings))]
    duration, interval, volume = settings
    duration = _process_note(duration)
    interval = _process_note(interval, mode=1, value2=duration)
    volume = _process_note(volume, mode=2)
    return [duration, interval, volume]


def _process_normalize_tempo(obj, tempo_changes_ranges, bpm, mode=0):
    whole_notes = obj.notes
    intervals = obj.interval
    count_length = 0
    for k in range(len(obj)):
        current_note = whole_notes[k]
        current_interval = intervals[k]
        if mode == 0:
            current_note_left, current_note_right = count_length, count_length + current_note.duration
            new_note_duration = 0
        current_interval_left, current_interval_right = count_length, count_length + current_interval
        new_interval_duration = 0
        for each in tempo_changes_ranges:
            each_left, each_right, each_tempo = each
            if mode == 0:
                if not (current_note_left >= each_right
                        or current_note_right <= each_left):
                    valid_length = min(current_note_right, each_right) - max(
                        current_note_left, each_left)
                    current_ratio = each_tempo / bpm
                    valid_length /= current_ratio
                    new_note_duration += valid_length

            if not (current_interval_left >= each_right
                    or current_interval_right <= each_left):
                valid_length = min(current_interval_right, each_right) - max(
                    current_interval_left, each_left)
                current_ratio = each_tempo / bpm
                valid_length /= current_ratio
                new_interval_duration += valid_length
        if mode == 0:
            current_note.duration = new_note_duration
        obj.interval[k] = new_interval_duration
        count_length += current_interval


def _piece_process_normalize_tempo(self,
                                   bpm,
                                   first_track_start_time,
                                   original_bpm=None):
    other_messages = self.other_messages
    temp = copy(self)
    start_time_ls = temp.start_times
    all_tracks = temp.tracks
    length = len(all_tracks)
    for k in range(length):
        current_track = all_tracks[k]
        for each in current_track.notes:
            each.track_num = k
        for each in current_track.tempos:
            each.track_num = k
        for each in current_track.pitch_bends:
            each.track_num = k

    first_track_ind = start_time_ls.index(first_track_start_time)
    start_time_ls.insert(0, start_time_ls.pop(first_track_ind))

    all_tracks.insert(0, all_tracks.pop(first_track_ind))
    first_track = all_tracks[0]

    for i in range(1, length):
        current_track = all_tracks[i]
        current_start_time = start_time_ls[i]
        current_shift = current_start_time - first_track_start_time
        first_track = first_track.add(current_track,
                                      start=current_shift,
                                      mode='head',
                                      adjust_msg=False)
    first_track.other_messages = other_messages
    if self.pan:
        for k in range(len(self.pan)):
            current_pan = self.pan[k]
            for each in current_pan:
                each.track = k
    if self.volume:
        for k in range(len(self.volume)):
            current_volume = self.volume[k]
            for each in current_volume:
                each.track = k
    whole_pan = mp.concat(self.pan) if self.pan else None
    whole_volume = mp.concat(self.volume) if self.volume else None
    current_start_time = first_track_start_time + first_track.start_time
    normalize_values = first_track.normalize_tempo(
        bpm,
        start_time=current_start_time,
        pan_msg=whole_pan,
        volume_msg=whole_volume,
        original_bpm=original_bpm)
    if normalize_values:
        normalize_result, first_track_start_time = normalize_values
    else:
        normalize_result = None
        first_track_start_time = current_start_time
    if normalize_result:
        new_other_messages = normalize_result[0]
        self.other_messages = new_other_messages
        if whole_pan or whole_volume:
            whole_pan, whole_volume = normalize_result[1], normalize_result[2]
            self.pan = [[i for i in whole_pan if i.track == j]
                        for j in range(len(self.tracks))]
            self.volume = [[i for i in whole_volume if i.track == j]
                           for j in range(len(self.tracks))]
    else:
        new_other_messages = self.other_messages
    start_times_inds = [[
        i for i in range(len(first_track))
        if first_track.notes[i].track_num == k
    ] for k in range(length)]
    start_times_inds = [each[0] if each else -1 for each in start_times_inds]
    new_start_times = [
        first_track_start_time + first_track[:k].bars(mode=0) if k != -1 else 0
        for k in start_times_inds
    ]
    new_track_notes = [[] for k in range(length)]
    new_track_inds = [[] for k in range(length)]
    new_track_intervals = [[] for k in range(length)]
    new_track_tempos = [[] for k in range(length)]
    new_track_pitch_bends = [[] for k in range(length)]
    whole_length = len(first_track)
    for j in range(whole_length):
        current_note = first_track.notes[j]
        new_track_notes[current_note.track_num].append(current_note)
        new_track_inds[current_note.track_num].append(j)
    for i in first_track.tempos:
        new_track_tempos[i.track_num].append(i)
    for i in first_track.pitch_bends:
        new_track_pitch_bends[i.track_num].append(i)
    whole_interval = first_track.interval
    new_track_intervals = [[
        sum(whole_interval[inds[i]:inds[i + 1]]) for i in range(len(inds) - 1)
    ] for inds in new_track_inds]
    for i in range(length):
        if new_track_inds[i]:
            new_track_intervals[i].append(
                sum(whole_interval[new_track_inds[i][-1]:]))
    new_tracks = []
    for k in range(length):
        current_track_ind = k
        current_track = chord(
            new_track_notes[current_track_ind],
            interval=new_track_intervals[current_track_ind],
            tempos=new_track_tempos[current_track_ind],
            pitch_bends=new_track_pitch_bends[current_track_ind],
            other_messages=[
                each for each in new_other_messages if each.track == k
            ])
        new_tracks.append(current_track)
    self.tracks = new_tracks
    self.start_times = new_start_times


def copy_list(current_list, n, start_time=0):
    result = []
    unit = copy(current_list)
    for i in range(n):
        current = copy(unit)
        if start_time != 0 and i != n - 1:
            current[-1] += start_time
        result.extend(current)
    return result


process_note = _process_note

import musicpy as mp
