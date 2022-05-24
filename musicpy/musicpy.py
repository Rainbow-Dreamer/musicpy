import os
import math
import struct
import chunk
from io import BytesIO
import midiutil
import mido
from ast import literal_eval

if __name__ == '__main__' or __name__ == 'musicpy':
    from database import *
    from structures import *
else:
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


def degrees_to_chord(ls, *args, **kwargs):
    return chord([degree_to_note(i) for i in ls], *args, **kwargs)


def note_to_degree(obj):
    if not isinstance(obj, note):
        obj = toNote(obj)
    return standard[obj.name] + 12 * (obj.num + 1)


def trans_note(notename, duration=0.25, volume=100, pitch=4, channel=None):
    num = ''.join([x for x in notename if x.isdigit()])
    if not num:
        num = pitch
    else:
        num = eval(num)
    name = ''.join([x for x in notename if not x.isdigit()])
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


def modulation(current_chord, old_scale, new_scale):
    '''
    change notes (including both of melody and chords) in the given piece
    of music from a given scale to another given scale, and return
    the new changing piece of music.
    '''
    return current_chord.modulation(old_scale, new_scale)


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


def translate(pattern,
              default_duration=1 / 8,
              default_interval=0,
              default_volume=100):
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
        return translate(
            ','.join(units[1:]),
            default_duration=default_duration,
            default_interval=default_interval,
            default_volume=default_volume).special_set(*whole_set_values)
    elif units[-1].startswith('!'):
        whole_set = True
        whole_set_values = units[-1][1:].split(';')
        whole_set_values = [k.replace('|', ',') for k in whole_set_values]
        whole_set_values = process_settings(whole_set_values)
        return translate(
            ','.join(units[:-1]),
            default_duration=default_duration,
            default_interval=default_interval,
            default_volume=default_volume).special_set(*whole_set_values)
    for i in units:
        if i == '':
            continue
        if i[0] == '{' and i[-1] == '}':
            part_replace_ind2 = len(notes)
            current_part = parts[part_counter]
            part_counter += 1
            part_settings = i[1:-1].split('|')
            find_default = False
            for each in part_settings:
                if each.startswith('de:'):
                    find_default = True
                    current_default_settings = each[3:].split(';')
                    current_default_settings = process_settings(
                        current_default_settings)
                    if current_default_settings[0] is None:
                        current_default_settings[0] = 1 / 8
                    if current_default_settings[1] is None:
                        current_default_settings[1] = 0
                    if current_default_settings[2] is None:
                        current_default_settings[2] = 100
                    current_part_notes = translate(
                        current_part,
                        default_duration=current_default_settings[0],
                        default_interval=current_default_settings[1],
                        default_volume=current_default_settings[2])
                    break
            if not find_default:
                current_part_notes = translate(
                    current_part,
                    default_duration=default_duration,
                    default_interval=default_interval,
                    default_volume=default_volume)
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
                repeat_part = translate(repeat_part,
                                        default_duration=default_duration,
                                        default_interval=default_interval,
                                        default_volume=default_volume)
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
                config_part = translate(config_part,
                                        default_duration=default_duration,
                                        default_interval=default_interval,
                                        default_volume=default_volume)
            current_notes = config_part.special_set(*current_drum_settings)
            notes.extend(current_notes.notes)
            pattern_intervals.extend(current_notes.interval)
            pattern_durations.extend(current_notes.get_duration())
            pattern_volumes.extend(current_notes.get_volume())
        elif ';' in i:
            same_time_notes = i.split(';')
            current_notes = [
                translate(k,
                          default_duration=default_duration,
                          default_interval=default_interval,
                          default_volume=default_volume)
                for k in same_time_notes
            ]
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
            pattern_intervals.append(default_interval)
            pattern_durations.append(default_duration)
            pattern_volumes.append(default_volume)

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


def dotted(duration, num=1):
    return duration * sum([(1 / 2)**i for i in range(num + 1)])


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


def reset(self, **kwargs):
    temp = copy(self)
    for i, j in kwargs.items():
        setattr(temp, i, j)
    return temp


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


def read_notes(note_ls, rootpitch=4):
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
                start_time += each.duration
            elif intervals:
                intervals[-1] += each.duration
        elif isinstance(each, str):
            if each.startswith('tempo'):
                current = [literal_eval(k) for k in each.split(';')[1:]]
                current_tempo = tempo(*current)
                notes_result.append(current_tempo)
                intervals.append(0)
            elif each.startswith('pitch'):
                current = each.split(';')[1:]
                length = len(current)
                if length > 2:
                    current = [literal_eval(k) for k in current[:2]] + [
                        current[2]
                    ] + [literal_eval(k) for k in current[3:]]
                else:
                    current = [literal_eval(k) for k in current]
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
                        duration = info[0]
                        if duration[0] == '.':
                            if '.' in duration[1:]:
                                dotted_notes = duration[1:].count('.')
                                duration = duration.replace('.', '')
                                duration = (1 / eval(duration)) * sum(
                                    [(1 / 2)**i for i in range(dotted_notes)])
                            else:
                                duration = 1 / eval(duration[1:])
                        else:
                            if duration[-1] == '.':
                                dotted_notes = duration.count('.')
                                duration = duration.replace('.', '')
                                duration = eval(duration) * sum(
                                    [(1 / 2)**i for i in range(dotted_notes)])
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
                                duration = (1 / eval(duration)) * sum(
                                    [(1 / 2)**i for i in range(dotted_notes)])
                            else:
                                duration = 1 / eval(duration[1:])
                        else:
                            if duration[-1] == '.':
                                dotted_notes = duration.count('.')
                                duration = duration.replace('.', '')
                                duration = eval(duration) * sum(
                                    [(1 / 2)**i for i in range(dotted_notes)])
                            else:
                                duration = eval(duration)
                        if interval[0] == '.':
                            if len(interval) > 1 and interval[1].isdigit():
                                if '.' in interval[1:]:
                                    dotted_notes = interval[1:].count('.')
                                    interval = interval.replace('.', '')
                                    interval = (1 / eval(interval)) * sum([
                                        (1 / 2)**i for i in range(dotted_notes)
                                    ])
                                else:
                                    interval = 1 / eval(interval[1:])
                            else:
                                interval = eval(
                                    interval.replace('.', str(duration)))
                        else:
                            if interval[-1] == '.':
                                dotted_notes = interval.count('.')
                                interval = interval.replace('.', '')
                                interval = eval(interval) * sum(
                                    [(1 / 2)**i for i in range(dotted_notes)])
                            else:
                                interval = eval(interval)
                        if notename != 'r':
                            intervals.append(interval)
                    if notename == 'r':
                        if not notes_result:
                            start_time += duration
                        elif intervals:
                            intervals[-1] += duration
                    else:
                        notes_result.append(
                            toNote(notename, duration, volume, rootpitch))
                else:
                    if each == 'r':
                        if not notes_result:
                            start_time += 1 / 4
                        elif intervals:
                            intervals[-1] += 1 / 4
                    else:
                        intervals.append(0)
                        notes_result.append(toNote(each, pitch=rootpitch))
        else:
            notes_result.append(each)
    if len(intervals) != len(notes_result):
        intervals = []
    return notes_result, intervals, start_time


def process_dotted_note(value):
    length = len(value)
    if value[0] != '.':
        num_ind = length - 1
        for k in range(num_ind, -1, -1):
            if value[k] != '.':
                num_ind = k
                break
        dotted_notes = value[num_ind + 1:].count('.')
        value = value[:num_ind + 1]
        value = eval(value) * sum([(1 / 2)**i
                                   for i in range(dotted_notes + 1)])
    elif length > 1:
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


def process_normalize_tempo(obj, tempo_changes_ranges, bpm, mode=0):
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


def piece_process_normalize_tempo(self, bpm, first_track_start_time):
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
    whole_pan = concat(self.pan) if self.pan else None
    whole_volume = concat(self.volume) if self.volume else None
    normalize_result, first_track_start_time = first_track.normalize_tempo(
        bpm,
        start_time=first_track_start_time + first_track.start_time,
        pan_msg=whole_pan,
        volume_msg=whole_volume)
    new_other_messages = normalize_result[0]
    self.other_messages = new_other_messages
    if whole_pan or whole_volume:
        whole_pan, whole_volume = normalize_result[1], normalize_result[2]
        self.pan = [[i for i in whole_pan if i.track == j]
                    for j in range(len(self.tracks))]
        self.volume = [[i for i in whole_volume if i.track == j]
                       for j in range(len(self.tracks))]
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


C = trans
N = toNote
S = toScale
P = piece
arp = arpeggio

for each in [
        note, chord, piece, track, scale, drum, rest, tempo, pitch_bend, pan,
        volume
]:
    each.reset = reset

for each in [
        controller_event, copyright_event, key_signature, sysex, text_event,
        time_signature, universal_sysex, rpn, tuning_bank, tuning_program,
        channel_pressure, program_change, track_name
]:
    each.__repr__ = lambda self: f'{self.__class__.__name__}({", ".join(["=".join([i, str(j)]) for i, j in self.__dict__.items()])})'

if __name__ == '__main__' or __name__ == 'musicpy':
    import algorithms as alg
else:
    from . import algorithms as alg
