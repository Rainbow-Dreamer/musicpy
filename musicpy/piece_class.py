from copy import deepcopy as copy
from fractions import Fraction
from dataclasses import dataclass
import functools

if __name__ == 'musicpy.piece_class':
    from . import database
    from .primitives import note, tempo, pitch_bend, pan, volume, event, beat, rest_symbol, continue_symbol, rest
    from .chord_class import chord, chord_type
    from .scale_class import scale
else:
    import database
    from primitives import note, tempo, pitch_bend, pan, volume, event, beat, rest_symbol, continue_symbol, rest
    from chord_class import chord, chord_type
    from scale_class import scale


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
        if isinstance(n, tuple):
            return self | n
        else:
            temp = copy(self)
            for i in range(n - 1):
                temp |= self
            return temp

    def __or__(self, n):
        if isinstance(n, tuple):
            n, start_time = n
            if isinstance(n, int):
                temp = copy(self)
                for k in range(n - 1):
                    temp |= (self, start_time)
                return temp
            elif isinstance(n, piece):
                return self.merge_track(n,
                                        mode='after',
                                        extra_interval=start_time)
        elif isinstance(n, piece):
            return self + n
        elif isinstance(n, (int, float)):
            return self.rest(n)

    def __and__(self, n):
        if isinstance(n, tuple):
            n, start_time = n
            if isinstance(n, int):
                temp = copy(self)
                for k in range(n - 1):
                    temp &= (self, (k + 1) * start_time)
                return temp
        elif isinstance(n, int):
            return self & (n, 0)
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
                    ind_mode=1,
                    include_last_interval=False,
                    ignore_last_duration=False,
                    extra_interval=0):
        temp = copy(self)
        temp2 = copy(n)
        max_track_number = max(len(self), len(n))
        temp_length = len(temp)
        if temp_length < max_track_number:
            temp.pan.extend([[]
                             for i in range(max_track_number - temp_length)])
            temp.volume.extend([[]
                                for i in range(max_track_number - temp_length)
                                ])
        if temp.channels is not None:
            free_channel_numbers = [
                i for i in range(16) if i not in temp.channels
            ]
            counter = 0
        if mode == 'after':
            if ignore_last_duration:
                bars_mode = 0
            else:
                bars_mode = 1 if not include_last_interval else 2
            start_time = temp.bars(mode=bars_mode) + extra_interval
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
                for each in temp2.pan[i]:
                    each.start_time += start_time
                for each in temp2.volume[i]:
                    each.start_time += start_time
                temp.pan[current_ind].extend(temp2.pan[i])
                temp.volume[current_ind].extend(temp2.volume[i])
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
                for each in temp2.pan[i]:
                    each.start_time += start_time
                for each in temp2.volume[i]:
                    each.start_time += start_time
                temp.pan.append(temp2.pan[i])
                temp.volume.append(temp2.volume[i])
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

    def repeat(self,
               n,
               start_time=0,
               include_last_interval=False,
               ignore_last_duration=False,
               ind_mode=1,
               mode='after'):
        temp = copy(self)
        if mode == 'after':
            for k in range(n - 1):
                temp = temp.merge_track(
                    self,
                    mode=mode,
                    extra_interval=start_time,
                    include_last_interval=include_last_interval,
                    ignore_last_duration=ignore_last_duration,
                    ind_mode=ind_mode)
        elif mode == 'head':
            for k in range(n - 1):
                temp = temp.merge_track(
                    self,
                    mode=mode,
                    start_time=(k + 1) * start_time,
                    include_last_interval=include_last_interval,
                    ignore_last_duration=ignore_last_duration,
                    ind_mode=ind_mode)
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
        relative_pitch_num = 0
        if '(' in current_append_notes and ')' in current_append_notes:
            current_append_notes, relative_pitch_settings = current_append_notes.split(
                '(', 1)
            relative_pitch_settings = relative_pitch_settings[:-1]
            relative_pitch_num = _parse_change_num(relative_pitch_settings)[0]
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
        if relative_pitch_num != 0:
            dotted_num_list = [i.dotted_num for i in current_append_notes]
            current_append_notes = [
                each_note + relative_pitch_num
                for each_note in current_append_notes
            ]
            for i, each_note in enumerate(current_append_notes):
                each_note.dotted_num = dotted_num_list[i]
            self.last_non_num_note = current_append_notes[-1]
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
        relative_pitch_num = 0
        if '(' in current_append_notes and ')' in current_append_notes:
            current_append_notes, relative_pitch_settings = current_append_notes.split(
                '(', 1)
            relative_pitch_settings = relative_pitch_settings[:-1]
            relative_pitch_num = _parse_change_num(relative_pitch_settings)[0]
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

        if relative_pitch_num != 0:
            dotted_num_list = [i.dotted_num for i in current_append_notes]
            current_append_notes = [
                each_note + relative_pitch_num
                for each_note in current_append_notes
            ]
            for i, each_note in enumerate(current_append_notes):
                each_note.dotted_num = dotted_num_list[i]
            self.last_non_num_note = current_append_notes[-1]
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


if __name__ == 'musicpy.piece_class':
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
