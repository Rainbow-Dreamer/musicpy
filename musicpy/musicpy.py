import os
import math
import struct
import chunk
from io import BytesIO
import mido

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
    name = database.standard_reverse[degree % 12]
    num = (degree // 12) - 1
    return note(name, num, duration, volume, channel)


def degrees_to_chord(ls, *args, **kwargs):
    return chord([degree_to_note(i) for i in ls], *args, **kwargs)


def note_to_degree(obj):
    if not isinstance(obj, note):
        obj = toNote(obj)
    return database.standard[obj.name] + 12 * (obj.num + 1)


def trans_note(notename, duration=0.25, volume=100, pitch=4, channel=None):
    num = ''.join([x for x in notename if x.isdigit()])
    if not num:
        num = pitch
    else:
        num = int(num)
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
    interval_premode = database.chordTypes(premode, mode=1, index=ind)
    if interval_premode != 'not found':
        interval = interval_premode
    else:
        interval_mode = database.chordTypes(mode, mode=1, index=ind)
        if interval_mode != 'not found':
            interval = interval_mode
        else:
            raise ValueError('could not detect the chord types')
    for i in range(len(interval)):
        chordlist.append(degree_to_note(initial + interval[i]))
    return chord(chordlist, duration, intervals, start_time=start_time)


chd = getchord


def concat(chordlist, mode='+', extra=None, start=None):
    if not chordlist:
        return chordlist
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
        name = name.name
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
                midi_to_chord(each,
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
            midi_to_chord(available_tracks[j],
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
            midi_to_chord(each,
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
        if (not tracks_names_list) or (len(tracks_names_list) !=
                                       len(channels_list)):
            tracks_names_list = [f'Channel {i+1}' for i in channels_list]
            rename_track_names = True
        result_merge_track = all_tracks[0]
        result_piece = piece(
            tracks=[chord([]) for i in range(len(channels_list))],
            instruments=[database.reverse_instruments[i] for i in instruments],
            bpm=whole_bpm,
            track_names=tracks_names_list,
            channels=channels_list,
            name=os.path.splitext(os.path.basename(name))[0],
            pan=[[] for i in range(len(channels_list))],
            volume=[[] for i in range(len(channels_list))])
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
    if current_type == 1 and changes:
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
    return result_piece


def midi_to_chord(current_track,
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
        return [result, bpm, start_time]
    else:
        return [result, start_time]


def read_other_messages(message, other_messages, time, track_ind):
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
        current_start_time = int(start_times[i] * ticks_per_beat * 4)
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
            add_other_messages(
                current_midi=current_midi,
                other_messages=current_chord.other_messages,
                write_type='piece' if not is_track_type else 'track',
                ticks_per_beat=ticks_per_beat)
        elif msg:
            add_other_messages(
                current_midi=current_midi,
                other_messages=msg,
                write_type='piece' if not is_track_type else 'track',
                ticks_per_beat=ticks_per_beat)
    for i, each in enumerate(current_midi.tracks):
        each.sort(key=lambda s: s.time)
        current_midi.tracks[i] = mido.MidiTrack(
            mido.midifiles.tracks._to_reltime(each))
    if save_as_file:
        current_midi.save(name)
    else:
        current_io = BytesIO()
        current_midi.save(file=current_io)
        return current_io


def add_other_messages(current_midi,
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


def modulation(current_chord, old_scale, new_scale, **args):
    '''
    change notes (including both of melody and chords) in the given piece
    of music from a given scale to another given scale, and return
    the new changing piece of music.
    '''
    return current_chord.modulation(old_scale, new_scale, **args)


def trans(obj, pitch=4, duration=0.25, interval=None):
    obj = obj.replace(' ', '')
    if ':' in obj:
        current = obj.split(':')
        current[0] = toNote(current[0])
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
            if first in database.standard and types in database.chordTypes:
                return chd(first,
                           types,
                           pitch=pitch,
                           duration=duration,
                           intervals=interval)
        elif N > 2:
            first_two = obj[:2]
            type1 = obj[2:]
            if first_two in database.standard and type1 in database.chordTypes:
                return chd(first_two,
                           type1,
                           pitch=pitch,
                           duration=duration,
                           intervals=interval)
            first_one = obj[0]
            type2 = obj[1:]
            if first_one in database.standard and type2 in database.chordTypes:
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
    instruments = []
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
            instruments.append(each.instrument)
            start_times.append(each.start_time)
            channels.append(each.channel)
            track_names.append(each.track_name)
            pan_msg.append(each.pan if each.pan else [])
            volume_msg.append(each.volume if each.volume else [])
            sampler_channels.append(each.sampler_channel)
        else:
            new_each = each + remain_list[len(each) - 1:]
            tracks.append(new_each[0])
            instruments.append(new_each[1])
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
               instruments=instruments,
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
            return f'unrecognizable accidentals {accidental_a}'
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
                current = [eval(k) for k in each.split(';')[1:]]
                current_tempo = tempo(*current)
                notes_result.append(current_tempo)
                intervals.append(0)
            elif each.startswith('pitch'):
                current = each.split(';')[1:]
                length = len(current)
                if length > 2:
                    current = [eval(k) for k in current[:2]] + [current[2]] + [
                        eval(k) for k in current[3:]
                    ]
                else:
                    current = [eval(k) for k in current]
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
                        duration = process_note(info[0])
                        if notename != 'r':
                            intervals.append(0)
                    else:
                        if info_len == 2:
                            duration, interval = info
                        else:
                            duration, interval, volume = info
                            volume = eval(volume)
                        duration = process_note(duration)
                        interval = process_note(
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


def process_note(value, mode=0, value2=None):
    if mode == 1 and value == '.':
        return value2
    if ';' in value:
        result = [process_note(i) for i in value.split(';')]
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
            value = eval(value) * sum([(1 / 2)**i
                                       for i in range(dotted_notes + 1)])
        elif length > 1:
            num_ind = 0
            for k, each in enumerate(value):
                if each != '.':
                    num_ind = k
                    break
            if value[-1] != '.':
                value = 1 / eval(value[num_ind:])
            else:
                dotted_notes_start_ind = length - 1
                for k in range(dotted_notes_start_ind, -1, -1):
                    if value[k] != '.':
                        dotted_notes_start_ind = k + 1
                        break
                dotted_notes = length - dotted_notes_start_ind
                value = (1 / eval(value[num_ind:dotted_notes_start_ind])
                         ) * sum([(1 / 2)**i for i in range(dotted_notes + 1)])
        if mode == 2:
            if isinstance(value, float) and value.is_integer():
                value = int(value)
        return value


def process_settings(settings):
    settings += ['n' for i in range(3 - len(settings))]
    duration, interval, volume = settings
    duration = process_note(duration)
    interval = process_note(interval, mode=1, value2=duration)
    volume = process_note(volume, mode=2)
    return [duration, interval, volume]


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


def closest_note(note1, note2, get_distance=False):
    if not isinstance(note1, note):
        note1 = toNote(note1)
    if isinstance(note2, note):
        note2 = note2.name
    current_note = [
        note(note2, note1.num),
        note(note2, note1.num - 1),
        note(note2, note1.num + 1)
    ]
    if not get_distance:
        result = min(current_note, key=lambda s: abs(s.degree - note1.degree))
        return result
    else:
        distances = [[i, abs(i.degree - note1.degree)] for i in current_note]
        distances.sort(key=lambda s: s[1])
        result = distances[0]
        return result


def closest_note_from_chord(note1, chord1):
    if not isinstance(note1, note):
        note1 = toNote(note1)
    names = [database.standard_dict.get(i, i) for i in chord1.names()]
    current_name = database.standard_dict.get(note1.name, note1.name)
    if current_name in names:
        result = note1
    else:
        distances = [
            closest_note(note1, i, get_distance=True) for i in chord1.notes
        ]
        distances.sort(key=lambda s: s[1])
        result = distances[0][0]
    return result


def note_range(note1, note2):
    current_range = list(range(note1.degree, note2.degree))
    result = [degree_to_note(i) for i in current_range]
    return result


def adjust_to_scale(current_chord, current_scale):
    temp = copy(current_chord)
    current_notes = current_scale.getScale()
    for i, each in enumerate(temp):
        current_note = closest_note_from_chord(each, current_notes)
        each.name = current_note.name
        each.num = current_note.num
    return temp


C = trans
N = toNote
S = toScale
P = piece
arp = arpeggio

for each in [
        note, chord, piece, track, scale, drum, rest, tempo, pitch_bend, pan,
        volume, event
]:
    each.reset = reset
    each.__hash__ = lambda self: hash(repr(self))
    each.copy = lambda self: copy(self)

event.__repr__ = lambda self: f'{self.__class__.__name__}({", ".join(["=".join([i, str(j)]) for i, j in self.__dict__.items()])})'

if __name__ == '__main__' or __name__ == 'musicpy':
    import algorithms as alg
else:
    from . import algorithms as alg
