from copy import deepcopy as copy
import functools

if __name__ == 'musicpy.parsers':
    from . import database
    from .primitives import note, tempo, pitch_bend, pan, volume, event, beat, rest_symbol, continue_symbol, rest
else:
    import database
    from primitives import note, tempo, pitch_bend, pan, volume, event, beat, rest_symbol, continue_symbol, rest


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
            relative_pitch_num = 0
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
            if '(' in each and ')' in each:
                each, relative_pitch_settings = each.split('(', 1)
                relative_pitch_settings = relative_pitch_settings[:-1]
                relative_pitch_num = _parse_change_num(
                    relative_pitch_settings)[0]
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
                    has_same_time=has_same_time,
                    relative_pitch_num=relative_pitch_num)
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
                      has_same_time=False,
                      relative_pitch_num=0):
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
        current_note = last_non_num_note + current_num + relative_pitch_num
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
        current_note = mp.to_note(
            each, duration=duration, volume=volume,
            pitch=rootpitch) + relative_pitch_num
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
    else:
        raise ValueError('Invalid relative pitch syntax')
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
    if __name__ == 'musicpy.parsers':
        from .chord_class import chord
    else:
        from chord_class import chord
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