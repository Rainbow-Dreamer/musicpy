from copy import deepcopy as copy
from fractions import Fraction
from dataclasses import dataclass
import functools

if __name__ == 'musicpy.chord_class':
    from . import database
    from .primitives import note, tempo, pitch_bend, pan, volume, event, beat, rest_symbol, continue_symbol, rest
else:
    import database
    from primitives import note, tempo, pitch_bend, pan, volume, event, beat, rest_symbol, continue_symbol, rest


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
        if current_intervals and interval is None:
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
        return type(
            other
        ) is chord and self.notes == other.notes and self.interval == other.interval

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
        else:
            raise ValueError('Invalid bars mode')
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
        if dotted is not None and dotted != 0:
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
        transdict = {
            mp.standardize_note(i): mp.standardize_note(j)
            for i, j in transdict.items()
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
        result.pitch_bends += pitch_bend_changes
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
        chord_type = self.detect_chord_type(get_chord_type=True, **detect_args)
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
        interval = str(interval)
        if mode == 0:
            if interval in database.degree_match:
                self_notes_degrees = [i.degree for i in self.notes]
                degrees = database.degree_match[interval]
                for each in degrees:
                    current_note = self.notes[0] + each
                    if current_note.degree in self_notes_degrees:
                        return current_note
            if interval in database.precise_degree_match:
                self_notes_degrees = [i.degree for i in self.notes]
                degrees = database.precise_degree_match[interval]
                current_note = self.notes[0] + degrees
                if current_note.degree in self_notes_degrees:
                    return current_note
        elif mode == 1:
            if interval in database.precise_degree_match:
                interval = database.precise_degree_match[interval]
                return self.notes[0] + interval

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
            if current_interval in database.reverse_precise_degree_number_match:
                return database.reverse_precise_degree_number_match[
                    current_interval]
        elif mode == 1:
            return database.INTERVAL[current_interval]

    def get_voicing(self, voicing, mode=0):
        notes = [self.interval_note(i, mode=mode).name for i in voicing]
        pitch = self.notes[self.names().index(notes[0])].num
        return chord(notes, rootpitch=pitch)

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
        if num == 0:
            return temp
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


if __name__ == 'musicpy.chord_class':
    from .parsers import (_read_notes, _read_single_note, _parse_change_num,
                          _process_note, _process_settings,
                          _process_normalize_tempo,
                          _piece_process_normalize_tempo, copy_list,
                          process_note)
else:
    from parsers import (_read_notes, _read_single_note, _parse_change_num,
                         _process_note, _process_settings,
                         _process_normalize_tempo,
                         _piece_process_normalize_tempo, copy_list,
                         process_note)

import musicpy as mp
