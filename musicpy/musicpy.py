import os
import sys
import math
import random
import struct
import chunk
from io import BytesIO
from difflib import SequenceMatcher
import midiutil
import mido
from .database import *
from .structures import *

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

has_audio_interface = True
try:
    pygame.mixer.init(44100, -16, 2, 1024)
except pygame.error:
    has_audio_interface = False


def toNote(notename, duration=0.25, volume=100, pitch=4, channel=None):
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
        return note(name, num, duration, volume, channel)


def degree_to_note(degree, duration=0.25, volume=100, channel=None):
    name = standard_reverse[degree % 12]
    num = (degree // 12) - 1
    return note(name, num, duration, volume, channel)


def totuple(obj):
    if isinstance(obj, str):
        return (obj, )
    try:
        return tuple(obj)
    except:
        return (obj, )


def get_freq(y, standard=440):
    if isinstance(y, str):
        y = toNote(y)
    semitones = y.degree - 69
    return standard * 2**(semitones / 12)


def freq_to_note(freq, to_str=False, standard=440):
    quotient = freq / standard
    semitones = round(math.log(quotient, 2) * 12)
    result = N('A4') + semitones
    if to_str:
        return str(result)
    return result


def secondary_dom(root, mode='major'):
    if isinstance(root, str):
        root = toNote(root)
    newscale = scale(root, mode)
    return newscale.dom_chord()


def secondary_dom7(root, mode='major'):
    if isinstance(root, str):
        root = toNote(root)
    newscale = scale(root, mode)
    return newscale.dom7_chord()


def getchord_by_interval(start,
                         interval1,
                         duration=0.25,
                         interval=0,
                         cummulative=True,
                         start_time=0):

    if isinstance(start, str):
        start = toNote(start)
    result = [start]
    if cummulative:
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


def getchord(start,
             mode=None,
             duration=0.25,
             intervals=None,
             interval=None,
             cummulative=True,
             pitch=4,
             ind=0,
             start_time=0):
    if not isinstance(start, note):
        start = toNote(start, pitch=pitch)
    if interval is not None:
        return getchord_by_interval(start,
                                    interval,
                                    duration,
                                    intervals,
                                    cummulative,
                                    start_time=start_time)
    premode = mode
    mode = mode.lower().replace(' ', '')
    initial = start.degree
    chordlist = [start]
    interval_premode = chordTypes(premode, mode=1, index=ind)
    if interval_premode != 'not found':
        interval = interval_premode
    else:
        interval_mode = chordTypes(mode, mode=1, index=ind)
        if interval_mode != 'not found':
            interval = interval_mode
        else:
            raise ValueError('could not detect the chord types')
    for i in range(len(interval)):
        chordlist.append(degree_to_note(initial + interval[i]))
    return chord(chordlist, duration, intervals, start_time=start_time)


chd = getchord


def concat(chordlist, mode='+', extra=None, start=None):
    temp = copy(chordlist[0]) if start is None else start
    start_ind = 1 if start is None else 0
    if mode == '+':
        for t in chordlist[start_ind:]:
            temp += t
    elif mode == '|':
        if not extra:
            for t in chordlist[start_ind:]:
                temp |= t
        else:
            for t in chordlist[start_ind:]:
                temp |= (t, extra)
    elif mode == '&':
        if not extra:
            for t in chordlist[start_ind:]:
                temp &= t
        else:
            extra_unit = extra
            for t in chordlist[start_ind:]:
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
         deinterleave=False,
         remove_duplicates=False,
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
                 deinterleave=deinterleave,
                 remove_duplicates=remove_duplicates,
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
         split_channels=False,
         clear_empty_notes=False,
         clear_other_channel_msg=False):
    if is_file:
        name.seek(0)
        try:
            current_midi = mido.midifiles.MidiFile(file=name, clip=True)
            name.close()
        except Exception as OSError:
            name.seek(0)
            current_midi = mido.midifiles.MidiFile(file=riff_to_midi(name),
                                                   clip=True)
            name.close()
            split_channels = True
        name = name.name

    else:
        try:
            current_midi = mido.midifiles.MidiFile(name, clip=True)
        except Exception as OSError:
            current_midi = mido.midifiles.MidiFile(file=riff_to_midi(name),
                                                   clip=True)
            split_channels = True
    whole_tracks = current_midi.tracks
    current_track = None
    find_changes = False
    whole_bpm = 120
    changes = []
    changes_track = [
        each for each in whole_tracks
        if all((i.is_meta or i.type == 'sysex') for i in each)
    ]
    if not changes_track:
        changes_track = [
            each for each in whole_tracks
            if any(i.type == 'set_tempo' for i in each)
        ]
    else:
        find_changes = True
    if changes_track:
        changes = [
            midi_to_chord(current_midi,
                          each,
                          add_track_num=split_channels,
                          clear_empty_notes=clear_empty_notes)[0]
            for each in changes_track
        ]
        changes = concat(changes)
        whole_bpm_list = [i for i in changes if isinstance(i, tempo)]
        if whole_bpm_list:
            min_start_time = min([i.start_time for i in whole_bpm_list])
            whole_bpm_list = [
                i for i in whole_bpm_list if i.start_time == min_start_time
            ]
            whole_bpm = whole_bpm_list[-1].bpm
    available_tracks = [
        each for each in whole_tracks
        if any(not (i.is_meta or i.type == 'sysex') for i in each)
    ]
    if get_off_drums:
        available_tracks = [
            each for each in available_tracks
            if not any(j.type == 'note_on' and j.channel == 9 for j in each)
        ]
    all_tracks = [
        midi_to_chord(current_midi,
                      available_tracks[j],
                      whole_bpm,
                      add_track_num=split_channels,
                      clear_empty_notes=clear_empty_notes,
                      track_ind=j) for j in range(len(available_tracks))
    ]
    start_times_list = [j[2] for j in all_tracks]
    if available_tracks:
        channels_list = [[i.channel for i in each if hasattr(i, 'channel')]
                         for each in available_tracks]
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
                    unassigned_channels_number.append(free_channel_numbers[k])
                else:
                    unassigned_channels_number.append(
                        16 + k - free_channel_numbers_length)
            channels_list = [
                each if each != -1 else unassigned_channels_number.pop(0)
                for each in channels_list
            ]
    else:
        channels_list = None

    instruments_list = []
    for each in available_tracks:
        current_program = [i.program for i in each if hasattr(i, 'program')]
        if current_program:
            instruments_list.append(current_program[0] + 1)
        else:
            instruments_list.append(1)
    chords_list = [each[1] for each in all_tracks]
    pan_list = [k.pan_list for k in chords_list]
    volume_list = [k.volume_list for k in chords_list]
    tracks_names_list = [[k.name for k in each if k.type == 'track_name']
                         for each in available_tracks]
    if all(j for j in tracks_names_list):
        tracks_names_list = [j[0] for j in tracks_names_list]
    else:
        tracks_names_list = None
    result_piece = piece(chords_list, instruments_list, whole_bpm,
                         start_times_list, tracks_names_list, channels_list,
                         os.path.splitext(os.path.basename(name))[0], pan_list,
                         volume_list)
    if split_channels:
        remain_available_tracks = [
            each for each in whole_tracks
            if any(not (j.is_meta or j.type == 'sysex') for j in each)
        ]
        channels_numbers = concat(
            [[i.channel for i in each if hasattr(i, 'channel')]
             for each in remain_available_tracks])
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
        remain_tracks_length = len(remain_available_tracks)
        remain_all_tracks = [
            midi_to_chord(current_midi,
                          remain_available_tracks[j],
                          whole_bpm,
                          add_track_num=split_channels,
                          clear_empty_notes=clear_empty_notes,
                          track_ind=j,
                          track_channels=track_channels)
            for j in range(remain_tracks_length)
        ]
        if remain_tracks_length > 1:
            available_tracks = concat(remain_available_tracks)
            pitch_bends = concat([
                i[1].split(pitch_bend, get_time=True)
                for i in remain_all_tracks
            ])
            for each in remain_all_tracks:
                each[1].clear_pitch_bend('all')
            start_time_ls = [j[2] for j in remain_all_tracks]
            first_track_ind = start_time_ls.index(min(start_time_ls))
            remain_all_tracks.insert(0, remain_all_tracks.pop(first_track_ind))
            first_track = remain_all_tracks[0]
            tempos, all_track_notes, first_track_start_time = first_track
            for i in remain_all_tracks[1:]:
                all_track_notes &= (i[1], i[2] - first_track_start_time)
            all_track_notes.other_messages = concat(
                [each[1].other_messages for each in remain_all_tracks])
            all_track_notes += pitch_bends
            all_track_notes.pan_list = concat(
                [k[1].pan_list for k in remain_all_tracks])
            all_track_notes.volume_list = concat(
                [k[1].volume_list for k in remain_all_tracks])
            all_tracks = [tempos, all_track_notes, first_track_start_time]
        else:
            available_tracks = remain_available_tracks[0]
            all_tracks = remain_all_tracks[0]
        pan_list = all_tracks[1].pan_list
        volume_list = all_tracks[1].volume_list
        current_instruments_list = [[
            i for i in available_tracks
            if i.type == 'program_change' and i.channel == k
        ] for k in channels_list]
        instruments_list = [
            each[0].program + 1 if each else 1
            for each in current_instruments_list
        ]
        tracks_names_list = [
            i.name for i in available_tracks if i.type == 'track_name'
        ]
        rename_track_names = False
        if (not tracks_names_list) or (len(tracks_names_list) !=
                                       len(channels_list)):
            tracks_names_list = [f'Channel {i+1}' for i in channels_list]
            rename_track_names = True
        result_merge_track = all_tracks[1]
        result_piece.tracks = [chord([]) for i in range(len(channels_list))]
        result_piece.instruments_list = [
            reverse_instruments[i] for i in instruments_list
        ]
        result_piece.instruments_numbers = instruments_list
        result_piece.track_names = tracks_names_list
        result_piece.channels = channels_list
        result_piece.pan = [[] for i in range(len(channels_list))]
        result_piece.volume = [[] for i in range(len(channels_list))]
        result_piece.track_number = len(channels_list)
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
            current_track_names = result_piece.get_msg(track_name)
            for i in range(len(current_track_names)):
                result_piece.tracks[i].other_messages.append(
                    current_track_names[i])
        if get_off_drums:
            drum_ind = result_piece.channels.index(9)
            del result_piece[drum_ind]
    else:
        if result_piece.tracks:
            result_piece.other_messages = concat([
                each_track.other_messages for each_track in result_piece.tracks
            ],
                                                 start=[])
        else:
            raise ValueError(
                'No tracks found in the MIDI file, you can try to set the parameter `split_channels` to True, or check if the input MIDI file is empty'
            )
    if find_changes and changes:
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
    return result_piece


def midi_to_chord(current_midi,
                  current_track,
                  bpm=None,
                  add_track_num=False,
                  clear_empty_notes=False,
                  track_ind=0,
                  track_channels=None):
    interval_unit = current_midi.ticks_per_beat * 4
    intervals = []
    notelist = []
    notes_len = len(current_track)
    find_first_note = False
    start_time = 0
    current_time = 0
    pan_list = []
    volume_list = []
    other_messages = []

    counter = 0
    for i in range(notes_len):
        current_msg = current_track[i]
        current_time += current_msg.time
        if current_msg.type == 'note_on' and current_msg.velocity != 0:
            counter += 1
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
            current_tempo = tempo(mido.midifiles.units.tempo2bpm(
                current_msg.tempo),
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
                read_other_messages(current_msg, other_messages,
                                    current_time / interval_unit,
                                    current_track_ind)
        else:
            if track_channels and hasattr(current_msg, 'channel'):
                current_msg_channel = current_msg.channel
                current_track_ind = track_channels.index(current_msg_channel)
            else:
                current_track_ind = track_ind
            read_other_messages(current_msg, other_messages,
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
        return [bpm, result, start_time]
    else:
        return [result, start_time]


def read_other_messages(message, other_messages, time, track_ind):
    current_type = message.type
    if current_type == 'control_change':
        current_message = controller_event(track=track_ind,
                                           channel=message.channel,
                                           time=time,
                                           controller_number=message.control,
                                           parameter=message.value)
    elif current_type == 'aftertouch':
        current_message = channel_pressure(track=track_ind,
                                           channel=message.channel,
                                           time=time,
                                           pressure_value=message.value)
    elif current_type == 'program_change':
        current_message = program_change(track=track_ind,
                                         channel=message.channel,
                                         time=time,
                                         program=message.program)
    elif current_type == 'copyright':
        current_message = copyright_event(track=track_ind,
                                          time=time,
                                          notice=message.text)
    elif current_type == 'sysex':
        current_message = sysex(track=track_ind,
                                time=time,
                                payload=struct.pack(f">{len(message.data)-1}B",
                                                    *(message.data[1:])),
                                manID=message.data[0])
    elif current_type == 'track_name':
        current_message = track_name(track=track_ind,
                                     time=time,
                                     name=message.name)
    elif current_type == 'time_signature':
        current_message = time_signature(
            track=track_ind,
            time=time,
            numerator=message.numerator,
            denominator=message.denominator,
            clocks_per_tick=message.clocks_per_click,
            notes_per_quarter=message.notated_32nd_notes_per_beat)
    elif current_type == 'key_signature':
        current_key = message.key
        if current_key[-1] == 'm':
            current_mode = midiutil.MidiFile.MINOR
            current_key = scale(current_key[:-1], 'minor')
        else:
            current_mode = midiutil.MidiFile.MAJOR
            current_key = scale(current_key, 'major')
        current_accidental_type = midiutil.MidiFile.SHARPS
        current_accidentals = len(
            [i for i in current_key.names() if i[-1] == '#'])
        current_message = key_signature(
            track=track_ind,
            time=time,
            accidentals=current_accidentals,
            accidental_type=current_accidental_type,
            mode=current_mode)
    elif current_type == 'text':
        current_message = text_event(track=track_ind,
                                     time=time,
                                     text=message.text)
    else:
        return
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
          deinterleave=False,
          remove_duplicates=False,
          **midi_args):
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
            [current_chord], [instrument],
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
        current_chord = P([current_chord.notes], [current_chord.instrument],
                          bpm, [
                              current_chord.notes.start_time
                              if start_time is None else start_time
                          ],
                          channels=[9])
    track_number, start_times, instruments_numbers, bpm, tracks_contents, track_names, channels, pan_msg, volume_msg = \
    current_chord.track_number, current_chord.start_times, current_chord.instruments_numbers, current_chord.bpm, current_chord.tracks, current_chord.track_names, current_chord.channels, current_chord.pan, current_chord.volume
    instruments_numbers = [
        i if isinstance(i, int) else instruments[i]
        for i in instruments_numbers
    ]
    MyMIDI = midiutil.MidiFile.MIDIFile(track_number,
                                        deinterleave=deinterleave,
                                        removeDuplicates=remove_duplicates,
                                        **midi_args)
    MyMIDI.addTempo(0, 0, bpm)
    for i in range(track_number):
        if channels:
            current_channel = channels[i]
        else:
            current_channel = i
        MyMIDI.addProgramChange(i, current_channel, 0,
                                instruments_numbers[i] - 1)
        if track_names:
            MyMIDI.addTrackName(i, 0, track_names[i])

        current_pan_msg = pan_msg[i]
        if current_pan_msg:
            for each in current_pan_msg:
                current_pan_track = i if each.track is None else each.track
                current_pan_channel = current_channel if each.channel is None else each.channel
                MyMIDI.addControllerEvent(
                    current_pan_track if not is_track_type else 0,
                    current_pan_channel, each.start_time * 4, 10, each.value)
        current_volume_msg = volume_msg[i]
        if current_volume_msg:
            for each in current_volume_msg:
                current_volume_channel = current_channel if each.channel is None else each.channel
                current_volume_track = i if each.track is None else each.track
                MyMIDI.addControllerEvent(
                    current_volume_track if not is_track_type else 0,
                    current_volume_channel, each.start_time * 4, 7, each.value)

        content = tracks_contents[i]
        content_notes = content.notes
        content_intervals = content.interval
        current_start_time = start_times[i] * 4
        for j in range(len(content)):
            current_note = content_notes[j]
            current_type = type(current_note)
            if current_type == note:
                MyMIDI.addNote(
                    i, current_channel
                    if current_note.channel is None else current_note.channel,
                    current_note.degree, current_start_time,
                    current_note.duration * 4, current_note.volume)
                current_start_time += content_intervals[j] * 4
            elif current_type == tempo:
                if current_note.start_time is not None:
                    if current_note.start_time < 0:
                        tempo_change_time = 0
                    else:
                        tempo_change_time = current_note.start_time * 4
                else:
                    tempo_change_time = current_start_time
                MyMIDI.addTempo(0, tempo_change_time, current_note.bpm)
            elif current_type == pitch_bend:
                if current_note.start_time is not None:
                    if current_note.start_time < 0:
                        pitch_bend_time = 0
                    else:
                        pitch_bend_time = current_note.start_time * 4
                else:
                    pitch_bend_time = current_start_time
                pitch_bend_track = i if current_note.track is None else current_note.track
                pitch_bend_channel = current_channel if current_note.channel is None else current_note.channel
                MyMIDI.addPitchWheelEvent(
                    pitch_bend_track if not is_track_type else 0,
                    pitch_bend_channel, pitch_bend_time, current_note.value)
            elif current_type == tuning:
                note_tuning_track = i if current_note.track is None else current_note.track
                MyMIDI.changeNoteTuning(
                    note_tuning_track if not is_track_type else 0,
                    current_note.tunings, current_note.sysExChannel,
                    current_note.realTime, current_note.tuningProgam)

    if not nomsg:
        if current_chord.other_messages:
            add_other_messages(MyMIDI, current_chord.other_messages,
                               'piece' if not is_track_type else 'track')
        elif msg:
            add_other_messages(MyMIDI, msg,
                               'piece' if not is_track_type else 'track')
    if save_as_file:
        with open(name, "wb") as output_file:
            MyMIDI.writeFile(output_file)
        return
    else:
        current_io = BytesIO()
        MyMIDI.writeFile(current_io)
        return current_io


def add_other_messages(MyMIDI, other_messages, write_type='piece'):
    for each in other_messages:
        try:
            current_type = type(each)
            curernt_track = each.track if write_type == 'piece' else 0
            if current_type == controller_event:
                MyMIDI.addControllerEvent(curernt_track, each.channel,
                                          each.time, each.controller_number,
                                          each.parameter)
            elif current_type == copyright_event:
                MyMIDI.addCopyright(curernt_track, each.time, each.notice)
            elif current_type == key_signature:
                MyMIDI.addKeySignature(curernt_track, each.time,
                                       each.accidentals, each.accidental_type,
                                       each.mode)
            elif current_type == sysex:
                MyMIDI.addSysEx(curernt_track, each.time, each.manID,
                                each.payload)
            elif current_type == text_event:
                MyMIDI.addText(curernt_track, each.time, each.text)
            elif current_type == time_signature:
                MyMIDI.addTimeSignature(curernt_track, each.time,
                                        each.numerator,
                                        int(math.log(each.denominator,
                                                     2)), each.clocks_per_tick,
                                        each.notes_per_quarter)
            elif current_type == universal_sysex:
                MyMIDI.addUniversalSysEx(curernt_track, each.time, each.code,
                                         each.subcode, each.payload,
                                         each.sysExChannel, each.realTime)
            elif current_type == rpn:
                if each.registered:
                    MyMIDI.makeRPNCall(curernt_track, each.channel, each.time,
                                       each.controller_msb,
                                       each.controller_lsb, each.data_msb,
                                       each.data_lsb, each.time_order)
                else:
                    MyMIDI.makeNRPNCall(curernt_track, each.channel, each.time,
                                        each.controller_msb,
                                        each.controller_lsb, each.data_msb,
                                        each.data_lsb, each.time_order)
            elif current_type == tuning_bank:
                MyMIDI.changeTuningBank(curernt_track, each.channel, each.time,
                                        each.bank, each.time_order)
            elif current_type == tuning_program:
                MyMIDI.changeTuningProgram(curernt_track, each.channel,
                                           each.time, each.program,
                                           each.time_order)
            elif current_type == channel_pressure:
                MyMIDI.addChannelPressure(curernt_track, each.channel,
                                          each.time, each.pressure_value)
            elif current_type == program_change:
                MyMIDI.addProgramChange(curernt_track, each.channel, each.time,
                                        each.program)
            elif current_type == track_name:
                MyMIDI.addTrackName(curernt_track, each.time, each.name)
        except:
            pass


def detect_in_scale(current_chord,
                    most_like_num=3,
                    get_scales=False,
                    search_all=True,
                    search_all_each_num=2,
                    major_minor_preference=True,
                    find_altered=True,
                    altered_max_number=1):
    if not isinstance(current_chord, chord):
        current_chord = chord([trans_note(i) for i in current_chord])
    whole_notes = current_chord.names()
    note_names = list(set(whole_notes))
    note_names = [
        standard_dict[i] if i not in standard2 else i for i in note_names
    ]
    first_note = whole_notes[0]
    results = []
    if find_altered:
        altered_scales = []
    for each in scaleTypes:
        scale_name = each[0]
        if scale_name != '12':
            current_scale = scale(first_note, scale_name)
            current_scale_notes = current_scale.names()
            if all(i in current_scale_notes for i in note_names):
                results.append(current_scale)
                if not search_all:
                    break
            else:
                if find_altered:
                    altered = [
                        i for i in note_names if i not in current_scale_notes
                    ]
                    if len(altered) <= altered_max_number:
                        altered = [trans_note(i) for i in altered]
                        if all((j.up().name in current_scale_notes
                                or j.down().name in current_scale_notes)
                               for j in altered):
                            altered_msg = []
                            for k in altered:
                                altered_note = k.up().name
                                header = 'b'
                                if not (altered_note in current_scale_notes
                                        and altered_note not in note_names):
                                    altered_note = k.down().name
                                    header = '#'
                                if altered_note in current_scale_notes and altered_note not in note_names:
                                    inds = current_scale_notes.index(
                                        altered_note) + 1
                                    test_scale_exist = copy(
                                        current_scale.notes)
                                    if k.degree - test_scale_exist[
                                            inds - 2].degree < 0:
                                        k = k.up(octave)
                                    test_scale_exist[inds - 1] = k
                                    if chord(test_scale_exist).intervalof(
                                            cummulative=False
                                    ) not in scaleTypes.values():
                                        altered_msg.append(f'{header}{inds}')
                                        altered_scales.append(
                                            f"{current_scale.start.name} {current_scale.mode} {', '.join(altered_msg)}"
                                        )
    if search_all:
        current_chord_len = len(current_chord)
        results.sort(key=lambda s: current_chord_len / len(s), reverse=True)
    if results:
        first_note_scale = results[0]
        inversion_scales = [
            first_note_scale.inversion(i)
            for i in range(2, len(first_note_scale))
        ]
        inversion_scales = [
            i for i in inversion_scales if i.mode != 'not found'
        ][:search_all_each_num]
        results += inversion_scales
        if major_minor_preference:
            major_or_minor_inds = [
                i for i in range(len(results))
                if results[i].mode in ['major', 'minor']
            ]
            if len(major_or_minor_inds) > 1:
                results.insert(1, results.pop(major_or_minor_inds[1]))
            else:
                if len(major_or_minor_inds) > 0:
                    first_major_minor_ind = major_or_minor_inds[0]
                    if results[first_major_minor_ind].mode == 'major':
                        results.insert(first_major_minor_ind + 1,
                                       results[first_major_minor_ind] - 3)
                    elif results[first_major_minor_ind].mode == 'minor':
                        results.insert(first_major_minor_ind + 1,
                                       results[first_major_minor_ind] + 3)

    results = results[:most_like_num]
    if get_scales:
        if (not results) and find_altered:
            return altered_scales
        return results
    detect_result = f'most likely scales: {", ".join([f"{each.start.name} {each.mode}" for each in results])}'
    if find_altered and altered_scales:
        if results:
            detect_result += ', '
        detect_result += ', '.join(altered_scales)
    return detect_result


def most_appear_notes_detect_scale(current_chord,
                                   most_appeared_note,
                                   get_scales=False):
    third_degree_major = most_appeared_note.up(major_third).name
    third_degree_minor = most_appeared_note.up(minor_third).name
    if current_chord.count(third_degree_major) > current_chord.count(
            third_degree_minor):
        current_mode = 'major'
        if current_chord.count(most_appeared_note.up(
                augmented_fourth).name) > current_chord.count(
                    most_appeared_note.up(perfect_fourth).name):
            current_mode = 'lydian'
        else:
            if current_chord.count(most_appeared_note.up(
                    minor_seventh).name) > current_chord.count(
                        most_appeared_note.up(major_seventh).name):
                current_mode = 'mixolydian'
    else:
        current_mode = 'minor'
        if current_chord.count(
                most_appeared_note.up(major_sixth).name) > current_chord.count(
                    most_appeared_note.up(minor_sixth).name):
            current_mode = 'dorian'
        else:
            if current_chord.count(most_appeared_note.up(
                    minor_second).name) > current_chord.count(
                        most_appeared_note.up(major_second).name):
                current_mode = 'phrygian'
                if current_chord.count(
                        most_appeared_note.up(
                            diminished_fifth).name) > current_chord.count(
                                most_appeared_note.up(perfect_fifth).name):
                    current_mode = 'locrian'
    if get_scales:
        return scale(most_appeared_note.name, current_mode)
    return f'{most_appeared_note.name} {current_mode}'


def detect_scale(current_chord,
                 melody_tol=minor_seventh,
                 chord_tol=major_sixth,
                 get_off_overlap_notes=True,
                 average_degree_length=8,
                 melody_degree_tol=toNote('B4'),
                 most_like_num=3,
                 count_num=3,
                 get_scales=False,
                 not_split=False,
                 most_appear_num=5,
                 major_minor_preference=True):
    # receive a piece of music and analyze what modes it is using,
    # return a list of most likely and exact modes the music has.

    # newly added on 2020/4/25, currently in development
    current_chord = current_chord.only_notes()
    counts = current_chord.count_appear(sort=True)
    most_appeared_note = [N(each[0]) for each in counts[:most_appear_num]]
    result_scales = [
        most_appear_notes_detect_scale(current_chord, each, get_scales)
        for each in most_appeared_note
    ]
    '''
        if result_scale_types == 'major':
            melody_notes = split_melody(
                current_chord, 'notes', melody_tol, chord_tol, get_off_overlap_notes,
                average_degree_length,
                melody_degree_tol) if not not_split else current_chord
            melody_notes = [i.name for i in melody_notes]
            scale_notes = result_scale.names()
            scale_notes_counts = [melody_notes.count(k) for k in scale_notes]
            # each mode's (except major and minor modes) tonic checking parameter is the sum of
            # melody notes's counts of 3 notes: the mode's first note (tonic note),
            # the third note (b3 or 3 or other special cases),
            # the most important characteristic note of the mode.
            # if the the mode to check is either major or minor modes,
            # then these 3 notes are the tonic triad of the mode,
            # for major scale it is 1, 3, 5, for minor scale it is 6, 1, 3 (in terms of major scale 1234567)
            current_mode_check_parameters = [[
                each[0],
                sum(scale_notes_counts[j - 1] for j in each[1]), each[2]
            ] for each in mode_check_parameters]
            current_mode_check_parameters.sort(key=lambda j: j[1],
                                               reverse=True)
            most_probably = current_mode_check_parameters[:most_like_num]
            most_probably_scale_ls = [
                result_scale.inversion(each[2]) for each in most_probably
            ]
            if get_scales:
                return most_probably_scale_ls
            return f'most likely scales: {", ".join([f"{each.start.name} {each.mode}" for each in most_probably_scale_ls])}'
    else:
        melody_notes = split_melody(
            current_chord, 'notes', melody_tol, chord_tol, get_off_overlap_notes,
            average_degree_length, melody_degree_tol) if not not_split else current_chord
        melody_notes = [i.name for i in melody_notes]
        appear_note_names = set(whole_notes)
        notes_count = {y: whole_notes.count(y) for y in appear_note_names}
        counts = list(notes_count.keys())
        counts.sort(key=lambda j: notes_count[j], reverse=True)
        try_scales = [scale(g, 'major') for g in counts[:count_num]]
        scale_notes_counts_ls = [[
            each.start.name, [melody_notes.count(k) for k in each.names()]
        ] for each in try_scales]
        current_mode_check_parameters = [[[
            y[0], each[0],
            sum(y[1][j - 1] for j in each[1]), each[2]
        ] for each in mode_check_parameters] for y in scale_notes_counts_ls]
        for each in current_mode_check_parameters:
            each.sort(key=lambda j: j[2], reverse=True)
        count_ls = [i for j in current_mode_check_parameters for i in j]
        count_ls.sort(key=lambda y: y[2], reverse=True)
        most_probably = count_ls[:most_like_num]
        most_probably_scale_ls = [
            scale(each[0], 'major').inversion(each[3])
            for each in most_probably
        ]
        if get_scales:
            return most_probably_scale_ls
        return f'most likely scales: {", ".join([f"{each.start.name} {each.mode}" for each in most_probably_scale_ls])}'
    '''
    if major_minor_preference:
        if get_scales:
            major_minor_inds = [
                i for i in range(len(result_scales))
                if result_scales[i].mode in ['major', 'minor']
            ]
        else:
            major_minor_inds = [
                i for i in range(len(result_scales))
                if any(k in result_scales[i] for k in ['major', 'minor'])
            ]
        result_scales = [result_scales[i] for i in major_minor_inds] + [
            result_scales[i]
            for i in range(len(result_scales)) if i not in major_minor_inds
        ]
    if get_scales:
        return result_scales
    return f'most likely scales: {", ".join(result_scales)}'


def get_chord_root_note(chord_name, get_chord_types=False):
    types = type(chord_name)
    if types == chord:
        chord_name = detect(chord_name)
        if isinstance(chord_name, list):
            chord_name = chord_name[0]
    elif types == list:
        chord_name = chord_name[0]
    elif types == note:
        chord_name = str(chord_name)
    if chord_name.startswith('note '):
        result = chord_name.split('note ')[1][:2]
        if result in standard:
            if result not in standard2:
                result = standard_dict[result]
        else:
            result = result[0]
            if result in standard:
                if result not in standard2:
                    result = standard_dict[result]
        if get_chord_types:
            return result, ''
        return result
    if get_chord_types:
        situation = 0
    if chord_name[0] != '[':
        result = chord_name[:2]
        if get_chord_types:
            if '/' in chord_name:
                situation = 0
                part1, part2 = chord_name.split('/')
            else:
                situation = 1

    else:
        if chord_name[-1] == ']':
            inds = chord_name.rfind('[') - 1
        else:
            inds = chord_name.index('/')
        upper, lower = chord_name[:inds], chord_name[inds + 1:]
        if lower[0] != '[':
            result = upper[1:3]
            if get_chord_types:
                situation = 2
        else:
            result = lower[1:3]
            if get_chord_types:
                situation = 3
    if result in standard:
        if result not in standard2:
            result = standard_dict[result]
    else:
        result = result[0]
        if result in standard:
            if result not in standard2:
                result = standard_dict[result]
    if get_chord_types:
        if situation == 0:
            chord_types = part1.split(' ')[0][len(result):]
        elif situation == 1:
            chord_types = chord_name.split(' ')[0][len(result):]
        elif situation == 2:
            upper = upper[1:-1].split(' ')[0]
            chord_types = upper[len(result):]
        elif situation == 3:
            lower = lower[1:-1].split(' ')[0]
            chord_types = lower[len(result):]
        if chord_types == '':
            if 'with ' in chord_name:
                chord_types = 'with ' + chord_name.split('with ')[1]
            else:
                chord_types = 'major'
        return result, chord_types
    return result


def get_chord_functions(mode, chords, as_list=False, functions_interval=1):
    if not isinstance(chords, list):
        chords = [chords]
    note_names = mode.names()
    root_note_list = [get_chord_root_note(i, True) for i in chords]
    functions = []
    for each in root_note_list:
        root_note, chord_types = each
        root_note_obj = note(root_note, 5)
        header = ''
        if root_note not in note_names:
            root_note_obj = root_note_obj.up(1)
            root_note = root_note_obj.name
            if root_note in note_names:
                header = 'b'
            else:
                root_note_obj = root_note_obj.down(2)
                root_note = root_note_obj.name
                if root_note in note_names:
                    header = '#'
        scale_degree = note_names.index(root_note)
        current_function = chord_functions_roman_numerals[scale_degree + 1]
        if chord_types == '' or chord_types == '5':
            original_chord = mode(scale_degree)
            third_type = original_chord[1].degree - original_chord[0].degree
            if third_type == minor_third:
                current_function = current_function.lower()
        else:
            current_chord = chd(root_note, chord_types)
            if current_chord != 'could not detect the chord types':
                current_chord_names = current_chord.names()
            else:
                current_chord_names = [
                    root_note_obj.name,
                    root_note_obj.up(NAME_OF_INTERVAL[chord_types[5:]]).name
                ]
            if chord_types in chord_function_dict:
                to_lower, function_name = chord_function_dict[chord_types]
                if to_lower:
                    current_function = current_function.lower()
                current_function += function_name
            else:
                M3 = root_note_obj.up(major_third).name
                m3 = root_note_obj.up(minor_third).name
                if m3 in current_chord_names:
                    current_function = current_function.lower()
                if len(current_chord_names) >= 3:
                    current_function += '?'
        current_function = header + current_function
        functions.append(current_function)
    if as_list:
        return functions
    return (' ' * functions_interval + '–' +
            ' ' * functions_interval).join(functions)


def get_chord_notations(chords,
                        as_list=False,
                        functions_interval=1,
                        split_symbol='|'):
    if not isinstance(chords, list):
        chords = [chords]
    root_note_list = [get_chord_root_note(i, True) for i in chords]
    notations = []
    for each in root_note_list:
        root_note, chord_types = each
        current_notation = root_note
        root_note_obj = note(root_note, 5)
        if chord_types in chord_notation_dict:
            current_notation += chord_notation_dict[chord_types]
        else:
            current_chord = chd(root_note, chord_types)
            if current_chord != 'could not detect the chord types':
                current_chord_names = current_chord.names()
            else:
                current_chord_names = [
                    root_note_obj.name,
                    root_note_obj.up(NAME_OF_INTERVAL[chord_types[5:]]).name
                ]
            M3 = root_note_obj.up(major_third).name
            m3 = root_note_obj.up(minor_third).name
            if m3 in current_chord_names:
                current_notation += '-'
            if len(current_chord_names) >= 3:
                current_notation += '?'
        notations.append(current_notation)
    if as_list:
        return notations
    return (' ' * functions_interval + split_symbol +
            ' ' * functions_interval).join(notations)


def chord_functions_analysis(current_chord,
                             scale_type='major',
                             as_list=False,
                             functions_interval=1,
                             split_symbol='|',
                             chord_mode='function',
                             fixed_scale_type=None,
                             write_to_file=False,
                             each_line_chords_number=15,
                             space_lines=2,
                             full_chord_msg=False,
                             **detect_args):
    current_chord = current_chord.only_notes()
    if fixed_scale_type:
        scales = fixed_scale_type
    else:
        scales = current_chord.detect_scale(get_scales=True)
        if scale_type:
            scales = [i for i in scales if i.mode == scale_type][0]
        else:
            scales = scales[0]
    result = chord_analysis(current_chord, mode='chords')
    result = [i.standardize() for i in result]
    actual_chords = [detect(i, **detect_args) for i in result if len(i) > 1]
    actual_chords = [i[0] if isinstance(i, list) else i for i in actual_chords]
    if chord_mode == 'function':
        if not write_to_file:
            chord_progressions = get_chord_functions(scales, actual_chords,
                                                     as_list,
                                                     functions_interval)
        else:
            chord_progressions = get_chord_functions(scales, actual_chords,
                                                     True, functions_interval)
            if full_chord_msg:
                chord_progressions = [
                    chord_progressions[i] + ' ' +
                    ' '.join(actual_chords[i].split(' ')[1:])
                    for i in range(len(chord_progressions))
                ]
            num = (len(chord_progressions) // each_line_chords_number) + 1
            delimiter = ' ' * functions_interval + '–' + ' ' * functions_interval
            chord_progressions = [
                delimiter.join(chord_progressions[each_line_chords_number *
                                                  i:each_line_chords_number *
                                                  (i + 1)]) + delimiter
                for i in range(num)
            ]
            chord_progressions[-1] = chord_progressions[-1][:-len(delimiter)]
            chord_progressions = ('\n' * space_lines).join(chord_progressions)
    elif chord_mode == 'notation':
        if full_chord_msg:
            num = (len(actual_chords) // each_line_chords_number) + 1
            delimiter = ' ' * functions_interval + split_symbol + ' ' * functions_interval
            chord_progressions = [
                delimiter.join(actual_chords[each_line_chords_number *
                                             i:each_line_chords_number *
                                             (i + 1)]) + delimiter
                for i in range(num)
            ]
            chord_progressions[-1] = chord_progressions[-1][:-len(delimiter)]
            chord_progressions = ('\n' * space_lines).join(chord_progressions)
        elif not write_to_file:
            chord_progressions = get_chord_notations(actual_chords, as_list,
                                                     functions_interval,
                                                     split_symbol)
        else:
            chord_progressions = get_chord_notations(actual_chords, True,
                                                     functions_interval,
                                                     split_symbol)
            num = (len(chord_progressions) // each_line_chords_number) + 1
            delimiter = ' ' * functions_interval + split_symbol + ' ' * functions_interval
            chord_progressions = [
                delimiter.join(chord_progressions[each_line_chords_number *
                                                  i:each_line_chords_number *
                                                  (i + 1)]) + delimiter
                for i in range(num)
            ]
            chord_progressions[-1] = chord_progressions[-1][:-len(delimiter)]
            chord_progressions = ('\n' * space_lines).join(chord_progressions)
    spaces = '\n' * space_lines
    analysis_result = f'key: {scales[0].name} {scales.mode}{spaces}{chord_progressions}'
    if write_to_file:
        with open('chords functions analysis result.txt',
                  'w',
                  encoding='utf-8') as f:
            f.write(analysis_result)
        analysis_result += spaces + "Successfully write the chord analysis result as a text file, please see 'chords functions analysis result.txt'."
        return analysis_result
    else:
        return analysis_result


def split_melody(current_chord,
                 mode='index',
                 melody_tol=minor_seventh,
                 chord_tol=major_sixth,
                 get_off_overlap_notes=True,
                 average_degree_length=8,
                 melody_degree_tol=toNote('B4')):
    # if mode == 'notes', return a list of main melody notes
    # if mode == 'index', return a list of indexes of main melody notes
    # if mode == 'hold', return a chord with main melody notes with original places
    if not isinstance(melody_degree_tol, note):
        melody_degree_tol = toNote(melody_degree_tol)
    if mode == 'notes':
        result = split_melody(current_chord, 'index', melody_tol, chord_tol,
                              get_off_overlap_notes, average_degree_length,
                              melody_degree_tol)
        current_chord_notes = current_chord.notes
        melody = [current_chord_notes[t] for t in result]
        return melody
    elif mode == 'hold':
        result = split_melody(current_chord, 'index', melody_tol, chord_tol,
                              get_off_overlap_notes, average_degree_length,
                              melody_degree_tol)
        return current_chord.pick(result)

    elif mode == 'index':
        current_chord_notes = current_chord.notes
        current_chord_interval = current_chord.interval
        whole_length = len(current_chord)
        for k in range(whole_length):
            current_chord_notes[k].number = k
        other_messages_inds = [
            i for i in range(whole_length)
            if not isinstance(current_chord_notes[i], note)
        ]
        temp = current_chord.only_notes()
        N = len(temp)
        whole_notes = temp.notes
        whole_interval = temp.interval
        if get_off_overlap_notes:
            for j in range(N):
                current_note = whole_notes[j]
                current_interval = whole_interval[j]
                if current_interval != 0:
                    if current_note.duration >= current_interval:
                        current_note.duration = current_interval
                else:
                    for y in range(j + 1, N):
                        next_interval = whole_interval[y]
                        if next_interval != 0:
                            if current_note.duration >= next_interval:
                                current_note.duration = next_interval
                            break
            unit_duration = min([i.duration for i in whole_notes])
            for each in whole_notes:
                each.duration = unit_duration
            whole_interval = [
                current_chord_interval[j.number] for j in whole_notes
            ]
            k = 0
            while k < len(whole_notes) - 1:
                current_note = whole_notes[k]
                next_note = whole_notes[k + 1]
                current_interval = whole_interval[k]
                if current_note.degree == next_note.degree:
                    if current_interval == 0:
                        del whole_notes[k + 1]
                        del whole_interval[k]
                k += 1

        play_together = find_all_continuous(whole_interval, 0)
        for each in play_together:
            max_ind = max(each, key=lambda t: whole_notes[t].degree)
            get_off = set(each) - {max_ind}
            for each_ind in get_off:
                whole_notes[each_ind] = None
        whole_notes = [x for x in whole_notes if x is not None]
        N = len(whole_notes) - 1
        start = 0
        if whole_notes[1].degree - whole_notes[0].degree >= chord_tol:
            start = 1
        i = start + 1
        melody = [whole_notes[start]]
        notes_num = 1
        melody_duration = [melody[0].duration]
        while i < N:
            current_note = whole_notes[i]
            next_note = whole_notes[i + 1]
            next_degree_diff = next_note.degree - current_note.degree
            recent_notes = add_to_index(melody_duration, average_degree_length,
                                        notes_num - 1, -1, -1)
            if recent_notes:
                current_average_degree = sum(
                    [melody[j].degree
                     for j in recent_notes]) / len(recent_notes)
                average_diff = current_average_degree - current_note.degree
                if average_diff <= melody_tol:
                    if melody[-1].degree - current_note.degree < chord_tol:
                        melody.append(current_note)
                        notes_num += 1
                        melody_duration.append(current_note.duration)
                    else:
                        if abs(
                                next_degree_diff
                        ) < chord_tol and current_note.degree >= melody_degree_tol.degree:
                            melody.append(current_note)
                            notes_num += 1
                            melody_duration.append(current_note.duration)
                else:

                    if (melody[-1].degree - current_note.degree < chord_tol
                            and next_degree_diff < chord_tol
                            and all(k.degree - current_note.degree < chord_tol
                                    for k in melody[-2:])):
                        melody.append(current_note)
                        notes_num += 1
                        melody_duration.append(current_note.duration)
                    else:
                        if (abs(next_degree_diff) < chord_tol and
                                current_note.degree >= melody_degree_tol.degree
                                and all(
                                    k.degree - current_note.degree < chord_tol
                                    for k in melody[-2:])):
                            melody.append(current_note)
                            notes_num += 1
                            melody_duration.append(current_note.duration)
            i += 1
        melody_inds = [each.number for each in melody]
        whole_inds = melody_inds + other_messages_inds
        whole_inds.sort()
        return whole_inds


def split_chord(current_chord,
                mode='index',
                melody_tol=minor_seventh,
                chord_tol=major_sixth,
                get_off_overlap_notes=True,
                average_degree_length=8,
                melody_degree_tol=toNote('B4')):
    melody_ind = split_melody(current_chord, 'index', melody_tol, chord_tol,
                              get_off_overlap_notes, average_degree_length,
                              melody_degree_tol)
    N = len(current_chord)
    whole_notes = current_chord.notes
    other_messages_inds = [
        i for i in range(N) if not isinstance(whole_notes[i], note)
    ]
    chord_ind = [
        i for i in range(N)
        if (i not in melody_ind) or (i in other_messages_inds)
    ]
    if mode == 'index':
        return chord_ind
    elif mode == 'notes':
        return [whole_notes[k] for k in chord_ind]
    elif mode == 'hold':
        return current_chord.pick(chord_ind)


def split_all(current_chord,
              mode='index',
              melody_tol=minor_seventh,
              chord_tol=major_sixth,
              get_off_overlap_notes=True,
              average_degree_length=8,
              melody_degree_tol=toNote('B4')):
    # split the main melody and chords part of a piece of music,
    # return both of main melody and chord part
    melody_ind = split_melody(current_chord, 'index', melody_tol, chord_tol,
                              get_off_overlap_notes, average_degree_length,
                              melody_degree_tol)
    N = len(current_chord)
    whole_notes = current_chord.notes
    chord_ind = [
        i for i in range(N)
        if (i not in melody_ind) or (not isinstance(whole_notes[i], note))
    ]
    if mode == 'index':
        return [melody_ind, chord_ind]
    elif mode == 'notes':
        return [[whole_notes[j] for j in melody_ind],
                [whole_notes[k] for k in chord_ind]]
    elif mode == 'hold':
        result_chord = current_chord.pick(chord_ind)
        result_melody = current_chord.pick(melody_ind)
        # shift is the start time that chord part starts after main melody starts,
        # or the start time that main melody starts after chord part starts,
        # depends on which starts earlier, if shift >= 0, chord part starts after main melody,
        # if shift < 0, chord part starts before main melody
        shift = result_chord.start_time - result_melody.start_time
        result_chord.start_time = 0
        return [result_melody, result_chord, shift]


def chord_analysis(chords,
                   melody_tol=minor_seventh,
                   chord_tol=major_sixth,
                   get_off_overlap_notes=True,
                   average_degree_length=8,
                   melody_degree_tol=toNote('B4'),
                   mode='chord names',
                   get_chord_inds=False,
                   is_chord=False,
                   new_chord_tol=minor_seventh,
                   get_original_order=False,
                   formated=False,
                   formated_mode=1,
                   output_as_file=False,
                   each_line_chords_number=5,
                   functions_interval=1,
                   split_symbol='|',
                   space_lines=2,
                   **detect_args):
    chords = chords.only_notes()
    if not is_chord:
        chord_notes = split_chord(chords, 'hold', melody_tol, chord_tol,
                                  get_off_overlap_notes, average_degree_length,
                                  melody_degree_tol)
    else:
        chord_notes = chords
    if formated or (mode in ['inds', 'bars', 'bars start']):
        get_original_order = True
    whole_notes = chord_notes.notes
    chord_ls = []
    current_chord = [whole_notes[0]]
    if get_original_order:
        chord_inds = []
    N = len(whole_notes) - 1
    for i in range(N):
        current_note = whole_notes[i]
        next_note = whole_notes[i + 1]
        if current_note.degree <= next_note.degree:
            if i > 0 and chord_notes.interval[
                    i - 1] == 0 and chord_notes.interval[i] != 0:
                chord_ls.append(chord(current_chord).sortchord())
                if get_original_order:
                    chord_inds.append([i + 1 - len(current_chord), i + 1])
                current_chord = []
                current_chord.append(next_note)

            else:
                current_chord.append(next_note)
        elif chord_notes.interval[i] == 0:
            current_chord.append(next_note)
        elif current_note.degree > next_note.degree:
            if len(current_chord) < 3:
                if len(current_chord) == 2:
                    if next_note.degree > min(
                        [k.degree for k in current_chord]):
                        current_chord.append(next_note)
                    else:
                        chord_ls.append(chord(current_chord).sortchord())
                        if get_original_order:
                            chord_inds.append(
                                [i + 1 - len(current_chord), i + 1])
                        current_chord = []
                        current_chord.append(next_note)
                else:
                    current_chord.append(next_note)
            else:
                current_chord_degrees = sorted(
                    [k.degree for k in current_chord])
                if next_note.degree >= current_chord_degrees[2]:
                    if current_chord_degrees[
                            -1] - next_note.degree >= new_chord_tol:
                        chord_ls.append(chord(current_chord).sortchord())
                        if get_original_order:
                            chord_inds.append(
                                [i + 1 - len(current_chord), i + 1])
                        current_chord = []
                        current_chord.append(next_note)
                    else:
                        current_chord.append(next_note)
                else:
                    chord_ls.append(chord(current_chord).sortchord())
                    if get_original_order:
                        chord_inds.append([i + 1 - len(current_chord), i + 1])
                    current_chord = []
                    current_chord.append(next_note)
    chord_ls.append(chord(current_chord).sortchord())
    if get_original_order:
        chord_inds.append([N + 1 - len(current_chord), N + 1])
    current_chord = []
    if formated:
        result = [detect(each, **detect_args) for each in chord_ls]
        result = [i if not isinstance(i, list) else i[0] for i in result]
        result_notes = [chord_notes[k[0]:k[1]] for k in chord_inds]
        result_notes = [
            each.sortchord() if all(j == 0
                                    for j in each.interval[:-1]) else each
            for each in result_notes
        ]
        if formated_mode == 0:
            chords_formated = '\n\n'.join([
                f'chord {i+1}: {result[i]}    notes: {result_notes[i]}'
                for i in range(len(result))
            ])
        elif formated_mode == 1:
            num = (len(result) // each_line_chords_number) + 1
            delimiter = ' ' * functions_interval + split_symbol + ' ' * functions_interval
            chords_formated = [
                delimiter.join(result[each_line_chords_number *
                                      i:each_line_chords_number * (i + 1)]) +
                delimiter for i in range(num)
            ]
            chords_formated[-1] = chords_formated[-1][:-len(delimiter)]
            chords_formated = ('\n' * space_lines).join(chords_formated)
        if output_as_file:
            with open('chord analysis result.txt', 'w', encoding='utf-8') as f:
                f.write(chords_formated)
            chords_formated += "\n\nSuccessfully write the chord analysis result as a text file, please see 'chord analysis result.txt'."
        return chords_formated
    if mode == 'chords':
        if get_original_order:
            return [chord_notes[k[0]:k[1]] for k in chord_inds]
        return chord_ls
    elif mode == 'chord names':
        result = [detect(each, **detect_args) for each in chord_ls]
        return [i if not isinstance(i, list) else i[0] for i in result]
    elif mode == 'inds':
        return [[i[0], i[1]] for i in chord_inds]
    elif mode == 'bars':
        inds = [[i[0], i[1]] for i in chord_inds]
        return [chord_notes.count_bars(k[0], k[1]) for k in inds]
    elif mode == 'bars start':
        inds = [[i[0], i[1]] for i in chord_inds]
        return [chord_notes.count_bars(k[0], k[1])[0] for k in inds]


def find_continuous(current_chord, value, start=None, stop=None):
    if start is None:
        start = 0
    if stop is None:
        stop = len(current_chord)
    inds = []
    appear = False
    for i in range(start, stop):
        if not appear:
            if current_chord[i] == value:
                appear = True
                inds.append(i)
        else:
            if current_chord[i] == value:
                inds.append(i)
            else:
                break
    return inds


def find_all_continuous(current_chord, value, start=None, stop=None):
    if start is None:
        start = 0
    if stop is None:
        stop = len(current_chord)
    result = []
    inds = []
    appear = False
    for i in range(start, stop):
        if current_chord[i] == value:
            if appear:
                inds.append(i)
            else:
                if inds:
                    inds.append(inds[-1] + 1)
                    result.append(inds)
                appear = True
                inds = [i]
        else:
            appear = False
    if inds:
        result.append(inds)
    try:
        if result[-1][-1] >= len(current_chord):
            del result[-1][-1]
    except:
        pass
    return result


def add_to_index(current_chord, value, start=None, stop=None, step=1):
    if start is None:
        start = 0
    if stop is None:
        stop = len(current_chord)
    inds = []
    counter = 0
    for i in range(start, stop, step):
        counter += current_chord[i]
        inds.append(i)
        if counter == value:
            inds.append(i + 1)
            break
        elif counter > value:
            break
    if not inds:
        inds = [0]
    return inds


def add_to_last_index(current_chord, value, start=None, stop=None, step=1):
    if start is None:
        start = 0
    if stop is None:
        stop = len(current_chord)
    ind = 0
    counter = 0
    for i in range(start, stop, step):
        counter += current_chord[i]
        ind = i
        if counter == value:
            ind += 1
            break
        elif counter > value:
            break
    return ind


def modulation(current_chord, old_scale, new_scale):
    # change notes (including both of melody and chords) in the given piece
    # of music from a given scale to another given scale, and return
    # the new changing piece of music.
    return current_chord.modulation(old_scale, new_scale)


def exp(form, obj_name='x', mode='tail'):
    # return a function that follows a mode of translating a given chord to the wanted result,
    # form is a chains of functions you want to perform on the variables.
    if mode == 'tail':
        try:
            func = eval(f'lambda x: x.{form}')
        except:
            raise ValueError('not a valid expression')
    elif mode == 'whole':
        try:
            func = eval(f'lambda {obj_name}: {form}')
        except:
            raise ValueError('not a valid expression')

    return func


def trans(obj, pitch=4, duration=0.25, interval=None):
    obj = obj.replace(' ', '')
    if obj in standard:
        return chd(obj,
                   'M',
                   pitch=pitch,
                   duration=duration,
                   intervals=interval)
    if '/' not in obj:
        check_structure = obj.split(',')
        check_structure_len = len(check_structure)
        if check_structure_len > 1:
            return trans(check_structure[0], pitch)(','.join(
                check_structure[1:])) % (duration, interval)
        N = len(obj)
        if N == 2:
            first = obj[0]
            types = obj[1]
            if first in standard and types in chordTypes:
                return chd(first,
                           types,
                           pitch=pitch,
                           duration=duration,
                           intervals=interval)
        elif N > 2:
            first_two = obj[:2]
            type1 = obj[2:]
            if first_two in standard and type1 in chordTypes:
                return chd(first_two,
                           type1,
                           pitch=pitch,
                           duration=duration,
                           intervals=interval)
            first_one = obj[0]
            type2 = obj[1:]
            if first_one in standard and type2 in chordTypes:
                return chd(first_one,
                           type2,
                           pitch=pitch,
                           duration=duration,
                           intervals=interval)
    else:
        parts = obj.split('/')
        part1, part2 = parts[0], '/'.join(parts[1:])
        first_chord = trans(part1, pitch)
        if isinstance(first_chord, chord):
            if part2.isdigit() or (part2[0] == '-' and part2[1:].isdigit()):
                return (first_chord / int(part2)) % (duration, interval)
            elif part2[-1] == '!' and part2[:-1].isdigit():
                return (first_chord @ int(part2[:-1])) % (duration, interval)
            elif part2 in standard:
                if part2 not in standard2:
                    part2 = standard_dict[part2]
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
        'not a valid chord representation or chord types not in database')


def toScale(obj, pitch=None):
    tonic, scale_name = obj.strip(' ').split(' ', 1)
    tonic = N(tonic)
    if pitch is not None:
        tonic.num = pitch
    scale_name = scale_name.strip(' ')
    return scale(tonic, scale_name)


def inversion_from(a, b, num=False, mode=0):
    N = len(b)
    for i in range(1, N):
        temp = b.inversion(i)
        if [x.name for x in temp.notes] == [y.name for y in a.notes]:
            return f'/{a[0].name}' if not num else f'{i} inversion'
    return f'could not get chord {a.notes} from a single inversion of chord {b.notes}, you could try sort from' if mode == 0 else None


def sort_from(a, b, getorder=False):
    names = [i.name for i in b]
    try:
        order = [names.index(j.name) + 1 for j in a]
        return f'{b.notes} sort as {order}' if not getorder else order
    except:
        return


def omit_from(a, b, showls=False, alter_notes_show_degree=False):
    a_notes = a.names()
    b_notes = b.names()
    omitnotes = list(set(b_notes) - set(a_notes))
    if alter_notes_show_degree:
        b_first_note = b[0].degree
        omitnotes_degree = []
        for j in omitnotes:
            current = reverse_degree_match[b[b_notes.index(j)].degree -
                                           b_first_note]
            if current == 'not found':
                omitnotes_degree.append(j)
            else:
                omitnotes_degree.append(current)
        omitnotes = omitnotes_degree
    if showls:
        result = omitnotes
    else:
        result = f"omit {', '.join(omitnotes)}"
        order_omit = chord([x for x in b_notes if x in a_notes])
        if order_omit.names() != a.names():
            result += ' ' + inversion_way(a, order_omit)
    return result


def change_from(a,
                b,
                octave_a=False,
                octave_b=False,
                same_degree=True,
                alter_notes_show_degree=False):
    # how a is changed from b (flat or sharp some notes of b to get a)
    # this is used only when two chords have the same number of notes
    # in the detect chord function
    if octave_a:
        a = a.inoctave()
    if octave_b:
        b = b.inoctave()
    if same_degree:
        b = b.down(12 * (b[0].num - a[0].num))
    N = min(len(a), len(b))
    anotes = [x.degree for x in a.notes]
    bnotes = [x.degree for x in b.notes]
    anames = a.names()
    bnames = b.names()
    M = min(len(anotes), len(bnotes))
    changes = [(bnames[i], bnotes[i] - anotes[i]) for i in range(M)]
    changes = [x for x in changes if x[1] != 0]
    if any(abs(j[1]) != 1 for j in changes):
        changes = []
    else:
        if not alter_notes_show_degree:
            changes = [f'b{j[0]}' if j[1] > 0 else f'#{j[0]}' for j in changes]
        else:
            b_first_note = b[0].degree
            for i in range(len(changes)):
                note_name, note_change = changes[i]
                current_degree = reverse_degree_match[
                    bnotes[bnames.index(note_name)] - b_first_note]
                if current_degree == 'not found':
                    current_degree = note_name
                if note_change > 0:
                    changes[i] = f'b{current_degree}'
                else:
                    changes[i] = f'#{current_degree}'

    return ', '.join(changes)


def contains(a, b):
    # if b contains a (notes), in other words,
    # all of a's notes is inside b's notes
    return set(a.names()) < set(b.names()) and len(a) < len(b)


def inversion_way(a, b, inv_num=False, chordtype=None, only_msg=False):
    if samenotes(a, b):
        return f'{b[0].name}{chordtype}'
    if samenote_set(a, b):
        inversion_msg = inversion_from(
            a, b, mode=1) if not inv_num else inversion_from(
                a, b, num=True, mode=1)
        if inversion_msg is not None:
            if not only_msg:
                if chordtype is not None:
                    return f'{b[0].name}{chordtype}{inversion_msg}' if not inv_num else f'{b[0].name}{chordtype} {inversion_msg}'
                else:
                    return inversion_msg
            else:
                return inversion_msg
        else:
            sort_msg = sort_from(a, b, getorder=True)
            if sort_msg is not None:
                if not only_msg:
                    if chordtype is not None:
                        return f'{b[0].name}{chordtype} sort as {sort_msg}'
                    else:
                        return f'sort as {sort_msg}'
                else:
                    return f'sort as {sort_msg}'
            else:
                return f'a voicing of {b[0].name}{chordtype}'
    else:
        return 'not good'


def samenotes(a, b):
    return a.names() == b.names()


def samenote_set(a, b):
    return set(a.names()) == set(b.names())


def find_similarity(a,
                    b=None,
                    only_ratio=False,
                    fromchord_name=True,
                    getgoodchord=False,
                    listall=False,
                    ratio_and_chord=False,
                    ratio_chordname=False,
                    provide_name=None,
                    result_ratio=False,
                    change_from_first=False,
                    same_note_special=True,
                    get_types=False,
                    alter_notes_show_degree=False):
    result = ''
    types = None
    if b is None:
        wholeTypes = chordTypes.keynames()
        selfname = a.names()
        rootnote = a[0]
        possible_chords = [(chd(rootnote, i), i) for i in wholeTypes]
        lengths = len(possible_chords)
        if same_note_special:
            ratios = [(1 if samenote_set(a, x[0]) else SequenceMatcher(
                None, selfname, x[0].names()).ratio(), x[1])
                      for x in possible_chords]
        else:
            ratios = [(SequenceMatcher(None, selfname,
                                       x[0].names()).ratio(), x[1])
                      for x in possible_chords]
        alen = len(a)
        ratios_temp = [
            ratios[k] for k in range(len(ratios))
            if len(possible_chords[k][0]) >= alen
        ]
        if len(ratios_temp) != 0:
            ratios = ratios_temp
        ratios.sort(key=lambda x: x[0], reverse=True)
        if listall:
            return ratios
        if only_ratio:
            return ratios[0]
        first = ratios[0]
        highest = first[0]
        chordfrom = possible_chords[wholeTypes.index(first[1])][0]
        if ratio_and_chord:
            if ratio_chordname:
                return first, chordfrom
            return highest, chordfrom
        if highest > 0.6:
            if change_from_first:
                result = find_similarity(
                    a,
                    chordfrom,
                    fromchord_name=False,
                    alter_notes_show_degree=alter_notes_show_degree)
                cff_ind = 0
                while result == 'not good':
                    cff_ind += 1
                    try:
                        first = ratios[cff_ind]
                    except:
                        first = ratios[0]
                        highest = first[0]
                        chordfrom = possible_chords[wholeTypes.index(
                            first[1])][0]
                        result = ''
                        break
                    highest = first[0]
                    chordfrom = possible_chords[wholeTypes.index(first[1])][0]
                    if highest > 0.6:
                        result = find_similarity(
                            a,
                            chordfrom,
                            fromchord_name=False,
                            alter_notes_show_degree=alter_notes_show_degree)
                    else:
                        first = ratios[0]
                        highest = first[0]
                        chordfrom = possible_chords[wholeTypes.index(
                            first[1])][0]
                        result = ''
                        break
            if highest == 1:
                chordfrom_type = first[1]
                if samenotes(a, chordfrom):
                    result = f'{rootnote.name}{chordfrom_type}'
                    types = 'original'
                else:
                    if samenote_set(a, chordfrom):
                        result = inversion_from(a, chordfrom, mode=1)
                        types = 'inversion'
                        if result is None:
                            sort_message = sort_from(a,
                                                     chordfrom,
                                                     getorder=True)
                            if sort_message is None:
                                result = f'a voicing of the chord {rootnote.name}{chordfrom_type}'
                            else:
                                result = f'{rootnote.name}{chordfrom_type} sort as {sort_message}'
                        else:
                            result = f'{rootnote.name}{chordfrom_type} {result}'
                    else:
                        return 'not good'
                if get_types:
                    result = [result, types]
                if result_ratio:
                    return (highest, result) if not getgoodchord else (
                        (highest,
                         result), chordfrom, f'{chordfrom[0].name}{first[1]}')
                return result if not getgoodchord else (
                    result, chordfrom, f'{chordfrom[0].name}{first[1]}')
            else:
                if samenote_set(a, chordfrom):
                    result = inversion_from(a, chordfrom, mode=1)
                    types = 'inversion'
                    if result is None:
                        sort_message = sort_from(a, chordfrom, getorder=True)
                        types = 'inversion'
                        if sort_message is None:
                            return f'a voicing of the chord {rootnote.name}{chordfrom_type}'
                        else:
                            result = f'sort as {sort_message}'
                elif contains(a, chordfrom):
                    result = omit_from(
                        a,
                        chordfrom,
                        alter_notes_show_degree=alter_notes_show_degree)
                    types = 'omit'
                elif len(a) == len(chordfrom):
                    result = change_from(
                        a,
                        chordfrom,
                        alter_notes_show_degree=alter_notes_show_degree)
                    types = 'change'
                if result == '':
                    return 'not good'

                if fromchord_name:
                    from_chord_names = f'{rootnote.name}{first[1]}'
                    result = f'{from_chord_names} {result}'
                if get_types:
                    result = [result, types]
                if result_ratio:
                    return (highest,
                            result) if not getgoodchord else ((highest,
                                                               result),
                                                              chordfrom,
                                                              from_chord_names)
                return result if not getgoodchord else (result, chordfrom,
                                                        from_chord_names)

        else:
            return 'not good'
    else:
        if samenotes(a, b):
            if fromchord_name:
                if provide_name != None:
                    bname = b[0].name + provide_name
                else:
                    bname = detect(b)
                return bname if not getgoodchord else (bname, chordfrom, bname)
            else:
                return 'same'
        if only_ratio or listall:
            return SequenceMatcher(None, a.names(), b.names()).ratio()
        chordfrom = b
        if samenote_set(a, chordfrom):
            result = inversion_from(a, chordfrom, mode=1)
            if result is None:
                sort_message = sort_from(a, chordfrom, getorder=True)
                if sort_message is None:
                    return f'a voicing of the chord {rootnote.name}{chordfrom_type}'
                else:
                    result = f'sort as {sort_message}'
        elif contains(a, chordfrom):
            result = omit_from(a,
                               chordfrom,
                               alter_notes_show_degree=alter_notes_show_degree)
        elif len(a) == len(chordfrom):
            result = change_from(
                a, chordfrom, alter_notes_show_degree=alter_notes_show_degree)
        if result == '':
            return 'not good'
        bname = None
        if fromchord_name:
            if provide_name != None:
                bname = b[0].name + provide_name
            else:
                bname = detect(b)
            if isinstance(bname, list):
                bname = bname[0]
        return result if not getgoodchord else (result, chordfrom, bname)


def detect_variation(current_chord,
                     mode='chord',
                     inv_num=False,
                     change_from_first=False,
                     original_first=False,
                     same_note_special=True,
                     N=None,
                     alter_notes_show_degree=False):
    for each in range(1, N):
        each_current = current_chord.inversion(each)
        each_detect = detect(each_current,
                             mode,
                             inv_num,
                             change_from_first,
                             original_first,
                             same_note_special,
                             whole_detect=False,
                             return_fromchord=True,
                             alter_notes_show_degree=alter_notes_show_degree)
        if each_detect is not None:
            detect_msg, change_from_chord, chord_name_str = each_detect
            inv_msg = inversion_way(current_chord, each_current, inv_num)
            result = f'{detect_msg} {inv_msg}'
            if any(x in detect_msg
                   for x in ['sort', '/']) and any(y in inv_msg
                                                   for y in ['sort', '/']):
                inv_msg = inversion_way(current_chord, change_from_chord,
                                        inv_num)
                if inv_msg == 'not good':
                    inv_msg = find_similarity(
                        current_chord,
                        change_from_chord,
                        alter_notes_show_degree=alter_notes_show_degree)
                result = f'{chord_name_str} {inv_msg}'
            return result
    for each2 in range(1, N):
        each_current = current_chord.inversion_highest(each2)
        each_detect = detect(each_current,
                             mode,
                             inv_num,
                             change_from_first,
                             original_first,
                             same_note_special,
                             whole_detect=False,
                             return_fromchord=True,
                             alter_notes_show_degree=alter_notes_show_degree)
        if each_detect is not None:
            detect_msg, change_from_chord, chord_name_str = each_detect
            inv_msg = inversion_way(current_chord, each_current, inv_num)
            result = f'{detect_msg} {inv_msg}'
            if any(x in detect_msg
                   for x in ['sort', '/']) and any(y in inv_msg
                                                   for y in ['sort', '/']):
                inv_msg = inversion_way(current_chord, change_from_chord,
                                        inv_num)
                if inv_msg == 'not good':
                    inv_msg = find_similarity(
                        current_chord,
                        change_from_chord,
                        alter_notes_show_degree=alter_notes_show_degree)
                result = f'{chord_name_str} {inv_msg}'
            return result


def detect_split(current_chord, N=None):
    if N < 6:
        splitind = 1
        lower = current_chord.notes[0].name
        upper = detect(current_chord.notes[splitind:])
        if isinstance(upper, list):
            upper = upper[0]
        return f'[{upper}]/{lower}'
    else:
        splitind = N // 2
        lower = detect(current_chord.notes[:splitind])
        upper = detect(current_chord.notes[splitind:])
        if isinstance(lower, list):
            lower = lower[0]
        if isinstance(upper, list):
            upper = upper[0]
        return f'[{upper}]/[{lower}]'


def interval_check(current_chord):
    TIMES, DIST = divmod(
        (current_chord.notes[1].degree - current_chord.notes[0].degree), 12)
    if DIST == 0 and TIMES != 0:
        DIST = 12
    interval_name = INTERVAL[DIST]
    root_note_name = current_chord[0].name
    if interval_name == 'perfect fifth':
        return f'{root_note_name} with perfect fifth / {root_note_name}5 ({root_note_name} power chord)'
    return f'{root_note_name} with {interval_name}'


def detect(current_chord,
           mode='chord',
           inv_num=False,
           change_from_first=True,
           original_first=True,
           same_note_special=False,
           whole_detect=True,
           return_fromchord=False,
           poly_chord_first=False,
           root_position_return_first=True,
           alter_notes_show_degree=False):
    # mode could be chord/scale
    if mode == 'chord':
        if not isinstance(current_chord, chord):
            current_chord = chord(current_chord)
        N = len(current_chord)
        if N == 1:
            return f'note {current_chord.notes[0]}'
        if N == 2:
            return interval_check(current_chord)
        current_chord = current_chord.standardize()
        N = len(current_chord)
        if N == 1:
            return f'note {current_chord.notes[0]}'
        if N == 2:
            return interval_check(current_chord)
        root = current_chord[0].degree
        rootNote = current_chord[0].name
        distance = tuple(i.degree - root for i in current_chord[1:])
        findTypes = detectTypes[distance]
        if findTypes != 'not found':
            return [
                rootNote + i for i in findTypes
            ] if not root_position_return_first else rootNote + findTypes[0]
        original_detect = find_similarity(
            current_chord,
            result_ratio=True,
            change_from_first=change_from_first,
            same_note_special=same_note_special,
            getgoodchord=return_fromchord,
            get_types=True,
            alter_notes_show_degree=alter_notes_show_degree)
        if original_detect != 'not good':
            if return_fromchord:
                original_ratio, original_msg = original_detect[0]
            else:
                original_ratio, original_msg = original_detect
            types = original_msg[1]
            original_msg = original_msg[0]
            if original_first:
                if original_ratio > 0.86 and types != 'change':
                    return original_msg if not return_fromchord else (
                        original_msg, original_detect[1], original_detect[2])
            if original_ratio == 1:
                return original_msg if not return_fromchord else (
                    original_msg, original_detect[1], original_detect[2])
        for i in range(1, N):
            current = chord(current_chord.inversion(i).names())
            root = current[0].degree
            distance = tuple(i.degree - root for i in current[1:])
            result1 = detectTypes[distance]
            if result1 != 'not found':
                inversion_result = inversion_way(current_chord, current,
                                                 inv_num, result1[0])
                if 'sort' in inversion_result:
                    continue
                else:
                    return inversion_result if not return_fromchord else (
                        inversion_result, current,
                        f'{current[0].name}{result1[0]}')
            else:
                current = current.inoctave()
                root = current[0].degree
                distance = tuple(i.degree - root for i in current[1:])
                result1 = detectTypes[distance]
                if result1 != 'not found':
                    inversion_result = inversion_way(current_chord, current,
                                                     inv_num, result1[0])
                    if 'sort' in inversion_result:
                        continue
                    else:
                        return inversion_result if not return_fromchord else (
                            inversion_result, current,
                            f'{current[0].name}{result1[0]}')
        for i in range(1, N):
            current = chord(current_chord.inversion_highest(i).names())
            root = current[0].degree
            distance = tuple(i.degree - root for i in current[1:])
            result1 = detectTypes[distance]
            if result1 != 'not found':
                inversion_high_result = inversion_way(current_chord, current,
                                                      inv_num, result1[0])
                if 'sort' in inversion_high_result:
                    continue
                else:
                    return inversion_high_result if not return_fromchord else (
                        inversion_high_result, current,
                        f'{current[0].name}{result1[0]}')
            else:
                current = current.inoctave()
                root = current[0].degree
                distance = tuple(i.degree - root for i in current[1:])
                result1 = detectTypes[distance]
                if result1 != 'not found':
                    inversion_high_result = inversion_way(
                        current_chord, current, inv_num, result1[0])
                    if 'sort' in inversion_high_result:
                        continue
                    else:
                        return inversion_high_result if not return_fromchord else (
                            inversion_high_result, current,
                            f'{current[0].name}{result1[0]}')
        if poly_chord_first and N > 3:
            return detect_split(current_chord, N)
        inversion_final = True
        possibles = [
            (find_similarity(current_chord.inversion(j),
                             result_ratio=True,
                             change_from_first=change_from_first,
                             same_note_special=same_note_special,
                             getgoodchord=True,
                             alter_notes_show_degree=alter_notes_show_degree),
             j) for j in range(1, N)
        ]
        possibles = [x for x in possibles if x[0] != 'not good']
        if len(possibles) == 0:
            possibles = [(find_similarity(
                current_chord.inversion_highest(j),
                result_ratio=True,
                change_from_first=change_from_first,
                same_note_special=same_note_special,
                getgoodchord=True,
                alter_notes_show_degree=alter_notes_show_degree), j)
                         for j in range(1, N)]
            possibles = [x for x in possibles if x[0] != 'not good']
            inversion_final = False
        if len(possibles) == 0:
            if original_detect != 'not good':
                return original_msg if not return_fromchord else (
                    original_msg, original_detect[1], original_detect[2])
            if not whole_detect:
                return
            else:
                detect_var = detect_variation(current_chord, mode, inv_num,
                                              change_from_first,
                                              original_first,
                                              same_note_special, N,
                                              alter_notes_show_degree)
                if detect_var is None:
                    result_change = detect(
                        current_chord,
                        mode,
                        inv_num,
                        not change_from_first,
                        original_first,
                        same_note_special,
                        False,
                        return_fromchord,
                        alter_notes_show_degree=alter_notes_show_degree)
                    if result_change is None:
                        return detect_split(current_chord, N)
                    else:
                        return result_change
                else:
                    return detect_var
        possibles.sort(key=lambda x: x[0][0][0], reverse=True)
        best = possibles[0][0]
        highest_ratio, highest_msg = best[0]
        if original_detect != 'not good':
            if original_ratio > 0.6 and (original_ratio >= highest_ratio
                                         or 'sort' in highest_msg):
                return original_msg if not return_fromchord else (
                    original_msg, original_detect[1], original_detect[2])
        if highest_ratio > 0.6:
            if inversion_final:
                current_invert = current_chord.inversion(possibles[0][1])
            else:
                current_invert = current_chord.inversion_highest(
                    possibles[0][1])
            invfrom_current_invert = inversion_way(current_chord,
                                                   current_invert, inv_num)
            highest_msg = best[0][1]
            if any(x in highest_msg
                   for x in ['sort', '/']) and any(y in invfrom_current_invert
                                                   for y in ['sort', '/']):
                retry_msg = find_similarity(
                    current_chord,
                    best[1],
                    fromchord_name=return_fromchord,
                    getgoodchord=return_fromchord,
                    alter_notes_show_degree=alter_notes_show_degree)
                if not return_fromchord:
                    invfrom_current_invert = retry_msg
                else:
                    invfrom_current_invert, fromchord, chordnames = retry_msg
                    current_invert = fromchord
                    highest_msg = chordnames
                final_result = f'{best[2]} {invfrom_current_invert}'
            else:
                final_result = f'{highest_msg} {invfrom_current_invert}'
            return final_result if not return_fromchord else (final_result,
                                                              current_invert,
                                                              highest_msg)

        if not whole_detect:
            return
        else:
            detect_var = detect_variation(current_chord, mode, inv_num,
                                          change_from_first, original_first,
                                          same_note_special, N,
                                          alter_notes_show_degree)
            if detect_var is None:
                result_change = detect(
                    current_chord,
                    mode,
                    inv_num,
                    not change_from_first,
                    original_first,
                    same_note_special,
                    False,
                    return_fromchord,
                    alter_notes_show_degree=alter_notes_show_degree)
                if result_change is None:
                    return detect_split(current_chord, N)
                else:
                    return result_change
            else:
                return detect_var

    elif mode == 'scale':
        if isinstance(current_chord[0], int):
            try:
                scales = detectScale[tuple(current_chord)]
                if scales != 'not found':
                    return scales[0]
                else:
                    return scales
            except:
                raise ValueError('cannot detect this scale')
        else:
            if isinstance(current_chord, (chord, scale)):
                current_chord = current_chord.notes
            try:
                scales = detectScale[tuple(
                    current_chord[i].degree - current_chord[i - 1].degree
                    for i in range(1, len(current_chord)))]
                if scales == 'not found':
                    return scales
                return scales[0]
            except:
                raise ValueError('cannot detect this scale')


def intervalof(current_chord, cummulative=True, translate=False):
    if isinstance(current_chord, scale):
        current_chord = current_chord.getScale()
    if not isinstance(current_chord, chord):
        current_chord = chord(current_chord)
    return current_chord.intervalof(cummulative, translate)


def sums(*chordls):
    if len(chordls) == 1:
        chordls = chordls[0]
        start = chordls[0]
        for i in chordls[1:]:
            start += i
        return start
    else:
        return sums(list(chordls))


def choose_melody(focused, now_focus, focus_ratio, focus_notes, remained_notes,
                  pick, avoid_dim_5, chordinner, newchord, choose_from_chord):
    if focused:
        now_focus = random.choices([1, 0], [focus_ratio, 1 - focus_ratio])[0]
        if now_focus == 1:
            firstmelody = random.choice(focus_notes)
        else:
            firstmelody = random.choice(remained_notes)
    else:
        if choose_from_chord:
            current = random.randint(0, 1)
            if current == 0:
                # pick up melody notes outside chord inner notes
                firstmelody = random.choice(pick)
                # avoid to choose a melody note that appears a diminished fifth interval with the current chord
                if avoid_dim_5:
                    while any(
                        (firstmelody.degree - x.degree) % diminished_fifth == 0
                            for x in newchord.notes):
                        firstmelody = random.choice(pick)
            else:
                # pick up melody notes from chord inner notes
                firstmelody = random.choice(chordinner)
        else:
            firstmelody = random.choice(pick)
            if avoid_dim_5:
                while any(
                    (firstmelody.degree - x.degree) % diminished_fifth == 0
                        for x in newchord.notes):
                    firstmelody = random.choice(pick)
    return firstmelody


def random_composing(mode,
                     length,
                     difficulty='easy',
                     init_notes=None,
                     pattern=None,
                     focus_notes=None,
                     focus_ratio=0.7,
                     avoid_dim_5=True,
                     num=3,
                     left_hand_velocity=70,
                     right_hand_velocity=80,
                     left_hand_meter=4,
                     right_hand_meter=4,
                     choose_intervals=[1 / 8, 1 / 4, 1 / 2],
                     choose_durations=[1 / 8, 1 / 4, 1 / 2],
                     melody_interval_tol=perfect_fourth,
                     choose_from_chord=False):
    # Composing a piece of music randomly from a given mode (here means scale),
    # difficulty, number of start notes (or given notes) and an approximate length.
    # length is the total approximate total number of notes you want the music to be.
    if pattern is not None:
        pattern = [int(x) for x in pattern]
    standard = mode.notes[:-1]
    # pick is the sets of notes from the required scales which used to pick up notes for melody
    pick = [x.up(2 * octave) for x in standard]
    focused = False
    if focus_notes != None:
        focused = True
        focus_notes = [pick[i - 1] for i in focus_notes]
        remained_notes = [j for j in pick if j not in focus_notes]
        now_focus = 0
    else:
        focus_notes = None
        remained_notes = None
        now_focus = 0
    # the chord part and melody part will be written separately,
    # but still with some relevations. (for example, avoiding dissonant intervals)
    # the draft of the piece of music would be generated first,
    # and then modify the details of the music (durations, intervals,
    # notes volume, rests and so on)
    basechord = mode.get_allchord(num=num)
    # count is the counter for the total number of notes in the piece
    count = 0
    patterncount = 0
    result = chord([])
    while count <= length:
        if pattern is None:
            newchordnotes = random.choice(basechord)
        else:
            newchordnotes = basechord[pattern[patterncount] - 1]
            patterncount += 1
            if patterncount == len(pattern):
                patterncount = 0
        newduration = random.choice(choose_durations)
        newinterval = random.choice(choose_intervals)
        newchord = newchordnotes.set(newduration, newinterval)
        '''
        # check if current chord belongs to a kind of (closer to) major/minor
        check_chord_types = newchord[1].degree - newchord[0].degree
        if check_chord_types == 2:
            chord_types = 'sus2'        
        elif check_chord_types == 3:
            chord_types = 'minor'
        elif check_chord_types == 4:
            chord_types = 'major'
        elif check_chord_types == 5:
            chord_types = 'sus4'
        '''
        newchord_len = len(newchord)
        if newchord_len < left_hand_meter:
            choose_more = [x for x in mode if x not in newchord]
            for g in range(left_hand_meter - newchord_len):
                current_choose = random.choice(choose_more)
                if current_choose.degree < newchord[-1].degree:
                    current_choose = current_choose.up(octave)
                newchord += current_choose
        do_inversion = random.randint(0, 1)
        if do_inversion == 1:
            newchord = newchord.inversion_highest(
                random.randint(2, left_hand_meter - 1))
        for each in newchord.notes:
            each.volume = left_hand_velocity
        chord_notenames = newchord.names()
        chordinner = [x for x in pick if x.name in chord_notenames]
        while True:
            firstmelody = choose_melody(focused, now_focus, focus_ratio,
                                        focus_notes, remained_notes, pick,
                                        avoid_dim_5, chordinner, newchord,
                                        choose_from_chord)
            firstmelody.volume = right_hand_velocity
            newmelody = [firstmelody]
            length_of_chord = sum(newchord.interval)
            intervals = [random.choice(choose_intervals)]
            firstmelody.duration = random.choice(choose_durations)
            while sum(intervals) <= length_of_chord:
                currentmelody = choose_melody(focused, now_focus, focus_ratio,
                                              focus_notes, remained_notes,
                                              pick, avoid_dim_5, chordinner,
                                              newchord, choose_from_chord)
                while abs(currentmelody.degree -
                          newmelody[-1].degree) > melody_interval_tol:
                    currentmelody = choose_melody(focused, now_focus,
                                                  focus_ratio, focus_notes,
                                                  remained_notes, pick,
                                                  avoid_dim_5, chordinner,
                                                  newchord, choose_from_chord)
                currentmelody.volume = right_hand_velocity
                newinter = random.choice(choose_intervals)
                intervals.append(newinter)
                currentmelody.duration = random.choice(choose_durations)
                newmelody.append(currentmelody)

            distance = [
                abs(x.degree - y.degree) for x in newmelody for y in newmelody
            ]
            if diminished_fifth in distance:
                continue
            else:
                break
        newmelodyall = chord(newmelody, interval=intervals)
        while sum(newmelodyall.interval) > length_of_chord:
            newmelodyall.notes.pop()
            newmelodyall.interval.pop()
        newcombination = newchord.add(newmelodyall, mode='head')
        result = result.add(newcombination)
        count += len(newcombination)
    return result


def fugue(mode,
          length,
          interval_bass=0.5,
          interval_melody=0.5,
          duration_bass=0.5,
          duration_melody=0.5):
    bassls = mode.notes[:-1]
    melodyls = [x.up(octave) for x in bassls]
    bassnotes = [random.choice(bassls) for j in range(length)]
    melodynotes = [random.choice(melodyls) for k in range(length)]
    bass = chord(bassnotes, duration_bass, interval_bass)
    melody = chord(melodynotes, duration_melody, interval_melody)
    return bass.add(melody, mode='head')


def perm(n, k=None):
    # return all of the permutations of the elements in x
    if isinstance(n, int):
        n = list(range(1, n + 1))
    if isinstance(n, str):
        n = list(n)
    if k is None:
        k = len(n)
    return eval(
        f'''[{f"[{', '.join([f'n[a{i}]' for i in range(k)])}]"} {''.join([f'for a{i} in range(len(n)) ' if i == 0 else f"for a{i} in range(len(n)) if a{i} not in [{', '.join([f'a{t}' for t in range(i)])}] " for i in range(k)])}]''',
        locals())


def negative_harmony(key, current_chord=None, sort=False, get_map=False):
    notes_dict = [
        'C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F'
    ] * 2
    key_tonic = key[0].name
    if key_tonic in standard_dict:
        key_tonic = standard_dict[key_tonic]
    inds = notes_dict.index(key_tonic) + 1
    right_half = notes_dict[inds:inds + 6]
    left_half = notes_dict[inds + 6:inds + 12]
    left_half.reverse()
    map_dict = {
        **{left_half[i]: right_half[i]
           for i in range(6)},
        **{right_half[i]: left_half[i]
           for i in range(6)}
    }
    if get_map:
        return map_dict
    if current_chord:
        if isinstance(current_chord, chord):
            temp = copy(current_chord)
            notes = temp.notes
            for each in range(len(notes)):
                current = notes[each]
                if isinstance(current, note):
                    if current.name in standard_dict:
                        current.name = standard_dict[current.name]
                    notes[each] = note(map_dict[current.name],
                                       current.num,
                                       volume=current.volume,
                                       duration=current.duration)
            if sort:
                temp.notes.sort(key=lambda s: s.degree)
            return temp
        else:
            raise ValueError('requires a chord object')
    else:
        temp = copy(key)
        if temp.notes[-1].degree - temp.notes[0].degree == octave:
            temp.notes = temp.notes[:-1]
        notes = temp.notes
        for each in range(len(notes)):
            current = notes[each]
            notes[each] = note(map_dict[current.name], current.num)
        temp.notes.sort(key=lambda s: s.degree)
        temp.notes.append(temp.notes[0].up(octave))
        temp.mode = None
        temp.interval = None
        temp.interval = temp.getInterval()
        temp.mode = detect(temp, mode='scale')
        return temp


def guitar_chord(frets,
                 return_chord=False,
                 tuning=['E2', 'A2', 'D3', 'G3', 'B3', 'E4'],
                 duration=0.25,
                 interval=0,
                 **detect_args):
    # the default tuning is the standard tuning E-A-D-G-B-E,
    # you can set the tuning to whatever you want
    # the parameter frets is a list contains the frets of each string of
    # the guitar you want to press in this chord, sorting from 6th string
    # to 1st string (which is from E2 string to E4 string in standard tuning),
    # the fret of a string is an integer, if it is 0, then it means you
    # play that string open (not press any fret on that string),
    # if it is 3 for example, then it means you press the third fret on that
    # string, if it is None, then that means you did not play that string
    # (mute or just not touch that string)
    # this function will return the chord types that form by the frets pressing
    # at the strings on a guitar, or you can choose to just return the chord
    tuning = [N(i) for i in tuning]
    guitar_notes = [
        tuning[j].up(frets[j]) for j in range(6) if frets[j] is not None
    ]
    result = chord(guitar_notes, duration, interval)
    if return_chord:
        return result
    return detect(result.sortchord(), **detect_args)


def build(*tracks_list, **kwargs):
    if len(tracks_list) == 1 and isinstance(tracks_list[0], list):
        current_tracks_list = tracks_list[0]
        if current_tracks_list and isinstance(current_tracks_list[0],
                                              (list, track)):
            return build(*tracks_list[0], **kwargs)
    tracks = []
    instruments_list = []
    start_times = []
    channels = []
    track_names = []
    pan_msg = []
    volume_msg = []
    sampler_channels = []
    remain_list = [1, 0, None, None, [], [], None]
    for each in tracks_list:
        if isinstance(each, track):
            tracks.append(each.content)
            instruments_list.append(each.instrument)
            start_times.append(each.start_time)
            channels.append(each.channel)
            track_names.append(each.track_name)
            pan_msg.append(each.pan if each.pan else [])
            volume_msg.append(each.volume if each.volume else [])
            sampler_channels.append(each.sampler_channel)
        else:
            new_each = each + remain_list[len(each) - 1:]
            tracks.append(new_each[0])
            instruments_list.append(new_each[1])
            start_times.append(new_each[2])
            channels.append(new_each[3])
            track_names.append(new_each[4])
            pan_msg.append(new_each[5])
            volume_msg.append(new_each[6])
            sampler_channels.append(new_each[7])
    if any(i is None for i in channels):
        channels = None
    if all(i is None for i in track_names):
        track_names = None
    else:
        track_names = [i if i else '' for i in track_names]
    if any(i is None for i in sampler_channels):
        sampler_channels = None
    result = P(tracks=tracks,
               instruments_list=instruments_list,
               start_times=start_times,
               track_names=track_names,
               channels=channels,
               pan=pan_msg,
               volume=volume_msg,
               sampler_channels=sampler_channels)
    for key, value in kwargs.items():
        setattr(result, key, value)
    return result


def translate(pattern):
    start_time = 0
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
        return translate(','.join(units[1:])).special_set(*whole_set_values)
    elif units[-1].startswith('!'):
        whole_set = True
        whole_set_values = units[-1][1:].split(';')
        whole_set_values = [k.replace('|', ',') for k in whole_set_values]
        whole_set_values = process_settings(whole_set_values)
        return translate(','.join(units[:-1])).special_set(*whole_set_values)
    for i in units:
        if i == '':
            continue
        if i[0] == '{' and i[-1] == '}':
            part_replace_ind2 = len(notes)
            current_part = parts[part_counter]
            current_part_notes = translate(current_part)
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
            notes[
                part_replace_ind1:part_replace_ind2] = current_part_notes.notes
            pattern_intervals[part_replace_ind1:
                              part_replace_ind2] = current_part_notes.interval
            pattern_durations[
                part_replace_ind1:
                part_replace_ind2] = current_part_notes.get_duration()
            pattern_volumes[part_replace_ind1:
                            part_replace_ind2] = current_part_notes.get_volume(
                            )
            part_replace_ind1 = len(notes)
        elif i[0] == '[' and i[-1] == ']':
            current_content = i[1:-1]
            current_interval = process_settings([current_content])[0]
            if pattern_intervals:
                pattern_intervals[-1] += current_interval
            else:
                start_time += current_interval
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
                repeat_part = translate(repeat_part)
            current_notes = repeat_part % repeat_times
            notes.extend(current_notes.notes)
            pattern_intervals.extend(current_notes.interval)
            pattern_durations.extend(current_notes.get_duration())
            pattern_volumes.extend(current_notes.get_volume())
        elif '[' in i and ']' in i:
            current_drum_settings = (i[i.index('[') + 1:i.index(']')].replace(
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
                config_part = translate(config_part)
            current_notes = config_part.special_set(*current_drum_settings)
            notes.extend(current_notes.notes)
            pattern_intervals.extend(current_notes.interval)
            pattern_durations.extend(current_notes.get_duration())
            pattern_volumes.extend(current_notes.get_volume())
        elif ';' in i:
            same_time_notes = i.split(';')
            current_notes = [translate(k) for k in same_time_notes]
            current_notes = concat(
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
            notes.append(N(i))
            pattern_intervals.append(0)
            pattern_durations.append(1 / 8)
            pattern_volumes.append(100)

    intervals = pattern_intervals
    durations = pattern_durations
    volumes = pattern_volumes
    result = chord(notes) % (durations, intervals, volumes)
    result.start_time = start_time
    return result


def chord_progression(chords,
                      durations=1 / 4,
                      intervals=0,
                      volumes=None,
                      chords_interval=None,
                      merge=True,
                      scale=None):
    if scale:
        return scale.chord_progression(chords, durations, intervals, volumes,
                                       chords_interval, merge)
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
        for i in range(1, chords_len):
            if chords_interval:
                result |= chords_interval[i - 1]
            result |= chords[i]
        return result
    else:
        return chords


def find_chords_for_melody(melody,
                           mode=None,
                           num=3,
                           chord_num=8,
                           get_pattern=False,
                           chord_length=None,
                           down_octave=1):
    if isinstance(melody, (str, list)):
        melody = chord(melody)
    possible_scales = detect_in_scale(melody, num, get_scales=True)
    if not possible_scales:
        raise ValueError('cannot find a scale suitable for this melody')
    current_scale = possible_scales[0]
    if current_scale.mode != 'major' and current_scale.mode in modern_modes:
        current_scale = current_scale.inversion(
            8 - modern_modes.index(current_scale.mode))
    chordtypes = list(chordTypes.dic.keys())
    result = []
    if get_pattern:
        choose_patterns = [
            '6451', '1645', '6415', '1564', '4565', '4563', '6545', '6543',
            '4536', '6251'
        ]
        roots = [
            current_scale[i]
            for i in [int(k) for k in random.choice(choose_patterns)]
        ]
        length = len(roots)
        counter = 0
    for i in range(chord_num):
        if not get_pattern:
            current_root = random.choice(current_scale.notes[:6])
        else:
            current_root = roots[counter]
            counter += 1
            if counter >= length:
                counter = 0
        current_chord_type = random.choice(chordtypes)[0]
        current_chord = chd(current_root, current_chord_type)
        while current_chord not in current_scale or current_chord_type == '5' or current_chord in result or (
                chord_length is not None
                and len(current_chord) < chord_length):
            current_chord_type = random.choice(chordtypes)[0]
            current_chord = chd(current_root, current_chord_type)
        result.append(current_chord)
    if chord_length is not None:
        result = [each[:chord_length + 1] for each in result]
    result = [each - octave * down_octave for each in result]
    return result


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
        raise IOError(f"Already a Standard MIDI format file: {riff_name}")
    elif chunk_id != b'RIFF':
        raise IOError(f"Not an RIFF file: {riff_name}")

    chunk_size = root.getsize()
    chunk_raw = root.read(chunk_size)
    (hdr_id, hdr_data, midi_size) = struct.unpack("<4s4sL", chunk_raw[0:12])

    if hdr_id != b'RMID' or hdr_data != b'data':
        raise IOError(f"Invalid or unsupported input file: {riff_name}")
    try:
        midi_raw = chunk_raw[12:12 + midi_size]
    except IndexError:
        raise IOError(f"Broken input file: {riff_name}")

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


C = trans
N = toNote
S = toScale
P = piece
arp = arpeggio
