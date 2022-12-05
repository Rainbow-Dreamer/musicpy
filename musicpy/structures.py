from copy import deepcopy as copy
from fractions import Fraction
if __name__ == 'musicpy.structures':
    from . import database
else:
    import database


class note:

    def __init__(self, name, num=4, duration=0.25, volume=100, channel=None):
        if name not in database.standard:
            raise ValueError(
                f"Invalid note name '{name}', accepted note names are {list(database.standard.keys())}"
            )
        self.name = name
        self.num = num
        self.duration = duration
        volume = int(volume)
        if volume > 127:
            volume = 127
        self.volume = volume
        self.channel = channel

    @property
    def degree(self):
        return database.standard[self.name] + 12 * (self.num + 1)

    @degree.setter
    def degree(self, value):
        self.name = database.standard_reverse[value % 12]
        self.num = (value // 12) - 1

    def __repr__(self):
        return f'{self.name}{self.num}'

    def __eq__(self, other):
        return type(
            other
        ) is note and self.name == other.name and self.num == other.num

    def __matmul__(self, other):
        return self.name == other.name

    def setvolume(self, vol):
        vol = int(vol)
        if vol > 127:
            vol = 127
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
        return mp.degree_to_note(self.degree + unit, self.duration,
                                 self.volume, self.channel)

    def down(self, unit=1):
        return self.up(-unit)

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

    def __add__(self, obj):
        if isinstance(obj, int):
            return self.up(obj)
        if not isinstance(obj, note):
            obj = mp.to_note(obj)
        return chord([copy(self), copy(obj)])

    def __sub__(self, obj):
        if isinstance(obj, int):
            return self.down(obj)

    def __call__(self, obj=''):
        return mp.C(self.name + obj, self.num)

    def with_interval(self, interval):
        result = chord([copy(self), self + interval])
        return result

    def getchord_by_interval(start,
                             interval1,
                             duration=0.25,
                             interval=0,
                             cummulative=True):
        return mp.getchord_by_interval(start, interval1, duration, interval,
                                       cummulative)

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


class chord:
    ''' This class can contain a chord with many notes played simultaneously and either has intervals, the default interval is 0.'''

    def __init__(self,
                 notes,
                 duration=None,
                 interval=None,
                 rootpitch=4,
                 other_messages=[],
                 start_time=None):
        standardize_msg = False
        if isinstance(notes, str):
            notes = notes.replace(' ', '').split(',')
            if all(not any(i.isdigit() for i in j) for j in notes
                   if (not j.startswith('tempo')) and (
                       not j.startswith('pitch'))):
                standardize_msg = True
        elif isinstance(notes, list) and all(
                not isinstance(i, note)
                for i in notes) and all(not any(j.isdigit() for j in i)
                                        for i in notes if isinstance(i, str)):
            standardize_msg = True
        notes_msg = _read_notes(notes, rootpitch)
        notes, current_intervals, current_start_time = notes_msg
        if current_intervals and not interval:
            interval = current_intervals
        if standardize_msg and notes:
            root = notes[0]
            notels = [root]
            last = None
            for i in range(1, len(notes)):
                last_note = notels[i - 1]
                if isinstance(last_note, note):
                    last = last_note
                current_note = notes[i]
                if not isinstance(current_note, note):
                    notels.append(current_note)
                else:
                    if last is not None:
                        current = note(current_note.name, last.num)
                        if database.standard[
                                current.name] <= database.standard[last.name]:
                            current = note(current.name, last.num + 1)
                    else:
                        current = current_note
                    notels.append(current)
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
        if start_time is None:
            self.start_time = current_start_time
        else:
            self.start_time = start_time
        self.other_messages = other_messages

    def get_duration(self):
        return [i.duration for i in self.notes]

    def get_volume(self):
        return [i.volume for i in self.notes]

    def get_degree(self):
        return [i.degree for i in self]

    def names(self):
        return [i.name for i in self if isinstance(i, note)]

    def __eq__(self, other):
        return type(
            other
        ) is chord and self.notes == other.notes and self.interval == other.interval

    def split(self, return_type, get_time=False, sort=False):
        temp = copy(self)
        inds = [
            i for i in range(len(temp))
            if isinstance(temp.notes[i], return_type)
        ]
        notes = [temp.notes[i] for i in inds]
        intervals = [temp.interval[i] for i in inds]
        if get_time and return_type != note:
            no_time = [k for k in inds if temp.notes[k].start_time is None]
            for each in no_time:
                current_time = temp[:each].bars()
                current = temp.notes[each]
                current.start_time = current_time
            if sort:
                notes.sort(key=lambda s: s.start_time)
        return chord(notes, interval=intervals, start_time=temp.start_time)

    def get_msg(self, types):
        return [i for i in self.other_messages if i.type == types]

    def cut(self, ind1=0, ind2=None, start_time=0, return_inds=False):
        # get parts of notes between two bars
        temp = copy(self)
        start_offset = start_time - ind1
        if start_offset < 0:
            start_offset = 0
        ind1 -= start_time
        if ind1 < 0:
            ind1 = 0
        if ind2 is not None:
            ind2 -= start_time
            if ind2 <= 0:
                ind2 = 0
        else:
            ind2 = temp.bars(mode=0)

        changes = []
        for i in range(len(temp.notes)):
            each = temp.notes[i]
            if isinstance(each, (tempo, pitch_bend)):
                if each.start_time is None:
                    each.start_time = temp[:i].bars(mode=0)
                each.start_time -= (ind1 + start_time - start_offset)
                if 0 <= each.start_time < ind2 - ind1:
                    changes.append(each)
        temp = temp.only_notes()

        current_bar = 0
        notes = temp.notes
        intervals = temp.interval
        length = len(notes)
        start_ind = 0
        to_ind = length
        find_start = False
        if ind1 == 0:
            find_start = True
        actual_start_time = 0
        for i in range(length):
            current_note = notes[i]
            if isinstance(current_note, note):
                current_bar += intervals[i]
                if (not find_start) and current_bar >= ind1:
                    start_ind = i + 1
                    find_start = True
                    actual_start_time = current_bar - ind1
                    if ind2 is None:
                        break
                elif ind2 and current_bar >= ind2:
                    to_ind = i + 1
                    break
        if not find_start:
            start_ind = to_ind
        if return_inds:
            return start_ind, to_ind
        result = temp[start_ind:to_ind]
        result += chord(changes)
        result.other_messages = [
            i for i in result.other_messages if ind1 <= i.start_time < ind2
        ]
        result.start_time = actual_start_time
        return result

    def cut_time(self,
                 bpm,
                 time1=0,
                 time2=None,
                 start_time=0,
                 return_inds=False,
                 normalize_tempo=False):
        if normalize_tempo:
            temp = copy(self)
            temp.normalize_tempo(bpm)
            return temp.cut_time(bpm, time1, time2, start_time, return_inds)
        time1 -= start_time
        if time1 < 0:
            return chord([]) if not return_inds else (0, 0)
        if time2 is not None:
            time2 -= start_time
            if time2 <= 0:
                return chord([]) if not return_inds else (0, 0)
        current_bar = 0
        notes = self.notes
        intervals = self.interval
        length = len(notes)
        start_ind = 0
        to_ind = length
        find_start = False
        if time1 == 0:
            find_start = True
        actual_start_time = 0
        start_length = (time1 / 4) * bpm / 60
        for i in range(length):
            current_note = notes[i]
            if isinstance(current_note, note):
                current_bar += intervals[i]
                if (not find_start) and (60 / bpm) * current_bar * 4 >= time1:
                    start_ind = i + 1
                    find_start = True
                    actual_start_time = current_bar - start_length
                    if time2 is None:
                        break
                elif time2 and (60 / bpm) * current_bar * 4 >= time2:
                    to_ind = i + 1
                    break
        if not find_start:
            start_ind = to_ind
        if return_inds:
            return start_ind, to_ind
        result = self[start_ind:to_ind]
        result.start_time = actual_start_time
        return result

    def last_note_standardize(self):
        for i in range(len(self.notes) - 1, -1, -1):
            current = self.notes[i]
            if isinstance(current, note):
                self.interval[i] = current.duration
                break

    def bars(self, start_time=0, mode=1, audio_mode=0):
        if mode == 0:
            max_length = sum(self.interval)
        elif mode == 1:
            temp = self.only_notes(audio_mode=audio_mode)
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
            if isinstance(each, note) and each.name in database.standard_dict:
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
            whole_bars = self.bars(start_time, audio_mode=audio_mode)
        else:
            if ind2 is None:
                ind2 = self.bars(start_time, audio_mode=audio_mode)
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
            start = self[:ind1].bars()
            return [start, start + bars_length]
        else:
            return bars_length

    def clear_pitch_bend(self, value=0, cond=None):
        length = len(self)
        whole_notes = self.notes
        if cond is None:
            if value == 0:
                inds = [
                    i for i in range(length)
                    if not (isinstance(whole_notes[i], pitch_bend)
                            and whole_notes[i].value == 0)
                ]
            elif value == 'all':
                inds = [
                    i for i in range(length)
                    if not isinstance(whole_notes[i], pitch_bend)
                ]
        else:
            inds = [
                i for i in range(length)
                if not isinstance(whole_notes[i], pitch_bend)
                or not cond(whole_notes[i])
            ]
        self.notes = [whole_notes[k] for k in inds]
        self.interval = [self.interval[k] for k in inds]

    def clear_tempo(self, cond=None):
        length = len(self)
        whole_notes = self.notes
        if cond is None:
            inds = [
                i for i in range(length)
                if not isinstance(whole_notes[i], tempo)
            ]
        else:
            inds = [
                i for i in range(length)
                if (not isinstance(whole_notes[i], tempo)) or (
                    not cond(whole_notes[i]))
            ]
        self.notes = [whole_notes[k] for k in inds]
        self.interval = [self.interval[k] for k in inds]

    def __mod__(self, alist):
        if isinstance(alist, (list, tuple)):
            return self.set(*alist)
        elif isinstance(alist, (str, note)):
            return self.on(alist)

    def standardize(self):
        temp = self.only_notes()
        notenames = temp.names()
        intervals = temp.interval
        durations = temp.get_duration()
        names_standard = [
            database.standard_dict[i] if i in database.standard_dict else i
            for i in notenames
        ]
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
            result.setvolume(volume, ind)
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
        result.setvolume(volume)
        if volume is not None:
            result.setvolume(volume, ind)
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
        return f'{self.notes} with interval {self.interval}'

    def __contains__(self, note1):
        if not isinstance(note1, note):
            note1 = mp.to_note(note1)
            if note1.name in database.standard_dict:
                note1.name = database.standard_dict[note1.name]
        return note1 in self.same_accidentals().notes

    def __add__(self, obj):
        if isinstance(obj, (int, list)):
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
        elif isinstance(obj, int):
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
        if isinstance(obj, list):
            return self.get(obj)
        elif isinstance(obj, int):
            return self.inv(obj)
        elif isinstance(obj, str):
            return self.inv(self.names().index(obj))
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
                        current_note = temp[0].up(i)
                        if current_note in temp:
                            ind = temp.notes.index(current_note)
                            temp.notes[ind] = temp.notes[ind].up(
                            ) if first == '#' else temp.notes[ind].down()
                            found = True
                            break
                    if not found:
                        temp += temp[0].up(
                            degree_ls[0]).up() if first == '#' else temp[0].up(
                                degree_ls[0]).down()
                else:
                    if degree in database.standard:
                        if degree in database.standard_dict:
                            degree = database.standard_dict[degree]
                        self_names = [
                            i if i not in database.standard_dict else
                            database.standard_dict[i] for i in temp.names()
                        ]
                        if degree in self_names:
                            ind = temp.names().index(degree)
                            temp.notes[ind] = temp.notes[ind].up(
                            ) if first == '#' else temp.notes[ind].down()
            elif each.startswith('omit') or each.startswith('no'):
                degree = each[4:] if each.startswith('omit') else each[2:]
                if degree in database.degree_match:
                    degree_ls = database.degree_match[degree]
                    for i in degree_ls:
                        current_note = temp[0].up(i)
                        if current_note in temp:
                            ind = temp.notes.index(current_note)
                            del temp.notes[ind]
                            del temp.interval[ind]
                            break
                else:
                    if degree in database.standard:
                        if degree in database.standard_dict:
                            degree = database.standard_dict[degree]
                        self_names = [
                            i if i not in database.standard_dict else
                            database.standard_dict[i] for i in temp.names()
                        ]
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
                    temp += temp[0].up(degree_ls[0])
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
        if isinstance(obj, (int, list)):
            return self.down(obj)
        if isinstance(obj, tuple):
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
            changes = []
            for i in range(len(temp.notes)):
                each = temp.notes[i]
                if isinstance(each, (tempo, pitch_bend)):
                    if each.start_time is None:
                        each.start_time = temp[:i].bars()
                    else:
                        each.start_time -= start_time
                    each.start_time = bar_length - each.start_time
                    changes.append(each)
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
            temp2 += chord(changes)
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
        for i in temp.notes:
            if isinstance(i, (tempo, pitch_bend)):
                if i.start_time is None:
                    i.start_time = temp[:i].bars()
                else:
                    i.start_time -= start_time
                i.start_time = bar_length - i.start_time
        return temp

    def intervalof(self, cummulative=True, translate=False):
        degrees = self.get_degree()
        if not cummulative:
            N = len(degrees)
            result = [degrees[i] - degrees[i - 1] for i in range(1, N)]
        else:
            root = degrees[0]
            others = degrees[1:]
            result = [i - root for i in others]
        if not translate:
            return result
        return [database.INTERVAL[x % database.octave] for x in result]

    def add(self, note1=None, mode='after', start=0, duration=0.25):
        if len(self) == 0:
            result = copy(note1)
            if start != 0:
                result.start_time += start
            return result
        temp = copy(self)
        if isinstance(note1, int):
            temp += temp[0].up(note1)
            return temp
        if len(note1) == 0:
            return temp
        if mode == 'tail':
            note1 = copy(note1)
            temp.notes += note1.notes
            temp.interval += note1.interval
            temp.other_messages += note1.other_messages
            return temp
        elif mode == 'head':
            note1 = copy(note1)
            if isinstance(note1, chord):
                inter = note1.interval
            else:
                if isinstance(note1, str):
                    note1 = chord([mp.to_note(note1, duration=duration)])
                elif isinstance(note1, note):
                    note1 = chord([note1])
                elif isinstance(note1, list):
                    note1 = chord(note1)
            # calculate the absolute distances of all of the notes of the chord to add and self,
            # and then sort them, make differences between each two distances
            not_notes = temp.split(pitch_bend, get_time=True) + temp.split(
                tempo, get_time=True) + note1.split(
                    pitch_bend, get_time=True) + note1.split(tempo,
                                                             get_time=True)
            temp.clear_pitch_bend(value='all')
            temp.clear_tempo()
            note1.clear_pitch_bend(value='all')
            note1.clear_tempo()
            if not temp.notes:
                result = note1 + not_notes
                if start != 0:
                    result.start_time += start
                return result
            distance = []
            intervals1 = temp.interval
            intervals2 = note1.interval
            current_start_time = min(temp.start_time, note1.start_time + start)
            start += (note1.start_time - temp.start_time)
            if start != 0:
                note1.notes.insert(0, temp.notes[0])
                intervals2.insert(0, start)
            counter = 0
            for i in range(len(intervals1)):
                distance.append([counter, temp.notes[i]])
                counter += intervals1[i]
            counter = 0
            for j in range(len(intervals2)):
                if not (j == 0 and start != 0):
                    distance.append([counter, note1.notes[j]])
                counter += intervals2[j]
            distance.sort(key=lambda s: s[0])
            newnotes = [each[1] for each in distance]
            newinterval = [each[0] for each in distance]
            newinterval = [
                newinterval[i] - newinterval[i - 1]
                for i in range(1, len(newinterval))
            ] + [distance[-1][1].duration]
            return chord(newnotes,
                         interval=newinterval,
                         start_time=current_start_time,
                         other_messages=temp.other_messages +
                         note1.other_messages) + not_notes
        elif mode == 'after':
            if self.interval[-1] == 0:
                return (self.rest(0) | (start + note1.start_time)).add(
                    note1, mode='tail')
            else:
                return (self | (start + note1.start_time)).add(note1,
                                                               mode='tail')

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
            chord(x, rootpitch=rootpitch).set(duration, interval)
            for x in mp.alg.perm(notenames)
        ]

    def inversion_highest(self, ind):
        if 1 <= ind < len(self):
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

    def on(self, root, duration=0.25, interval=None, each=0):
        temp = copy(self)
        if each == 0:
            if isinstance(root, chord):
                return root + self
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
        if not isinstance(unit, int):
            temp.notes = [temp.notes[k].up(unit[k]) for k in range(len(unit))]
            return temp
        if not isinstance(ind, int) and ind is not None:
            temp.notes = [
                temp.notes[i].up(unit) if i in ind else temp.notes[i]
                for i in range(len(temp.notes))
            ]
            return temp
        if ind2 is None:
            if ind is None:
                temp.notes = [
                    each.up(unit) if isinstance(each, note) else each
                    for each in temp.notes
                ]
            else:
                change_note = temp[ind]
                if isinstance(change_note, note):
                    temp[ind] = change_note.up(unit)
        else:
            temp.notes = temp.notes[:ind] + [
                each.up(unit)
                for each in temp.notes[ind:ind2] if isinstance(each, note)
            ] + temp.notes[ind2:]
        return temp

    def down(self, unit=1, ind=None, ind2=None):
        if not isinstance(unit, int):
            unit = [-i for i in unit]
            return self.up(unit, ind, ind2)
        return self.up(-unit, ind, ind2)

    def drop(self, ind):
        if not isinstance(ind, list):
            ind = [ind]
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
                return self.drop(current_ind)
            elif isinstance(ind[0],
                            str) and not any(i for i in ind[0] if i.isdigit()):
                temp = self.same_accidentals()
                self_notenames = temp.names()
                ind = chord(ind).same_accidentals().names()
                current_ind = [
                    k for k in range(len(self_notenames))
                    if self_notenames[k] in ind
                ]
                return self.drop(current_ind)
            else:
                return self
        else:
            return self

    def omit(self, ind, mode=0):
        if not isinstance(ind, list):
            ind = [ind]
        if ind and isinstance(ind[0], int):
            if mode == 0:
                return self.drop([self.interval_note(i) for i in ind])
            elif mode == 1:
                current_ind = [self.notes[0] + i for i in ind]
                return self.drop(current_ind)
        else:
            return self.drop(ind)

    def sus(self, num=4):
        temp = self.copy()
        first_note = temp[0]
        if num == 4:
            temp.notes = [
                i.up() if abs(i.degree - first_note.degree) %
                database.octave == database.major_third else
                i.up(2) if abs(i.degree - first_note.degree) %
                database.octave == database.minor_third else i
                for i in temp.notes
            ]
        elif num == 2:
            temp.notes = [
                i.down(2) if abs(i.degree - first_note.degree) %
                database.octave == database.major_third else
                i.down() if abs(i.degree - first_note.degree) %
                database.octave == database.minor_third else i
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
            if isinstance(current, note):
                if current.name in database.standard_dict:
                    current_name = database.standard_dict[current.name]
                else:
                    current_name = current.name
                if current_name in transdict:
                    current_note = mp.closest_note(current,
                                                   transdict[current_name])
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
        return chord(self.notes[i:j],
                     interval=self.interval[i:j],
                     other_messages=self.other_messages,
                     start_time=self.start_time)

    def __len__(self):
        return len(self.notes)

    def setvolume(self, vol, ind='all'):
        if isinstance(ind, int):
            each = self.notes[ind]
            each.setvolume(vol)
        elif isinstance(ind, list):
            if isinstance(vol, list):
                for i in range(len(ind)):
                    current = ind[i]
                    each = self.notes[current]
                    each.setvolume(vol[i])
            elif isinstance(vol, (int, float)):
                vol = int(vol)
                for i in range(len(ind)):
                    current = ind[i]
                    each = self.notes[current]
                    each.setvolume(vol)
        elif ind == 'all':
            if isinstance(vol, list):
                for i in range(len(vol)):
                    current = self.notes[i]
                    current.setvolume(vol[i])
            elif isinstance(vol, (int, float)):
                vol = int(vol)
                for each in self.notes:
                    each.setvolume(vol)

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
        tempo_changes = temp.split(tempo)
        if tempo_changes:
            temp.normalize_tempo(tempo_changes[0].bpm)
        result = temp.reverse()
        return result

    def pitch_inversion(self):
        pitch_bend_changes = self.split(pitch_bend, get_time=True)
        temp = self.copy()
        temp.clear_pitch_bend('all')
        tempo_changes = temp.split(tempo)
        if tempo_changes:
            temp.normalize_tempo(tempo_changes[0].bpm)
        volumes = temp.get_volume()
        pitch_intervals = temp.intervalof(cummulative=False)
        result = mp.getchord_by_interval(temp[0],
                                         [-i for i in pitch_intervals],
                                         temp.get_duration(), temp.interval,
                                         False)
        result.setvolume(volumes)
        result += pitch_bend_changes
        return result

    def only_notes(self, audio_mode=0):
        temp = copy(self)
        whole_notes = temp.notes
        intervals = temp.interval
        if audio_mode == 0:
            inds = [
                i for i in range(len(temp))
                if isinstance(whole_notes[i], note)
            ]
        else:
            from pydub import AudioSegment
            inds = [
                i for i in range(len(temp))
                if isinstance(whole_notes[i], (note, AudioSegment))
            ]
        temp.notes = [whole_notes[k] for k in inds]
        temp.interval = [intervals[k] for k in inds]
        return temp

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
            self.append(tempo(bpm=original_bpm, start_time=0))
        if all(i.bpm == bpm for i in self.notes if isinstance(i, tempo)):
            self.clear_tempo()
            return
        if start_time > 0:
            self.notes.insert(0, note('C', 5, duration=0))
            self.interval.insert(0, start_time)
        tempo_changes = [
            i for i in range(len(self.notes))
            if isinstance(self.notes[i], tempo)
        ]
        tempo_changes_no_time = [
            k for k in tempo_changes if self.notes[k].start_time is None
        ]
        for each in tempo_changes_no_time:
            current_time = self[:each].bars(mode=0)
            current_tempo = self.notes[each]
            current_tempo.start_time = current_time
        tempo_changes = [self.notes[j] for j in tempo_changes]
        tempo_changes.insert(0, tempo(bpm, 0))
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
        pitch_bend_msg = self.split(pitch_bend, get_time=True)
        self.clear_pitch_bend('all')
        _process_normalize_tempo(self, tempo_changes_ranges, bpm)
        other_types = pitch_bend_msg.notes + self.other_messages
        if pan_msg:
            other_types += pan_msg
        if volume_msg:
            other_types += volume_msg
        other_types.sort(key=lambda s: s.start_time)
        other_types.insert(0, pitch_bend(0, start_time=0))
        other_types_interval = [
            other_types[i + 1].start_time - other_types[i].start_time
            for i in range(len(other_types) - 1)
        ]
        other_types_interval.append(0)
        other_types_chord = chord(other_types, interval=other_types_interval)
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
            if isinstance(each, (pitch_bend, pan, volume)):
                each.start_time = current_start_time
            else:
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
        self.notes.extend(new_pitch_bends)
        self.interval.extend([0 for i in range(len(new_pitch_bends))])
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
        for i in temp.notes:
            if isinstance(i, (tempo, pitch_bend)):
                if i.start_time is not None:
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

    def info(self,
             alter_notes_show_degree=True,
             get_dict=False,
             **detect_args):
        chord_type = self.detect(
            alter_notes_show_degree=alter_notes_show_degree, **detect_args)
        if chord_type is None:
            return
        standard_notes = self.standardize()
        if len(standard_notes) == 1:
            if get_dict:
                return {
                    'type': 'note',
                    'note name': str(standard_notes[0]),
                    'whole name': chord_type
                }
            else:
                return f'note name: {standard_notes[0]}'
        elif len(standard_notes) == 2:
            if get_dict:
                return {
                    'type': 'interval',
                    'interval name': chord_type.split('with ')[1],
                    'root': str(standard_notes[0]),
                    'whole name': chord_type
                }
            else:
                return f'interval name: {chord_type.split("with ")[1]}\nroot: {standard_notes[0]}'
        original_chord_type = copy(chord_type)
        other_msg = {
            'omit': None,
            'altered': None,
            'non-chord bass note': None,
            'voicing': None
        }
        has_split = False
        if '/' in chord_type:
            has_split = True
            if ']/[' in chord_type:
                chord_speciality = 'polychord'
            else:
                chord_speciality = 'inverted chord'
        elif 'sort as' in chord_type:
            chord_speciality = 'chord voicings'
        else:
            alter_notes = chord_type.split(' ')
            if len(alter_notes) > 1 and alter_notes[1][0] in ['#', 'b']:
                chord_speciality = 'altered chord'
            else:
                chord_speciality = 'root position'
        if 'omit' in chord_type:
            if chord_speciality != 'polychord':
                other_msg['omit'] = [
                    int(i) if i.isdigit() else i for i in chord_type.split(
                        '/', 1)[0].split('sort as', 1)[0].strip('[]').split(
                            'omit', 1)[1].replace(' ', '').split(',')
                ]
        if 'sort as' in chord_type:
            if chord_speciality != 'polychord':
                other_msg['voicing'] = [
                    int(i) for i in chord_type.split(
                        '/', 1)[0].strip('[]').split('sort as', 1)[1].replace(
                            ' ', '').strip('[]').split(',')
                ]
        try:
            alter_notes = chord_type.split('/', 1)[0].split(
                'sort as',
                1)[0].strip('[]').split(' ', 1)[1].replace(' ', '').split(',')
        except:
            alter_notes = None
        if alter_notes:
            other_msg['altered'] = []
            for each in alter_notes:
                if each and each[0] in ['#', 'b']:
                    other_msg['altered'].append(each)
            if not other_msg['altered']:
                other_msg['altered'] = None
        if has_split:
            inversion_split = chord_type.split('/')
            first_part = inversion_split[0].replace(',', '')
            if first_part[0] == '[':
                current_type = first_part[1:-1].split(' ')
            else:
                current_type = first_part.split(' ')
            current_type = [i for i in current_type if i]
            if len(current_type) > 1 and current_type[1][0] in ['#', 'b']:
                chord_types_root = ','.join(current_type)
                if len(inversion_split) > 1:
                    chord_type = '/'.join(
                        [chord_types_root, inversion_split[1]])
            else:
                chord_types_root = current_type[0]
        else:
            chord_types_root = chord_type.split(' ')[0]
        note_names = self.names()
        note_names.sort(key=lambda s: len(s), reverse=True)
        for each in note_names:
            each_standard = f"{each[0].upper()}{''.join(each[1:])}"
            if each_standard in chord_types_root:
                root_note = each
                break
            elif each_standard in database.standard_dict and database.standard_dict[
                    each_standard] in chord_types_root:
                root_note = each
                break
        if has_split:
            try:
                inversion_msg = mp.alg.inversion_from(mp.C(chord_type),
                                                      mp.C(chord_types_root),
                                                      num=True)
                if 'could not get chord' in inversion_msg:
                    if inversion_split[1][0] == '[':
                        chord_type = original_chord_type
                        chord_types_root = chord_type
                    else:
                        first_part, second_part = chord_type.split('/', 1)
                        if first_part[0] == '[':
                            first_part = first_part[1:-1]
                        chord_speciality = self._get_chord_speciality_helper(
                            first_part)
                        other_msg['non-chord bass note'] = second_part
            except:
                if 'omit' in first_part and first_part[0] != '[':
                    temp_ind = first_part.index(' ')
                    current_chord_types_root = first_part[:
                                                          temp_ind] + ',' + first_part[
                                                              temp_ind:]
                else:
                    current_chord_types_root = chord_types_root
                try:
                    inversion_msg = mp.alg.inversion_from(
                        self, mp.C(current_chord_types_root), num=True)
                    if 'could not get chord' in inversion_msg:
                        if inversion_split[1][0] == '[':
                            chord_type = original_chord_type
                            chord_types_root = chord_type
                        else:
                            first_part, second_part = chord_type.split('/', 1)
                            if first_part[0] == '[':
                                first_part = first_part[1:-1]
                            chord_speciality = self._get_chord_speciality_helper(
                                first_part)
                            other_msg['non-chord bass note'] = second_part
                except:
                    chord_type = original_chord_type
                    chord_types_root = chord_type
                    if chord_speciality == 'inverted chord':
                        inversion_msg = None
        if other_msg['altered']:
            chord_types_root = chord_types_root.split(',')[0]
            chord_type = original_chord_type
        root_note = database.standard_dict.get(root_note, root_note)
        if chord_speciality == 'polychord' or (chord_speciality
                                               == 'inverted chord'
                                               and inversion_msg is None):
            chord_type_name = chord_type
        else:
            chord_type_name = chord_types_root[len(root_note):]
        if get_dict:
            return {
                'type':
                'chord',
                'chord name':
                chord_type,
                'root position':
                chord_types_root,
                'root':
                root_note,
                'chord type':
                chord_type_name,
                'chord speciality':
                chord_speciality,
                'inversion':
                inversion_msg
                if chord_speciality == 'inverted chord' else None,
                'other':
                other_msg
            }
        else:
            other_msg_str = '\n'.join(
                [f'{i}: {j}' for i, j in other_msg.items() if j])
            return f"chord name: {chord_type}\nroot position: {chord_types_root}\nroot: {root_note}\nchord type: {chord_type_name}\nchord speciality: {chord_speciality}" + (
                f"\ninversion: {inversion_msg}" if chord_speciality
                == 'inverted chord' else '') + (f'\n{other_msg_str}'
                                                if other_msg_str else '')

    def get_chord_speciality(self, mode=0, **kwargs):
        info = self.info(get_dict=True, **kwargs)
        if mode == 0:
            return info['chord speciality']
        elif mode == 1:
            return info['chord speciality'], info['other']

    def get_chord_root(self, **kwargs):
        return self.info(get_dict=True, **kwargs)['root']

    def _get_chord_speciality_helper(self, chord_type):
        if '/' in chord_type:
            has_split = True
            if chord_type[0] == '[':
                chord_speciality = 'polychord'
            elif 'top' in chord_type:
                chord_speciality = 'chord voicings'
            else:
                chord_speciality = 'inverted chord'
        elif 'sort as' in chord_type:
            chord_speciality = 'chord voicings'
        else:
            alter_notes = chord_type.split(' ')
            if len(alter_notes) > 1 and alter_notes[1][0] in ['#', 'b']:
                chord_speciality = 'altered chord'
            else:
                chord_speciality = 'root position'
        return chord_speciality

    def same_accidentals(self, mode='#'):
        temp = copy(self)
        for each in temp.notes:
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
        if all(x.degree <= i.degree <= y.degree for i in self.notes
               if isinstance(i, note)):
            return self, 0
        temp = self.copy()
        available_inds = [
            k for k in range(len(temp))
            if not (isinstance(temp.notes[k], note)
                    and not (x.degree <= temp.notes[k].degree <= y.degree))
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
            return self[0] + interval

    def note_interval(self, current_note, mode=0):
        if isinstance(current_note, str):
            if not any(i.isdigit() for i in current_note):
                current_note = mp.to_note(current_note)
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
                     root_lower=False,
                     standardize=True):
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
            root_note_step = database.standard2[
                root_note.name] - database.standard2[other_root_note.name]
            root_note_steps = [abs(root_note_step), 12 - abs(root_note_step)]
            nearest_step = min(root_note_steps)
            if root_lower:
                if root_note_step < 0:
                    root_note = other_root_note + root_note_step
                else:
                    root_note = other_root_note - root_note_steps[1]
            else:
                if nearest_step == root_note_steps[0]:
                    root_note = other_root_note + root_note_step
                else:
                    if root_note_step < 0:
                        root_note = other_root_note + root_note_steps[1]
                    else:
                        root_note = other_root_note - root_note_steps[1]
            remain_notes = []
            for each in temp.notes[1:]:
                note_steps = [
                    database.standard2[each.name] - database.standard2[i.name]
                    for i in other.notes[1:]
                ]
                note_steps_path = [
                    min([abs(i), 12 - abs(i)]) for i in note_steps
                ]
                most_near_note_steps = min(note_steps_path)
                most_near_note = other.notes[note_steps_path.index(
                    most_near_note_steps)]
                current_step = database.standard2[
                    each.name] - database.standard2[most_near_note.name]
                current_steps = [abs(current_step), 12 - abs(current_step)]
                if most_near_note_steps == current_steps[0]:
                    new_note = most_near_note + current_step
                else:
                    if current_step < 0:
                        new_note = most_near_note + current_steps[1]
                    else:
                        new_note = most_near_note - current_steps[1]
                remain_notes.append(new_note)
            remain_notes.insert(0, root_note)
            temp.notes = remain_notes
            temp = temp.sortchord()
            temp = temp.set(duration=original_duration, volume=original_volume)
            if temp[0].name != root_note.name:
                temp[0] += database.octave * (
                    (12 -
                     (temp[0].degree - root_note.degree)) // database.octave)
                temp = temp.sortchord()
            return temp
        else:
            remain_notes = []
            for each in temp.notes:
                note_steps = [
                    database.standard2[each.name] - database.standard2[i.name]
                    for i in other.notes
                ]
                note_steps_path = [
                    min([abs(i), 12 - abs(i)]) for i in note_steps
                ]
                most_near_note_steps = min(note_steps_path)
                most_near_note = other.notes[note_steps_path.index(
                    most_near_note_steps)]
                current_step = database.standard2[
                    each.name] - database.standard2[most_near_note.name]
                current_steps = [abs(current_step), 12 - abs(current_step)]
                if most_near_note_steps == current_steps[0]:
                    new_note = most_near_note + current_step
                else:
                    if current_step < 0:
                        new_note = most_near_note + current_steps[1]
                    else:
                        new_note = most_near_note - current_steps[1]
                remain_notes.append(new_note)
            temp.notes = remain_notes
            temp = temp.sortchord()
            temp = temp.set(duration=original_duration, volume=original_volume)
            return temp

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
        for each in self.notes:
            if isinstance(each, (tempo, pitch_bend)):
                if each.start_time is not None:
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
        if reset_pitch_bend or reset_note:
            for i in self.notes:
                if isinstance(i, pitch_bend) and reset_pitch_bend:
                    i.channel = channel
                elif isinstance(i, note) and reset_note:
                    i.channel = channel

    def reset_track(self, track, reset_msg=True, reset_pitch_bend=True):
        if reset_msg:
            for i in self.other_messages:
                i.track = track
        if reset_pitch_bend:
            for i in self.notes:
                if isinstance(i, pitch_bend):
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
        available_inds = [
            i for i, each in enumerate(self.notes)
            if not (isinstance(each, (tempo, pitch_bend))
                    and each.track == current_ind)
        ]
        self.notes = [self.notes[i] for i in available_inds]
        self.interval = [self.interval[i] for i in available_inds]
        for i in self.notes:
            if isinstance(i, (tempo, pitch_bend)
                          ) and i.track is not None and i.track > current_ind:
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


class scale:

    def __init__(self, start=None, mode=None, interval=None, notes=None):
        self.interval = interval
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
            self.interval = self.get_interval()
        if mode is None:
            current_mode = mp.alg.detect_scale_type(self.interval,
                                                    mode='interval')
            if current_mode != 'not found':
                self.mode = current_mode

    def set_mode_name(self, name):
        self.mode = name

    def change_interval(self, interval):
        self.interval = interval

    def __repr__(self):
        return f'[scale]\nscale name: {self.start} {self.mode} scale\nscale intervals: {self.get_interval()}\nscale notes: {self.get_scale().notes}'

    def __eq__(self, other):
        return type(other) is scale and self.notes == other.notes

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

    def __call__(self, n, duration=0.25, interval=0, num=3, step=2):
        if isinstance(n, int):
            return self.pickchord_by_degree(n, duration, interval, num, step)
        elif isinstance(n, str):
            altered_notes = n.replace(' ', '').split(',')
            notes = copy(self.notes)
            for each in altered_notes:
                if each.startswith('#'):
                    current_ind = int(each.split('#')[1]) - 1
                    notes[current_ind] = notes[current_ind].up()
                elif each.startswith('b'):
                    current_ind = int(each.split('b')[1]) - 1
                    notes[current_ind] = notes[current_ind].down()
            return scale(notes=notes)

    def get_interval(self):
        if self.mode is None:
            if self.interval is None:
                if self.notes is None:
                    raise ValueError(
                        'a mode or interval or notes list should be settled')
                else:
                    notes = self.notes
                    rootdegree = notes[0].degree
                    return [
                        notes[i].degree - notes[i - 1].degree
                        for i in range(1, len(notes))
                    ]
            else:
                return self.interval
        else:
            if self.interval is not None:
                return self.interval
            mode = self.mode.lower()
            result = database.scaleTypes[mode]
            if result != 'not found':
                return result
            else:
                if self.notes is None:
                    raise ValueError('could not find this scale')
                else:
                    notes = self.notes
                    rootdegree = notes[0].degree
                    return [
                        notes[i].degree - notes[i - 1].degree
                        for i in range(1, len(notes))
                    ]

    def get_scale(self, intervals=0.25, durations=None):
        if self.mode == None:
            if self.interval == None:
                raise ValueError(
                    'at least one of mode or interval in the scale should be settled'
                )
            else:
                result = [self.start]
                count = self.start.degree
                for t in self.interval:
                    count += t
                    result.append(mp.degree_to_note(count))
                return chord(result, duration=durations, interval=intervals)
        else:
            result = [self.start]
            count = self.start.degree
            interval1 = self.get_interval()
            if isinstance(interval1, str):
                raise ValueError('cannot find this scale')
            for t in interval1:
                count += t
                result.append(mp.degree_to_note(count))
            return chord(result, duration=durations, interval=intervals)

    def __len__(self):
        return len(self.notes)

    def names(self):
        temp = [x.name for x in self.notes]
        result = []
        for i in temp:
            if i not in result:
                result.append(i)
        return result

    def pickchord_by_degree(self,
                            degree1,
                            duration=0.25,
                            interval=0,
                            num=3,
                            step=2):
        result = []
        high = False
        if degree1 == 7:
            degree1 = 0
            high = True
        temp = copy(self)
        scale_notes = temp.notes[:-1]
        for i in range(degree1, degree1 + step * num, step):
            result.append(scale_notes[i % 7])
        resultchord = chord(result,
                            rootpitch=temp[0].num,
                            interval=interval,
                            duration=duration).standardize()
        if high:
            resultchord = resultchord.up(database.octave)
        return resultchord

    def pickdegree(self, degree1):
        return self[degree1]

    def pattern(self, indlist, duration=0.25, interval=0, num=3, step=2):
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

    def leading7_chord(self):
        return chord(
            [self[6].down(database.octave), self[1], self[3], self[5]])

    def scalefrom(self, degree=5, mode=None, interval=None):
        # default is pick the dominant mode of the scale
        if mode is None and interval is None:
            mode, interval = self.mode, self.interval
        return scale(self[degree], mode, interval)

    def secondary_dom(self, degree=5):
        newscale = self.scalefrom(degree, self.mode, self.interval)
        return newscale.dom_chord()

    def secondary_dom7(self, degree=5):
        return self.scalefrom(degree, self.mode, self.interval).dom7_chord()

    def secondary_leading7(self, degree=5):
        return self.scalefrom(degree, self.mode,
                              self.interval).leading7_chord()

    def pickchord_by_index(self, indlist):
        return chord([self[i] for i in indlist])

    def __matmul__(self, indlist):
        return self.pickchord_by_index(indlist)

    def detect(self):
        return mp.alg.detect_scale_type(self)

    def get_allchord(self, duration=None, interval=0, num=3, step=2):
        return [
            self.pickchord_by_degree(i,
                                     duration=duration,
                                     interval=interval,
                                     num=num,
                                     step=step)
            for i in range(len(self.get_interval()) + 1)
        ]

    def relative_key(self):
        if self.mode == 'major':
            return scale(self[5], 'minor')
        elif self.mode == 'minor':
            return scale(self[2], 'major')
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

    def get(self, degree):
        return self[degree]

    def get_chord(self, degree, chord_type=None, natural=False):
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
                return f'{degree} is not a valid roman numerals chord representation'
        current_degree = database.roman_numerals_dict[degree]
        if current_degree == 'not found':
            return f'{degree} is not a valid roman numerals chord representation'
        current_note = self[current_degree].name
        if natural:
            temp = mp.C(current_note + chord_type)
            if not isinstance(temp, chord):
                return f'{chord_type} is not a valid chord type'
            length = len(temp)
            return self.pickchord_by_degree(current_degree, num=length)
        if degree.islower():
            current_note += 'm'
        current_chord_type = current_note + chord_type
        return mp.C(current_chord_type)

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

    def play(self, intervals=0.25, durations=None, *args, **kwargs):
        mp.play(self.get_scale(intervals, durations), *args, **kwargs)

    def __add__(self, obj):
        if isinstance(obj, int):
            return self.up(obj)
        elif isinstance(obj, tuple):
            return self.up(*obj)

    def __sub__(self, obj):
        if isinstance(obj, int):
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
                current_degree = database.roman_numerals_dict[
                    current_degree_name] - 1
                if current_degree == 'not found':
                    return f'{current_chord} is not a valid roman numerals chord representation'
                current_note = self[current_degree].name
                if current_degree_name.islower():
                    current_note += 'm'
                chords[k] = current_note + current_chord[1]
            else:
                found = False
                current_degree = None
                for each in current_keys:
                    for i in each:
                        if current_chord.startswith(i):
                            found = True
                            current_degree = database.roman_numerals_dict[i] - 1
                            current_note = self[current_degree].name
                            if i.islower():
                                current_note += 'm'
                            chords[k] = current_note + current_chord[len(i):]
                            break
                    if found:
                        break
                if not found:
                    return f'{current_chord} is not a valid roman numerals chord representation'
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


class circle_of_fifths:
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
    outer = list(reversed(circle_of_fifths.outer))
    outer.insert(0, outer.pop())
    inner = list(reversed(circle_of_fifths.inner))
    inner.insert(0, inner.pop())

    def __init__(self):
        pass

    def __repr__(self):
        return f'[circle of fourths]\nouter circle: {self.outer}\ninner circle: {self.inner}\ndirection: clockwise'


class piece:

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
                 sampler_channels=None):
        self.tracks = tracks
        if instruments is None:
            self.instruments = [
                database.reverse_instruments[1]
                for i in range(len(self.tracks))
            ]
            self.instruments_numbers = [
                database.INSTRUMENTS[j] for j in self.instruments
            ]
        else:
            self.instruments = [
                database.reverse_instruments[i] if isinstance(i, int) else i
                for i in instruments
            ]
            self.instruments_numbers = [
                database.INSTRUMENTS[j] for j in self.instruments
            ]
        self.bpm = bpm
        self.start_times = start_times
        self.track_number = len(tracks)
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
        self.sampler_channels = sampler_channels

    def __repr__(self):
        return (
            f'[piece] {self.name if self.name else ""}\n'
        ) + f'BPM: {round(self.bpm, 3)}\n' + '\n'.join([
            f'track {i+1}{" channel " + str(self.channels[i]) if self.channels else ""} {self.track_names[i] + " " if self.track_names and self.track_names[i] else ""}| instrument: {self.instruments[i]} | start time: {self.start_times[i]} | {self.tracks[i]}'
            for i in range(len(self.tracks))
        ])

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
            channel=self.channels[i] if self.channels else None,
            track_name=self.track_names[i] if self.track_names else None,
            pan=self.pan[i],
            volume=self.volume[i],
            bpm=self.bpm,
            name=self.name,
            sampler_channel=self.sampler_channels[i]
            if self.sampler_channels else None)

    def __delitem__(self, i):
        del self.tracks[i]
        del self.instruments[i]
        del self.instruments_numbers[i]
        del self.start_times[i]
        if self.track_names:
            del self.track_names[i]
        if self.channels:
            del self.channels[i]
        del self.pan[i]
        del self.volume[i]
        if self.sampler_channels:
            del self.sampler_channels[i]
        self.track_number -= 1

    def __setitem__(self, i, new_track):
        self.tracks[i] = new_track.content
        self.instruments[i] = new_track.instrument
        self.instruments_numbers[i] = new_track.instruments_number
        self.start_times[i] = new_track.start_time
        if self.track_names and new_track.track_name:
            self.track_names[i] = new_track.track_name
        if self.channels and new_track.channel is not None:
            self.channels[i] = new_track.channel
        if new_track.pan:
            self.pan[i] = new_track.pan
        if new_track.volume:
            self.volume[i] = new_track.volume
        if self.sampler_channels and new_track.sampler_channel is not None:
            self.sampler_channels[i] = new_track.sampler_channel

    def __len__(self):
        return len(self.tracks)

    def mute(self, i=None):
        if not hasattr(self, 'muted_msg'):
            self.muted_msg = [each.get_volume() for each in self.tracks]
        if i is None:
            for k in range(len(self.tracks)):
                self.tracks[k].setvolume(0)
        else:
            self.tracks[i].setvolume(0)

    def unmute(self, i=None):
        if not hasattr(self, 'muted_msg'):
            return
        if i is None:
            for k in range(len(self.tracks)):
                self.tracks[k].setvolume(self.muted_msg[k])
        else:
            self.tracks[i].setvolume(self.muted_msg[i])

    def append(self, new_track):
        if not isinstance(new_track, track):
            raise ValueError('must be a track type to be appended')
        self.tracks.append(new_track.content)
        self.instruments.append(new_track.instrument)
        self.instruments_numbers.append(new_track.instruments_number)
        self.start_times.append(new_track.start_time)
        if self.channels:
            if new_track.channel:
                self.channels.append(new_track.channel)
            else:
                self.channels.append(max(self.channels) + 1)
        if self.track_names:
            if new_track.track_name:
                self.track_names.append(new_track.track_name)
            else:
                self.track_names.append(
                    new_track.name if new_track.
                    name is not None else f'track {self.track_number+1}')
        self.pan.append(new_track.pan if new_track.pan else [])
        self.volume.append(new_track.volume if new_track.volume else [])
        if self.sampler_channels:
            if new_track.sampler_channel:
                self.sampler_channels.append(new_track.sampler_channel)
            else:
                self.sampler_channels.append(0)
        self.track_number += 1

    def insert(self, i, new_track):
        if not isinstance(new_track, track):
            raise ValueError('must be a track type to be inserted')
        self.tracks.insert(i, new_track.content)
        self.instruments.insert(i, new_track.instrument)
        self.instruments_numbers.insert(i, new_track.instruments_number)
        self.start_times.insert(i, new_track.start_time)
        if self.channels:
            if new_track.channel:
                self.channels.insert(i, new_track.channel)
            else:
                self.channels.insert(i, max(self.channels) + 1)
        if self.track_names:
            if new_track.track_name:
                self.track_names.insert(i, new_track.track_name)
            else:
                self.track_names.insert(
                    i, new_track.name if new_track.name is not None else
                    f'track {self.track_number+1}')
        self.pan.insert(i, new_track.pan if new_track.pan else [])
        self.volume.insert(i, new_track.volume if new_track.volume else [])
        if self.sampler_channels:
            if new_track.sampler_channel:
                self.sampler_channels.insert(i, new_track.sampler_channel)
            else:
                self.sampler_channels.insert(i, 0)
        self.track_number += 1

    def up(self, n=1, mode=0):
        temp = copy(self)
        for i in range(temp.track_number):
            if mode == 0 or (mode == 1 and
                             not (temp.channels and temp.channels[i] == 9)):
                temp.tracks[i] += n
        return temp

    def down(self, n=1, mode=0):
        temp = copy(self)
        for i in range(temp.track_number):
            if mode == 0 or (mode == 1 and
                             not (temp.channels and temp.channels[i] == 9)):
                temp.tracks[i] -= n
        return temp

    def __mul__(self, n):
        temp = copy(self)
        whole_length = temp.bars()
        for i in range(temp.track_number):
            current = temp.tracks[i]
            counter = 0
            for j in range(len(current) - 1, -1, -1):
                current_note = current.notes[j]
                if isinstance(current_note, note):
                    current.interval[j] = current.notes[j].duration
                    counter = j
                    break
            current_start_time = temp.start_times[i]
            current.interval[counter] += (whole_length - current.bars() -
                                          current_start_time)
            for k in range(n - 1):
                unit = copy(current)
                if current_start_time:
                    for j in range(len(current) - 1, -1, -1):
                        current_note = current.notes[j]
                        if isinstance(current_note, note):
                            current.interval[j] += current_start_time
                            break
                for each in unit.notes:
                    if isinstance(each, (tempo, pitch_bend)):
                        if each.start_time is not None:
                            each.start_time += (k + 1) * whole_length
                current.notes += unit.notes
                current.interval += unit.interval
            temp.tracks[i] = current
        return temp

    def __or__(self, n):
        if isinstance(n, piece):
            return self + n

    def __and__(self, n):
        if isinstance(n, tuple):
            n, start_time = n
        else:
            start_time = 0
        return self.merge_track(n, mode='head', start_time=start_time)

    def __add__(self, n):
        if isinstance(n, int):
            return self.up(n)
        elif isinstance(n, piece):
            return self.merge_track(n, mode='after')
        elif isinstance(n, tuple):
            return self.up(*n)

    def __sub__(self, n):
        if isinstance(n, int):
            return self.down(n)
        elif isinstance(n, tuple):
            return self.down(*n)

    def __neg__(self):
        return self.down()

    def __pos__(self):
        return self.up()

    def __call__(self, ind):
        return self.tracks[ind]

    def merge_track(self, n, mode='after', start_time=0):
        temp = copy(self)
        temp2 = copy(n)
        if temp.channels is not None:
            free_channel_numbers = [
                i for i in range(16) if i not in temp.channels
            ]
            counter = 0
        if mode == 'after':
            start_time = temp.bars()
        for i in range(len(temp2)):
            current_instrument_number = temp2.instruments_numbers[i]
            if current_instrument_number in temp.instruments_numbers:
                current_ind = temp.instruments_numbers.index(
                    current_instrument_number)
                current_track = temp2.tracks[i]
                for each in current_track:
                    if isinstance(each, (tempo, pitch_bend)):
                        if each.start_time is not None:
                            each.start_time += start_time
                current_start_time = temp2.start_times[
                    i] + start_time - temp.start_times[current_ind]
                temp.tracks[current_ind] &= (current_track, current_start_time)
                if current_start_time < 0:
                    temp.start_times[current_ind] += current_start_time
            else:
                current_instrument = temp2.instruments[i]
                temp.instruments.append(current_instrument)
                temp.instruments_numbers.append(current_instrument_number)
                current_start_time = temp2.start_times[i]
                current_start_time += start_time
                current_track = temp2.tracks[i]
                for each in current_track:
                    if isinstance(each, (tempo, pitch_bend)):
                        if each.start_time is not None:
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
        temp.track_number = len(temp.tracks)
        return temp

    def add_pitch_bend(self,
                       value,
                       start_time=0,
                       channel='all',
                       track=0,
                       mode='cents',
                       ind=None):
        if channel == 'all':
            for i in range(len(self.tracks)):
                current_channel = self.channels[
                    i] if self.channels is not None else i
                self.tracks[i] += chord([
                    pitch_bend(value, start_time, current_channel, track, mode)
                ])
        else:
            current_channel = self.channels[
                channel] if self.channels is not None else channel
            if ind is not None:
                self.tracks[channel].insert(
                    ind,
                    pitch_bend(value, start_time, current_channel, track,
                               mode))
            else:
                self.tracks[channel] += chord([
                    pitch_bend(value, start_time, current_channel, track, mode)
                ])

    def add_tempo_change(self, bpm, start_time=None, ind=None, track_ind=None):
        if ind is not None and track_ind is not None:
            self.tracks[track_ind].insert(ind, tempo(bpm, start_time))
        else:
            self.tracks[0] += chord([tempo(bpm, start_time)])

    def clear_pitch_bend(self, ind='all', value=0, cond=None):
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
                                   for i in each if isinstance(i, tempo)):
            self.clear_tempo()
            return
        temp = copy(self)
        original_bpm = None
        if bpm != self.bpm and not any(
                isinstance(i, tempo) for each in self.tracks for i in each):
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

    def get_tempo_changes(self):
        temp = copy(self)
        tempo_changes = []
        for each in temp.tracks:
            inds = [
                i for i in range(len(each))
                if isinstance(each.notes[i], tempo)
            ]
            notes = [each.notes[i] for i in inds]
            no_time = [k for k in inds if each.notes[k].start_time is None]
            for k in no_time:
                current_time = each[:k].bars()
                current = each.notes[k]
                current.start_time = current_time
            tempo_changes += notes
        tempo_changes.sort(key=lambda s: s.start_time)
        return chord(tempo_changes)

    def get_pitch_bend(self, ind=0):
        if ind == 'all':
            return mp.concat(
                [self.get_pitch_bend(i) for i in range(len(self))])
        temp = copy(self)
        if ind == 'all':
            return mp.concat(
                [self.get_pitch_bend(k) for k in range(len(self.tracks))])
        each = temp.tracks[ind]
        inds = [
            i for i in range(len(each))
            if isinstance(each.notes[i], pitch_bend)
        ]
        pitch_bend_changes = [each.notes[i] for i in inds]
        no_time = [k for k in inds if each.notes[k].start_time is None]
        for k in no_time:
            current_time = each[:k].bars()
            current = each.notes[k]
            current.start_time = current_time
        pitch_bend_changes.sort(key=lambda s: s.start_time)
        return chord(pitch_bend_changes)

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
        if self.channels:
            while 9 in self.channels:
                current_ind = self.channels.index(9)
                self.delete_track(current_ind)
        self.delete_channel(9)

    def get_off_not_notes(self):
        j = 0
        while j < len(self):
            current_track = self.tracks[j]
            if all(not isinstance(k, note) for k in current_track):
                self.delete_track(j)
                continue
            j += 1

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
        tempo_changes = temp.get_tempo_changes()
        temp.clear_tempo()
        if track_names_add_channel and temp.channels:
            for i, each in enumerate(temp.tracks):
                for j in each.other_messages:
                    if j.type == 'track_name':
                        j.channel = temp.channels[i]
        all_tracks = temp.tracks
        length = len(all_tracks)
        track_map_dict = {}
        if temp.channels:
            merge_channels = list(dict.fromkeys(temp.channels))
            merge_length = len(merge_channels)
            if merge_length < length:
                for i in range(merge_length, length):
                    track_map_dict[i] = temp.channels.index(temp.channels[i])
        start_time_ls = temp.start_times
        pitch_bends = mp.concat(
            [i.split(pitch_bend, get_time=True) for i in temp.tracks])
        temp.clear_pitch_bend(value='all')
        sort_tracks_inds = [[i, start_time_ls[i]] for i in range(length)]
        sort_tracks_inds.sort(key=lambda s: s[1])
        first_track_start_time = sort_tracks_inds[0][1]
        first_track_ind = sort_tracks_inds[0][0]
        first_track = all_tracks[first_track_ind]
        for i in sort_tracks_inds[1:]:
            first_track &= (all_tracks[i[0]], i[1] - first_track_start_time)
        first_track += tempo_changes
        first_track += pitch_bends
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
        if track_map_dict:
            for i in first_track.notes:
                if isinstance(i, (tempo, pitch_bend)):
                    if i.track in track_map_dict:
                        current_track = track_map_dict[i.track]
                        i.track = current_track
                        if add_labels:
                            i.track_num = current_track
                else:
                    if add_labels:
                        if i.track_num in track_map_dict:
                            i.track_num = track_map_dict[i.track_num]
            for i in first_track.other_messages:
                if i.track in track_map_dict:
                    i.track = track_map_dict[i.track]
        return first_track, temp.bpm, first_track_start_time

    def add_track_labels(self):
        all_tracks = self.tracks
        length = len(all_tracks)
        for k in range(length):
            for each in all_tracks[k]:
                each.track_num = k

    def reconstruct(self,
                    track,
                    start_time=0,
                    offset=0,
                    correct=False,
                    include_empty_track=False,
                    get_channels=True):
        no_notes = [i for i in track.notes if not isinstance(i, note)]
        track = track.only_notes()
        first_track, first_track_start_time = track, start_time
        length = len(self.tracks)
        start_times_inds = [[
            i for i in range(len(first_track))
            if isinstance(first_track.notes[i], note)
            and first_track.notes[i].track_num == k
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
        new_track_intervals = [[] for k in range(length)]
        whole_length = len(first_track)
        for j in range(whole_length):
            current_note = first_track.notes[j]
            new_track_notes[current_note.track_num].append(current_note)
            new_track_inds[current_note.track_num].append(j)
        whole_interval = first_track.interval
        new_track_intervals = [[
            sum(whole_interval[inds[i]:inds[i + 1]])
            for i in range(len(inds) - 1)
        ] for inds in new_track_inds]
        for i in available_tracks_inds:
            if new_track_inds[i]:
                new_track_intervals[i].append(
                    sum(whole_interval[new_track_inds[i][-1]:]))
        if no_notes:
            for i in range(length):
                current_no_notes = [j for j in no_notes if j.track_num == i]
                new_track_notes[i] += current_no_notes
                new_track_intervals[i] += [
                    0 for k in range(len(current_no_notes))
                ]

        new_tracks = [
            chord(new_track_notes[available_tracks_inds[i]],
                  interval=new_track_intervals[available_tracks_inds[i]],
                  other_messages=available_tracks_messages[i])
            for i in range(len(available_tracks_inds))
        ]
        for j in range(len(available_tracks_inds)):
            new_tracks[j].track_ind = available_tracks_inds[j]
        self.tracks = new_tracks
        self.start_times = [
            int(i) if isinstance(i, float) and i.is_integer() else i
            for i in new_start_times
        ]
        self.instruments = [self.instruments[k] for k in available_tracks_inds]
        self.instruments_numbers = [
            self.instruments_numbers[k] for k in available_tracks_inds
        ]
        if self.track_names:
            self.track_names = [
                self.track_names[k] for k in available_tracks_inds
            ]
        if self.channels:
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
        self.track_number = len(self.tracks)
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

    def cut(self, ind1=0, ind2=None, correct=False):
        merged_result, temp_bpm, start_time = self.merge()
        if ind1 < 0:
            ind1 = 0
        result = merged_result.cut(ind1, ind2, start_time)
        offset = ind1
        temp = copy(self)
        start_time -= ind1
        if start_time < 0:
            start_time = 0
        temp.reconstruct(result, start_time, offset, correct)
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
        tempo_changes = temp.get_tempo_changes()
        temp.clear_tempo()
        k = 0
        while k < len(temp.tracks):
            current = temp.tracks[k]
            if all(not isinstance(i, note) for i in current.notes):
                del temp[k]
                continue
            k += 1
        track_inds = [each.track_ind for each in temp.tracks]
        temp.other_messages = [
            i for i in temp.other_messages if ind1 <= i.start_time < ind2
        ]
        temp.other_messages = [
            i for i in temp.other_messages if i.track in track_inds
        ]
        for each in temp.other_messages:
            each.track = track_inds.index(each.track)
        temp.tracks[0] += tempo_changes
        temp.reset_track([*range(len(temp.tracks))])
        return temp

    def cut_time(self, time1=0, time2=None, bpm=None, start_time=0):
        temp = copy(self)
        temp.normalize_tempo()
        if bpm is not None:
            temp_bpm = bpm
        else:
            temp_bpm = temp.bpm
        bar_left = time1 / ((60 / temp_bpm) * 4)
        bar_right = time2 / (
            (60 / temp_bpm) * 4) if time2 is not None else temp.bars()
        result = temp.cut(bar_left, bar_right)
        return result

    def get_bar(self, n):
        start_time = min(self.start_times)
        return self.cut(n + start_time, n + start_time)

    def firstnbars(self, n):
        start_time = min(self.start_times)
        return self.cut(start_time, n + start_time)

    def bars(self, mode=1, audio_mode=0):
        return max([
            self.tracks[i].bars(start_time=self.start_times[i],
                                mode=mode,
                                audio_mode=audio_mode)
            for i in range(len(self.tracks))
        ])

    def total(self, mode='all'):
        if mode == 'all':
            return sum([len(i) for i in self.tracks])
        elif mode == 'notes':
            return sum([
                len([k for k, each in enumerate(i) if isinstance(each, note)])
                for i in self.tracks
            ])

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
            for each in current_track.notes:
                if isinstance(each, (tempo, pitch_bend)):
                    if each.start_time is not None:
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
                self.instruments_numbers = copy(instruments)
                self.instruments = [
                    database.reverse_instruments[i]
                    for i in self.instruments_numbers
                ]
            elif all(isinstance(i, str) for i in instruments):
                self.instruments = copy(instruments)
                self.instruments_numbers = [
                    database.INSTRUMENTS[i] for i in self.instruments
                ]
            elif any(
                    isinstance(i, list) and all(isinstance(j, int) for j in i)
                    for i in instruments):
                self.instruments_numbers = copy(instruments)
        else:
            if isinstance(instruments, int):
                self.instruments_numbers[ind] = instruments
                self.instruments[ind] = database.reverse_instruments[
                    instruments]
            elif isinstance(instruments, str):
                self.instruments[ind] = instruments
                self.instruments_numbers[ind] = database.INSTRUMENTS[
                    instruments]
            elif isinstance(instruments, list) and all(
                    isinstance(j, int) for j in instruments):
                self.instruments_numbers[ind] = copy(instruments)

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
            if not (mode == 1 and temp.channels and temp.channels[i] == 9):
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
            if reset_pitch_bend or reset_note:
                for each in current_track.notes:
                    if isinstance(each, pitch_bend) and reset_pitch_bend:
                        each.channel = current_channel
                    elif isinstance(each, note) and reset_note:
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
                for each in current_track.notes:
                    if isinstance(each, pitch_bend):
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
    this is a class to change tempo for the notes after it when it is read,
    it can be inserted into a chord, and if the chord is in a piece,
    then it also works for the piece.
    '''

    def __init__(self, bpm, start_time=None, channel=None, track=None):
        self.bpm = bpm
        self.start_time = start_time
        self.degree = 0
        self.duration = 0
        self.volume = 100
        self.channel = channel
        self.track = track

    def __repr__(self):
        attributes = ['bpm', 'start_time', 'channel', 'track']
        result = f'tempo({", ".join([f"{i}={j}" for i, j in self.__dict__.items() if i in attributes])})'
        return result

    def setvolume(self, vol):
        vol = int(vol)
        if vol > 127:
            vol = 127
        self.volume = vol

    def set_channel(self, channel):
        self.channel = channel

    def with_channel(self, channel):
        temp = copy(self)
        temp.channel = channel
        return temp


class pitch_bend:

    def __init__(self,
                 value,
                 start_time=None,
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
        self.degree = 0
        self.duration = 0
        self.volume = 100

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

    def setvolume(self, vol):
        vol = int(vol)
        if vol > 127:
            vol = 127
        self.volume = vol

    def set_channel(self, channel):
        self.channel = channel

    def with_channel(self, channel):
        temp = copy(self)
        temp.channel = channel
        return temp


class track:

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
                 sampler_channel=None):
        self.content = content
        self.instrument = database.reverse_instruments[
            instrument] if isinstance(instrument, int) else instrument
        self.instruments_number = database.INSTRUMENTS[self.instrument]
        self.bpm = bpm
        self.start_time = start_time
        self.track_name = track_name
        self.channel = channel
        self.name = name
        self.pan = pan
        self.volume = volume
        self.sampler_channel = sampler_channel
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
        msg = []
        if self.channel is not None:
            msg.append(f'{"channel " + str(self.channel)}')
        if self.track_name:
            msg.append(self.track_name)
        msg = ' '.join(msg)
        if msg:
            msg += ' | '
        return (f'[track] {self.name if self.name is not None else ""}\n') + (
            f'BPM: {round(self.bpm, 3)}\n' if self.bpm is not None else ""
        ) + f'{msg}instrument: {self.instrument} | start time: {self.start_time} | {self.content}'

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
        if isinstance(i, int):
            return self.up(i)
        else:
            temp = copy(self)
            temp.content += i
            return temp

    def __sub__(self, i):
        if isinstance(i, int):
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
    this is a class to set the pan position for a midi channel,
    it only works in piece class or track class, and must be set as one of the elements
    of the pan list of a piece
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
    this is a class to set the volume for a midi channel,
    it only works in piece class or track class, and must be set as one of the elements
    of the volume list of a piece
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
        return f"[drum] {self.name if self.name else ''}\n{self.notes}"

    def translate(self,
                  pattern,
                  mapping,
                  default_duration=1 / 8,
                  default_interval=1 / 8,
                  default_volume=100,
                  translate_mode=0):
        current_rest_symbol = '0'
        current_continue_symbol = '-'
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
                if symbol_inds:
                    last_symbol_ind = None
                    last_symbol_start_ind = None
                    for ind in symbol_inds:
                        if ind > 0:
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
                            if isinstance(current_symbol, rest_symbol):
                                last_symbol_interval = current_intervals[
                                    last_symbol_start_ind]
                                last_symbol_interval[-1] += current_intervals[
                                    ind][0]
                            elif isinstance(current_symbol, continue_symbol):
                                last_symbol_interval = current_intervals[
                                    last_symbol_start_ind]
                                last_symbol_duration = current_durations[
                                    last_symbol_start_ind]
                                last_symbol_interval[-1] += current_intervals[
                                    ind][0]
                                if current_symbol.mode is None:
                                    if all(k == 0
                                           for k in last_symbol_interval[:-1]):
                                        for j in range(
                                                len(last_symbol_duration)):
                                            last_symbol_duration[
                                                j] += current_durations[ind][0]
                                    else:
                                        last_symbol_duration[
                                            -1] += current_durations[ind][0]
                                elif current_symbol.mode == 0:
                                    last_symbol_duration[
                                        -1] += current_durations[ind][0]
                                elif current_symbol.mode == 1:
                                    for j in range(len(last_symbol_duration)):
                                        last_symbol_duration[
                                            j] += current_durations[ind][0]
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
                    current_intervals = copy_list(current_intervals,
                                                  current_part_repeat_times)
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
            intervals = copy_list(intervals, global_repeat_times)
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
        current_chord_same_time = False
        current_repeat_times = 1
        current_after_repeat_times = 1
        current_fix_length = None
        current_fix_beats = None
        current_inner_fix_beats = 1
        current_append_durations = [
            default_duration for i in current_append_notes
        ]
        current_append_intervals = [
            default_interval for i in current_append_notes
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
                        new_current_append_notes.append(current_each_note)
            current_append_notes = new_current_append_notes
        custom_durations = False
        for j in current_brackets:
            num_keywords = j.count(':')
            if num_keywords == 1:
                current_bracket_settings = [j.split(':')]
            else:
                current_bracket_settings = [k.split(':') for k in j.split(';')]
            for each_setting in current_bracket_settings:
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
                    current_inner_fix_beats = _process_note(current_content)
                elif current_setting_keyword == 'i':
                    if current_content == '.':
                        current_append_intervals = _process_note(
                            current_content,
                            mode=1,
                            value2=current_append_durations)
                    else:
                        current_append_intervals = _process_note(
                            current_content)
                    if not isinstance(current_append_intervals, list):
                        current_append_intervals = [
                            current_append_intervals
                            for k in current_append_notes
                        ]
                elif current_setting_keyword == 'l':
                    current_append_durations = _process_note(current_content)
                    if not isinstance(current_append_durations, list):
                        current_append_durations = [
                            current_append_durations
                            for k in current_append_notes
                        ]
                        custom_durations = True
                elif current_setting_keyword == 'v':
                    current_append_volumes = _process_note(current_content,
                                                           mode=2)
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
                        new_current_append_notes.extend(
                            current_each_note.notes)
            current_append_notes = new_current_append_notes

        current_append_durations = [
            default_duration
            if not current_part_fix_length_unit else self._apply_dotted_notes(
                current_part_fix_length_unit, k.dotted_num)
            for k in current_append_notes
        ]
        current_append_intervals = [
            default_interval
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
        if '.' in text:
            text, dotted = text.split('.', 1)
            dotted_num = len(dotted) + 1
        if mode == 0:
            result = mp.degree_to_note(mapping[text])
        else:
            result = mp.N(text)
        result.dotted_num = dotted_num
        return result

    def _get_dotted(self, text):
        result = 0
        if isinstance(text, str):
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
        return sum([mp.dotted(1, self._get_dotted(i)) for i in notes])

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rhythm_name = 'rest'


class continue_symbol(beat):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rhythm_name = 'continue'


class rest(rest_symbol):
    pass


class rhythm(list):

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


def _read_notes(note_ls, rootpitch=4):
    intervals = []
    notes_result = []
    start_time = 0
    for each in note_ls:
        if each == '':
            continue
        if isinstance(each, note):
            notes_result.append(each)
        elif isinstance(each, (tempo, pitch_bend)):
            notes_result.append(each)
        elif isinstance(each, rest):
            if not notes_result:
                start_time += each.get_duration()
            elif intervals:
                intervals[-1] += each.get_duration()
        elif isinstance(each, str):
            if each.startswith('tempo'):
                current = [mp.parse_num(k) for k in each.split(';')[1:]]
                current_tempo = tempo(*current)
                notes_result.append(current_tempo)
                intervals.append(0)
            elif each.startswith('pitch'):
                current = each.split(';')[1:]
                length = len(current)
                if length > 2:
                    current = [mp.parse_num(k) for k in current[:2]] + [
                        current[2]
                    ] + [mp.parse_num(k) for k in current[3:]]
                else:
                    current = [mp.parse_num(k) for k in current]
                current_pitch_bend = pitch_bend(*current)
                notes_result.append(current_pitch_bend)
                intervals.append(0)
            else:
                if any(all(i in each for i in j) for j in ['()', '[]', '{}']):
                    split_symbol = '(' if '(' in each else (
                        '[' if '[' in each else '{')
                    notename, info = each.split(split_symbol)
                    volume = 100
                    info = info[:-1].split(';')
                    info_len = len(info)
                    if info_len == 1:
                        duration = _process_note(info[0])
                        if notename != 'r':
                            intervals.append(0)
                    else:
                        if info_len == 2:
                            duration, interval = info
                        else:
                            duration, interval, volume = info
                            volume = mp.parse_num(volume)
                        duration = _process_note(duration)
                        interval = _process_note(
                            interval) if interval != '.' else duration
                        if notename != 'r':
                            intervals.append(interval)
                    if notename == 'r':
                        if not notes_result:
                            start_time += duration
                        elif intervals:
                            intervals[-1] += duration
                    else:
                        notes_result.append(
                            mp.to_note(notename, duration, volume, rootpitch))
                else:
                    if each == 'r':
                        if not notes_result:
                            start_time += 1 / 4
                        elif intervals:
                            intervals[-1] += 1 / 4
                    else:
                        intervals.append(0)
                        notes_result.append(mp.to_note(each, pitch=rootpitch))
        else:
            notes_result.append(each)
    if len(intervals) != len(notes_result):
        intervals = []
    return notes_result, intervals, start_time


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
        for each in all_tracks[k]:
            each.track_num = k

    first_track_ind = start_time_ls.index(first_track_start_time)
    start_time_ls.insert(0, start_time_ls.pop(first_track_ind))

    all_tracks.insert(0, all_tracks.pop(first_track_ind))
    first_track = all_tracks[0]

    for i in range(1, length):
        first_track &= (all_tracks[i],
                        start_time_ls[i] - first_track_start_time)
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
    whole_length = len(first_track)
    for j in range(whole_length):
        current_note = first_track.notes[j]
        new_track_notes[current_note.track_num].append(current_note)
        new_track_inds[current_note.track_num].append(j)
    whole_interval = first_track.interval
    new_track_intervals = [[
        sum(whole_interval[inds[i]:inds[i + 1]]) for i in range(len(inds) - 1)
    ] for inds in new_track_inds]
    for i in range(length):
        if new_track_inds[i]:
            new_track_intervals[i].append(
                sum(whole_interval[new_track_inds[i][-1]:]))
    new_tracks = [
        chord(new_track_notes[k],
              interval=new_track_intervals[k],
              other_messages=[
                  each for each in new_other_messages if each.track == k
              ]) for k in range(length)
    ]
    self.tracks = new_tracks
    self.start_times = new_start_times


def copy_list(current_list, n):
    result = []
    unit = copy(current_list)
    for i in range(n):
        result.extend(copy(unit))
    return result


import musicpy as mp
