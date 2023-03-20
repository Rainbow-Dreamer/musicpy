import os
import math
import struct
import chunk
from io import BytesIO
import mido_fix as mido
import functools
import json

if __name__ == '__main__' or __name__ == 'musicpy':
    import database
    from structures import *
else:
    from . import database
    from .structures import *

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

has_audio_interface = True
try:
    pygame.mixer.init(44100, -16, 2, 1024)
except pygame.error:
    has_audio_interface = False


class MetaSpec_key_signature(mido.midifiles.meta.MetaSpec_key_signature):

    def decode(self, message, data):
        try:
            super().decode(message, data)
        except mido.midifiles.meta.KeySignatureError:
            message.key = None

    def check(self, name, value):
        if value is not None:
            super().check(name, value)


mido.midifiles.meta.add_meta_spec(MetaSpec_key_signature)


def method_wrapper(cls):

    def method_decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return result

        if not isinstance(cls, list):
            types = [cls]
        else:
            types = cls
        for each in types:
            setattr(each, func.__name__, wrapper)
        return func

    return method_decorator


def to_note(notename, duration=1 / 4, volume=100, pitch=4, channel=None):
    num_text = ''.join([x for x in notename if x.isdigit()])
    if not num_text.isdigit():
        num = pitch
    else:
        num = int(num_text)
    name = ''.join([x for x in notename if not x.isdigit()])
    return note(name, num, duration, volume, channel)


def degree_to_note(degree, duration=1 / 4, volume=100, channel=None):
    name = database.standard_reverse[degree % 12]
    num = (degree // 12) - 1
    return note(name, num, duration, volume, channel)


def degrees_to_chord(ls, *args, **kwargs):
    return chord([degree_to_note(i) for i in ls], *args, **kwargs)


def note_to_degree(obj):
    if not isinstance(obj, note):
        obj = to_note(obj)
    return database.standard[obj.name] + 12 * (obj.num + 1)


def trans_note(notename, duration=1 / 4, volume=100, pitch=4, channel=None):
    num = ''.join([x for x in notename if x.isdigit()])
    if not num:
        num = pitch
    else:
        num = int(num)
    name = ''.join([x for x in notename if not x.isdigit()])
    return note(name, num, duration, volume, channel)


def to_tuple(obj):
    if isinstance(obj, str):
        return (obj, )
    try:
        return tuple(obj)
    except:
        return (obj, )


def get_freq(y, standard=440):
    if isinstance(y, str):
        y = to_note(y)
    semitones = y.degree - 69
    return standard * 2**(semitones / 12)


def freq_to_note(freq, to_str=False, standard=440):
    quotient = freq / standard
    semitones = round(math.log(quotient, 2) * 12)
    result = N('A4') + semitones
    if to_str:
        return str(result)
    return result


def secondary_dom(root, current_scale='major'):
    if isinstance(root, str):
        root = to_note(root)
    newscale = scale(root, current_scale)
    return newscale.dom_chord()


def secondary_dom7(root, current_scale='major'):
    if isinstance(root, str):
        root = to_note(root)
    newscale = scale(root, current_scale)
    return newscale.dom7_chord()


def get_chord_by_interval(start,
                          interval1,
                          duration=1 / 4,
                          interval=0,
                          cumulative=True,
                          start_time=0):

    if isinstance(start, str):
        start = to_note(start)
    result = [start]
    if cumulative:
        # in this case all the notes has distance only with the start note
        startind = start.degree
        result += [
            degree_to_note(startind + interval1[i])
            for i in range(len(interval1))
        ]
    else:
        # in this case current note and next note has distance corresponding to the given interval
        startind = start.degree
        for i in range(len(interval1)):
            startind += interval1[i]
            result.append(degree_to_note(startind))
    return chord(result, duration, interval, start_time=start_time)


def inversion(current_chord, num=1):
    return current_chord.inversion(num)


def get_chord(start,
              current_chord_type=None,
              duration=1 / 4,
              intervals=None,
              interval=None,
              cumulative=True,
              pitch=4,
              ind=0,
              start_time=0,
              custom_mapping=None):
    if not isinstance(start, note):
        start = to_note(start, pitch=pitch)
    if interval is not None:
        return get_chord_by_interval(start,
                                     interval,
                                     duration,
                                     intervals,
                                     cumulative,
                                     start_time=start_time)
    pre_chord_type = current_chord_type
    current_chord_type = current_chord_type.lower().replace(' ', '')
    initial = start.degree
    chordlist = [start]
    current_chord_types = database.chordTypes if custom_mapping is None else custom_mapping
    if pre_chord_type in current_chord_types:
        interval_pre_chord_type = current_chord_types[pre_chord_type][ind]
        interval = interval_pre_chord_type
    else:
        if current_chord_type in current_chord_types:
            interval_current_chord_type = current_chord_types[
                current_chord_type][ind]
            interval = interval_current_chord_type
        else:
            raise ValueError(
                f'could not detect the chord type {current_chord_type}')
    for i in range(len(interval)):
        chordlist.append(degree_to_note(initial + interval[i]))
    return chord(chordlist, duration, intervals, start_time=start_time)


def concat(chordlist, mode='+', extra=None, start=None):
    if not chordlist:
        return chordlist
    temp = copy(chordlist[0]) if start is None else start
    start_ind = 1 if start is None else 0
    chordlist = chordlist[start_ind:]
    if mode == '+':
        if not extra:
            for t in chordlist:
                temp += t
        else:
            for t in chordlist:
                temp += (t, extra)
    elif mode == '|':
        if not extra:
            for t in chordlist:
                temp |= t
        else:
            for t in chordlist:
                temp |= (t, extra)
    elif mode == '&':
        if not extra:
            for t in chordlist:
                temp &= t
        else:
            extra_unit = extra
            for t in chordlist:
                temp &= (t, extra)
                extra += extra_unit
    return temp


def multi_voice(*current_chord, method=chord, start_times=None):
    current_chord = [
        method(i) if isinstance(i, str) else i for i in current_chord
    ]
    if start_times is not None:
        current_chord = [current_chord[0]
                         ] + [i.with_start(0) for i in current_chord[1:]]
        result = copy(current_chord[0])
        for i in range(1, len(current_chord)):
            result &= (current_chord[i], start_times[i - 1])
    else:
        result = concat(current_chord, mode='&')
    return result


@method_wrapper([note, chord, piece, track, drum])
def play(current_chord,
         bpm=120,
         channel=0,
         start_time=None,
         name='temp.mid',
         instrument=None,
         i=None,
         save_as_file=True,
         msg=None,
         nomsg=False,
         ticks_per_beat=960,
         wait=False,
         **midi_args):
    file = write(current_chord=current_chord,
                 bpm=bpm,
                 channel=channel,
                 start_time=start_time,
                 name=name,
                 instrument=instrument,
                 i=i,
                 save_as_file=save_as_file,
                 msg=msg,
                 nomsg=nomsg,
                 ticks_per_beat=ticks_per_beat,
                 **midi_args)
    if save_as_file:
        result_file = name
        pygame.mixer.music.load(result_file)
        pygame.mixer.music.play()
        if wait:
            while pygame.mixer.music.get_busy():
                pygame.time.delay(10)
    else:
        file.seek(0)
        pygame.mixer.music.load(file)
        pygame.mixer.music.play()
        if wait:
            while pygame.mixer.music.get_busy():
                pygame.time.delay(10)


def read(name,
         is_file=False,
         get_off_drums=False,
         clear_empty_notes=False,
         clear_other_channel_msg=False,
         split_channels=None):
    if is_file:
        name.seek(0)
        try:
            current_midi = mido.MidiFile(file=name, clip=True)
            whole_bpm = find_first_tempo(name, is_file=is_file)
            name.close()
        except Exception as OSError:
            name.seek(0)
            current_midi = mido.MidiFile(file=riff_to_midi(name), clip=True)
            whole_bpm = find_first_tempo(name, is_file=is_file)
            name.close()
        name = getattr(name, 'name', '')
    else:
        try:
            current_midi = mido.MidiFile(name, clip=True)
        except Exception as OSError:
            current_midi = mido.MidiFile(file=riff_to_midi(name), clip=True)
        whole_bpm = find_first_tempo(name, is_file=is_file)
    whole_tracks = current_midi.tracks
    if not whole_tracks:
        raise ValueError(
            'No tracks found in the MIDI file, please check if the input MIDI file is empty'
        )
    current_type = current_midi.type
    interval_unit = current_midi.ticks_per_beat * 4
    if split_channels is None:
        if current_type == 0:
            split_channels = True
        elif current_type == 1:
            split_channels = False
        elif current_type == 2:
            split_channels = False
    changes = []
    if not split_channels:
        changes_track_ind = [
            i for i, each in enumerate(whole_tracks)
            if all((i.is_meta or i.type == 'sysex') for i in each)
        ]
        changes_track = [whole_tracks[i] for i in changes_track_ind]
        if changes_track:
            changes = [
                _midi_to_chord(each,
                               interval_unit,
                               add_track_num=split_channels,
                               clear_empty_notes=clear_empty_notes)[0]
                for each in changes_track
            ]
            changes = concat(changes)
        available_tracks = [
            whole_tracks[i] for i in range(len(whole_tracks))
            if i not in changes_track_ind
        ]
        all_tracks = [
            _midi_to_chord(available_tracks[j],
                           interval_unit,
                           whole_bpm,
                           add_track_num=split_channels,
                           clear_empty_notes=clear_empty_notes,
                           track_ind=j) for j in range(len(available_tracks))
        ]
        start_times_list = [j[2] for j in all_tracks]
        if available_tracks:
            channels_list = [[
                i.channel for i in each if hasattr(i, 'channel')
            ] for each in available_tracks]
            channels_list = [each[0] if each else -1 for each in channels_list]
            unassigned_channels = channels_list.count(-1)
            if unassigned_channels > 0:
                free_channel_numbers = [
                    i for i in range(16) if i not in channels_list
                ]
                free_channel_numbers_length = len(free_channel_numbers)
                unassigned_channels_number = []
                for k in range(unassigned_channels):
                    if k < free_channel_numbers_length:
                        unassigned_channels_number.append(
                            free_channel_numbers[k])
                    else:
                        unassigned_channels_number.append(
                            16 + k - free_channel_numbers_length)
                channels_list = [
                    each if each != -1 else unassigned_channels_number.pop(0)
                    for each in channels_list
                ]
        else:
            channels_list = None

        instruments = []
        for each in available_tracks:
            current_program = [
                i.program for i in each if hasattr(i, 'program')
            ]
            if current_program:
                instruments.append(current_program[0] + 1)
            else:
                instruments.append(1)
        chords_list = [each[0] for each in all_tracks]
        pan_list = [k.pan_list for k in chords_list]
        volume_list = [k.volume_list for k in chords_list]
        tracks_names_list = [[k.name for k in each if k.type == 'track_name']
                             for each in available_tracks]
        if all(j for j in tracks_names_list):
            tracks_names_list = [j[0] for j in tracks_names_list]
        else:
            tracks_names_list = None
        result_piece = piece(tracks=chords_list,
                             instruments=instruments,
                             bpm=whole_bpm,
                             start_times=start_times_list,
                             track_names=tracks_names_list,
                             channels=channels_list,
                             name=os.path.splitext(os.path.basename(name))[0],
                             pan=pan_list,
                             volume=volume_list)
        result_piece.other_messages = concat(
            [each_track.other_messages for each_track in result_piece.tracks],
            start=[])
    else:
        available_tracks = whole_tracks
        channels_numbers = concat(
            [[i.channel for i in j if hasattr(i, 'channel')]
             for j in available_tracks])
        if not channels_numbers:
            raise ValueError(
                'Split channels requires the MIDI file contains channel messages for tracks'
            )
        channels_list = []
        for each in channels_numbers:
            if each not in channels_list:
                channels_list.append(each)
        channels_num = len(channels_list)
        track_channels = channels_list
        all_tracks = [
            _midi_to_chord(each,
                           interval_unit,
                           whole_bpm,
                           add_track_num=split_channels,
                           clear_empty_notes=clear_empty_notes,
                           track_ind=j,
                           track_channels=track_channels)
            for j, each in enumerate(available_tracks)
        ]
        if len(available_tracks) > 1:
            available_tracks = concat(available_tracks)
            pitch_bends = concat(
                [i[0].split(pitch_bend, get_time=True) for i in all_tracks])
            for each in all_tracks:
                each[0].clear_pitch_bend('all')
            current_available_tracks = [
                each for each in all_tracks if any(
                    isinstance(i, note) for i in each[0])
            ]
            start_time_ls = [j[2] for j in all_tracks]
            available_start_time_ls = [j[2] for j in current_available_tracks]
            first_track_ind = start_time_ls.index(min(available_start_time_ls))
            all_tracks.insert(0, all_tracks.pop(first_track_ind))
            first_track = all_tracks[0]
            all_track_notes, tempos, first_track_start_time = first_track
            for i in all_tracks[1:]:
                all_track_notes &= (i[0], i[2] - first_track_start_time)
            all_track_notes.other_messages = concat(
                [each[0].other_messages for each in all_tracks])
            all_track_notes += pitch_bends
            all_track_notes.pan_list = concat(
                [k[0].pan_list for k in all_tracks])
            all_track_notes.volume_list = concat(
                [k[0].volume_list for k in all_tracks])
            all_tracks = [all_track_notes, tempos, first_track_start_time]
        else:
            available_tracks = available_tracks[0]
            all_tracks = all_tracks[0]
        pan_list = all_tracks[0].pan_list
        volume_list = all_tracks[0].volume_list
        current_instruments_list = [[
            i for i in available_tracks
            if i.type == 'program_change' and i.channel == k
        ] for k in channels_list]
        instruments = [
            each[0].program + 1 if each else 1
            for each in current_instruments_list
        ]
        tracks_names_list = [
            i.name for i in available_tracks if i.type == 'track_name'
        ]
        rename_track_names = False
        if (not tracks_names_list) or (len(tracks_names_list) != channels_num):
            tracks_names_list = [f'Channel {i+1}' for i in channels_list]
            rename_track_names = True
        result_merge_track = all_tracks[0]
        result_piece = piece(
            tracks=[chord([]) for i in range(channels_num)],
            instruments=[database.reverse_instruments[i] for i in instruments],
            bpm=whole_bpm,
            track_names=tracks_names_list,
            channels=channels_list,
            name=os.path.splitext(os.path.basename(name))[0],
            pan=[[] for i in range(channels_num)],
            volume=[[] for i in range(channels_num)])
        result_piece.reconstruct(result_merge_track,
                                 all_tracks[2],
                                 include_empty_track=True)
        if len(result_piece.channels) != channels_num:
            pan_list = [
                i for i in pan_list if i.channel in result_piece.channels
            ]
            volume_list = [
                i for i in volume_list if i.channel in result_piece.channels
            ]
            for each in pan_list:
                each.track = result_piece.channels.index(each.channel)
            for each in volume_list:
                each.track = result_piece.channels.index(each.channel)
            for k in range(len(result_piece.tracks)):
                for each in result_piece.tracks[k].notes:
                    if isinstance(each, pitch_bend):
                        each.track = k
            result_merge_track.other_messages = [
                i for i in result_merge_track.other_messages
                if not (hasattr(i, 'channel')
                        and i.channel not in result_piece.channels)
            ]
            for each in result_merge_track.other_messages:
                if hasattr(each, 'channel'):
                    each.track = result_piece.channels.index(each.channel)
        result_piece.other_messages = result_merge_track.other_messages
        for k in range(len(result_piece)):
            current_other_messages = [
                i for i in result_piece.other_messages if i.track == k
            ]
            result_piece.tracks[k].other_messages = current_other_messages
            current_pan = [i for i in pan_list if i.track == k]
            result_piece.pan[k] = current_pan
            current_volume = [i for i in volume_list if i.track == k]
            result_piece.volume[k] = current_volume
        if not rename_track_names:
            current_track_names = result_piece.get_msg('track_name')
            for i in range(len(current_track_names)):
                result_piece.tracks[i].other_messages.append(
                    current_track_names[i])
    if current_type == 1 and changes:
        if result_piece.tracks:
            result_piece.tracks[0].notes.extend(changes.notes)
            result_piece.tracks[0].interval.extend(changes.interval)
            result_piece.tracks[0].other_messages[0:0] = changes.other_messages
        result_piece.other_messages[0:0] = changes.other_messages

    if clear_other_channel_msg:
        result_piece.other_messages = [
            i for i in result_piece.other_messages
            if not (hasattr(i, 'channel')
                    and i.channel not in result_piece.channels)
        ]
    if get_off_drums:
        result_piece.get_off_drums()
    for i in result_piece.tracks:
        if hasattr(i, 'pan_list'):
            del i.pan_list
        if hasattr(i, 'volume_list'):
            del i.volume_list
    return result_piece


def _midi_to_chord(current_track,
                   interval_unit,
                   bpm=None,
                   add_track_num=False,
                   clear_empty_notes=False,
                   track_ind=0,
                   track_channels=None):
    intervals = []
    notelist = []
    notes_len = len(current_track)
    find_first_note = False
    start_time = 0
    current_time = 0
    pan_list = []
    volume_list = []
    other_messages = []

    for i in range(notes_len):
        current_msg = current_track[i]
        current_time += current_msg.time
        if current_msg.type == 'note_on' and current_msg.velocity != 0:
            current_msg_velocity = current_msg.velocity
            current_msg_note = current_msg.note
            current_msg_channel = current_msg.channel
            if not find_first_note:
                find_first_note = True
                start_time = sum(current_track[j].time
                                 for j in range(i + 1)) / interval_unit
                if start_time.is_integer():
                    start_time = int(start_time)
            current_interval = 0
            current_duration = 0
            current_note_interval = 0
            current_note_duration = 0
            find_interval = False
            find_duration = False
            for k in range(i + 1, notes_len):
                new_msg = current_track[k]
                new_msg_type = new_msg.type
                current_interval += new_msg.time
                current_duration += new_msg.time
                if not find_interval:
                    if new_msg_type == 'note_on' and new_msg.velocity != 0:
                        find_interval = True
                        current_interval /= interval_unit
                        if current_interval.is_integer():
                            current_interval = int(current_interval)
                        current_note_interval = current_interval
                if not find_duration:
                    if (
                            new_msg_type == 'note_off' or
                        (new_msg_type == 'note_on' and new_msg.velocity == 0)
                    ) and new_msg.note == current_msg_note and new_msg.channel == current_msg_channel:
                        find_duration = True
                        current_duration /= interval_unit
                        if current_duration.is_integer():
                            current_duration = int(current_duration)
                        current_note_duration = current_duration
                if find_interval and find_duration:
                    break
            if not find_interval:
                current_note_interval = current_note_duration
            current_append_note = degree_to_note(
                current_msg_note,
                duration=current_note_duration,
                volume=current_msg_velocity)
            current_append_note.channel = current_msg_channel
            intervals.append(current_note_interval)
            if add_track_num:
                if track_channels:
                    current_append_note.track_num = track_channels.index(
                        current_msg_channel)
                else:
                    current_append_note.track_num = track_ind
            notelist.append(current_append_note)
        elif current_msg.type == 'set_tempo':
            current_tempo = tempo(mido.tempo2bpm(current_msg.tempo),
                                  current_time / interval_unit,
                                  track=track_ind)
            if add_track_num:
                current_tempo.track_num = track_ind
            notelist.append(current_tempo)
            intervals.append(0)
        elif current_msg.type == 'pitchwheel':
            current_msg_channel = current_msg.channel
            if track_channels:
                current_track_ind = track_channels.index(current_msg_channel)
            else:
                current_track_ind = track_ind
            current_pitch_bend = pitch_bend(current_msg.pitch,
                                            current_time / interval_unit,
                                            channel=current_msg_channel,
                                            track=current_track_ind,
                                            mode='values')
            if add_track_num:
                current_pitch_bend.track_num = current_track_ind
            notelist.append(current_pitch_bend)
            intervals.append(0)
        elif current_msg.type == 'control_change':
            current_msg_channel = current_msg.channel
            if track_channels:
                current_track_ind = track_channels.index(current_msg_channel)
            else:
                current_track_ind = track_ind
            if current_msg.control == 10:
                current_pan_msg = pan(current_msg.value,
                                      current_time / interval_unit,
                                      'value',
                                      channel=current_msg_channel,
                                      track=current_track_ind)
                pan_list.append(current_pan_msg)
            elif current_msg.control == 7:
                current_volume_msg = volume(current_msg.value,
                                            current_time / interval_unit,
                                            'value',
                                            channel=current_msg_channel,
                                            track=current_track_ind)
                volume_list.append(current_volume_msg)
            else:
                _read_other_messages(current_msg, other_messages,
                                     current_time / interval_unit,
                                     current_track_ind)
        else:
            if track_channels and hasattr(current_msg, 'channel'):
                current_msg_channel = current_msg.channel
                current_track_ind = track_channels.index(current_msg_channel)
            else:
                current_track_ind = track_ind
            _read_other_messages(current_msg, other_messages,
                                 current_time / interval_unit,
                                 current_track_ind)
    result = chord(notelist, interval=intervals)
    if clear_empty_notes:
        result.interval = [
            result.interval[j] for j in range(len(result))
            if not isinstance(result.notes[j], note)
            or result.notes[j].duration > 0
        ]
        result.notes = [
            each for each in result.notes
            if not isinstance(each, note) or each.duration > 0
        ]
    result.pan_list = pan_list
    result.volume_list = volume_list
    result.other_messages = other_messages
    if bpm is not None:
        return [result, bpm, start_time]
    else:
        return [result, start_time]


def _read_other_messages(message, other_messages, time, track_ind):
    if message.type not in ['note_on', 'note_off']:
        current_attributes = {
            i: j
            for i, j in vars(message).items() if i != 'time'
        }
        current_message = event(track=track_ind,
                                start_time=time,
                                **current_attributes)
        current_message.is_meta = message.is_meta
        other_messages.append(current_message)


def write(current_chord,
          bpm=120,
          channel=0,
          start_time=None,
          name='temp.mid',
          instrument=None,
          i=None,
          save_as_file=True,
          msg=None,
          nomsg=False,
          ticks_per_beat=960,
          **midi_args):
    if i is not None:
        instrument = i
    is_track_type = False
    is_piece_like_type = True
    if isinstance(current_chord, note):
        current_chord = chord([current_chord])
    elif isinstance(current_chord, list):
        current_chord = concat(current_chord, '|')
    if isinstance(current_chord, chord):
        is_track_type = True
        is_piece_like_type = False
        if instrument is None:
            instrument = 1
        current_chord = P(
            tracks=[current_chord],
            instruments=[instrument],
            bpm=bpm,
            channels=[channel],
            start_times=[
                current_chord.start_time if start_time is None else start_time
            ],
            other_messages=current_chord.other_messages)
    elif isinstance(current_chord, track):
        is_track_type = True
        if hasattr(current_chord, 'other_messages'):
            msg = current_chord.other_messages
        else:
            msg = current_chord.content.other_messages
        current_chord = build(current_chord, bpm=current_chord.bpm)
    elif isinstance(current_chord, drum):
        is_track_type = True
        is_piece_like_type = False
        if hasattr(current_chord, 'other_messages'):
            msg = current_chord.other_messages
        current_chord = P(tracks=[current_chord.notes],
                          instruments=[current_chord.instrument],
                          bpm=bpm,
                          start_times=[
                              current_chord.notes.start_time
                              if start_time is None else start_time
                          ],
                          channels=[9])
    track_number, start_times, instruments_numbers, bpm, tracks_contents, track_names, channels, pan_msg, volume_msg = \
    current_chord.track_number, current_chord.start_times, current_chord.instruments_numbers, current_chord.bpm, current_chord.tracks, current_chord.track_names, current_chord.channels, current_chord.pan, current_chord.volume
    instruments_numbers = [
        i if isinstance(i, int) else database.INSTRUMENTS[i]
        for i in instruments_numbers
    ]
    current_midi = mido.MidiFile(ticks_per_beat=ticks_per_beat, **midi_args)
    current_midi.tracks.extend([mido.MidiTrack() for i in range(track_number)])
    current_midi.tracks[0].append(
        mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))
    for i in range(track_number):
        if channels:
            current_channel = channels[i]
        else:
            current_channel = i
        current_midi.tracks[i].append(
            mido.Message('program_change',
                         channel=current_channel,
                         time=0,
                         program=instruments_numbers[i] - 1))
        if track_names:
            current_midi.tracks[i].append(
                mido.MetaMessage('track_name', time=0, name=track_names[i]))

        current_pan_msg = pan_msg[i]
        if current_pan_msg:
            for each in current_pan_msg:
                current_pan_track = i if each.track is None else each.track
                current_pan_channel = current_channel if each.channel is None else each.channel
                current_midi.tracks[
                    current_pan_track if not is_track_type else 0].append(
                        mido.Message('control_change',
                                     channel=current_pan_channel,
                                     time=int(each.start_time *
                                              ticks_per_beat * 4),
                                     control=10,
                                     value=each.value))
        current_volume_msg = volume_msg[i]
        if current_volume_msg:
            for each in current_volume_msg:
                current_volume_channel = current_channel if each.channel is None else each.channel
                current_volume_track = i if each.track is None else each.track
                current_midi.tracks[
                    current_volume_track if not is_track_type else 0].append(
                        mido.Message('control_change',
                                     channel=current_volume_channel,
                                     time=int(each.start_time *
                                              ticks_per_beat * 4),
                                     control=7,
                                     value=each.value))

        content = tracks_contents[i]
        content_notes = content.notes
        content_intervals = content.interval
        current_start_time = start_times[i]
        if is_piece_like_type:
            current_start_time += content.start_time
        current_start_time = int(current_start_time * ticks_per_beat * 4)
        for j in range(len(content)):
            current_note = content_notes[j]
            current_type = type(current_note)
            if current_type == note:
                current_note_on_message = mido.Message(
                    'note_on',
                    time=current_start_time,
                    channel=current_channel
                    if current_note.channel is None else current_note.channel,
                    note=current_note.degree,
                    velocity=current_note.volume)
                current_note_off_message = mido.Message(
                    'note_off',
                    time=current_start_time +
                    int(current_note.duration * ticks_per_beat * 4),
                    channel=current_channel
                    if current_note.channel is None else current_note.channel,
                    note=current_note.degree,
                    velocity=current_note.volume)
                current_midi.tracks[i].append(current_note_on_message)
                current_midi.tracks[i].append(current_note_off_message)
                current_start_time += int(content_intervals[j] *
                                          ticks_per_beat * 4)
            elif current_type == tempo:
                if current_note.start_time is not None:
                    if current_note.start_time < 0:
                        tempo_change_time = 0
                    else:
                        tempo_change_time = int(current_note.start_time *
                                                ticks_per_beat * 4)
                else:
                    tempo_change_time = current_start_time
                current_midi.tracks[0].append(
                    mido.MetaMessage('set_tempo',
                                     time=tempo_change_time,
                                     tempo=mido.bpm2tempo(current_note.bpm)))
            elif current_type == pitch_bend:
                if current_note.start_time is not None:
                    if current_note.start_time < 0:
                        pitch_bend_time = 0
                    else:
                        pitch_bend_time = int(current_note.start_time *
                                              ticks_per_beat * 4)
                else:
                    pitch_bend_time = current_start_time
                pitch_bend_track = i if current_note.track is None else current_note.track
                pitch_bend_channel = current_channel if current_note.channel is None else current_note.channel
                current_midi.tracks[
                    pitch_bend_track if not is_track_type else 0].append(
                        mido.Message('pitchwheel',
                                     time=pitch_bend_time,
                                     channel=pitch_bend_channel,
                                     pitch=current_note.value))

    if not nomsg:
        if current_chord.other_messages:
            _add_other_messages(
                current_midi=current_midi,
                other_messages=current_chord.other_messages,
                write_type='piece' if not is_track_type else 'track',
                ticks_per_beat=ticks_per_beat)
        elif msg:
            _add_other_messages(
                current_midi=current_midi,
                other_messages=msg,
                write_type='piece' if not is_track_type else 'track',
                ticks_per_beat=ticks_per_beat)
    for i, each in enumerate(current_midi.tracks):
        reset_control_change_list = [120, 121, 123]
        each.sort(key=lambda s: (s.time, not (s.is_cc() and s.control in
                                              reset_control_change_list)))
        current_relative_time = [each[0].time] + [
            each[j].time - each[j - 1].time for j in range(1, len(each))
        ]
        for k, each_msg in enumerate(each):
            each_msg.time = current_relative_time[k]
    if save_as_file:
        current_midi.save(name)
    else:
        current_io = BytesIO()
        current_midi.save(file=current_io)
        return current_io


def _add_other_messages(current_midi,
                        other_messages,
                        write_type='piece',
                        ticks_per_beat=960):
    for each in other_messages:
        try:
            current_time = int(each.start_time * ticks_per_beat * 4)
            current_attributes = {
                i: j
                for i, j in vars(each).items()
                if i not in ['start_time', 'track', 'is_meta']
            }
            if not each.is_meta:
                current_message = mido.Message(time=current_time,
                                               **current_attributes)
            else:
                current_message = mido.MetaMessage(time=current_time,
                                                   **current_attributes)
        except:
            continue
        current_track = each.track if write_type == 'piece' else 0
        current_midi.tracks[current_track].append(current_message)


def find_first_tempo(file, is_file=False):
    if is_file:
        file.seek(0)
        try:
            current_midi = mido.MidiFile(file=file, clip=True)
            file.close()
        except Exception as OSError:
            file.seek(0)
            current_midi = mido.MidiFile(file=riff_to_midi(file), clip=True)
            file.close()
    else:
        try:
            current_midi = mido.MidiFile(file, clip=True)
        except Exception as OSError:
            current_midi = mido.MidiFile(file=riff_to_midi(file), clip=True)
    for track in current_midi.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                return mido.tempo2bpm(msg.tempo)
    return 120


def get_ticks_per_beat(file, is_file=False):
    if is_file:
        file.seek(0)
        try:
            current_midi = mido.MidiFile(file=file, clip=True)
            file.close()
        except Exception as OSError:
            file.seek(0)
            current_midi = mido.MidiFile(file=riff_to_midi(file), clip=True)
            file.close()
    else:
        try:
            current_midi = mido.MidiFile(file, clip=True)
        except Exception as OSError:
            current_midi = mido.MidiFile(file=riff_to_midi(file), clip=True)
    return current_midi.ticks_per_beat


def chord_to_piece(current_chord, bpm=120, start_time=0, has_track_num=False):
    channels_numbers = [i.channel for i in current_chord] + [
        i.channel
        for i in current_chord.other_messages if hasattr(i, 'channel')
    ]
    channels_list = []
    for each in channels_numbers:
        if each not in channels_list:
            channels_list.append(each)
    channels_list = [i for i in channels_list if i is not None]
    if not channels_list:
        channels_list = [0]
    channels_num = len(channels_list)
    current_start_time = start_time + current_chord.start_time
    pan_list = [
        pan(i.value,
            mode='value',
            start_time=i.start_time,
            channel=i.channel,
            track=i.track) for i in current_chord.other_messages
        if i.type == 'control_change' and i.control == 10
    ]
    volume_list = [
        volume(i.value,
               mode='value',
               start_time=i.start_time,
               channel=i.channel,
               track=i.track) for i in current_chord.other_messages
        if i.type == 'control_change' and i.control == 7
    ]
    track_names_msg = [[
        i for i in current_chord.other_messages
        if i.type == 'track_name' and i.track == j
    ] for j in range(channels_num)]
    track_names_msg = [i[0] for i in track_names_msg if i]
    if not track_names_msg:
        track_names_list = []
    else:
        if not has_track_num and all(
                hasattr(i, 'channel') for i in track_names_msg):
            track_names_channels = [i.channel for i in track_names_msg]
            current_track_names = [
                track_names_msg[track_names_channels.index(i)]
                for i in channels_list
            ]
        else:
            current_track_names = track_names_msg
        track_names_list = [i.name for i in current_track_names]
    rename_track_names = False
    if (not track_names_list) or (len(track_names_list) != channels_num):
        track_names_list = [f'Channel {i+1}' for i in range(channels_num)]
        rename_track_names = True
    if not has_track_num:
        for each in current_chord.notes:
            each.track_num = channels_list.index(
                each.channel) if each.channel is not None else 0
            if isinstance(each, pitch_bend) and each.track != each.track_num:
                each.track = each.track_num
        for each in current_chord.other_messages:
            if hasattr(each, 'channel') and each.channel is not None:
                each.track = channels_list.index(each.channel)
        for each in pan_list:
            if each.channel is not None:
                each.track = channels_list.index(each.channel)
        for each in volume_list:
            if each.channel is not None:
                each.track = channels_list.index(each.channel)
    result_piece = piece(tracks=[chord([]) for i in range(channels_num)],
                         bpm=bpm,
                         pan=[[] for i in range(channels_num)],
                         volume=[[] for i in range(channels_num)])
    result_piece.reconstruct(current_chord,
                             current_start_time,
                             include_empty_track=True)
    if result_piece.channels:
        if len(result_piece.channels) != channels_num:
            pan_list = [
                i for i in pan_list if i.channel in result_piece.channels
            ]
            volume_list = [
                i for i in volume_list if i.channel in result_piece.channels
            ]
            for each in pan_list:
                each.track = result_piece.channels.index(each.channel)
            for each in volume_list:
                each.track = result_piece.channels.index(each.channel)
            for k in range(len(result_piece.tracks)):
                for each in result_piece.tracks[k].notes:
                    if isinstance(each, pitch_bend):
                        each.track = k
            current_chord.other_messages = [
                i for i in current_chord.other_messages
                if not (hasattr(i, 'channel')
                        and i.channel not in result_piece.channels)
            ]
            for each in current_chord.other_messages:
                if hasattr(each, 'channel'):
                    each.track = result_piece.channels.index(each.channel)
    result_piece.other_messages = current_chord.other_messages
    for k in range(len(result_piece)):
        current_other_messages = [
            i for i in result_piece.other_messages if i.track == k
        ]
        result_piece.tracks[k].other_messages = current_other_messages
        current_pan = [i for i in pan_list if i.track == k]
        result_piece.pan[k] = current_pan
        current_volume = [i for i in volume_list if i.track == k]
        result_piece.volume[k] = current_volume
    result_piece.track_names = track_names_list
    result_piece.other_messages = concat(
        [i.other_messages for i in result_piece.tracks], start=[])
    current_instruments_list = [[
        i for i in result_piece.other_messages
        if i.type == 'program_change' and i.track == k
    ] for k in range(len(result_piece))]
    instruments = [
        each[0].program + 1 if each else 1 for each in current_instruments_list
    ]
    result_piece.change_instruments(instruments)
    return result_piece


def modulation(current_chord, old_scale, new_scale, **args):
    '''
    change notes (including both of melody and chords) in the given piece
    of music from a given scale to another given scale, and return
    the new changing piece of music.
    '''
    return current_chord.modulation(old_scale, new_scale, **args)


def trans(obj, pitch=4, duration=1 / 4, interval=None, custom_mapping=None):
    obj = obj.replace(' ', '')
    if ':' in obj:
        current = obj.split(':')
        current[0] = to_note(current[0])
        return trans(f'{current[0].name}{current[1]}', current[0].num,
                     duration, interval)
    if obj.count('/') > 1:
        current_parts = obj.split('/')
        current_parts = [int(i) if i.isdigit() else i for i in current_parts]
        result = trans(current_parts[0], pitch, duration, interval)
        for each in current_parts[1:]:
            if each in database.standard:
                each = database.standard_dict.get(each, each)
            elif not isinstance(each, int):
                each = trans(each, pitch, duration, interval)
            result /= each
        return result
    if obj in database.standard:
        return get_chord(obj,
                         'M',
                         pitch=pitch,
                         duration=duration,
                         intervals=interval,
                         custom_mapping=custom_mapping)
    if '/' not in obj:
        check_structure = obj.split(',')
        check_structure_len = len(check_structure)
        if check_structure_len > 1:
            return trans(check_structure[0], pitch)(','.join(
                check_structure[1:])) % (duration, interval)
        current_chord_types = database.chordTypes if custom_mapping is None else custom_mapping
        N = len(obj)
        if N == 2:
            first = obj[0]
            types = obj[1]
            if first in database.standard and types in current_chord_types:
                return get_chord(first,
                                 types,
                                 pitch=pitch,
                                 duration=duration,
                                 intervals=interval,
                                 custom_mapping=custom_mapping)
        elif N > 2:
            first_two = obj[:2]
            type1 = obj[2:]
            if first_two in database.standard and type1 in current_chord_types:
                return get_chord(first_two,
                                 type1,
                                 pitch=pitch,
                                 duration=duration,
                                 intervals=interval,
                                 custom_mapping=custom_mapping)
            first_one = obj[0]
            type2 = obj[1:]
            if first_one in database.standard and type2 in current_chord_types:
                return get_chord(first_one,
                                 type2,
                                 pitch=pitch,
                                 duration=duration,
                                 intervals=interval,
                                 custom_mapping=custom_mapping)
    else:
        parts = obj.split('/')
        part1, part2 = parts[0], '/'.join(parts[1:])
        first_chord = trans(part1, pitch)
        if isinstance(first_chord, chord):
            if part2.isdigit() or (part2[0] == '-' and part2[1:].isdigit()):
                return (first_chord / int(part2)) % (duration, interval)
            elif part2[-1] == '!' and part2[:-1].isdigit():
                return (first_chord @ int(part2[:-1])) % (duration, interval)
            elif part2 in database.standard:
                if part2 not in database.standard2:
                    part2 = database.standard_dict[part2]
                first_chord_notenames = first_chord.names()
                if part2 in first_chord_notenames and part2 != first_chord_notenames[
                        0]:
                    return (first_chord.inversion(
                        first_chord_notenames.index(part2))) % (duration,
                                                                interval)
                return chord([part2] + first_chord_notenames,
                             rootpitch=pitch,
                             duration=duration,
                             interval=interval)
            else:
                second_chord = trans(part2, pitch)
                if isinstance(second_chord, chord):
                    return chord(second_chord.names() + first_chord.names(),
                                 rootpitch=pitch,
                                 duration=duration,
                                 interval=interval)
    raise ValueError(
        f'{obj} is not a valid chord representation or chord types not in database'
    )


def to_scale(obj, pitch=None):
    tonic, scale_name = obj.strip(' ').split(' ', 1)
    tonic = N(tonic)
    if pitch is not None:
        tonic.num = pitch
    scale_name = scale_name.strip(' ')
    return scale(tonic, scale_name)


def intervalof(current_chord, cumulative=True, translate=False):
    if isinstance(current_chord, scale):
        current_chord = current_chord.get_scale()
    if not isinstance(current_chord, chord):
        current_chord = chord(current_chord)
    return current_chord.intervalof(cumulative, translate)


def sums(*chordls):
    if len(chordls) == 1:
        chordls = chordls[0]
        start = chordls[0]
        for i in chordls[1:]:
            start += i
        return start
    else:
        return sums(list(chordls))


def build(*tracks_list, **kwargs):
    if len(tracks_list) == 1 and isinstance(tracks_list[0], list):
        current_tracks_list = tracks_list[0]
        if current_tracks_list and isinstance(current_tracks_list[0],
                                              (list, track)):
            return build(*tracks_list[0], **kwargs)
    tracks = []
    instruments = []
    start_times = []
    channels = []
    track_names = []
    pan_msg = []
    volume_msg = []
    daw_channels = []
    remain_list = [1, 0, None, None, [], [], None]
    for each in tracks_list:
        if isinstance(each, track):
            tracks.append(each.content)
            instruments.append(each.instrument)
            start_times.append(each.start_time)
            channels.append(each.channel)
            track_names.append(each.track_name)
            pan_msg.append(each.pan if each.pan else [])
            volume_msg.append(each.volume if each.volume else [])
            daw_channels.append(each.daw_channel)
        else:
            new_each = each + remain_list[len(each) - 1:]
            tracks.append(new_each[0])
            instruments.append(new_each[1])
            start_times.append(new_each[2])
            channels.append(new_each[3])
            track_names.append(new_each[4])
            pan_msg.append(new_each[5])
            volume_msg.append(new_each[6])
            daw_channels.append(new_each[7])
    if any(i is None for i in channels):
        channels = None
    if all(i is None for i in track_names):
        track_names = None
    else:
        track_names = [i if i else '' for i in track_names]
    if any(i is None for i in daw_channels):
        daw_channels = None
    result = P(tracks=tracks,
               instruments=instruments,
               start_times=start_times,
               track_names=track_names,
               channels=channels,
               pan=pan_msg,
               volume=volume_msg,
               daw_channels=daw_channels)
    for key, value in kwargs.items():
        setattr(result, key, value)
    return result


def translate(pattern,
              default_duration=1 / 8,
              default_interval=0,
              default_volume=100,
              start_time=None):
    result = drum(pattern,
                  default_duration=default_duration,
                  start_time=start_time,
                  default_interval=default_interval,
                  default_volume=default_volume,
                  translate_mode=1).notes
    return result


def chord_progression(chords,
                      durations=1 / 4,
                      intervals=0,
                      volumes=None,
                      chords_interval=None,
                      merge=True,
                      scale=None,
                      separator=','):
    if scale:
        return scale.chord_progression(chords, durations, intervals, volumes,
                                       chords_interval, merge)
    if isinstance(chords, str):
        if ' ' not in separator:
            chords = chords.replace(' ', '')
        chords = chords.split(separator)
    chords = [(i, ) if isinstance(i, str) else i for i in chords]
    chords_len = len(chords)
    if not isinstance(durations, list):
        durations = [durations for i in range(chords_len)]
    if not isinstance(intervals, list):
        intervals = [intervals for i in range(chords_len)]
    if volumes and not isinstance(volumes, list):
        volumes = [volumes for i in range(chords_len)]
    if chords_interval and not isinstance(chords_interval, list):
        chords_interval = [chords_interval for i in range(chords_len)]
    chords = [C(*i) if isinstance(i, tuple) else i for i in chords]
    for i in range(chords_len):
        chords[i] %= (durations[i], intervals[i],
                      volumes[i] if volumes else volumes)
    if merge:
        result = chords[0]
        current_interval = 0
        for i in range(1, chords_len):
            if chords_interval:
                current_interval += chords_interval[i - 1]
                result = result & (chords[i], current_interval)
            else:
                result |= chords[i]
        return result
    else:
        return chords


def arpeggio(chord_type,
             start=3,
             stop=7,
             durations=1 / 4,
             intervals=1 / 32,
             first_half=True,
             second_half=False):
    if isinstance(chord_type, str):
        rule = lambda chord_type, start, stop: concat([
            C(chord_type, i) % (durations, intervals)
            for i in range(start, stop)
        ], '|')
    else:
        rule = lambda chord_type, start, stop: concat([
            chord_type.reset_octave(i) % (durations, intervals)
            for i in range(start, stop)
        ], '|')
    result = chord([])
    first_half_part = rule(chord_type, start, stop)
    second_half_part = ~first_half_part[:-1]
    if first_half:
        result += first_half_part
    if second_half:
        result += second_half_part
    return result


def distribute(current_chord,
               length=1 / 4,
               start=0,
               stop=None,
               method=translate,
               mode=0):
    if isinstance(current_chord, str):
        current_chord = method(current_chord)
    elif isinstance(current_chord, list):
        current_chord = chord(current_chord)
    if stop is None:
        stop = len(current_chord)
    temp = copy(current_chord)
    part = temp.notes[start:stop]
    intervals = temp.interval[start:stop]
    durations = [i.duration for i in part]
    whole_duration = sum(durations)
    whole_interval = sum(intervals)
    durations = [length * (i / whole_duration) for i in durations]
    if whole_interval != 0:
        intervals = [length * (i / whole_interval) for i in intervals]
    else:
        intervals = [0 for i in intervals]
    if mode == 1:
        intervals = durations
    new_duration = temp.get_duration()
    new_duration[start:stop] = durations
    new_interval = temp.interval
    new_interval[start:stop] = intervals
    temp %= (new_duration, new_interval)
    return temp


def get_chords_from_rhythm(chords, current_rhythm, set_duration=True):
    if isinstance(chords, note):
        chords = chord(
            [copy(chords) for i in range(current_rhythm.get_beat_num())])
        return chords.apply_rhythm(current_rhythm, set_duration=set_duration)
    if isinstance(chords, chord):
        chords = [copy(chords) for i in range(current_rhythm.get_beat_num())]
    else:
        chords = copy(chords)
    length = len(chords)
    counter = -1
    has_beat = False
    current_start_time = 0
    chord_intervals = [0 for i in range(len(chords))]
    for i, each in enumerate(current_rhythm):
        current_duration = each.get_duration()
        if type(each) is beat:
            counter += 1
            if counter >= length:
                break
            current_chord = chords[counter]
            if set_duration:
                if current_duration != 0:
                    for k in current_chord:
                        k.duration = current_duration
            chord_intervals[counter] += current_duration
            has_beat = True
        elif type(each) is rest_symbol:
            if not has_beat:
                current_start_time += current_duration
            else:
                chord_intervals[counter] += current_duration
        elif type(each) is continue_symbol:
            if not has_beat:
                current_start_time += current_duration
            else:
                current_chord = chords[counter]
                for k in current_chord:
                    k.duration += current_duration
                chord_intervals[counter] += current_duration
    result = chords[0]
    current_interval = 0
    for i, each in enumerate(chords[1:]):
        current_interval += chord_intervals[i]
        result = result & (each, current_interval)
    extra_interval = chord_intervals[len(chords) - 1]
    result.interval[-1] = extra_interval
    result.start_time = current_start_time
    return result


@method_wrapper(chord)
def analyze_rhythm(current_chord,
                   include_continue=True,
                   total_length=None,
                   remove_empty_beats=False,
                   unit=None,
                   find_unit_ignore_duration=False,
                   merge_continue=True):
    if all(i <= 0 for i in current_chord.interval):
        return rhythm([beat(0) for i in range(len(current_chord))])
    if unit is None:
        current_interval = copy(current_chord.interval)
        if not find_unit_ignore_duration:
            current_interval += [
                current_chord.interval[i] - current_chord[i].duration
                for i in range(len(current_chord))
            ]
        current_interval = [i for i in current_interval if i > 0]
        unit = min(current_interval)
    beat_list = []
    if current_chord.start_time > 0:
        beat_list.extend([
            rest_symbol(unit)
            for i in range(int(current_chord.start_time // unit))
        ])
    for i, each in enumerate(current_chord.interval):
        if each == 0:
            beat_list.append(beat(0))
        else:
            current_beat = beat(unit)
            remain_interval = each - unit
            rest_num, extra_beat = divmod(remain_interval, unit)
            if extra_beat > 0:
                current_dotted_num = int(
                    math.log(1 / (1 -
                                  (((extra_beat + unit) / unit) / 2)), 2)) - 1
                current_beat.dotted = current_dotted_num
            beat_list.append(current_beat)
            if not include_continue:
                beat_list.extend(
                    [rest_symbol(unit) for k in range(int(rest_num))])
            else:
                current_duration = current_chord.notes[i].duration
                if current_duration >= each:
                    if not merge_continue:
                        beat_list.extend([
                            continue_symbol(unit) for k in range(int(rest_num))
                        ])
                    else:
                        beat_list[-1].duration += unit * int(rest_num)
                else:
                    current_rest_duration = each - current_duration
                    rest_num = current_rest_duration // unit
                    current_continue_duration = current_duration - unit
                    continue_num = current_continue_duration // unit
                    if not merge_continue:
                        beat_list.extend([
                            continue_symbol(unit)
                            for k in range(int(continue_num))
                        ])
                    else:
                        beat_list[-1].duration += unit * int(continue_num)
                    beat_list.extend(
                        [rest_symbol(unit) for k in range(int(rest_num))])
    result = rhythm(beat_list)
    if total_length is not None:
        current_time_signature = Fraction(result.get_total_duration() /
                                          total_length).limit_denominator()
        if current_time_signature == 1:
            current_time_signature = [4, 4]
        else:
            current_time_signature = [
                current_time_signature.numerator,
                current_time_signature.denominator
            ]
        result.time_signature = current_time_signature
    if remove_empty_beats:
        result = rhythm([i for i in result if i.duration != 0],
                        time_signature=result.time_signature)
    return result


def stopall():
    pygame.mixer.stop()
    pygame.mixer.music.stop()


def riff_to_midi(riff_name, name='temp.mid', output_file=False):
    if isinstance(riff_name, str):
        current_file = open(riff_name, 'rb')
        root = chunk.Chunk(current_file, bigendian=False)
    else:
        root = chunk.Chunk(riff_name, bigendian=False)

    chunk_id = root.getname()
    if chunk_id == b'MThd':
        raise IOError(f'Already a Standard MIDI format file: {riff_name}')
    elif chunk_id != b'RIFF':
        chunk_size = root.getsize()
        chunk_raw = root.read(chunk_size)
        if b'MThd' in chunk_raw:
            midi_raw = chunk_raw[chunk_raw.index(b'MThd'):]
        else:
            raise ValueError('Cannot find header')
    else:
        chunk_size = root.getsize()
        chunk_raw = root.read(chunk_size)
        (hdr_id, hdr_data, midi_size) = struct.unpack("<4s4sL",
                                                      chunk_raw[0:12])

        if hdr_id != b'RMID' or hdr_data != b'data':
            raise IOError(f'Invalid or unsupported input file: {riff_name}')
        try:
            midi_raw = chunk_raw[12:12 + midi_size]
        except IndexError:
            raise IOError(f'Broken input file: {riff_name}')

    root.close()
    if isinstance(riff_name, str):
        current_file.close()

    if output_file:
        with open(name, 'wb') as f:
            f.write(midi_raw)
    else:
        result = BytesIO()
        result.write(midi_raw)
        result.seek(0)
        return result


def write_data(obj, name='untitled.mpb'):
    import pickle
    with open(name, 'wb') as f:
        pickle.dump(obj, f)


def load_data(name):
    import pickle
    with open(name, 'rb') as f:
        result = pickle.load(f)
    return result


def dotted(duration, num=1):
    return duration * sum([(1 / 2)**i for i in range(num + 1)])


def parse_dotted(text, get_fraction=False):
    length = len(text)
    dotted_num = 0
    ind = 0
    for i in range(length - 1, -1, -1):
        if text[i] != '.':
            ind = i
            break
        else:
            dotted_num += 1
    duration = parse_num(text[:ind + 1], get_fraction=get_fraction)
    current_duration = mp.beat(duration, dotted_num).get_duration()
    return current_duration


def parse_num(duration, get_fraction=False):
    if '/' in duration:
        numerator, denominator = duration.split('/')
        numerator = int(numerator) if numerator.isdigit() else float(numerator)
        denominator = int(denominator) if denominator.isdigit() else float(
            denominator)
        if get_fraction:
            if not (isinstance(numerator, int)
                    and isinstance(denominator, int)):
                duration = Fraction(numerator /
                                    denominator).limit_denominator()
            else:
                duration = Fraction(numerator, denominator)
        else:
            duration = numerator / denominator
    else:
        duration = int(duration) if duration.isdigit() else float(duration)
        if get_fraction:
            duration = Fraction(duration).limit_denominator()
    return duration


def relative_note(a, b):
    '''
    return the notation of note a from note b with accidentals
    (how note b adds accidentals to match the same pitch as note a),
    works for the accidentals including sharp, flat, natural,
    double sharp, double flat
    (a, b are strings that represents a note, could be with accidentals)
    '''
    len_a, len_b = len(a), len(b)
    a_name, b_name, accidental_a, accidental_b = a[0], b[0], a[1:], b[1:]
    if len_a == 1 and len_b > 1 and a_name == b_name:
        return a + '♮'
    if a in database.standard:
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
            raise ValueError(f'unrecognizable accidentals {accidental_a}')
    if b in database.standard:
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
            raise ValueError(f'unrecognizable accidentals {accidental_b}')
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


def get_note_name(current_note):
    if any(i.isdigit() for i in current_note):
        current_note = ''.join([i for i in current_note if not i.isdigit()])
    return current_note


def get_note_num(current_note):
    result = ''.join([i for i in current_note if i.isdigit()])
    return int(result) if result else None


def standardize_note(current_note):
    current_note = get_note_name(current_note)
    if current_note in database.standard2:
        return current_note
    elif current_note in database.standard_dict:
        return database.standard_dict[current_note]
    else:
        if current_note.endswith('bb'):
            current_name = current_note[:-2]
            result = (N(standardize_note(current_name)) - 2).name
        elif current_note.endswith('x'):
            current_name = current_note[:-1]
            result = (N(standardize_note(current_name)) + 2).name
        elif current_note.endswith('♮'):
            result = current_note[:-1]
        elif current_note.endswith('#'):
            current_name = current_note[:-1]
            result = (N(standardize_note(current_name)) + 1).name
        elif current_note.endswith('b'):
            current_name = current_note[:-1]
            result = (N(standardize_note(current_name)) - 1).name
        else:
            raise ValueError(f'Invalid note name or accidental {current_note}')
        return result


def get_accidental(current_note):
    if current_note.endswith('bb'):
        result = 'bb'
    elif current_note.endswith('x'):
        result = 'x'
    elif current_note.endswith('♮'):
        result = '♮'
    elif current_note.endswith('#'):
        result = '#'
    elif current_note.endswith('b'):
        result = 'b'
    else:
        result = ''
    return result


def reset(self, **kwargs):
    temp = copy(self)
    for i, j in kwargs.items():
        setattr(temp, i, j)
    return temp


def closest_note(note1, note2, get_distance=False):
    if isinstance(note1, note):
        note1 = note1.name
    if not isinstance(note2, note):
        note2 = to_note(note2)
    current_note = [
        note(note1, note2.num),
        note(note1, note2.num - 1),
        note(note1, note2.num + 1)
    ]
    if not get_distance:
        result = min(current_note, key=lambda s: abs(s.degree - note2.degree))
        return result
    else:
        distances = [[i, abs(i.degree - note2.degree)] for i in current_note]
        distances.sort(key=lambda s: s[1])
        result = distances[0]
        return result


def closest_note_from_chord(note1, chord1, mode=0, get_distance=False):
    if not isinstance(note1, note):
        note1 = to_note(note1)
    if isinstance(chord1, chord):
        chord1 = chord1.notes
    current_name = database.standard_dict.get(note1.name, note1.name)
    distances = [(closest_note(note1, each, get_distance=True), i)
                 for i, each in enumerate(chord1)]
    distances.sort(key=lambda s: s[0][1])
    result = chord1[distances[0][1]]
    if mode == 1:
        result = distances[0][0][0]
    if get_distance:
        result = (result, distances[0][0][1])
    return result


def note_range(note1, note2):
    current_range = list(range(note1.degree, note2.degree))
    result = [degree_to_note(i) for i in current_range]
    return result


def adjust_to_scale(current_chord, current_scale):
    temp = copy(current_chord)
    current_notes = current_scale.get_scale()
    for each in temp:
        current_note = closest_note_from_chord(each, current_notes)
        each.name = current_note.name
        each.num = current_note.num
    return temp


def dataclass_repr(s, keywords=None):
    if not keywords:
        result = f"{type(s).__name__}({', '.join([f'{i}={j}' for i, j in vars(s).items()])})"
    else:
        result = f"{type(s).__name__}({', '.join([f'{i}={vars(s)[i]}' for i in keywords])})"
    return result


def read_musicxml(file, load_musicxml_args={}, save_midi_args={}):
    import partitura
    current_score = partitura.load_musicxml(file, **load_musicxml_args)
    current_file = BytesIO()
    partitura.save_score_midi(current_score, current_file, **save_midi_args)
    result = read(current_file, is_file=True)
    result.musicxml_info = {
        i: j
        for i, j in vars(current_score).items()
        if i not in ['parts', 'part_structure']
    }
    return result


def write_musicxml(current_chord, filename, save_musicxml_args={}):
    import partitura
    current_file = BytesIO()
    current_file = write(current_chord, save_as_file=False)
    current_file.seek(0)
    current_file = partitura.io.importmidi.mido.MidiFile(file=current_file,
                                                         clip=True)
    current_midi = partitura.load_score_midi(current_file)
    partitura.save_musicxml(current_midi, filename, **save_musicxml_args)


def read_json(file):
    note_list_dict = {'note': note, 'pitch_bend': pitch_bend, 'tempo': tempo}
    with open(file, encoding='utf-8') as f:
        current = json.load(f)
    for j in current['tracks']:
        j['interval'] = [i['interval'] for i in j['notes']]
        for i in j['notes']:
            del i['interval']
        j['notes'] = [
            note_list_dict[k['type']](
                **{i: j
                   for i, j in k.items() if i != 'type'}) for k in j['notes']
        ]
        j['other_messages'] = [event(**k) for k in j['other_messages']]
    current['tracks'] = [chord(**i) for i in current['tracks']]
    current['other_messages'] = [event(**k) for k in current['other_messages']]
    current['pan'] = [[pan(**i) for i in j] for j in current['pan']]
    current['volume'] = [[volume(**i) for i in j] for j in current['volume']]
    result = piece(**current)
    return result


def write_json(current_chord,
               bpm=120,
               channel=0,
               start_time=None,
               filename='untitled.json',
               instrument=None,
               i=None,
               msg=None,
               nomsg=False):
    if i is not None:
        instrument = i
    is_track_type = False
    if isinstance(current_chord, note):
        current_chord = chord([current_chord])
    elif isinstance(current_chord, list):
        current_chord = concat(current_chord, '|')
    if isinstance(current_chord, chord):
        is_track_type = True
        if instrument is None:
            instrument = 1
        current_chord = P(
            tracks=[current_chord],
            instruments=[instrument],
            bpm=bpm,
            channels=[channel],
            start_times=[
                current_chord.start_time if start_time is None else start_time
            ],
            other_messages=current_chord.other_messages)
    elif isinstance(current_chord, track):
        is_track_type = True
        if hasattr(current_chord, 'other_messages'):
            msg = current_chord.other_messages
        else:
            msg = current_chord.content.other_messages
        current_chord = build(current_chord, bpm=current_chord.bpm)
    elif isinstance(current_chord, drum):
        is_track_type = True
        if hasattr(current_chord, 'other_messages'):
            msg = current_chord.other_messages
        current_chord = P(tracks=[current_chord.notes],
                          instruments=[current_chord.instrument],
                          bpm=bpm,
                          start_times=[
                              current_chord.notes.start_time
                              if start_time is None else start_time
                          ],
                          channels=[9])
    else:
        current_chord = copy(current_chord)
    track_number, start_times, instruments_numbers, bpm, tracks_contents, track_names, channels, pan_msg, volume_msg = \
    current_chord.track_number, current_chord.start_times, current_chord.instruments_numbers, current_chord.bpm, current_chord.tracks, current_chord.track_names, current_chord.channels, current_chord.pan, current_chord.volume
    instruments_numbers = [
        i if isinstance(i, int) else database.INSTRUMENTS[i]
        for i in instruments_numbers
    ]
    result = current_chord.__dict__
    result['tracks'] = [i.__dict__ for i in result['tracks']]
    for j in result['tracks']:
        for i, each in enumerate(j['notes']):
            current_dict = {'type': each.__class__.__name__}
            if isinstance(each, note):
                current_dict.update({
                    k1: k2
                    for k1, k2 in each.__dict__.items()
                    if k1 not in ['degree']
                })
            elif isinstance(each, pitch_bend):
                current_dict.update({
                    k1: k2
                    for k1, k2 in each.__dict__.items()
                    if k1 not in ['degree', 'volume', 'duration']
                })
                current_dict['mode'] = 'value'
            elif isinstance(each, tempo):
                current_dict.update({
                    k1: k2
                    for k1, k2 in each.__dict__.items()
                    if k1 not in ['degree', 'volume', 'duration']
                })
            j['notes'][i] = current_dict
        j['other_messages'] = [k.__dict__ for k in j['other_messages']]
        for i, each in enumerate(j['notes']):
            each['interval'] = j['interval'][i]
        del j['interval']
    result['other_messages'] = [i.__dict__ for i in result['other_messages']]
    result['pan'] = [[i.__dict__ for i in j] for j in result['pan']]
    result['volume'] = [[i.__dict__ for i in j] for j in result['volume']]
    for i in result['pan']:
        for j in i:
            j['mode'] = 'value'
            del j['value_percentage']
    for i in result['volume']:
        for j in i:
            j['mode'] = 'value'
            del j['value_percentage']
    del result['instruments_numbers']
    del result['track_number']
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result,
                  f,
                  indent=4,
                  separators=(',', ': '),
                  ensure_ascii=False)


def bar_to_real_time(bar, bpm, mode=0):
    # convert bar to time in ms
    return int(
        (60000 / bpm) * (bar * 4)) if mode == 0 else (60000 / bpm) * (bar * 4)


def real_time_to_bar(time, bpm):
    # convert time in ms to bar
    return (time / (60000 / bpm)) / 4


C = trans
N = to_note
S = to_scale
P = piece
arp = arpeggio

for each in [
        note, chord, piece, track, scale, drum, rest, tempo, pitch_bend, pan,
        volume, event, beat, rest_symbol, continue_symbol, rhythm
]:
    each.reset = reset
    each.__hash__ = lambda self: hash(repr(self))
    each.copy = lambda self: copy(self)
    if each.__eq__ == object.__eq__:
        each.__eq__ = lambda self, other: type(other) is type(
            self) and self.__dict__ == other.__dict__

if __name__ == '__main__' or __name__ == 'musicpy':
    import algorithms as alg
else:
    from . import algorithms as alg
