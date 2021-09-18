from copy import deepcopy as copy
from .database import *


class note:
    def __init__(self, name, num, duration=0.25, volume=100):
        self.name = name
        self.num = num
        self.degree = standard[name] + 12 * (num + 1)
        self.duration = duration
        volume = int(volume)
        if volume > 127:
            volume = 127
        self.volume = volume

    def __str__(self):
        return f'{self.name}{self.num}'

    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(
            other, note) and self.name == other.name and self.num == other.num

    def __matmul__(self, other):
        return self.name == other.name

    def setvolume(self, vol):
        vol = int(vol)
        if vol > 127:
            vol = 127
        self.volume = vol

    def set(self, duration=0.25, volume=100):
        return note(self.name, self.num, duration, volume)

    def __mod__(self, obj):
        return self.set(*obj)

    def join(self, other, ind, interval):
        if type(other) == str:
            other = toNote(other)
        if type(other) == note:
            return chord([copy(self), copy(other)], interval=interval)
        if type(other) == chord:
            temp = copy(other)
            temp.insert(ind, copy(self))
            temp.interval.insert(ind - 1, interval)
            return temp

    def up(self, unit=1, duration=None, volume=None):
        if duration is None:
            duration = self.duration
        if volume is None:
            volume = self.volume
        return degree_to_note(self.degree + unit, duration, volume)

    def down(self, unit=1, duration=None, volume=None):
        if duration is None:
            duration = self.duration
        if volume is None:
            volume = self.volume
        return degree_to_note(self.degree - unit, duration, volume)

    def __pos__(self):
        return self.up()

    def __neg__(self):
        return self.down()

    def __invert__(self):
        name = self.name
        if name in standard_dict:
            if '#' in name:
                return note(reverse_standard_dict[name], self.num)
            else:
                return note(standard_dict[name], self.num)
        elif name in reverse_standard_dict:
            return note(reverse_standard_dict[name], self.num)
        else:
            return note(name, self.num)

    def play(self, *args, **kwargs):
        import musicpy
        musicpy.play(self, *args, **kwargs)

    def __add__(self, obj):
        if isinstance(obj, int):
            return self.up(obj)
        if not isinstance(obj, note):
            obj = toNote(obj)
        return chord([copy(self), copy(obj)])

    def __sub__(self, obj):
        if isinstance(obj, int):
            return self.down(obj)

    def __call__(self, obj=''):
        import musicpy
        return musicpy.C(self.name + obj, self.num)

    def with_interval(self, interval):
        result = chord([copy(self), self + interval])
        return result

    def getchord_by_interval(start,
                             interval1,
                             duration=0.25,
                             interval=0,
                             cummulative=True):
        import musicpy
        return musicpy.getchord_by_interval(start, interval1, duration,
                                            interval, cummulative)

    def dotted(self, num=1):
        temp = copy(self)
        temp.duration = temp.duration * sum([(1 / 2)**i
                                             for i in range(num + 1)])
        return temp

    def reset_octave(self, num):
        temp = copy(self)
        temp.num = num
        temp.degree = standard[temp.name] + 12 * (temp.num + 1)
        return temp

    def reset_pitch(self, name):
        temp = copy(self)
        temp.name = name
        temp.degree = standard[temp.name] + 12 * (temp.num + 1)
        return temp


def toNote(notename, duration=0.25, volume=100, pitch=4):
    if any(all(i in notename for i in j) for j in ['()', '[]', '{}']):
        split_symbol = '(' if '(' in notename else (
            '[' if '[' in notename else '{')
        notename, info = notename.split(split_symbol)
        info = info[:-1].split(';')
        if len(info) == 1:
            duration = info[0]
        else:
            duration, volume = info[0], eval(info[1])
        if duration[0] == '.':
            duration = 1 / eval(duration[1:])
        else:
            duration = eval(duration)
        return toNote(notename, duration, volume)
    else:
        num_text = ''.join([x for x in notename if x.isdigit()])
        if not num_text.isdigit():
            num = pitch
        else:
            num = int(num_text)
        name = ''.join([x for x in notename if not x.isdigit()])
        return note(name, num, duration, volume)


def trans_note(notename, duration=0.25, volume=100, pitch=4):
    num = ''.join([x for x in notename if x.isdigit()])
    if not num:
        num = pitch
    else:
        num = eval(num)
    name = ''.join([x for x in notename if not x.isdigit()])
    return note(name, num, duration, volume)


def degrees_to_chord(ls, duration=0.25, interval=0):
    return chord([degree_to_note(i) for i in ls],
                 duration=duration,
                 interval=interval)


def degree_to_note(degree, duration=0.25, volume=100):
    name = standard_reverse[degree % 12]
    num = (degree // 12) - 1
    return note(name, num, duration, volume)


def read_notes(note_ls, rootpitch=4):
    intervals = []
    notes_result = []
    for each in note_ls:
        if each == '':
            continue
        if isinstance(each, note):
            notes_result.append(each)
        elif isinstance(each, tempo) or isinstance(each, pitch_bend):
            notes_result.append(each)
        elif isinstance(each, str):
            if each.startswith('tempo'):
                current = each.split(';')[1:]
                if len(current) == 2:
                    current_bpm, current_start_time = current
                else:
                    current_bpm, current_start_time = current[0], None
                if current_bpm[0] == '[':
                    current_bpm = current_bpm[1:-1].split(':')
                    current_bpm = [float(i) for i in current_bpm]
                    current_start_time = current_start_time[1:-1].split(':')
                    current_start_time = [float(i) for i in current_start_time]
                else:
                    current_bpm = float(current_bpm)
                    if current_start_time:
                        current_start_time = float(current_start_time)
                notes_result.append(tempo(current_bpm, current_start_time))
                intervals.append(0)
            elif each.startswith('pitch'):
                current = each.split(';')[1:]
                length = len(current)
                mode = 'cents'
                if length > 1:
                    current_time = current[1]
                    if current_time == 'None':
                        current[1] = None
                    else:
                        current[1] = float(current_time)
                if length > 2:
                    mode = current[2]
                    if mode != 'cents' and mode != 'semitones':
                        current[0] = int(current[0])
                    else:
                        current[0] = float(current[0])
                    if length > 3:
                        current[3] = int(current[3])
                    if length > 4:
                        current[4] = int(current[3])
                    del current[2]
                else:
                    current[0] = float(current[0])
                current_pitch_bend = pitch_bend(*current, mode=mode)
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
                        duration = info[0]
                        if duration[0] == '.':
                            if '.' in duration[1:]:
                                dotted_notes = duration[1:].count('.')
                                duration = duration.replace('.', '')
                                duration = (1 / eval(duration)) * sum([
                                    (1 / 2)**i for i in range(dotted_notes + 1)
                                ])
                            else:
                                duration = 1 / eval(duration[1:])
                        else:
                            if duration[-1] == '.':
                                dotted_notes = duration.count('.')
                                duration = duration.replace('.', '')
                                duration = eval(duration) * sum([
                                    (1 / 2)**i for i in range(dotted_notes + 1)
                                ])
                            else:
                                duration = eval(duration)
                        if notename != 'r':
                            intervals.append(0)
                    else:
                        if info_len == 2:
                            duration, interval = info
                        else:
                            duration, interval, volume = info
                            volume = eval(volume)
                        if duration[0] == '.':
                            if '.' in duration[1:]:
                                dotted_notes = duration[1:].count('.')
                                duration = duration.replace('.', '')
                                duration = (1 / eval(duration)) * sum([
                                    (1 / 2)**i for i in range(dotted_notes + 1)
                                ])
                            else:
                                duration = 1 / eval(duration[1:])
                        else:
                            if duration[-1] == '.':
                                dotted_notes = duration.count('.')
                                duration = duration.replace('.', '')
                                duration = eval(duration) * sum([
                                    (1 / 2)**i for i in range(dotted_notes + 1)
                                ])
                            else:
                                duration = eval(duration)
                        if interval[0] == '.':
                            if len(interval) > 1 and interval[1].isdigit():
                                if '.' in interval[1:]:
                                    dotted_notes = interval[1:].count('.')
                                    interval = interval.replace('.', '')
                                    interval = (1 / eval(interval)) * sum(
                                        [(1 / 2)**i
                                         for i in range(dotted_notes + 1)])
                                else:
                                    interval = 1 / eval(interval[1:])
                            else:
                                interval = eval(
                                    interval.replace('.', str(duration)))
                        else:
                            if interval[-1] == '.':
                                dotted_notes = interval.count('.')
                                interval = interval.replace('.', '')
                                interval = eval(interval) * sum([
                                    (1 / 2)**i for i in range(dotted_notes + 1)
                                ])
                            else:
                                interval = eval(interval)
                        if notename != 'r':
                            intervals.append(interval)
                    if notename == 'r':
                        if intervals:
                            intervals[-1] += duration
                    else:
                        notes_result.append(
                            toNote(notename, duration, volume, rootpitch))
                else:
                    if each == 'r':
                        if intervals:
                            intervals[-1] += 1 / 4
                    else:
                        intervals.append(0)
                        notes_result.append(toNote(each, pitch=rootpitch))
        else:
            notes_result.append(each)
    if len(intervals) != len(notes_result):
        intervals = []
    return notes_result, intervals


def process_dotted_note(value):
    if value[0] != '.':
        dotted_notes = value.count('.')
        value = value.replace('.', '')
        value = eval(value) * sum([(1 / 2)**i
                                   for i in range(dotted_notes + 1)])
    elif len(value) > 1:
        dotted_notes = value[1:].count('.')
        value = value.replace('.', '')
        value = (1 / eval(value)) * sum([(1 / 2)**i
                                         for i in range(dotted_notes + 1)])
    return value


def process_settings(settings):
    length = len(settings)
    if length == 1:
        settings += ['n', 'n']
    elif length == 2:
        settings += ['n']
    if length >= 2 and settings[1] == '.':
        settings[1] = settings[0]
    duration = settings[0]
    interval = settings[1]
    if duration[-1] == '.':
        settings[0] = process_dotted_note(duration)
    elif ',' in duration:
        duration = duration.split(',')
        duration = [
            process_dotted_note(i) if i[-1] == '.' else
            (1 / eval(i[1:]) if i[0] == '.' else eval(i)) for i in duration
        ]
        settings[0] = duration
    elif duration[0] == '.':
        settings[0] = (1 / eval(duration[1:]))
    elif duration == 'n':
        settings[0] = None
    else:
        settings[0] = eval(duration)
    if interval[-1] == '.':
        settings[1] = process_dotted_note(interval)
    elif ',' in interval:
        interval = interval.split(',')
        interval = [
            process_dotted_note(i) if i[-1] == '.' else
            (1 / eval(i[1:]) if i[0] == '.' else eval(i)) for i in interval
        ]
        settings[1] = interval
    elif interval[0] == '.':
        settings[1] = (1 / eval(interval[1:]))
    elif interval == 'n':
        settings[1] = None
    else:
        settings[1] = eval(interval)
    if settings[2] == 'n':
        settings[2] = None
    else:
        settings[2] = eval(settings[2])
    return settings


class chord:
    ''' This class can contain a chord with many notes played simultaneously and either has intervals, the default interval is 0.'''
    def __init__(self,
                 notes,
                 duration=None,
                 interval=None,
                 rootpitch=4,
                 other_messages=[]):
        self.other_messages = other_messages
        standardize_msg = False
        if type(notes) == str:
            notes = notes.replace(' ', '').split(',')
            if all(not any(i.isdigit() for i in j) for j in notes
                   if (not j.startswith('tempo')) and (
                       not j.startswith('pitch'))):
                standardize_msg = True
        elif type(notes) == list and all(type(i) != note
                                         for i in notes) and all(
                                             not any(j.isdigit() for j in i)
                                             for i in notes if type(i) == str):
            standardize_msg = True
        notes_msg = read_notes(notes, rootpitch)
        notes, current_intervals = notes_msg
        if current_intervals and not interval:
            interval = current_intervals
        if standardize_msg and notes:
            root = notes[0]
            notels = [root]
            for i in range(1, len(notes)):
                last_note = notels[i - 1]
                if type(last_note) == note:
                    last = last_note
                current_note = notes[i]
                if type(current_note) != note:
                    notels.append(current_note)
                else:
                    current = note(current_note.name, last.num)
                    if standard[current.name] <= standard[last.name]:
                        current = note(current.name, last.num + 1)
                    notels.append(current)
            notes = notels
        self.notes = notes
        # interval between each two notes one-by-one
        self.interval = [0 for i in range(len(notes))]
        if interval is not None:
            self.changeInterval(interval)
        if duration is not None:
            if isinstance(duration, int) or isinstance(duration, float):
                for t in self.notes:
                    t.duration = duration
            else:
                for k in range(len(duration)):
                    self.notes[k].duration = duration[k]

    def get_duration(self):
        return [i.duration for i in self.notes]

    def get_volume(self):
        return [i.volume for i in self.notes]

    def get_degree(self):
        return [i.degree for i in self]

    def names(self):
        return [i.name for i in self if type(i) == note]

    def __eq__(self, other):
        return isinstance(
            other, chord
        ) and self.notes == other.notes and self.interval == other.interval

    def addnote(self, newnote):
        if isinstance(newnote, note):
            self.notes.append(newnote)
            self.interval.append(self.interval[-1])
        else:
            self.notes.append(toNote(newnote))
            self.interval.append(self.interval[-1])

    def split(self, return_type, get_time=False, sort=False, **args):
        temp = copy(self)
        inds = [
            i for i in range(len(temp)) if type(temp.notes[i]) == return_type
        ]
        notes = [temp.notes[i] for i in inds]
        intervals = [temp.interval[i] for i in inds]
        if get_time and return_type != note:
            no_time = [k for k in inds if temp.notes[k].start_time is None]
            for each in no_time:
                current_time = temp[:each + 1].bars(**args) + 1
                current = temp.notes[each]
                current.start_time = current_time
            if sort:
                notes.sort(key=lambda s: s.start_time)
        return chord(notes, interval=intervals)

    def cut(self, ind1=1, ind2=None, start_time=0, return_inds=False):
        # get parts of notes between two bars
        temp = copy(self)
        start_offset = start_time + 1 - ind1
        if start_offset < 0:
            start_offset = 0
        ind1 -= start_time
        if ind1 < 1:
            ind1 = 1
        if ind2 is not None:
            ind2 -= start_time
            if ind2 <= 1:
                ind2 = 1
        else:
            ind2 = temp.bars(mode=0)

        changes = []
        for i in range(len(temp.notes)):
            each = temp.notes[i]
            if type(each) != note:
                if each.start_time is None:
                    each.start_time = temp[:i + 1].bars(mode=0) + 1
                each.start_time -= (ind1 - 1 + start_time - start_offset)
                if 1 <= each.start_time < ind2 - ind1 + 1:
                    changes.append(each)
        temp = temp.only_notes()

        current_bar = 1
        notes = temp.notes
        intervals = temp.interval
        length = len(notes)
        start_ind = 0
        to_ind = length
        find_start = False
        if ind1 == 1:
            find_start = True
        for i in range(length):
            current_note = notes[i]
            if type(current_note) == note:
                current_bar += intervals[i]
                if (not find_start) and current_bar >= ind1:
                    start_ind = i + 1
                    find_start = True
                    if ind2 is None:
                        break
                elif ind2 and current_bar >= ind2:
                    to_ind = i + 1
                    break
        if not find_start:
            start_ind = to_ind
        if return_inds:
            return start_ind, to_ind
        result = temp[start_ind + 1:to_ind + 1]
        result += chord(changes)

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
        for i in range(length):
            current_note = notes[i]
            if type(current_note) == note:
                current_bar += intervals[i]
                if (not find_start) and (60 / bpm) * current_bar * 4 >= time1:
                    start_ind = i + 1
                    find_start = True
                    if time2 is None:
                        break
                elif time2 and (60 / bpm) * current_bar * 4 >= time2:
                    to_ind = i + 1
                    break
        if not find_start:
            start_ind = to_ind
        if return_inds:
            return start_ind, to_ind
        return self[start_ind + 1:to_ind + 1]

    def last_note_standardize(self):
        for i in range(len(self.notes) - 1, -1, -1):
            current = self.notes[i]
            if type(current) == note:
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
        return self.cut(1, n + 1, start_time)

    def get_bar(self, n, start_time=0):
        return self.cut(n, n + 1, start_time)

    def split_bars(self, start_time=0, **args):
        bars_length = int(self.bars(start_time, **args))
        result = []
        for i in range(1, bars_length + 1):
            result.append(self.cut(i, i + 1, start_time))
        return result

    def count(self, note1, mode='name'):
        if type(note1) == str:
            if any(i.isdigit() for i in note1):
                mode = 'note'
            note1 = toNote(note1)
        if mode == 'name':
            return self.names().count(note1.name)
        elif mode == 'note':
            return self.notes.count(note1)

    def standard_notation(self):
        temp = copy(self)
        for each in temp.notes:
            if type(each) == note and each.name in standard_dict:
                each.name = standard_dict[each.name]
        return temp

    def most_appear(self, choices=None, mode='name', as_standard=False):
        test_obj = self
        if as_standard:
            test_obj = self.standard_notation()
        if not choices:
            return max([i for i in standard2], key=lambda s: test_obj.count(s))
        else:
            choices = [toNote(i) if type(i) == str else i for i in choices]
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
            choices = copy(standard2) if as_standard else copy(standard)
        else:
            choices = [
                toNote(i).anme if type(i) == str else i.name for i in choices
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

    def count_bars(self, ind1, ind2, bars_range=True, **args):
        bars_length = self[ind1:ind2].bars(**args)
        if bars_range:
            start = self[:ind1].bars(**args) + 1
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
                    if not (type(whole_notes[i]) == pitch_bend
                            and whole_notes[i].value == 0)
                ]
            elif value == 'all':
                inds = [
                    i for i in range(length)
                    if type(whole_notes[i]) != pitch_bend
                ]
        else:
            inds = [
                i for i in range(length)
                if not (type(whole_notes[i]) == pitch_bend) or (
                    not cond(whole_notes[i]))
            ]
        self.notes = [whole_notes[k] for k in inds]
        self.interval = [self.interval[k] for k in inds]

    def clear_tempo(self, cond=None):
        length = len(self)
        whole_notes = self.notes
        if cond is None:
            inds = [i for i in range(length) if type(whole_notes[i]) != tempo]
        else:
            inds = [
                i for i in range(length)
                if (type(whole_notes[i]) != tempo) or (
                    not cond(whole_notes[i]))
            ]
        self.notes = [whole_notes[k] for k in inds]
        self.interval = [self.interval[k] for k in inds]

    def __mod__(self, alist):
        types = type(alist)
        if types in [list, tuple]:
            return self.set(*alist)
        elif types == int:
            temp = copy(self)
            for i in range(alist - 1):
                temp //= self
            return temp
        elif types in [str, note]:
            return self.on(alist)

    def standardize(self):
        temp = self.only_notes()
        notenames = temp.names()
        intervals = temp.interval
        durations = temp.get_duration()
        names_standard = [
            standard_dict[i] if i in standard_dict else i for i in notenames
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
                           rootpitch=temp[1].num,
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
        result = chord(copy(self.notes), duration, interval)
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
        result = chord(copy(self.notes), duration, interval)
        result.interval = [
            0 if hasattr(self.notes[i], 'keep_same_time')
            and self.notes[i].keep_same_time else result.interval[i]
            for i in range(len(self))
        ]
        result.setvolume(volume)
        if volume is not None:
            result.setvolume(volume, ind)
        return result

    def changeInterval(self, newinterval):
        if isinstance(newinterval, int) or isinstance(newinterval, float):
            self.interval = [newinterval for i in range(len(self.notes))]
        else:
            if len(newinterval) == len(self.interval):
                self.interval = newinterval
            else:
                return 'please ensure the intervals between notes has the same numbers of the notes'

    def __str__(self):
        return f'{self.notes} with interval {self.interval}'

    def details(self):
        from fractions import Fraction
        notes_only = self.only_notes()
        notes_part = 'notes: ' + ', '.join([
            f"{notes_only.notes[i]}[{Fraction(notes_only.notes[i].duration)};{Fraction(notes_only.interval[i])};{notes_only.notes[i].volume}]"
            for i in range(len(notes_only.notes))
        ])
        tempo_part = 'tempo changes: ' + str(self.split(tempo, get_time=True))
        pitch_bend_part = 'pitch bend changes: ' + str(
            self.split(pitch_bend, get_time=True))
        return '\n'.join([notes_part, tempo_part, pitch_bend_part])

    __repr__ = __str__

    def __contains__(self, note1):
        if not isinstance(note1, note):
            note1 = toNote(note1)
            if note1.name in standard_dict:
                note1.name = standard_dict[note1.name]
        return note1 in self.same_accidentals().notes

    def __add__(self, obj):
        if isinstance(obj, int) or isinstance(obj, list):
            return self.up(obj)
        if isinstance(obj, tuple):
            return self.up(*obj)
        temp = copy(self)
        if isinstance(obj, note):
            temp.notes.append(copy(obj))
            temp.interval.append(temp.interval[-1])
        elif isinstance(obj, str):
            return temp.__add__(toNote(obj))
        elif isinstance(obj, chord):
            obj = copy(obj)
            temp.notes += obj.notes
            temp.interval += obj.interval
        return temp

    def __pos__(self):
        return self.up()

    def __neg__(self):
        return self.down()

    def __invert__(self):
        return self.reverse()

    def __floordiv__(self, obj):
        types = type(obj)
        if types == int or types == float:
            return self.rest(obj)
        elif types == str:
            import musicpy
            obj = musicpy.trans(obj)
        elif types == tuple:
            first = obj[0]
            start = obj[1] if len(obj) == 2 else 0
            if type(first) == int:
                temp = copy(self)
                for k in range(first - 1):
                    temp |= (self, start)
                return temp
            else:
                return self.add(first, start=start, mode='after')
        elif types == list:
            return self.rest(*obj)
        return self.add(obj, mode='after')

    def __or__(self, other):
        return self // other

    def __xor__(self, obj):
        if type(obj) == int:
            return self.inversion_highest(obj)
        if type(obj) == note:
            name = obj.name
        else:
            name = obj
        notenames = self.names()
        if name in notenames and name != notenames[-1]:
            return self.inversion_highest(notenames.index(name) + 1)
        else:
            return self + obj

    def __truediv__(self, obj):
        types = type(obj)
        if types == int:
            if obj > 0:
                return self.inversion(obj)
            else:
                return self.inversion_highest(-obj)
        elif types == list:
            return self.sort(obj)
        else:
            if types != chord:
                if types != note:
                    obj = trans_note(obj)
                notenames = self.names()
                if obj.name not in standard2:
                    obj.name = standard_dict[obj.name]
                if obj.name in notenames and obj.name != notenames[0]:
                    return self.inversion(notenames.index(obj.name))
            return self.on(obj)

    def __and__(self, obj):
        if type(obj) == tuple:
            if len(obj) == 2:
                first = obj[0]
                if type(first) == int:
                    temp = copy(self)
                    for k in range(first - 1):
                        temp &= (self, (k + 1) * obj[1])
                    return temp
                else:
                    return self.add(obj[0], start=obj[1], mode='head')
            else:
                return
        elif type(obj) == int:
            return self & (obj, 0)
        else:
            return self.add(obj, mode='head')

    def __matmul__(self, obj):
        types = type(obj)
        if types == list:
            return self.get(obj)
        elif types == int:
            return self.inv(obj)
        elif types == str:
            return self.inv(self.names().index(obj))
        else:
            import musicpy
            if types == tuple:
                return musicpy.negative_harmony(obj[0], self, *obj[1:])
            else:
                return musicpy.negative_harmony(obj, self)

    def negative_harmony(self, *args, **kwargs):
        import musicpy
        return musicpy.negative_harmony(a=self, *args, **kwargs)

    def __call__(self, obj):
        # deal with the chord's sharp or flat notes, or to omit some notes
        # of the chord.
        temp = copy(self)
        commands = obj.split(',')
        for each in commands:
            each = each.replace(' ', '')
            first = each[0]
            if first in ['#', 'b']:
                degree = each[1:]
                if degree in degree_match:
                    degree_ls = degree_match[degree]
                    found = False
                    for i in degree_ls:
                        current_note = temp[1].up(i)
                        if current_note in temp:
                            ind = temp.notes.index(current_note)
                            temp.notes[ind] = temp.notes[ind].up(
                            ) if first == '#' else temp.notes[ind].down()
                            found = True
                            break
                    if not found:
                        temp += temp[1].up(
                            degree_ls[0]).up() if first == '#' else temp[1].up(
                                degree_ls[0]).down()
                else:
                    if degree in standard:
                        if degree in standard_dict:
                            degree = standard_dict[degree]
                        self_names = [
                            i if i not in standard_dict else standard_dict[i]
                            for i in temp.names()
                        ]
                        if degree in self_names:
                            ind = temp.names().index(degree)
                            temp.notes[ind] = temp.notes[ind].up(
                            ) if first == '#' else temp.notes[ind].down()
            elif each.startswith('omit') or each.startswith('no'):
                degree = each[4:] if each.startswith('omit') else each[2:]
                if degree in degree_match:
                    degree_ls = degree_match[degree]
                    for i in degree_ls:
                        current_note = temp[1].up(i)
                        if current_note in temp:
                            ind = temp.notes.index(current_note)
                            del temp.notes[ind]
                            del temp.interval[ind]
                            break
                else:
                    if degree in standard:
                        if degree in standard_dict:
                            degree = standard_dict[degree]
                        self_names = [
                            i if i not in standard_dict else standard_dict[i]
                            for i in temp.names()
                        ]
                        if degree in self_names:
                            temp = temp.omit(degree, 2)
            elif each.startswith('sus'):
                num = each[3:]
                if num.isdigit():
                    num = int(num)
                else:
                    num = 4
                temp.notes = temp.sus(num).notes
            elif each.startswith('add'):
                degree = each[3:]
                if degree in degree_match:
                    degree_ls = degree_match[degree]
                    temp += temp[1].up(degree_ls[0])
        return temp

    def detect(self, *args, **kwargs):
        import musicpy
        return musicpy.detect(self, *args, **kwargs)

    def get(self, ls):
        result = []
        result_interval = []
        for each in ls:
            if isinstance(each, int):
                result.append(self[each])
                result_interval.append(self.interval[each - 1])
            elif isinstance(each, float):
                num, pitch = [int(j) for j in str(each).split('.')]
                if num > 0:
                    current_note = self[num] + pitch * octave
                else:
                    current_note = self[-num] - pitch * octave
                result.append(current_note)
                result_interval.append(self.interval[num - 1])
        return chord(result, interval=result_interval)

    def pop(self, ind=None):
        if ind is None:
            result = self.notes.pop()
            self.interval.pop()
        else:
            if ind > 0:
                ind -= 1
            result = self.notes.pop(ind)
            self.interval.pop(ind)
        return result

    def __sub__(self, obj):
        if isinstance(obj, int) or isinstance(obj, list):
            return self.down(obj)
        if isinstance(obj, tuple):
            return self.down(*obj)
        if not isinstance(obj, note):
            obj = toNote(obj)
        temp = copy(self)
        if obj in temp:
            ind = temp.notes.index(obj)
            del temp.notes[ind]
            del temp.interval[ind]
        return temp

    def __mul__(self, num):
        temp = copy(self)
        unit = copy(temp)
        for i in range(num - 1):
            temp += unit
        return temp

    def reverse(self, start=None, end=None, cut=False, start_time=0, **args):
        temp = copy(self)
        if start is None:
            temp2 = temp.only_notes()
            intervals = temp2.interval
            durations = temp2.get_duration()
            length = len(temp2)
            bar_length = temp2.bars(**args)
            changes = []
            for i in range(len(temp.notes)):
                each = temp.notes[i]
                if type(each) != note:
                    if each.start_time is None:
                        each.start_time = temp[:i + 1].bars(**args) + 1
                    else:
                        each.start_time -= start_time
                    each.start_time = bar_length - each.start_time + 2
                    changes.append(each)

            last_interval = intervals[-1]
            temp2.interval = [
                durations[length - 1 - i] -
                (durations[length - 2 - i] - intervals[length - 2 - i])
                for i in range(length - 1)
            ]
            temp2.interval.append(last_interval)
            temp2.notes = temp2.notes[::-1]
            temp2 += chord(changes)

            return temp2
        else:
            if end is None:
                result = temp[:start] + temp[start:].reverse(
                    start_time=start_time, **args)
                return result[start:] if cut else result
            else:
                result = temp[:start] + temp[start:end].reverse(
                    start_time=start_time, **args) + temp[end:]
                return result[start:end] if cut else result

    def reverse_chord(self, start_time=0, **args):
        temp = copy(self)
        bar_length = temp.bars(**args)
        temp.notes = temp.notes[::-1]
        temp.interval = temp.interval[::-1]
        temp.interval.append(temp.interval.pop(0))
        for i in temp.notes:
            if type(i) != note:
                if i.start_time is not None:
                    i.start_time = bar_length - (i.start_time - start_time) + 2
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
        return [INTERVAL[x % octave] for x in result]

    def add(self, note1=None, mode='tail', start=0, duration=0.25):
        if len(self) == 0:
            return note1
        temp = copy(self)
        if type(note1) == int:
            temp += temp[1].up(note1)
            return temp
        if len(note1) == 0:
            return temp
        if mode == 'tail':
            return temp + note1
        elif mode == 'head':
            note1 = copy(note1)
            if isinstance(note1, chord):
                inter = note1.interval
            else:
                if isinstance(note1, str):
                    note1 = chord([toNote(note1, duration=duration)])
                elif isinstance(note1, note):
                    note1 = chord([note1])
                elif isinstance(note1, list):
                    note1 = chord(note1)
            # calculate the absolute distances of all of the notes of the chord to add and self,
            # and then sort them, make differences between each two distances
            distance = []
            intervals1 = temp.interval
            intervals2 = note1.interval
            temp.notes[-1].inds = 0
            note1.notes[-1].inds = 1
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
            return chord(newnotes, interval=newinterval)
        elif mode == 'after':
            if self.interval[-1] == 0:
                return (self.rest(0) | start) + note1
            else:
                return (self | start) + note1

    def inversion(self, num=1):
        if num not in range(1, len(self.notes)):
            return 'the number of inversion is out of range of the notes in this chord'
        else:
            temp = copy(self)
            for i in range(num):
                temp.notes.append(temp.notes.pop(0) + octave)
            return temp

    def inv(self, num=1):
        temp = self.copy()
        if type(num) == str:
            return self @ num
        if num not in range(1, len(self.notes)):
            return 'the number of inversion is out of range of the notes in this chord'
        while temp[num + 1].degree >= temp[num].degree:
            temp[num + 1] = temp[num + 1].down(octave)
        temp.insert(1, temp.pop(num + 1))
        return temp

    def sort(self, indlist, rootpitch=None):
        temp = self.copy()
        names = [temp[i].name for i in indlist]
        if rootpitch is None:
            rootpitch = temp[indlist[0]].num
        elif rootpitch == 'same':
            rootpitch = temp[1].num
        new_interval = [temp.interval[i - 1] for i in indlist]
        new_duration = [temp[i].duration for i in indlist]
        return chord(names,
                     rootpitch=rootpitch,
                     interval=new_interval,
                     duration=new_duration)

    def voicing(self, rootpitch=None):
        if rootpitch is None:
            rootpitch = self[1].num
        duration, interval = [i.duration for i in self.notes], self.interval
        notenames = self.names()
        return [
            chord(x, rootpitch=rootpitch).set(duration, interval)
            for x in perm(notenames)
        ]

    def inversion_highest(self, ind):
        if ind in range(1, len(self)):
            temp = self.copy()
            while temp[ind].degree < temp[-1].degree:
                temp[ind] = temp[ind].up(octave)
            temp.notes.append(temp.notes.pop(ind - 1))
            return temp

    def inoctave(self):
        temp = self.copy()
        root = self[1].degree
        for i in range(2, len(temp) + 1):
            while temp[i].degree - root > octave:
                temp[i] = temp[i].down(octave)
        temp.notes.sort(key=lambda x: x.degree)
        return temp

    def on(self, root, duration=0.25, interval=None, each=0):
        temp = copy(self)
        if each == 0:
            if type(root) == chord:
                return root + self
            if type(root) != note:
                root = toNote(root)
                root.duration = duration
            temp.notes.insert(0, root)
            if interval is not None:
                temp.interval.insert(0, interval)
            else:
                temp.interval.insert(0, self.interval[0])
            return temp
        else:
            if type(root) == chord:
                root = list(root)
            else:
                root = [toNote(i) for i in root]
            return [self.on(x, duration, interval) for x in root]

    def up(self, unit=1, ind=None, ind2=None):
        temp = copy(self)
        if type(unit) != int:
            temp.notes = [temp.notes[k].up(unit[k]) for k in range(len(unit))]
            return temp
        if type(ind) != int and ind is not None:
            ind = [i - 1 if i > 0 else i for i in ind]
            temp.notes = [
                temp.notes[i].up(unit) if i in ind else temp.notes[i]
                for i in range(len(temp.notes))
            ]
            return temp
        if ind2 is None:
            if ind is None:
                temp.notes = [
                    degree_to_note(each.degree + unit, each.duration,
                                   each.volume) if type(each) == note else each
                    for each in temp.notes
                ]
            else:
                change_note = temp[ind]
                if type(change_note) == note:
                    temp[ind] = degree_to_note(change_note.degree + unit,
                                               change_note.duration,
                                               change_note.volume)
        else:
            temp.notes = temp.notes[:ind1] + [
                degree_to_note(each.degree + unit, each.duration, each.volume)
                for each in temp.notes[ind1:ind2] if type(each) == note
            ] + temp.notes[ind2:]
        return temp

    def down(self, unit=1, ind=None, ind2=None):
        if type(unit) != int:
            unit = [-i for i in unit]
            return self.up(unit, ind, ind2)
        return self.up(-unit, ind, ind2)

    def drop(self, ind):
        if type(ind) != list:
            ind = [ind]
        if ind:
            if type(ind[0]) == int:
                temp = copy(self)
                ind = [k - 1 for k in ind]
                temp.notes = [
                    temp.notes[k] for k in range(len(temp)) if k not in ind
                ]
                temp.interval = [
                    temp.interval[k] for k in range(len(temp)) if k not in ind
                ]
                return temp
            elif type(ind[0]) == note or (type(ind[0]) == str and any(
                    i for i in ind[0] if i.isdigit())):
                temp = self.same_accidentals()
                ind = chord(ind).same_accidentals().notes
                current_ind = [
                    k + 1 for k in range(len(temp)) if temp.notes[k] in ind
                ]
                return self.drop(current_ind)
            elif type(
                    ind[0]) == str and not any(i
                                               for i in ind[0] if i.isdigit()):
                temp = self.same_accidentals()
                self_notenames = temp.names()
                ind = chord(ind).same_accidentals().names()
                current_ind = [
                    k + 1 for k in range(len(self_notenames))
                    if self_notenames[k] in ind
                ]
                return self.drop(current_ind)
            else:
                return self
        else:
            return self

    def omit(self, ind, mode=0):
        if type(ind) != list:
            ind = [ind]
        if ind and type(ind[0]) == int:
            if mode == 0:
                return self.drop([self.interval_note(i) for i in ind])
            elif mode == 1:
                current_ind = [self.notes[0] + i for i in ind]
                return self.drop(current_ind)
        else:
            return self.drop(ind)

    def sus(self, num=4):
        temp = self.copy()
        first_note = temp[1]
        if num == 4:
            temp.notes = [
                i.up() if abs(i.degree - first_note.degree) %
                octave == major_third else
                i.up(2) if abs(i.degree - first_note.degree) %
                octave == minor_third else i for i in temp.notes
            ]
        elif num == 2:
            temp.notes = [
                i.down(2) if abs(i.degree - first_note.degree) %
                octave == major_third else
                i.down() if abs(i.degree - first_note.degree) %
                octave == minor_third else i for i in temp.notes
            ]
        return temp

    def copy(self):
        return copy(self)

    def __setitem__(self, ind, value):
        if type(value) == str:
            value = toNote(value)
        if type(ind) != slice:
            if ind > 0:
                ind -= 1
        else:
            ind = slice(
                ind.start - 1 if (ind.start and ind.start > 0) else ind.start,
                ind.stop - 1 if (ind.stop and ind.stop > 0) else ind.stop)
        self.notes[ind] = value
        if type(value) == chord:
            self.interval[ind] = value.interval

    def __delitem__(self, ind):
        if type(ind) != slice:
            if ind > 0:
                ind -= 1
        else:
            ind = slice(
                ind.start - 1 if (ind.start and ind.start > 0) else ind.start,
                ind.stop - 1 if (ind.stop and ind.stop > 0) else ind.stop)
        del self.notes[ind]
        del self.interval[ind]

    def index(self, value):
        if type(value) == str:
            if value not in standard:
                value = toNote(value)
                if value not in self:
                    return -1
                return self.notes.index(value) + 1
            else:
                note_names = self.names()
                if value not in note_names:
                    return -1
                return note_names.index(value) + 1
        else:
            return self.index(str(value))

    def remove(self, note1):
        if type(note1) == str:
            note1 = toNote(note1)
        if note1 in self:
            inds = self.notes.index(note1)
            self.notes.remove(note1)
            del self.interval[inds]

    def append(self, value, interval=None):
        if type(value) == str:
            value = toNote(value)
        self.notes.append(value)
        if interval is None:
            interval = self.interval[-1]
        self.interval.append(interval)

    def extend(self, values, intervals=None):
        values = [
            toNote(value) if type(value) == str else value for value in values
        ]
        if intervals is None:
            intervals = self.interval[-1]
        if type(intervals) == int:
            intervals = [intervals for i in range(len(values))]
        self.notes.extend(values)
        self.interval.extend(intervals)

    def delete(self, ind):
        if ind > 0:
            ind -= 1
        del self.notes[ind]
        del self.interval[ind]

    def insert(self, ind, value, interval=None):
        if ind > 0:
            ind -= 1
        if type(value) == chord:
            self.notes[ind:ind] = value.notes
            self.interval[ind:ind] = value.interval
        else:
            if type(value) == str:
                value = toNote(value)
            self.notes.insert(ind, value)
            if interval is None:
                interval = self.interval[-1]
            self.interval.insert(ind, interval)

    def replace(self, ind1, ind2=None, value=None, interval=None):
        if ind1 > 0:
            ind1 -= 1
        if ind2 is None:
            ind2 = ind1 + (len(value) if type(value) == chord else 1)
        if type(value) == chord:
            self.notes[ind1:ind2] = value.notes
            self.interval[ind1:ind2] = value.interval
        else:
            if type(value) == str:
                value = toNote(value)
            self.notes[ind1] = value
            if interval is None:
                interval = self.interval[-1]
            self.interval[ind1] = interval

    def drops(self, ind):
        temp = self.copy()
        dropnote = temp.notes.pop(-ind).down(octave)
        dropinterval = temp.interval.pop(-ind)
        temp.notes.insert(0, dropnote)
        temp.interval.insert(0, dropinterval)
        return temp

    def rest(self, length, dotted=None):
        temp = copy(self)
        last_interval = temp.interval[-1]
        if dotted is not None:
            length = length * sum([(1 / 2)**i for i in range(dotted + 1)])
        if last_interval != 0:
            temp.interval[-1] += length
        else:
            temp.interval[-1] += (temp.notes[-1].duration + length +
                                  last_interval)
        return temp

    def modulation(self, old_scale, new_scale):
        # change notes (including both of melody and chords) in the given piece
        # of music from a given scale to another given scale, and return
        # the new changing piece of music.
        temp = copy(self)
        old_scale_names = [
            i if i not in standard_dict else standard_dict[i]
            for i in old_scale.names()
        ]
        new_scale_names = [
            i if i not in standard_dict else standard_dict[i]
            for i in new_scale.names()
        ]
        number = len(new_scale_names)
        transdict = {
            old_scale_names[i]: new_scale_names[i]
            for i in range(number)
        }
        for k in range(len(temp)):
            current = temp.notes[k]
            if type(current) == note:
                if current.name in standard_dict:
                    current_name = standard_dict[current.name]
                else:
                    current_name = current.name
                if current_name in transdict:
                    temp.notes[k] = toNote(
                        f'{transdict[current_name]}{current.num}',
                        current.duration, current.volume)
        return temp

    def __getitem__(self, ind):
        if isinstance(ind, slice):
            start = ind.start if ind.start is None else (
                ind.start - 1 if ind.start > 0 else len(self) + ind.start)
            stop = ind.stop if ind.stop is None else (
                ind.stop - 1 if ind.stop > 0 else len(self) + ind.stop)
            return self.__getslice__(start, stop)
        temp = copy(self)
        if ind != 0:
            if ind > 0:
                ind -= 1
        return temp.notes[ind]

    def __iter__(self):
        for i in self.notes:
            yield i

    def __getslice__(self, i, j):
        temp = copy(self)
        return chord(temp.notes[i:j],
                     interval=temp.interval[i:j],
                     other_messages=temp.other_messages)

    def __len__(self):
        return len(self.notes)

    def setvolume(self, vol, ind='all'):
        if type(ind) == int:
            each = self.notes[ind - 1]
            each.setvolume(vol)
        elif type(ind) == list:
            if type(vol) == list:
                for i in range(len(ind)):
                    current = ind[i]
                    each = self.notes[current - 1]
                    each.setvolume(vol[i])
            elif type(vol) in [int, float]:
                vol = int(vol)
                for i in range(len(ind)):
                    current = ind[i]
                    each = self.notes[current - 1]
                    each.setvolume(vol)
        elif ind == 'all':
            if type(vol) == list:
                for i in range(len(vol)):
                    current = self.notes[i]
                    current.setvolume(vol[i])
            elif type(vol) in [int, float]:
                vol = int(vol)
                for each in self.notes:
                    each.setvolume(vol)

    def move(self, x):
        # x could be a dict or list of (index, move_steps)
        temp = self.copy()
        if type(x) == dict:
            for i in x:
                temp.notes[i - 1] = temp.notes[i - 1].up(x[i])
            return temp
        if type(x) == list:
            for i in x:
                temp.notes[i[0] - 1] = temp.notes[i[0] - 1].up(i[1])
            return temp

    def play(self, *args, **kwargs):
        import musicpy
        musicpy.play(self, *args, **kwargs)

    def split_melody(self, *args, **kwargs):
        import musicpy
        return musicpy.split_melody(self, *args, **kwargs)

    def split_chord(self, *args, **kwargs):
        import musicpy
        return musicpy.split_chord(self, *args, **kwargs)

    def split_all(self, *args, **kwargs):
        import musicpy
        return musicpy.split_all(self, *args, **kwargs)

    def detect_scale(self, *args, **kwargs):
        import musicpy
        return musicpy.detect_scale(self, *args, **kwargs)

    def detect_in_scale(self, *args, **kwargs):
        import musicpy
        return musicpy.detect_in_scale(self, *args, **kwargs)

    def chord_analysis(self, *args, **kwargs):
        import musicpy
        return musicpy.chord_analysis(self, *args, **kwargs)

    def clear_at(self, duration=0, interval=None, volume=None):
        temp = copy(self)
        i = 1
        while i <= len(temp):
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
            temp.normalize_tempo(tempo_changes[1].bpm)
        result = temp.reverse()
        return result

    def pitch_inversion(self):
        pitch_bend_changes = self.split(pitch_bend, get_time=True)
        temp = self.copy()
        temp.clear_pitch_bend('all')
        tempo_changes = temp.split(tempo)
        if tempo_changes:
            temp.normalize_tempo(tempo_changes[1].bpm)
        volumes = temp.get_volume()
        pitch_intervals = temp.intervalof(cummulative=False)
        import musicpy
        result = musicpy.getchord_by_interval(temp[1],
                                              [-i for i in pitch_intervals],
                                              temp.get_duration(),
                                              temp.interval, False)
        result.setvolume(volumes)
        result += pitch_bend_changes
        return result

    def only_notes(self, audio_mode=0):
        temp = copy(self)
        whole_notes = temp.notes
        intervals = temp.interval
        if audio_mode == 0:
            inds = [
                i for i in range(len(temp)) if type(whole_notes[i]) == note
            ]
        else:
            from pydub import AudioSegment
            inds = [
                i for i in range(len(temp))
                if type(whole_notes[i]) in [note, AudioSegment]
            ]
        temp.notes = [whole_notes[k] for k in inds]
        temp.interval = [intervals[k] for k in inds]
        return temp

    def normalize_tempo(self, bpm, start_time=0):
        # choose a bpm and apply to all of the notes, if there are tempo
        # changes, use relative ratios of the chosen bpms and changes bpms
        # to re-calculate the notes durations and intervals
        tempo_changes = [
            i for i in range(len(self.notes)) if type(self.notes[i]) == tempo
        ]
        if (not tempo_changes) or all(self.notes[i].bpm == bpm
                                      for i in tempo_changes):
            return
        tempo_changes_no_time = [
            k for k in tempo_changes if self.notes[k].start_time is None
        ]
        for each in tempo_changes_no_time:
            current_time = self[:each + 1].bars(mode=0) + 1
            current_tempo = self.notes[each]
            current_tempo.start_time = current_time
        tempo_changes = [self.notes[j] for j in tempo_changes]
        self.clear_tempo()
        tempo_changes.sort(key=lambda s: s.start_time)
        for each in tempo_changes:
            each.start_time -= start_time

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
            (new_tempo_changes[-1].start_time, 1 + self.bars(mode=0),
             new_tempo_changes[-1].bpm))
        whole_notes = self.notes
        intervals = self.interval
        count_length = 1
        for k in range(len(self)):
            current_note = whole_notes[k]
            current_interval = intervals[k]
            current_note_left, current_note_right = count_length, count_length + current_note.duration
            current_interval_left, current_interval_right = count_length, count_length + current_interval
            new_note_duration = 0
            new_interval_duration = 0
            for each in tempo_changes_ranges:
                each_left, each_right, each_tempo = each
                if not (current_note_left >= each_right
                        or current_note_right <= each_left):
                    valid_length = min(current_note_right, each_right) - max(
                        current_note_left, each_left)
                    current_ratio = each_tempo / bpm
                    valid_length /= current_ratio
                    new_note_duration += valid_length

                if not (current_interval_left >= each_right
                        or current_interval_right <= each_left):
                    valid_length = min(current_interval_right,
                                       each_right) - max(
                                           current_interval_left, each_left)
                    current_ratio = each_tempo / bpm
                    valid_length /= current_ratio
                    new_interval_duration += valid_length
            current_note.duration = new_note_duration
            self.interval[k] = new_interval_duration

            count_length += current_interval

    def get_chord_speciality(self, chord_type):
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

    def info(self, alter_notes_show_degree=True, **detect_args):
        import musicpy
        chord_type = self.detect(
            alter_notes_show_degree=alter_notes_show_degree, **detect_args)
        original_chord_type = copy(chord_type)
        other_msg = ''
        has_split = False
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
        if 'omit' in chord_type:
            other_msg += ' (with omitted notes)'
        if has_split:
            inversion_split = chord_type.split('/')
            first_part = inversion_split[0]
            if first_part[0] == '[':
                current_type = first_part[1:-1].split(' ')
            else:
                current_type = first_part.split(' ')
            current_type = [i for i in current_type if i]
            if len(current_type) > 1 and current_type[1][0] in ['#', 'b']:
                other_msg += ' (with altered notes)'
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
            elif each_standard in standard_dict and standard_dict[
                    each_standard] in chord_types_root:
                root_note = each
                break
        if has_split:
            try:
                inversion_msg = musicpy.inversion_from(
                    musicpy.C(chord_type),
                    musicpy.C(chord_types_root),
                    num=True)
            except:
                if 'omit' in first_part and first_part[0] != '[':
                    temp_ind = first_part.index(' ')
                    current_chord_types_root = first_part[:
                                                          temp_ind] + ',' + first_part[
                                                              temp_ind:]
                else:
                    current_chord_types_root = chord_types_root
                try:
                    inversion_msg = musicpy.inversion_from(
                        self, musicpy.C(current_chord_types_root), num=True)
                    if 'could not get chord' in inversion_msg:
                        if inversion_split[1][0] == '[':
                            chord_type = original_chord_type
                            chord_types_root = chord_type
                            other_msg = ''
                        else:
                            other_msg += ' (with a non-chord bass note)'
                            first_part = chord_type.split('/')[0]
                            if first_part[0] == '[':
                                first_part = first_part[1:-1]
                            chord_speciality = self.get_chord_speciality(
                                first_part)
                    else:
                        inversion_num = int(inversion_msg.split(' ')[0])
                        inversion_num = str(inversion_num) + {
                            1: "st",
                            2: "nd",
                            3: "rd"
                        }.get(
                            inversion_num if inversion_num < 20 else
                            inversion_num % 10, "th")
                        inversion_msg = ' '.join([inversion_num] +
                                                 inversion_msg.split(' ')[1:])
                except:
                    chord_type = original_chord_type
                    chord_types_root = chord_type
                    other_msg = ''

        else:
            if chord_speciality == 'chord voicings':
                current_type = chord_type.split(' ')
                if len(current_type) > 1 and current_type[1][0] in ['#', 'b']:
                    other_msg += ' (with altered notes)'
        root_note = f"{root_note[0].upper()}{''.join(root_note[1:])}"
        if 'altered' in other_msg:
            chord_types_root = chord_types_root.split(',')[0]
            chord_type = original_chord_type
        return f"chord name: {chord_type}\nroot position: {chord_types_root}\nroot: {root_note}\nchord speciality: {chord_speciality}" + (
            f"\ninversion: {inversion_msg}{other_msg}"
            if chord_speciality == 'inverted chord' else other_msg)

    def same_accidentals(self, mode='#'):
        temp = copy(self)
        for each in temp.notes:
            if mode == '#':
                if len(each.name) > 1 and each.name[-1] == 'b':
                    each.name = standard_dict[each.name]
            elif mode == 'b':
                if each.name[-1] == '#':
                    each.name = reverse_standard_dict[each.name]
        return temp

    def filter(self, cond, action=None, mode=0, action_mode=0):
        temp = self.copy()
        available_inds = [k for k in range(len(temp)) if cond(temp.notes[k])]
        if mode == 1:
            return available_inds
        if action is None:
            new_interval = []
            N = len(available_inds) - 1
            for i in range(N):
                new_interval.append(
                    sum(temp.interval[available_inds[i]:available_inds[i +
                                                                       1]]))
            new_interval.append(sum(temp.interval[available_inds[-1]:]))
            new_notes = [temp.notes[j] for j in available_inds]
            result = chord(new_notes, interval=new_interval)
            start_time = sum(temp.interval[:available_inds[0]])
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
        temp = self.copy()
        if type(x) == str:
            x = trans_note(x)
        if type(y) == str:
            y = trans_note(y)
        available_inds = [
            k for k in range(len(temp))
            if x.degree <= temp.notes[k].degree <= y.degree
        ]
        new_interval = []
        N = len(available_inds) - 1
        for i in range(N):
            new_interval.append(
                sum(temp.interval[available_inds[i]:available_inds[i + 1]]))
        new_interval.append(sum(temp.interval[available_inds[-1]:]))
        new_notes = [temp.notes[j] for j in available_inds]
        result = chord(new_notes, interval=new_interval)
        start_time = sum(temp.interval[:available_inds[0]])
        return result, start_time

    def interval_note(self, interval, mode=0):
        if mode == 0:
            interval = str(interval)
            if interval in degree_match:
                self_notes = self.same_accidentals().notes
                degrees = degree_match[interval]
                for each in degrees:
                    current_note = self_notes[0] + each
                    if current_note in self_notes:
                        return current_note
            if interval in precise_degree_match:
                self_notes = self.same_accidentals().notes
                degrees = precise_degree_match[interval]
                current_note = self_notes[0] + degrees
                if current_note in self_notes:
                    return current_note
        elif mode == 1:
            return self[1] + interval

    def note_interval(self, current_note, mode=0):
        if type(current_note) == str:
            if not any(i.isdigit() for i in current_note):
                current_note = toNote(current_note)
                current_chord = chord([self[1].name, current_note.name])
                current_interval = current_chord[2].degree - current_chord[
                    1].degree
            else:
                current_note = toNote(current_note)
                current_interval = current_note.degree - self[1].degree
        else:
            current_interval = current_note.degree - self[1].degree
        if mode == 0:
            if current_interval in reverse_precise_degree_match:
                return reverse_precise_degree_match[current_interval]
        elif mode == 1:
            return INTERVAL[current_interval]

    def get_voicing(self, voicing):
        notes = [self.interval_note(i).name for i in voicing]
        pitch = self.notes[self.names().index(notes[0])].num
        return chord(notes, interval=copy(self.interval), rootpitch=pitch)

    def near_voicing(self, other, keep_root=True, root_lower=False):
        temp = self.standardize()
        other = other.standardize()
        original_duration = temp.get_duration()
        original_volume = temp.get_volume()
        if keep_root:
            root_note = temp.notes[0]
            other_root_note = other.notes[0]
            root_note_step = standard2[root_note.name] - standard2[
                other_root_note.name]
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
                    standard2[each.name] - standard2[i.name]
                    for i in other.notes[1:]
                ]
                note_steps_path = [
                    min([abs(i), 12 - abs(i)]) for i in note_steps
                ]
                most_near_note_steps = min(note_steps_path)
                most_near_note = other.notes[
                    note_steps_path.index(most_near_note_steps) + 1]
                current_step = standard2[each.name] - standard2[
                    most_near_note.name]
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
            if temp[1].name != root_note.name:
                temp[1] += octave * (
                    (12 - (temp[1].degree - root_note.degree)) // octave)
                temp = temp.sortchord()
            return temp
        else:
            remain_notes = []
            for each in temp.notes:
                note_steps = [
                    standard2[each.name] - standard2[i.name]
                    for i in other.notes
                ]
                note_steps_path = [
                    min([abs(i), 12 - abs(i)]) for i in note_steps
                ]
                most_near_note_steps = min(note_steps_path)
                most_near_note = other.notes[note_steps_path.index(
                    most_near_note_steps)]
                current_step = standard2[each.name] - standard2[
                    most_near_note.name]
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
        diff = num - self[1].num
        return self + diff * octave

    def reset_pitch(self, pitch):
        if type(pitch) != note:
            pitch = toNote(pitch)
        return self + (pitch.degree - self[1].degree)

    def with_other_messages(self, other_messages):
        temp = copy(self)
        temp.other_messages = other_messages
        return temp

    def clear_program_change(self):
        self.other_messages = [
            i for i in self.other_messages if type(i) != program_change
        ]

    def clear_other_messages(self, types=None):
        if types is None:
            self.other_messages.clear()
        else:
            self.other_messages = [
                i for i in self.other_messages if type(i) != types
            ]

    def dotted(self, ind=-1, num=1, duration=True, interval=False):
        temp = copy(self)
        if duration:
            if type(ind) == list:
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
            if type(ind) == list:
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

    def apply_start_time_to_changes(self, start_time):
        for each in self.notes:
            if type(each) != note:
                if each.start_time is not None:
                    each.start_time += start_time


class scale:
    def __init__(self,
                 start=None,
                 mode=None,
                 interval=None,
                 name=None,
                 notels=None,
                 pitch=4):
        self.interval = interval
        if notels is not None:
            notels = [toNote(i) if type(i) != note else i for i in notels]
            self.notes = notels
            self.start = notels[0]
            self.mode = mode
            self.pitch = pitch
        else:
            if type(start) != note:
                start = trans_note(start)
            self.start = start
            self.pitch = self.start.num
            if mode is not None:
                self.mode = mode.lower()
            else:
                self.mode = name
            self.notes = self.getScale().notes

        if interval is None:
            self.interval = self.getInterval()
        if mode is None:
            import musicpy
            current_mode = musicpy.detect(self.interval, mode='scale')
            if current_mode != 'not found':
                self.mode = current_mode

    def set_mode_name(self, name):
        self.mode = name

    def change_interval(self, interval):
        self.interval = interval

    def __str__(self):
        return f'scale name: {self.start} {self.mode} scale\nscale intervals: {self.getInterval()}\nscale notes: {self.getScale().notes}'

    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, scale) and self.notes == other.notes

    def standard(self):
        if len(self) == 8:
            standard_notes = [i.name for i in copy(self.notes)[:-1]]
            compare_notes = [i.name for i in scale('C', 'major').notes[:-1]]
            inds = compare_notes.index(standard_notes[0][0])
            compare_notes = compare_notes[inds:] + compare_notes[:inds]
            standard_notes = [
                relative_note(standard_notes[i], compare_notes[i])
                for i in range(7)
            ]
            return standard_notes
        else:
            return self.names()

    def __contains__(self, note1):
        names = self.names()
        names = [standard_dict[i] if i in standard_dict else i for i in names]
        if type(note1) == chord:
            chord_names = note1.names()
            chord_names = [
                standard_dict[i] if i in standard_dict else i
                for i in chord_names
            ]
            return all(i in names for i in chord_names)
        else:
            if type(note1) == note:
                note1 = note1.name
            else:
                note1 = trans_note(note1).name
            return (standard_dict[note1]
                    if note1 in standard_dict else note1) in names

    def __getitem__(self, ind):
        if isinstance(ind, slice):
            return self.getScale()[ind]
        if ind != 0:
            if ind > 0:
                ind -= 1
        return self.notes[ind]

    def __iter__(self):
        for i in self.notes:
            yield i

    def __call__(self, n, duration=0.25, interval=0, num=3, step=2):
        return self.pickchord_by_degree(n, duration, interval, num, step)

    def getInterval(self):
        if self.mode is None:
            if self.interval is None:
                if self.notes is None:
                    return 'a mode or interval or notes list should be settled'
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
            result = scaleTypes[mode]
            if result != 'not found':
                return result
            else:
                return 'could not find this scale'

    def getScale(self, intervals=0.25, durations=None):
        if self.mode == None:
            if self.interval == None:
                return 'at least one of mode or interval in the scale should be settled'
            else:
                result = [self.start]
                count = self.start.degree
                for t in self.interval:
                    count += t
                    result.append(degree_to_note(count))
                return chord(result, duration=durations, interval=intervals)
        else:
            result = [self.start]
            count = self.start.degree
            interval1 = self.getInterval()
            if type(interval1) == str:
                raise ValueError('cannot find this scale')
            for t in interval1:
                count += t
                result.append(degree_to_note(count))
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
        if degree1 == 8:
            degree1 = 1
            high = True
        temp = copy(self)
        scale_notes = temp.notes[:-1]
        for i in range(degree1, degree1 + step * num, step):
            result.append(scale_notes[(i % 7) - 1])
        resultchord = chord(result,
                            rootpitch=temp.pitch,
                            interval=interval,
                            duration=duration).standardize()
        if high:
            resultchord = resultchord.up(octave)
        return resultchord

    def pickdegree(self, degree1):
        return self[degree1]

    def pattern(self, indlist, duration=0.25, interval=0, num=3, step=2):
        if type(indlist) == str:
            indlist = [int(i) for i in indlist]
        if type(indlist) == int:
            indlist = [int(i) for i in str(indlist)]
        return [
            self(n, num=num, step=step).set(duration, interval)
            for n in indlist
        ]

    def __mod__(self, x):
        if type(x) in [int, str]:
            x = [x]
        return self.pattern(*x)

    def dom(self):
        return self[5]

    def dom_mode(self):
        if self.mode is not None:
            return scale(self[5], mode=self.mode)
        else:
            return scale(self[5], interval=self.getInterval())

    def fifth(self, step=1, inner=False):
        # move the scale on the circle of fifths by number of steps,
        # if the step is > 0, then move clockwise,
        # if the step is < 0, then move counterclockwise,
        # if inner is True: pick the inner scales from the circle of fifths,
        # i.e. those minor scales.
        return circle_of_fifths().rotate_getScale(self[1].name,
                                                  step,
                                                  pitch=self[1].num,
                                                  inner=inner)

    def fourth(self, step=1, inner=False):
        # same as fifth but instead of circle of fourths
        # Maybe someone would notice that circle of fourths is just
        # the reverse of circle of fifths.
        return circle_of_fourths().rotate_getScale(self[1].name,
                                                   step,
                                                   pitch=self[1].num,
                                                   inner=inner)

    def tonic(self):
        return self[1]

    def supertonic(self):
        return self[2]

    def mediant(self):
        return self[3]

    def subdominant(self):
        return self[4]

    def dominant(self):
        return self[5]

    def submediant(self):
        return self[6]

    def leading_tone(self):
        return self[1].up(major_seventh)

    def subtonic(self):
        return self[1].up(minor_seventh)

    def tonic_chord(self):
        return self(1)

    def subdom(self):
        return self[4]

    def subdom_chord(self):
        return self(4)

    def dom_chord(self):
        return self(5)

    def dom7_chord(self):
        return self(5) + self[4].up(12)

    def leading7_chord(self):
        return chord([self[7].down(octave), self[2], self[4], self[6]])

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

    def detect(self, *args, **kwargs):
        import musicpy
        return musicpy.detect(self, *args, **kwargs, mode='scale')

    def get_allchord(self, duration=None, interval=0, num=3, step=2):
        return [
            self.pickchord_by_degree(i,
                                     duration=duration,
                                     interval=interval,
                                     num=num,
                                     step=step)
            for i in range(1,
                           len(self.getInterval()) + 2)
        ]

    def relative_key(self):
        if self.mode == 'major':
            return scale(self[6], 'minor')
        elif self.mode == 'minor':
            return scale(self[3], 'major')
        else:
            'this function only applies to major and minor scales'

    def parallel_key(self):
        if self.mode == 'major':
            return scale(self[1], 'minor')
        elif self.mode == 'minor':
            return scale(self[1], 'major')
        else:
            return 'this function only applies to major and minor scales'

    def get(self, degree):
        return self[degree]

    def get_chord(self, degree, chord_type=None, natural=False):
        import musicpy
        if not chord_type:
            current_keys = list(roman_numerals_dict.keys())
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
        current_degree = roman_numerals_dict[degree]
        if current_degree == 'not found':
            return f'{degree} is not a valid roman numerals chord representation'
        current_note = self[current_degree].name
        if natural:
            temp = musicpy.C(current_note + chord_type)
            if type(temp) != chord:
                return f'{chord_type} is not a valid chord type'
            length = len(temp)
            return self.pickchord_by_degree(current_degree, num=length)
        if degree.islower():
            current_note += 'm'
        current_chord_type = current_note + chord_type
        return musicpy.C(current_chord_type)

    def up(self, unit=1, ind=None, ind2=None):
        if ind2 is not None:
            notes = copy(self.notes)
            return scale(notels=[
                notes[i].up(unit) if ind <= i < ind2 else notes[i]
                for i in range(len(notes))
            ])
        if ind is None:
            return scale(self[1].up(unit), self.mode, self.interval)
        else:
            notes = copy(self.notes)
            if type(ind) == int:
                notes[ind - 1] = notes[ind - 1].up(unit)
            else:
                ind = [i - 1 if i > 0 else i for i in ind]
                notes = [
                    notes[i].up(unit) if i in ind else notes[i]
                    for i in range(len(notes))
                ]
            result = scale(notels=notes)
            current_mode = result.detect()
            if current_mode != 'not found':
                result.mode = current_mode
            return result

    def down(self, unit=1, ind=None, ind2=None):
        return self.up(-unit, ind, ind2)

    def __pos__(self):
        return self.up()

    def __neg__(self):
        return self.down()

    def __invert__(self):
        return scale(self[1],
                     interval=list(reversed(self.interval)),
                     pitch=self.pitch)

    def move(self, x):
        notes = copy(self.getScale())
        return scale(notels=notes.move(x))

    def inversion(self, ind, parallel=False, start=None):
        # return the inversion of a scale with the beginning note of a given index
        ind -= 1
        interval1 = self.getInterval()
        new_interval = interval1[ind:] + interval1[:ind]
        if parallel:
            start1 = self.start
        else:
            if start is not None:
                start1 = start
            else:
                start1 = self.getScale().notes[ind]
        result = scale(start=start1, interval=new_interval)
        result.mode = result.detect()
        return result

    def play(self, intervals=0.25, durations=None, *args, **kwargs):
        import musicpy
        musicpy.play(self.getScale(intervals, durations), *args, **kwargs)

    def __add__(self, obj):
        if type(obj) == int:
            return self.up(obj)
        elif type(obj) == tuple:
            return self.up(*obj)

    def __sub__(self, obj):
        if type(obj) == int:
            return self.down(obj)
        elif type(obj) == tuple:
            return self.down(*obj)

    def chord_progression(self,
                          chords,
                          durations=1 / 4,
                          intervals=0,
                          volumes=None,
                          chords_interval=None,
                          merge=True):
        current_keys = list(roman_numerals_dict.keys())
        current_keys.sort(key=lambda s: len(s[0]), reverse=True)
        for k in range(len(chords)):
            current_chord = chords[k]
            types = type(current_chord)
            if types == tuple or types == list:
                current_degree_name = current_chord[0]
                current_degree = roman_numerals_dict[current_degree_name]
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
                            current_degree = roman_numerals_dict[i]
                            current_note = self[current_degree].name
                            if i.islower():
                                current_note += 'm'
                            chords[k] = current_note + current_chord[len(i):]
                            break
                    if found:
                        break
                if not found:
                    return f'{current_chord} is not a valid roman numerals chord representation'
        import musicpy
        return musicpy.chord_progression(chords, durations, intervals, volumes,
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
            if type(start) != note:
                start = trans_note(start)
        if num is not None:
            start.num = num
        if mode is None and interval is None:
            mode = temp.mode
            interval = temp.interval
        return scale(start, mode, interval)


class circle_of_fifths:
    outer = ['C', 'G', 'D', 'A', 'E', 'B', 'Gb', 'Db', 'Ab', 'Eb', 'Bb', 'F']
    inner = [
        'Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'Ebm', 'Bbm', 'Fm', 'Cm', 'Gm',
        'Dm'
    ]

    def __init__(self):
        pass

    def __getitem__(self, ind):
        ind -= 1
        if type(ind) == int:
            if not (0 <= ind < 12):
                ind = ind % 12
            return self.outer[ind]
        elif type(ind) == tuple:
            ind = ind[0]
            if not (0 <= ind < 12):
                ind = ind % 12
            return self.inner[ind]

    def draw(self, inner=False):
        if not inner:
            return '\n         C \n    F         G\n   Bb          D\n  Eb            A\n   Ab          E  \n    Db        B\n         Gb'

        else:
            return '\n            C \n        F   Am   G\n     Bb  Dm    Em   D\n        Gm        Bm  \n    Eb Cm        F#m  A\n      Fm        C#m\n   Ab  Bbm   G#m    E  \n      Db   Ebm   B\n           Gb'

    def get(self, ind, mode=0):
        if mode == 0:
            return self[ind]
        else:
            return self[ind, ]

    def rotate(self, start, step=1, direction='cw', inner=False):
        if direction == 'ccw':
            step = -step
        types = type(start)
        if types == note:
            startind = self.outer.index(start.name)
        elif types == str:
            startind = self.outer.index(start)
        else:
            startind = start
        return self[startind + step] if not inner else self[startind + step, ]

    def rotate_getScale(self,
                        start,
                        step=1,
                        direction='cw',
                        pitch=None,
                        inner=False):
        if not inner:
            return scale(note(self.rotate(start, step, direction), pitch),
                         'major')
        else:
            return scale(
                note(self.rotate(start, step, direction, True)[:-1], pitch),
                'minor')

    def getScale(self, ind, pitch, inner=False):
        return scale(note(self[ind], pitch), 'major') if not inner else scale(
            note(self[ind, ][:-1], pitch), 'minor')

    def __repr__(self):
        return f'circle of fifths\nouter circle: {self.outer}\ninner circle: {self.inner}\ndirection: clockwise'


class circle_of_fourths(circle_of_fifths):
    outer = list(reversed(circle_of_fifths.outer))
    outer.insert(0, outer.pop())
    inner = list(reversed(circle_of_fifths.inner))
    inner.insert(0, inner.pop())

    def __init__(self):
        pass

    def __repr__(self):
        return f'circle of fourths\nouter circle: {self.outer}\ninner circle: {self.inner}\ndirection: clockwise'

    def draw(self, inner=False):
        if not inner:
            return '\n         C \n    G         F\n   D          Bb\n  A            Eb\n   E          Ab  \n    B        Db\n        Gb'
        else:
            return '\n            C \n        G   Am   F\n     D   Em    Dm   Bb\n        Bm       Gm  \n    A  F#m        Cm  Eb\n      C#m        Fm\n   E   G#m    Bbm    Ab  \n      B   Ebm   Db\n           Gb'


def perm(n, k=None):
    # this function returns all of the permutations of the elements in x
    if k is None:
        k = len(n)
    if isinstance(n, int):
        n = list(range(1, n + 1))
    if isinstance(n, str):
        n = list(n)
    return eval(
        f'''[{f"[{', '.join([f'n[a{i}]' for i in range(k)])}]"} {''.join([f'for a{i} in range(len(n)) ' if i == 0 else f"for a{i} in range(len(n)) if a{i} not in [{', '.join([f'a{t}' for t in range(i)])}] " for i in range(k)])}]''',
        locals())


def relative_note(a, b):
    # return the notation of note a from note b with accidentals
    # (how note b adds accidentals to match the same pitch as note a),
    # works for the accidentals including sharp, flat, natural,
    # double sharp, double flat
    # (a, b are strings that represents a note, could be with accidentals)
    len_a, len_b = len(a), len(b)
    a_name, b_name, accidental_a, accidental_b = a[0], b[0], a[1:], b[1:]
    if len_a == 1 and len_b > 1 and a_name == b_name:
        return a + '♮'
    if a in standard:
        a = note(a, 5)
    else:
        a = note(a_name, 5)
        if accidental_a == 'b':
            a = a.down()
        elif accidental_a == 'bb':
            a = a.down(2)
        elif accidental_a == '#':
            a = a.up()
        elif accidental_a == 'x':
            a = a.up(2)
        elif accidental_a == '♮':
            pass
        else:
            return f'unrecognizable accidentals {accidental_a}'
    if b in standard:
        b = note(b, 5)
    else:
        b = note(b_name, 5)
        if accidental_b == 'b':
            b = b.down()
        elif accidental_b == 'bb':
            b = b.down(2)
        elif accidental_b == '#':
            b = b.up()
        elif accidental_b == 'x':
            b = b.up(2)
        elif accidental_b == '♮':
            pass
        else:
            return f'unrecognizable accidentals {accidental_b}'
    degree1, degree2 = a.degree, b.degree
    diff1, diff2 = degree1 - degree2, (degree1 - degree2 -
                                       12 if degree1 >= degree2 else degree1 +
                                       12 - degree2)
    if abs(diff1) < abs(diff2):
        diff = diff1
    else:
        diff = diff2
    if diff == 0:
        return b.name
    if diff == 1:
        return b.name + '#'
    if diff == 2:
        return b.name + 'x'
    if diff == -1:
        return b.name + 'b'
    if diff == -2:
        return b.name + 'bb'


class piece:
    def __init__(self,
                 tracks,
                 instruments_list=None,
                 tempo=120,
                 start_times=None,
                 track_names=None,
                 channels=None,
                 name=None,
                 pan=None,
                 volume=None,
                 other_messages=[]):
        self.tracks = tracks
        if instruments_list is None:
            self.instruments_list = [
                reverse_instruments[1] for i in range(len(self.tracks))
            ]
            self.instruments_numbers = [
                instruments[j] for j in self.instruments_list
            ]
        else:
            self.instruments_list = [
                reverse_instruments[i] if isinstance(i, int) else i
                for i in instruments_list
            ]
            self.instruments_numbers = [
                instruments[j] for j in self.instruments_list
            ]
        self.tempo = tempo
        self.start_times = start_times
        self.track_number = len(tracks)
        if self.start_times is None:
            self.start_times = [0 for i in range(self.track_number)]
        self.track_names = track_names
        self.channels = channels
        self.name = name
        self.pan = pan
        self.volume = volume
        if self.pan:
            self.pan = [[i] if type(i) != list else i for i in self.pan]
        else:
            self.pan = [[] for i in range(self.track_number)]
        if self.volume:
            self.volume = [[i] if type(i) != list else i for i in self.volume]
        else:
            self.volume = [[] for i in range(self.track_number)]
        self.other_messages = other_messages

    def __repr__(self):
        return (
            f'[piece] {self.name if self.name else ""}\n'
        ) + f'BPM: {round(self.tempo, 3)}\n' + '\n'.join([
            f'track {i+1}{" channel " + str(self.channels[i]) if self.channels else ""} {self.track_names[i] + " " if self.track_names else ""}| instrument: {self.instruments_list[i]} | start time: {self.start_times[i]} | {self.tracks[i]}'
            for i in range(self.track_number)
        ])

    def __eq__(self, other):
        return isinstance(other, piece) and self.__dict__ == other.__dict__

    def __getitem__(self, i):
        if i > 0:
            i -= 1
        return track(self.tracks[i], self.instruments_list[i],
                     self.start_times[i], self.tempo,
                     self.track_names[i] if self.track_names else None,
                     self.channels[i] if self.channels else None, self.name,
                     self.pan[i], self.volume[i])

    def __delitem__(self, i):
        if i > 0:
            i -= 1
        del self.tracks[i]
        del self.instruments_list[i]
        del self.instruments_numbers[i]
        del self.start_times[i]
        if self.track_names:
            del self.track_names[i]
        if self.channels:
            del self.channels[i]
        if self.pan:
            del self.pan[i]
        if self.volume:
            del self.volume[i]
        self.track_number -= 1

    def __setitem__(self, i, new_track):
        if i > 0:
            i -= 1
        self.tracks[i] = new_track.content
        self.instruments_list[i] = new_track.instrument
        self.instruments_numbers[i] = new_track.instruments_number
        self.start_times[i] = new_track.start_time
        if self.track_names and new_track.track_name:
            self.track_names[i] = new_track.track_name
        if self.channels and new_track.channel is not None:
            self.channels[i] = new_track.channel
        if self.pan:
            self.pan[i] = new_track.pan
        if self.volume:
            self.volume[i] = new_track.volume

    def __len__(self):
        return len(self.tracks)

    def mute(self, i=None):
        if not hasattr(self, 'muted_msg'):
            self.muted_msg = [each.get_volume() for each in self.tracks]
        if i is None:
            for k in range(len(self.tracks)):
                self.tracks[k].setvolume(0)
        else:
            if i > 0:
                i -= 1
            self.tracks[i].setvolume(0)

    def unmute(self, i=None):
        if not hasattr(self, 'muted_msg'):
            return
        if i is None:
            for k in range(len(self.tracks)):
                self.tracks[k].setvolume(self.muted_msg[k])
        else:
            if i > 0:
                i -= 1
            self.tracks[i].setvolume(self.muted_msg[i])

    def append(self, new_track):
        if type(new_track) != track:
            return 'must be a track type to be appended'
        self.tracks.append(new_track.content)
        self.instruments_list.append(new_track.instrument)
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
        if self.pan:
            if new_track.pan:
                self.pan.append(new_track.pan)
            else:
                self.pan.append([])
        if self.volume:
            if new_track.volume:
                self.volume.append(new_track.volume)
            else:
                self.volume.append([])
        self.track_number += 1

    def up(self, n=1, mode=0):
        temp = copy(self)
        for i in range(temp.track_number):
            if mode == 0 or (
                    mode == 1 and not (temp.channels and temp.channels[i] == 9)
            ) or (mode == 2
                  and not ((temp.channels and temp.channels[i] == 9) or
                           ('drum' in temp.instruments_list[i].lower()))):
                temp.tracks[i] += n
        return temp

    def down(self, n=1, mode=0):
        temp = copy(self)
        for i in range(temp.track_number):
            if mode == 0 or (
                    mode == 1 and not (temp.channels and temp.channels[i] == 9)
            ) or (mode == 2
                  and not ((temp.channels and temp.channels[i] == 9) or
                           ('drum' in temp.instruments_list[i].lower()))):
                temp.tracks[i] -= n
        return temp

    def __mul__(self, n):
        temp = copy(self)
        for i in range(temp.track_number):
            temp.tracks[i] *= n
        return temp

    def __mod__(self, n):
        temp = copy(self)
        for i in range(temp.track_number):
            temp.tracks[i] %= n
        return temp

    def __or__(self, n):
        temp = copy(self)
        whole_length = None
        for i in range(temp.track_number):
            current = temp.tracks[i]
            counter = 0
            for j in range(len(current) - 1, -1, -1):
                current_note = current.notes[j]
                if type(current_note) == note:
                    current.interval[j] = current.notes[j].duration
                    counter = j
                    break
            if i == 0:
                whole_length = current.bars()
            else:
                current.interval[counter] += (whole_length - current.bars() -
                                              temp.start_times[i])
            unit = copy(current)
            for k in range(n - 1):
                current_start_time = temp.start_times[i]
                if current_start_time:
                    for j in range(len(current) - 1, -1, -1):
                        current_note = current.notes[j]
                        if type(current_note) == note:
                            current.interval[j] += current_start_time
                            break
                current.notes += unit.notes
                current.interval += unit.interval
            temp.tracks[i] = current
        return temp

    def __and__(self, n):
        if type(n) == tuple:
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

    def play(self, *args, **kwargs):
        import musicpy
        musicpy.play(self, *args, **kwargs)

    def __call__(self, num):
        if num > 0:
            num -= 1
        return [
            self.tracks[num], self.instruments_list[num], self.tempo,
            self.start_times[num],
            self.channels[num] if self.channels else None,
            self.track_names[num] if self.track_names else None, self.pan[num],
            self.volume[num]
        ]

    def merge_track(self,
                    n,
                    mode='after',
                    start_time=0,
                    keep_tempo=True,
                    **args):
        temp = copy(self)
        temp2 = copy(n)
        temp_length = temp.bars(**args)
        if temp.channels is not None:
            free_channel_numbers = [
                i for i in range(16) if i not in temp.channels
            ]
            counter = 0
        if mode == 'after':
            start_time = temp_length
        for i in range(len(temp2)):
            current_instrument_number = temp2.instruments_numbers[i]
            if current_instrument_number in temp.instruments_numbers:
                current_ind = temp.instruments_numbers.index(
                    current_instrument_number)
                current_track = temp2.tracks[i]
                for each in current_track:
                    if type(each) != note:
                        if each.start_time is not None:
                            each.start_time += start_time
                current_start_time = temp2.start_times[
                    i] + start_time - temp.start_times[current_ind]
                temp.tracks[current_ind] &= (current_track, current_start_time)
                if current_start_time < 0:
                    temp.start_times[current_ind] += current_start_time
            else:
                current_instrument = temp2.instruments_list[i]
                temp.instruments_list.append(current_instrument)
                temp.instruments_numbers.append(current_instrument_number)
                current_start_time = temp2.start_times[i]
                current_start_time += start_time
                current_track = temp2.tracks[i]
                for each in current_track:
                    if type(each) != note:
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
        if mode == 'after' and keep_tempo:
            temp.add_tempo_change(temp2.tempo, 1 + temp_length)
        temp.track_number = len(temp.tracks)
        return temp

    def add_pitch_bend(self,
                       value,
                       start_time=1,
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
                    ind + 1,
                    pitch_bend(value, start_time, current_channel, track,
                               mode))
            else:
                self.tracks[channel] += chord([
                    pitch_bend(value, start_time, current_channel, track, mode)
                ])

    def add_tempo_change(self, bpm, start_time=None, ind=None, track_ind=None):
        if ind is not None and track_ind is not None:
            self.tracks[track_ind].insert(ind + 1, tempo(bpm, start_time))
        else:
            self.tracks[0] += chord([tempo(bpm, start_time)])

    def clear_pitch_bend(self, ind='all', value=0, cond=None):
        if ind == 'all':
            for each in self.tracks:
                each.clear_pitch_bend(value, cond)
        else:
            self.tracks[ind - 1].clear_pitch_bend(value, cond)

    def clear_tempo(self, ind='all', cond=None):
        if ind == 'all':
            for each in self.tracks:
                each.clear_tempo(cond)
        else:
            self.tracks[ind - 1].clear_tempo(cond)

    def normalize_tempo(self, bpm=None):
        if bpm is None:
            bpm = self.tempo
        temp = copy(self)
        all_tracks = temp.tracks
        length = len(all_tracks)
        for k in range(length):
            for each in all_tracks[k]:
                each.track_num = k
        start_time_ls = temp.start_times
        first_track_start_time = min(start_time_ls)
        first_track_ind = start_time_ls.index(first_track_start_time)
        start_time_ls.insert(0, start_time_ls.pop(first_track_ind))

        all_tracks.insert(0, all_tracks.pop(first_track_ind))
        first_track = all_tracks[0]

        for i in range(1, length):
            first_track &= (all_tracks[i],
                            start_time_ls[i] - first_track_start_time)
        first_track.normalize_tempo(bpm, start_time=first_track_start_time)
        start_times_inds = [[
            i for i in range(len(first_track))
            if first_track.notes[i].track_num == k
        ][0] for k in range(length)]
        new_start_times = [
            first_track_start_time + first_track[:k + 1].bars(mode=0)
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
            sum(whole_interval[inds[i]:inds[i + 1]])
            for i in range(len(inds) - 1)
        ] for inds in new_track_inds]
        for i in range(length):
            new_track_intervals[i].append(
                sum(whole_interval[new_track_inds[i][-1]:]))
        new_tracks = [
            chord(new_track_notes[k],
                  interval=new_track_intervals[k],
                  other_messages=temp.tracks[k].other_messages)
            for k in range(length)
        ]
        self.tracks = new_tracks
        self.start_times = new_start_times

    def get_tempo_changes(self, **args):
        temp = copy(self)
        tempo_changes = []
        for each in temp.tracks:
            inds = [
                i for i in range(len(each)) if type(each.notes[i]) == tempo
            ]
            notes = [each.notes[i] for i in inds]
            no_time = [k for k in inds if each.notes[k].start_time is None]
            for k in no_time:
                current_time = each[:k + 1].bars(**args) + 1
                current = each.notes[k]
                current.start_time = current_time
            tempo_changes += notes
        tempo_changes.sort(key=lambda s: s.start_time)
        return chord(tempo_changes)

    def get_pitch_bend(self, track_number=1, **args):
        temp = copy(self)
        each = temp.tracks[track_number - 1]
        inds = [
            i for i in range(len(each)) if type(each.notes[i]) == pitch_bend
        ]
        pitch_bend_changes = [each.notes[i] for i in inds]
        no_time = [k for k in inds if each.notes[k].start_time is None]
        for k in no_time:
            current_time = each[:k + 1].bars(**args) + 1
            current = each.notes[k]
            current.start_time = current_time
        pitch_bend_changes.sort(key=lambda s: s.start_time)
        return chord(pitch_bend_changes)

    def add_pan(self, value, ind, start_time=1, mode='percentage'):
        self.pan[ind].append(pan(value, start_time, mode))

    def add_volume(self, value, ind, start_time=1, mode='percentage'):
        self.volume[ind].append(volume(value, start_time, mode))

    def clear_pan(self, ind='all'):
        if ind == 'all':
            for each in self.pan:
                each.clear()
        else:
            if ind > 0:
                ind -= 1
            self.pan[ind].clear()

    def clear_volume(self, ind='all'):
        if ind == 'all':
            for each in self.volume:
                each.clear()
        else:
            if ind > 0:
                ind -= 1
            self.volume[ind].clear()

    def reassign_channels(self, start=0):
        new_channels_numbers = [start + i for i in range(len(self.tracks))]
        self.channels = new_channels_numbers

    def merge(self, add_labels=True):
        import musicpy
        temp = copy(self)
        if add_labels:
            temp.add_track_labels()
        tempo_changes = temp.get_tempo_changes()
        temp.clear_tempo()
        all_tracks = temp.tracks
        length = len(all_tracks)
        start_time_ls = temp.start_times
        pitch_bends = musicpy.concat(
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
        return temp.tempo, first_track, first_track_start_time

    def add_track_labels(self):
        all_tracks = self.tracks
        length = len(all_tracks)
        for k in range(length):
            for each in all_tracks[k]:
                each.track_num = k

    def reconstruct(self, track, start_time=0, offset=0, correct=False):
        first_track, first_track_start_time = track, start_time
        length = len(self.tracks)
        tempo_messages = first_track.split(tempo)
        first_track.clear_tempo()
        start_times_inds = [[
            i for i in range(len(first_track))
            if first_track.notes[i].track_num == k
        ] for k in range(length)]
        available_tracks_inds = [
            k for k in range(length) if start_times_inds[k]
        ]
        available_tracks_messages = [
            self.tracks[i].other_messages for i in available_tracks_inds
        ]
        start_times_inds = [i[0] for i in start_times_inds if i]
        new_start_times = [
            first_track_start_time + first_track[:k + 1].bars(mode=0)
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
            new_track_intervals[i].append(
                sum(whole_interval[new_track_inds[i][-1]:]))
        new_tracks = [
            chord(new_track_notes[available_tracks_inds[i]],
                  interval=new_track_intervals[available_tracks_inds[i]],
                  other_messages=available_tracks_messages[i])
            for i in range(len(available_tracks_inds))
        ]
        new_tracks[0] += tempo_messages
        self.tracks = new_tracks
        self.start_times = new_start_times
        self.instruments_list = [
            self.instruments_list[k] for k in available_tracks_inds
        ]
        self.instruments_numbers = [
            self.instruments_numbers[k] for k in available_tracks_inds
        ]
        if self.track_names:
            self.track_names = [
                self.track_names[k] for k in available_tracks_inds
            ]
        if self.channels:
            self.channels = [self.channels[k] for k in available_tracks_inds]
        self.track_number = len(self.tracks)

    def eval_time(self,
                  bpm=None,
                  ind1=None,
                  ind2=None,
                  mode='seconds',
                  normalize_tempo=False,
                  audio_mode=0):
        temp_bpm, merged_result, start_time = self.merge()
        if bpm is not None:
            temp_bpm = bpm
        if normalize_tempo:
            merged_result.normalize_tempo(temp_bpm, start_time=start_time)
        return merged_result.eval_time(temp_bpm,
                                       ind1,
                                       ind2,
                                       mode,
                                       start_time=start_time,
                                       audio_mode=audio_mode)

    def cut(self, ind1=1, ind2=None, correct=False):
        temp_bpm, merged_result, start_time = self.merge()
        if ind1 < 1:
            ind1 = 1
        result = merged_result.cut(ind1, ind2, start_time)
        offset = ind1 - 1
        temp = copy(self)
        start_time -= (ind1 - 1)
        if start_time < 0:
            start_time = 0
        temp.reconstruct(result, start_time, offset, correct)
        if ind2 is None:
            ind2 = temp.bars()
        for each in temp.pan:
            for i in each:
                i.start_time -= (ind1 - 1)
                if i.start_time < 1:
                    i.start_time = 1
        for each in temp.volume:
            for i in each:
                i.start_time -= (ind1 - 1)
                if i.start_time < 1:
                    i.start_time = 1
        temp.pan = [[i for i in each if i.start_time < ind2]
                    for each in temp.pan]
        temp.volume = [[i for i in each if i.start_time < ind2]
                       for each in temp.volume]
        return temp

    def cut_time(self, time1=0, time2=None, bpm=None, start_time=0, **args):
        temp = copy(self)
        temp.normalize_tempo()
        if bpm is not None:
            temp_bpm = bpm
        else:
            temp_bpm = temp.tempo
        bar_left = time1 / ((60 / temp_bpm) * 4)
        bar_right = time2 / (
            (60 / temp_bpm) * 4) if time2 is not None else temp.bars(**args)
        result = temp.cut(1 + bar_left, 1 + bar_right)
        return result

    def get_bar(self, n):
        start_time = min(self.start_times)
        return self.cut(n + start_time, n + 1 + start_time)

    def firstnbars(self, n):
        start_time = min(self.start_times)
        return self.cut(1 + start_time, n + 1 + start_time)

    def bars(self, mode=1, audio_mode=0):
        return max([
            self.tracks[i].bars(start_time=self.start_times[i],
                                mode=mode,
                                audio_mode=audio_mode)
            for i in range(len(self.tracks))
        ])

    def count(self, note1, mode='name'):
        return self.merge()[1].count(note1, mode)

    def most_appear(self, choices=None, mode='name', as_standard=False):
        return self.merge()[1].most_appear(choices, mode, as_standard)

    def standard_notation(self):
        temp = copy(self)
        temp.tracks = [each.standard_notation() for each in temp.tracks]
        return temp

    def count_appear(self, choices=None, as_standard=True, sort=False):
        return self.merge()[1].count_appear(choices, as_standard, sort)

    def apply_start_time_to_changes(self, start_time):
        tracks = self.tracks
        for i in range(len(tracks)):
            current_start_time = start_time[i]
            current_track = tracks[i]
            for each in current_track:
                if type(each) != note:
                    if each.start_time is not None:
                        each.start_time += current_start_time

    def reverse(self, **args):
        temp = copy(self)
        temp.tracks = [
            temp.tracks[i].reverse(start_time=temp.start_times[i], **args)
            for i in range(len(temp.tracks))
        ]
        length = temp.bars(**args)
        start_times = temp.start_times
        tracks = temp.tracks
        track_num = len(temp.tracks)
        first_start_time = min(self.start_times)
        temp.start_times = [
            length -
            (start_times[i] + tracks[i].bars(**args) - first_start_time)
            for i in range(track_num)
        ]

        temp.apply_start_time_to_changes(temp.start_times)
        for each in temp.pan:
            for i in each:
                i.start_time = length - i.start_time + 2
                if i.start_time < 1:
                    i.start_time = 1
        for each in temp.volume:
            for i in each:
                i.start_time = length - i.start_time + 2
                if i.start_time < 1:
                    i.start_time = 1
        return temp

    def reverse_chord(self, **args):
        temp = copy(self)
        temp.tracks = [
            temp.tracks[i].reverse_chord(start_time=temp.start_times[i],
                                         **args)
            for i in range(len(temp.tracks))
        ]
        length = temp.bars(**args)
        start_times = temp.start_times
        tracks = temp.tracks
        track_num = len(temp.tracks)
        first_start_time = min(self.start_times)
        temp.start_times = [
            length -
            (start_times[i] + tracks[i].bars(**args) - first_start_time)
            for i in range(track_num)
        ]
        temp.apply_start_time_to_changes(temp.start_times)
        for each in temp.pan:
            for i in each:
                i.start_time = length - i.start_time + 2
                if i.start_time < 1:
                    i.start_time = 1
        for each in temp.volume:
            for i in each:
                i.start_time = length - i.start_time + 2
                if i.start_time < 1:
                    i.start_time = 1
        return temp

    def __invert__(self):
        return self.reverse()

    def clear_program_change(self, apply_tracks=True):
        if apply_tracks:
            for each in self.tracks:
                each.clear_program_change()
        self.other_messages = [
            i for i in self.other_messages if type(i) != program_change
        ]

    def clear_other_messages(self, types=None, apply_tracks=True):
        if apply_tracks:
            for each in self.tracks:
                each.clear_other_messages(types)
        if types is None:
            self.other_messages.clear()
        else:
            self.other_messages = [
                i for i in self.other_messages if type(i) != types
            ]

    def change_instruments(self, instruments_list, ind=None):
        if ind is None:
            if all(type(i) == int for i in instruments_list):
                self.instruments_numbers = copy(instruments_list)
                self.instruments_list = [
                    reverse_instruments[i] for i in self.instruments_numbers
                ]
            elif all(type(i) == str for i in instruments_list):
                self.instruments_list = copy(instruments_list)
                self.instruments_numbers = [
                    instruments[i] for i in self.instruments_list
                ]
            elif any(
                    type(i) == list and all(type(j) == int for j in i)
                    for i in instruments_list):
                self.instruments_numbers = copy(instruments_list)
        else:
            if ind > 0:
                ind -= 1
            if type(instruments_list) == int:
                self.instruments_numbers[ind] = instruments_list
                self.instruments_list[ind] = reverse_instruments[
                    instruments_list]
            elif type(instruments_list) == str:
                self.instruments_list[ind] = instruments_list
                self.instruments_numbers[ind] = instruments[instruments_list]
            elif type(instruments_list) == list and all(
                    type(j) == int for j in instruments_list):
                self.instruments_numbers[ind] = copy(instruments_list)

    def move(self, time=0, ind='all'):
        temp = copy(self)
        if ind == 'all':
            temp.start_times = [i + time for i in temp.start_times]
            temp.apply_start_time_to_changes(
                [time for i in range(len(temp.start_times))])
            for each in temp.pan:
                for i in each:
                    i.start_time += time
            for each in temp.volume:
                for i in each:
                    i.start_time += time
        else:
            if ind > 0:
                ind -= 1
            temp.start_times[ind] += time
            for i in temp.tracks[ind]:
                if type(i) != note:
                    if i.start_time is not None:
                        i.start_time += time
            for each in temp.pan[ind]:
                each.start_time += time
            for each in temp.volume[ind]:
                each.start_time += time
        return temp

    def copy(self):
        return copy(self)


P = piece


class tempo:
    # this is a class to change tempo for the notes after it when it is read,
    # it can be inserted into a chord, and if the chord is in a piece,
    # then it also works for the piece.
    def __init__(self, bpm, start_time=None):
        self.bpm = bpm
        self.start_time = start_time
        self.degree = 0
        self.duration = 0
        self.volume = 100

    def __str__(self):
        result = f'tempo change to {self.bpm}'
        if self.start_time is not None:
            result += f' starts at {self.start_time}'
        return result

    def setvolume(self, vol):
        vol = int(vol)
        if vol > 127:
            vol = 127
        self.volume = vol

    __repr__ = __str__


class pitch_bend:
    def __init__(self,
                 value,
                 start_time=None,
                 channel=None,
                 track=0,
                 mode='cents'):
        # general midi pitch bend values could be taken from -8192 to 8192,
        # and the default pitch bend range is -2 semitones to 2 semitones,
        # which is -200 cents to 200 cents, which means 1 cent equals to
        # 8192/200 = 40.96, about 41 values, and 1 semitone equals to
        # 8192/2 = 4096 values.
        # if mode == 'cents', convert value as cents to midi pitch bend values,
        # if mode == 'semitones', convert value as semitones to midi pitch bend values,
        # if mode == other values, use value as midi pitch bend values
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

    def __str__(self):
        result = f'pitch bend {"up" if self.value >= 0 else "down"} by {abs(self.value/40.96)} cents'
        if self.start_time is not None:
            result += f' starts at {self.start_time}'
        return result

    def setvolume(self, vol):
        vol = int(vol)
        if vol > 127:
            vol = 127
        self.volume = vol

    __repr__ = __str__


class tuning:
    def __init__(self,
                 tuning_dict,
                 track=0,
                 sysExChannel=127,
                 realTime=True,
                 tuningProgam=0):
        self.tuning_dict = tuning_dict
        keys = list(self.tuning_dict.keys())
        values = list(self.tuning_dict.values())
        keys = [
            i.degree if type(i) == note else toNote(i).degree for i in keys
        ]
        self.tunings = [(keys[i], values[i]) for i in range(len(keys))]
        self.track = track
        self.sysExChannel = sysExChannel
        self.realTime = realTime
        self.tuningProgam = tuningProgam

    def __str__(self):
        return f'tuning: {self.tuning_dict}'

    __repr__ = __str__


class track:
    def __init__(self,
                 content,
                 instrument=1,
                 start_time=0,
                 tempo=None,
                 track_name=None,
                 channel=None,
                 name=None,
                 pan=None,
                 volume=None):
        self.content = content
        self.instrument = reverse_instruments[instrument] if isinstance(
            instrument, int) else instrument
        self.instruments_number = instruments[self.instrument]
        self.tempo = tempo
        self.start_time = start_time
        self.track_name = track_name
        self.channel = channel
        self.name = name
        self.pan = pan
        self.volume = volume
        if self.pan:
            self.pan = [self.pan] if type(self.pan) != list else self.pan
        else:
            self.pan = []
        if self.volume:
            self.volume = [self.volume
                           ] if type(self.volume) != list else self.volume
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
            f'BPM: {round(self.tempo, 3)}\n' if self.tempo is not None else ""
        ) + f'{msg}instrument: {self.instrument} | start time: {self.start_time} | {self.content}'

    def add_pan(self, value, start_time=1, mode='percentage'):
        self.pan.append(pan(value, start_time, mode))

    def add_volume(self, value, start_time=1, mode='percentage'):
        self.volume.append(volume(value, start_time, mode))

    def play(self, *args, **kwargs):
        import musicpy
        musicpy.play(self, *args, **kwargs)

    def get_interval(self):
        return self.content.interval

    def get_duration(self):
        return self.content.get_duration()

    def get_volume(self):
        return self.content.get_volume()

    def reverse(self, *args, **kwargs):
        temp = copy(self)
        temp.content = temp.content.reverse(*args, **kwargs)
        for each in temp.pan:
            for i in each:
                i.start_time = length - i.start_time + 2
                if i.start_time < 1:
                    i.start_time = 1
        for each in temp.volume:
            for i in each:
                i.start_time = length - i.start_time + 2
                if i.start_time < 1:
                    i.start_time = 1
        return temp

    def reverse_chord(self, *args, **kwargs):
        temp = copy(self)
        temp.content = temp.content.reverse_chord(*args, **kwargs)
        for each in temp.pan:
            for i in each:
                i.start_time = length - i.start_time + 2
                if i.start_time < 1:
                    i.start_time = 1
        for each in temp.volume:
            for i in each:
                i.start_time = length - i.start_time + 2
                if i.start_time < 1:
                    i.start_time = 1
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

    def __mod__(self, n):
        temp = copy(self)
        temp.content %= n
        return temp

    def __pos__(self):
        return self.up()

    def __neg__(self):
        return self.down()

    def __add__(self, i):
        if type(i) == int:
            return self.up(i)
        else:
            temp = copy(self)
            temp.content += i
            return temp

    def __sub__(self, i):
        if type(i) == int:
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


class pan:
    # this is a class to set the pan position for a midi channel,
    # it only works in piece class or track class, and must be set as one of the elements
    # of the pan list of a piece
    def __init__(self, value, start_time=1, mode='percentage'):
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
            self.value_percentage = round((self.value / 127) * 100, 3)
        self.start_time = start_time

    def __str__(self):
        result = f'pan left to {round(((50-self.value_percentage)/50)*100, 3)}%' if self.value_percentage <= 50 else f'pan right to {round(((self.value_percentage-50)/50)*100, 3)}%'
        if self.start_time is not None:
            result += f' starts at {self.start_time}'
        return result

    def get_pan_value(self):
        return -((50 - self.value_percentage) /
                 50) if self.value_percentage <= 50 else (
                     self.value_percentage - 50) / 50

    __repr__ = __str__


class volume:
    # this is a class to set the volume for a midi channel,
    # it only works in piece class or track class, and must be set as one of the elements
    # of the volume list of a piece
    def __init__(self, value, start_time=1, mode='percentage'):
        # when mode == 'percentage', percentage ranges from 0% to 100%,
        # value takes an integer or float number from 0 to 100 (inclusive),
        # when mode == 'value', value takes an integer from 0 to 127 (inclusive)
        self.mode = mode
        if self.mode == 'percentage':
            self.value = int(127 * value / 100)
            self.value_percentage = value
        elif self.mode == 'value':
            self.value = value
            self.value_percentage = round((self.value / 127) * 100, 3)
        self.start_time = start_time

    def __str__(self):
        result = f'volume set to {self.value_percentage}%'
        if self.start_time is not None:
            result += f' starts at {self.start_time}'
        return result

    __repr__ = __str__


class drum:
    def __init__(self,
                 pattern='',
                 mapping=drum_mapping,
                 name=None,
                 notes=None,
                 i=1):
        self.pattern = pattern
        self.mapping = mapping
        self.name = name
        self.notes = self.translate(self.pattern,
                                    self.mapping) if not notes else notes
        self.instrument = i if type(i) == int else (
            drum_set_dict_reverse[i] if i in drum_set_dict_reverse else 1)

    def __str__(self):
        return f"[drum] {self.name if self.name else ''}\n{self.notes}"

    __repr__ = __str__

    def translate(self, pattern, mapping):
        import musicpy
        notes = []
        pattern_intervals = []
        pattern_durations = []
        pattern_volumes = []
        pattern = pattern.replace(' ', '').replace('\n', '')
        units = pattern.split(',')
        repeat_times = 1
        whole_set = False
        left_part_symbol_inds = [
            i - 1 for i in range(len(pattern)) if pattern[i] == '{'
        ]
        right_part_symbol_inds = [0] + [
            i + 2 for i in range(len(pattern)) if pattern[i] == '}'
        ][:-1]
        part_ranges = [[right_part_symbol_inds[k], left_part_symbol_inds[k]]
                       for k in range(len(left_part_symbol_inds))]
        parts = [pattern[k[0]:k[1]] for k in part_ranges]
        part_counter = 0
        named_dict = dict()
        part_replace_ind1 = 0
        part_replace_ind2 = 0
        if units[0].startswith('!'):
            whole_set = True
            whole_set_values = units[0][1:].split(';')
            whole_set_values = [k.replace('|', ',') for k in whole_set_values]
            whole_set_values = process_settings(whole_set_values)
            return self.translate(','.join(units[1:]),
                                  mapping).special_set(*whole_set_values)
        elif units[-1].startswith('!'):
            whole_set = True
            whole_set_values = units[-1][1:].split(';')
            whole_set_values = [k.replace('|', ',') for k in whole_set_values]
            whole_set_values = process_settings(whole_set_values)
            return self.translate(','.join(units[:-1]),
                                  mapping).special_set(*whole_set_values)
        for i in units:
            if i == '':
                continue
            if i[0] == '{' and i[-1] == '}':
                part_replace_ind2 = len(notes)
                current_part = parts[part_counter]
                current_part_notes = self.translate(current_part, mapping)
                part_counter += 1
                part_settings = i[1:-1].split('|')
                for each in part_settings:
                    if each.startswith('!'):
                        current_settings = each[1:].split(';')
                        current_settings = [
                            k.replace('`', ',') for k in current_settings
                        ]
                        current_settings = process_settings(current_settings)
                        current_part_notes = current_part_notes.special_set(
                            *current_settings)
                    elif each.isdigit():
                        current_part_notes %= int(each)
                    elif each.startswith('$'):
                        named_dict[each] = current_part_notes
                notes[part_replace_ind1:
                      part_replace_ind2] = current_part_notes.notes
                pattern_intervals[
                    part_replace_ind1:
                    part_replace_ind2] = current_part_notes.interval
                pattern_durations[
                    part_replace_ind1:
                    part_replace_ind2] = current_part_notes.get_duration()
                pattern_volumes[
                    part_replace_ind1:
                    part_replace_ind2] = current_part_notes.get_volume()
                part_replace_ind1 = len(notes)
            elif i[0] == '[' and i[-1] == ']':
                current_content = i[1:-1]
                current_interval = process_settings([current_content])[0]
                if pattern_intervals:
                    pattern_intervals[-1] += current_interval
            elif '(' in i and i[-1] == ')':
                repeat_times = int(i[i.index('(') + 1:-1])
                repeat_part = i[:i.index('(')]
                if repeat_part.startswith('$'):
                    if '[' in repeat_part and ']' in repeat_part:
                        current_drum_settings = (
                            repeat_part[repeat_part.index('[') +
                                        1:repeat_part.index(']')].replace(
                                            '|', ',')).split(';')
                        repeat_part = repeat_part[:repeat_part.index('[')]
                        current_drum_settings = process_settings(
                            current_drum_settings)
                        repeat_part = named_dict[repeat_part].special_set(
                            *current_drum_settings)
                    else:
                        repeat_part = named_dict[repeat_part]
                else:
                    repeat_part = self.translate(repeat_part, mapping)
                current_notes = repeat_part % repeat_times
                notes.extend(current_notes.notes)
                pattern_intervals.extend(current_notes.interval)
                pattern_durations.extend(current_notes.get_duration())
                pattern_volumes.extend(current_notes.get_volume())
            elif '[' in i and ']' in i:
                current_drum_settings = (i[i.index('[') +
                                           1:i.index(']')].replace(
                                               '|', ',')).split(';')
                current_drum_settings = process_settings(current_drum_settings)
                config_part = i[:i.index('[')]
                if config_part.startswith('$'):
                    if '(' in config_part and ')' in config_part:
                        repeat_times = int(config_part[config_part.index('(') +
                                                       1:-1])
                        config_part = config_part[:config_part.index('(')]
                        config_part = named_dict[config_part] % repeat_times
                    else:
                        config_part = named_dict[config_part]
                else:
                    config_part = self.translate(config_part, mapping)
                current_notes = config_part.special_set(*current_drum_settings)
                notes.extend(current_notes.notes)
                pattern_intervals.extend(current_notes.interval)
                pattern_durations.extend(current_notes.get_duration())
                pattern_volumes.extend(current_notes.get_volume())
            elif ';' in i:
                same_time_notes = i.split(';')
                current_notes = [
                    self.translate(k, mapping) for k in same_time_notes
                ]
                current_notes = musicpy.concat(
                    [k.set(interval=0)
                     for k in current_notes[:-1]] + [current_notes[-1]])
                for j in current_notes.notes[:-1]:
                    j.keep_same_time = True
                notes.extend(current_notes.notes)
                pattern_intervals.extend(current_notes.interval)
                pattern_durations.extend(current_notes.get_duration())
                pattern_volumes.extend(current_notes.get_volume())
            elif i.startswith('$'):
                current_notes = named_dict[i]
                notes.extend(current_notes.notes)
                pattern_intervals.extend(current_notes.interval)
                pattern_durations.extend(current_notes.get_duration())
                pattern_volumes.extend(current_notes.get_volume())
            else:
                notes.append(degree_to_note(mapping[i]))
                pattern_intervals.append(1 / 8)
                pattern_durations.append(1 / 8)
                pattern_volumes.append(100)

        intervals = pattern_intervals
        durations = pattern_durations
        volumes = pattern_volumes
        result = chord(notes) % (durations, intervals, volumes)
        return result

    def play(self, tempo=80, instrument=None, start_time=0):
        import musicpy
        musicpy.play(
            P([self.notes],
              [instrument if instrument is not None else self.instrument],
              tempo, [start_time],
              channels=[9]))

    def __mul__(self, n):
        temp = copy(self)
        temp.notes %= n
        return temp

    def __add__(self, other):
        temp = copy(self)
        if type(other) == tuple and type(other[0]) == drum:
            other = (other[0].notes, ) + other[1:]
        temp.notes += (other.notes if type(other) == drum else other)
        return temp

    def __and__(self, other):
        temp = copy(self)
        if type(other) == tuple and type(other[0]) == drum:
            other = (other[0].notes, ) + other[1:]
        temp.notes &= (other.notes if type(other) == drum else other)
        return temp

    def __or__(self, other):
        temp = copy(self)
        if type(other) == tuple and type(other[0]) == drum:
            other = (other[0].notes, ) + other[1:]
        temp.notes |= (other.notes if type(other) == drum else other)
        return temp

    def __mod__(self, n):
        temp = copy(self)
        temp.notes %= n
        return temp

    def set(self, durations=None, intervals=None, volumes=None):
        return self % (durations, intervals, volumes)

    def info(self):
        return f"[drum] {self.name if self.name else ''}\ninstrument: {drum_set_dict[self.instrument] if self.instrument in drum_set_dict else 'unknown'}\n{', '.join([drum_types[k.degree] for k in self.notes])} with interval {self.notes.interval}"


def event(mode='controller', *args, **kwargs):
    if mode == 'controller':
        return controller_event(*args, **kwargs)
    elif mode == 'copyright':
        return copyright_event(*args, **kwargs)
    elif mode == 'key signature':
        return key_signature(*args, **kwargs)
    elif mode == 'sysex':
        return sysex(*args, **kwargs)
    elif mode == 'text':
        return text_event(*args, **kwargs)
    elif mode == 'time signature':
        return time_signature(*args, **kwargs)
    elif mode == 'universal sysex':
        return universal_sysex(*args, **kwargs)
    elif mode == 'nrpn':
        return rpn(*args, **kwargs, registered=False)
    elif mode == 'rpn':
        return rpn(*args, **kwargs, registered=True)
    elif mode == 'tuning bank':
        return tuning_bank(*args, **kwargs)
    elif mode == 'tuning program':
        return tuning_program(*args, **kwargs)
    elif mode == 'channel pressure':
        return channel_pressure(*args, **kwargs)
    elif mode == 'program change':
        return program_change(*args, **kwargs)
    elif mode == 'track name':
        return track_name(*args, **kwargs)


class controller_event:
    def __init__(self,
                 track=0,
                 channel=0,
                 time=1,
                 controller_number=None,
                 parameter=None):
        self.track = track
        self.channel = channel
        self.time = (time - 1) * 4
        self.controller_number = controller_number
        self.parameter = parameter


class copyright_event:
    def __init__(self, track=0, time=1, notice=None):
        self.track = track
        self.time = (time - 1) * 4
        self.notice = notice


class key_signature:
    def __init__(self,
                 track=0,
                 time=1,
                 accidentals=None,
                 accidental_type=None,
                 mode=None):
        self.track = track
        self.time = (time - 1) * 4
        self.accidentals = accidentals
        self.accidental_type = accidental_type
        self.mode = mode


class sysex:
    def __init__(self, track=0, time=1, manID=None, payload=None):
        self.track = track
        self.time = (time - 1) * 4
        self.manID = manID
        self.payload = payload


class text_event:
    def __init__(self, track=0, time=1, text=''):
        self.track = track
        self.time = (time - 1) * 4
        self.text = text


class time_signature:
    def __init__(self,
                 track=0,
                 time=1,
                 numerator=None,
                 denominator=None,
                 clocks_per_tick=None,
                 notes_per_quarter=8):
        self.track = track
        self.time = (time - 1) * 4
        self.numerator = numerator
        self.denominator = denominator
        self.clocks_per_tick = clocks_per_tick
        self.notes_per_quarter = notes_per_quarter


class universal_sysex:
    def __init__(self,
                 track=0,
                 time=1,
                 code=None,
                 subcode=None,
                 payload=None,
                 sysExChannel=127,
                 realTime=False):
        self.track = track
        self.time = (time - 1) * 4
        self.code = code
        self.subcode = subcode
        self.payload = payload
        self.sysExChannel = sysExChannel
        self.realTime = realTime


class rpn:
    def __init__(self,
                 track=0,
                 channel=0,
                 time=1,
                 controller_msb=None,
                 controller_lsb=None,
                 data_msb=None,
                 data_lsb=None,
                 time_order=False,
                 registered=True):
        self.track = track
        self.channel = channel
        self.time = (time - 1) * 4
        self.controller_msb = controller_msb
        self.controller_lsb = controller_lsb
        self.data_msb = data_msb
        self.data_lsb = data_lsb
        self.time_order = time_order
        self.registered = registered


class tuning_bank:
    def __init__(self,
                 track=0,
                 channel=0,
                 time=1,
                 bank=None,
                 time_order=False):
        self.track = track
        self.channel = channel
        self.time = (time - 1) * 4
        self.bank = bank
        self.time_order = time_order


class tuning_program:
    def __init__(self,
                 track=0,
                 channel=0,
                 time=1,
                 program=None,
                 time_order=False):
        self.track = track
        self.channel = channel
        self.time = (time - 1) * 4
        self.program = program
        self.time_order = time_order


class channel_pressure:
    def __init__(self, track=0, channel=0, time=1, pressure_value=None):
        self.track = track
        self.channel = channel
        self.time = (time - 1) * 4
        self.pressure_value = pressure_value


class program_change:
    def __init__(self, track=0, channel=0, time=1, program=0):
        self.track = track
        self.channel = channel
        self.time = (time - 1) * 4
        self.program = program


class track_name:
    def __init__(self, track=0, time=1, name=''):
        self.track = track
        self.time = (time - 1) * 4
        self.name = name
