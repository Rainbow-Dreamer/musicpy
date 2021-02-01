import os
import sys
import math
import random
from difflib import SequenceMatcher
from midiutil import MIDIFile
import mido
from mido.midifiles.midifiles import MidiFile as midi
from mido import Message
import mido.midifiles.units as unit
from mido.midifiles.tracks import merge_tracks as merge
from mido.midifiles.tracks import MidiTrack
from mido.midifiles.meta import MetaMessage
from .database import *
from .structures import *
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
pygame.mixer.init(44100, -16, 1, 1024)
'''
mido and midiutil is requried for this module, please make sure you have
these two modules with this file
'''


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


def degree_to_note(degree, duration=0.25, volume=100):
    name = standard_reverse[degree % 12]
    num = (degree // 12) - 1
    return note(name, num, duration, volume)


def totuple(x):
    if isinstance(x, str):
        return (x, )
    try:
        return tuple(x)
    except:
        return (x, )


def getf(y):
    if type(y) != note:
        y = toNote(y)
    return 440 * math.exp((y.degree - 57) * math.log(2) / 12)


def secondary_dom(root, mode='major'):
    if type(root) == str:
        root = toNote(root)
    newscale = scale(root, mode)
    return newscale.dom_chord()


def secondary_dom7(root, mode='major'):
    if type(root) == str:
        root = toNote(root)
    newscale = scale(root, mode)
    return newscale.dom7_chord()


def get_related_chord(scale1):
    # get secondary dominant chords
    pass


def getchord_by_interval(start,
                         interval1,
                         duration=0.25,
                         interval=0,
                         cummulative=True):

    if not isinstance(start, note):
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
    return chord(result, duration, interval)


def inversion(chord1, num=1):
    return chord1.inversion(num)


def getchord(start,
             mode=None,
             duration=0.25,
             intervals=None,
             addition=None,
             interval=None,
             cummulative=True,
             pitch=4,
             b=None,
             sharp=None,
             ind=0):
    if not isinstance(start, note):
        start = toNote(start, pitch=pitch)
    if interval is not None:
        return getchord_by_interval(start, interval, duration, intervals,
                                    cummulative)
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
            if mode[:3] == 'add':
                try:
                    addnum = int(mode[3:])
                    interval = [
                        major_third, perfect_fifth,
                        scale(start,
                              'major').notes[:-1][(addnum % 7) - 1].degree -
                        start.degree + octave * (addnum // 7)
                    ]
                except:
                    return 'add(n) chord: n should be an integer'
            elif mode[:4] == 'madd':
                try:
                    addnum = int(mode[4:])
                    interval = [
                        minor_third, perfect_fifth,
                        scale(start,
                              'minor').notes[:-1][(addnum % 7) - 1].degree -
                        start.degree + octave * (addnum // 7)
                    ]
                except:
                    return 'add(n) chord: n should be an integer'
            else:
                return 'could not detect the chord types'
    for i in range(len(interval)):
        chordlist.append(degree_to_note(initial + interval[i]))
    if addition is not None:
        chordlist.append(degree_to_note(initial + addition))
    if b != None:
        for each in b:
            chordlist[each - 1] = chordlist[each - 1].down()
    if sharp != None:
        for every in sharp:
            chordlist[every - 1] = chordlist[every - 1].up()
    return chord(chordlist, duration, intervals)


chd = getchord


def concat(chordlist, mode='+', extra=None):
    temp = copy(chordlist[0])
    if mode == '+':
        for t in chordlist[1:]:
            temp += t
    elif mode == '|':
        for t in chordlist[1:]:
            temp |= t
    elif mode == '&':
        if not extra:
            for t in chordlist[1:]:
                temp &= t
        else:
            extra_unit = extra
            for t in chordlist[1:]:
                temp &= (t, extra)
                extra += extra_unit
    return temp


def play(chord1,
         bpm=80,
         track=0,
         channel=0,
         time1=0,
         track_num=1,
         name='temp.mid',
         modes='quick',
         instrument=None,
         i=None,
         save_as_file=True,
         deinterleave=True):
    file = write(name_of_midi=name,
                 chord1=chord1,
                 bpm=bpm,
                 track=track,
                 channel=channel,
                 time1=time1,
                 track_num=track_num,
                 mode=modes,
                 instrument=instrument,
                 i=i,
                 save_as_file=save_as_file,
                 deinterleave=deinterleave)
    if save_as_file:
        result_file = name
        pygame.mixer.music.load(result_file)
        pygame.mixer.music.play()
    else:
        return file


def get_tracks(name):
    x = midi(name)
    return x.tracks


def read(name,
         trackind=1,
         mode='find',
         is_file=False,
         merge=False,
         get_off_drums=True,
         to_piece=False):
    # read from a midi file and return a notes list

    # if mode is set to 'find', then will automatically search for
    # the first available midi track (has notes inside it)
    if is_file:
        name.seek(0)
        x = midi(file=name)
        name.close()
    else:
        x = midi(name)
    whole_tracks = x.tracks
    t = None
    changes_track = [
        each for each in whole_tracks
        if any(i.type == 'set_tempo' for i in each)
    ][0]
    if mode == 'find':
        for each in whole_tracks[1:]:
            if any(each_msg.type == 'note_on' for each_msg in each):
                t = each
                break
    elif mode == 'all':
        available_tracks = [
            each for each in whole_tracks[1:]
            if any(each_msg.type == 'note_on' for each_msg in each)
        ]
        if get_off_drums:
            available_tracks = [
                each for each in available_tracks if not (any(
                    hasattr(j, 'channel') and j.channel == 9
                    for j in each) or any(
                        hasattr(j, 'program') and 'drum' in
                        reverse_instruments[j.program + 1].lower()
                        for j in each))
            ]
        all_tracks = [midi_to_chord(x, j) for j in available_tracks]
        if merge:
            start_time_ls = [j[2] for j in all_tracks]
            first_track_ind = start_time_ls.index(min(start_time_ls))
            all_tracks.insert(0, all_tracks.pop(first_track_ind))
            first_track = all_tracks[0]
            tempo, all_track_notes, first_track_start_time = first_track
            for i in all_tracks[1:]:
                all_track_notes &= (i[1], i[2] - first_track_start_time)
            return tempo, all_track_notes, first_track_start_time
        else:
            if not to_piece:
                return all_tracks
            else:
                start_times_list = [j[2] for j in all_tracks]
                channels_list = [each[1].channel for each in available_tracks]
                current_tempo = all_tracks[0][0]
                instruments_list = []
                for each in available_tracks:
                    current_program = [
                        i.program for i in each if hasattr(i, 'program')
                    ]
                    if current_program:
                        instruments_list.append(current_program[0] + 1)
                    else:
                        instruments_list.append(1)
                chords_list = [each[1] for each in all_tracks]
                changes = midi_to_chord(x, changes_track)[1]
                chords_list[0] += changes
                tracks_names_list = [
                    each[0].name for each in available_tracks
                    if hasattr(each[0], 'name')
                ]
                if not tracks_names_list:
                    tracks_names_list = None
                return piece(chords_list, instruments_list, current_tempo,
                             start_times_list, tracks_names_list,
                             channels_list)
    else:
        try:
            t = whole_tracks[trackind]
        except:
            return 'error'
    result = midi_to_chord(x, t)
    changes = midi_to_chord(x, changes_track)[1]
    result[1] += changes
    return result


def midi_to_chord(x, t):
    interval_unit = x.ticks_per_beat * 4
    hason = []
    hasoff = []
    intervals = []
    notelist = []
    notes_len = len(t)
    find_first_note = False
    start_time = 0
    tempo_times = 1
    for i in range(notes_len):
        current_msg = t[i]
        if current_msg.type == 'note_on' and current_msg.velocity != 0:
            current_msg_velocity = current_msg.velocity
            current_msg_note = current_msg.note
            if i not in hason and i not in hasoff:
                if not find_first_note:
                    find_first_note = True
                    start_time = sum(t[j].time
                                     for j in range(i + 1)) / interval_unit
                    if start_time.is_integer():
                        start_time = int(start_time)
                hason.append(i)
                find_interval = False
                find_end = False
                time2 = 0
                realtime = None
                for k in range(i + 1, notes_len - 1):
                    current_note = t[k]
                    current_note_type = current_note.type
                    time2 += current_note.time
                    if not find_interval:
                        if current_note_type == 'note_on' and current_note.velocity != 0:
                            find_interval = True
                            interval1 = time2 / interval_unit
                            if interval1.is_integer():
                                interval1 = int(interval1)
                            intervals.append(interval1)
                    if not find_end:
                        if current_note_type == 'note_off' or (
                                current_note_type == 'note_on'
                                and current_note.velocity == 0):
                            if current_note.note == current_msg_note:
                                hasoff.append(k)
                                find_end = True
                                realtime = time2

                if not find_interval:
                    intervals.append(
                        sum([t[x].time for x in range(i, notes_len - 1)]) /
                        interval_unit)
                if not find_end:
                    realtime = time2
                duration1 = realtime / interval_unit
                if duration1.is_integer():
                    duration1 = int(duration1)
                notelist.append(
                    degree_to_note(current_msg_note,
                                   duration=duration1,
                                   volume=current_msg_velocity))
        elif current_msg.type == 'set_tempo':
            tempo_times += current_msg.time / interval_unit
            current_tempo = tempo(unit.tempo2bpm(current_msg.tempo),
                                  tempo_times)
            notelist.append(current_tempo)
            intervals.append(0)
        elif current_msg.type == 'pitchwheel':
            current_pitch_bend = pitch_bend(current_msg.pitch,
                                            channel=current_msg.channel,
                                            mode='values')
            notelist.append(current_pitch_bend)
            intervals.append(0)
    result = chord(notelist, interval=intervals)
    result.interval = [
        result.interval[j] for j in range(len(result))
        if type(result.notes[j]) != note or result.notes[j].duration > 0
    ]
    result.notes = [
        each for each in result.notes
        if type(each) != note or each.duration > 0
    ]
    find_tempo = False
    for msg in x.tracks[0]:
        if hasattr(msg, 'tempo'):
            tempo_msg = msg.tempo
            find_tempo = True
    if find_tempo:
        bpm = unit.tempo2bpm(tempo_msg)
    else:
        for each_track in x.tracks[1:]:
            for msg in each_track:
                if hasattr(msg, 'tempo'):
                    tempo_msg = msg.tempo
        bpm = unit.tempo2bpm(tempo_msg)
    return [bpm, result, start_time]


def write(name_of_midi,
          chord1,
          bpm=80,
          track=0,
          channel=0,
          time1=0,
          track_num=1,
          mode='quick',
          instrument=None,
          i=None,
          save_as_file=True,
          midi_io=None,
          deinterleave=True):
    if i is not None:
        instrument = i
    if isinstance(chord1, piece):
        mode = 'multi'
    if mode == 'multi':
        '''
        write a whole piece (multi tracks with different instruments) to a midi file,
        requires a piece object
        '''
        if not isinstance(chord1, piece):
            return 'multi mode requires a piece object'
        track_number, start_times, instruments_numbers, bpm, tracks_contents, track_names, channels = \
        chord1.track_number, chord1.start_times, chord1.instruments_numbers, chord1.tempo, chord1.tracks, chord1.track_names, chord1.channels
        instruments_numbers = [
            i if type(i) == int else instruments[i]
            for i in instruments_numbers
        ]
        MyMIDI = MIDIFile(track_number, deinterleave=deinterleave)
        for i in range(track_number):
            if channels:
                current_channel = channels[i]
            else:
                current_channel = i
            MyMIDI.addTempo(i, 0, bpm)
            MyMIDI.addProgramChange(i, current_channel, 0,
                                    instruments_numbers[i] - 1)
            if track_names:
                MyMIDI.addTrackName(i, 0, track_names[i])

            content = tracks_contents[i]
            content_notes = content.notes
            content_intervals = content.interval
            current_start_time = start_times[i] * 4
            for j in range(len(content)):
                current_note = content_notes[j]
                current_type = type(current_note)
                if current_type == note:
                    MyMIDI.addNote(i, current_channel, current_note.degree,
                                   current_start_time,
                                   current_note.duration * 4,
                                   current_note.volume)
                    current_start_time += content_intervals[j] * 4
                elif current_type == tempo:
                    if type(current_note.bpm) == list:
                        for k in range(len(current_note.bpm)):
                            MyMIDI.addTempo(
                                i, (current_note.start_time[k] - 1) * 4,
                                current_note.bpm[k])
                    else:
                        if current_note.start_time:
                            MyMIDI.addTempo(i,
                                            (current_note.start_time - 1) * 4,
                                            current_note.bpm)
                        else:
                            MyMIDI.addTempo(i, current_start_time,
                                            current_note.bpm)
                elif current_type == pitch_bend:
                    if current_note.time is not None:
                        pitch_bend_time = (current_note.time - 1) * 4
                    else:
                        pitch_bend_time = current_start_time
                    pitch_bend_channel = i if current_note.channel is None else current_note.channel
                    MyMIDI.addPitchWheelEvent(current_note.track,
                                              pitch_bend_channel,
                                              pitch_bend_time,
                                              current_note.value)

        if save_as_file:
            with open(name_of_midi, "wb") as output_file:
                MyMIDI.writeFile(output_file)
            return
        else:
            from io import BytesIO
            current_io = BytesIO()
            MyMIDI.writeFile(current_io)
            return current_io
    if isinstance(chord1, note):
        chord1 = chord([chord1])
    chordall = concat(chord1) if isinstance(chord1, list) else chord1

    if mode == 'quick':
        MyMIDI = MIDIFile(track_num, deinterleave=deinterleave)
        current_channel = 0
        MyMIDI.addTempo(0, 0, bpm)
        if instrument is None:
            instrument = 1
        if type(instrument) != int:
            instrument = instruments[instrument]
        instrument -= 1
        MyMIDI.addProgramChange(0, current_channel, 0, instrument)
        content = chordall
        content_notes = content.notes
        content_intervals = content.interval
        current_start_time = time1 * 4
        N = len(content)
        for j in range(N):
            current_note = content_notes[j]
            current_type = type(current_note)
            if current_type == note:
                MyMIDI.addNote(0, current_channel, current_note.degree,
                               current_start_time, current_note.duration * 4,
                               current_note.volume)
                current_start_time += content_intervals[j] * 4
            elif current_type == tempo:
                if type(current_note.bpm) == list:
                    for k in range(len(current_note.bpm)):
                        MyMIDI.addTempo(i,
                                        (current_note.start_time[k] - 1) * 4,
                                        current_note.bpm[k])
                else:
                    if current_note.start_time:
                        MyMIDI.addTempo(0, (current_note.start_time - 1) * 4,
                                        current_note.bpm)
                    else:
                        MyMIDI.addTempo(0, current_start_time,
                                        current_note.bpm)
            elif current_type == pitch_bend:
                if current_note.time is not None:
                    pitch_bend_time = (current_note.time - 1) * 4
                else:
                    pitch_bend_time = current_start_time
                MyMIDI.addPitchWheelEvent(current_note.track, channel,
                                          pitch_bend_time, current_note.value)
            #elif type(current_note) == tuning:
            #MyMIDI.changeNoteTuning(current_note.track, current_note.tunings, current_note.sysExChannel, current_note.realTime, current_note.tuningProgam)

        if save_as_file:
            with open(name_of_midi, "wb") as output_file:
                MyMIDI.writeFile(output_file)
            return
        else:
            from io import BytesIO
            current_io = BytesIO()
            MyMIDI.writeFile(current_io)
            return current_io

    elif mode == 'new':
        '''
        write to a new midi file or overwrite an existing midi file,
        only supports writing to a single track in this mode
        '''
        MyMIDI = MIDIFile(track_num, deinterleave=deinterleave)
        time1 *= 4
        MyMIDI.addTempo(track, time1, bpm)
        degrees = [x.degree for x in chordall.notes]
        duration = [x.duration * 4 for x in chordall.notes]
        for i in range(len(degrees)):
            MyMIDI.addNote(track, channel, degrees[i], time1, duration[i],
                           chordall[i + 1].volume)
            time1 += chordall.interval[i] * 4
        if save_as_file:
            with open(name_of_midi, "wb") as output_file:
                MyMIDI.writeFile(output_file)
        else:
            from io import BytesIO
            current_io = BytesIO()
            MyMIDI.writeFile(current_io)
            return current_io
    elif mode == 'new2':
        '''
        this mode also writes to a new midi file or overwrite an existing midi file
        as the 'new' mode does, but uses mido ways instead of midiutil ways,
        also only supports writing to a single track
        '''
        newmidi = midi()
        newtempo = unit.bpm2tempo(bpm)
        for g in range(track_num + 1):
            newmidi.add_track()
        newmidi.tracks[0] = MidiTrack([
            MetaMessage('set_tempo', bpm=newtempo, time=0),
            MetaMessage('end_of_track', time=0)
        ])
        if save_as_file:
            newmidi.save(name_of_midi)
            current_io = None
        else:
            current_io = newmidi
        return write(name_of_midi,
                     chord1,
                     bpm,
                     track,
                     channel,
                     time1,
                     track_num,
                     mode='m+',
                     instrument=instrument,
                     i=i,
                     save_as_file=save_as_file,
                     midi_io=current_io,
                     deinterleave=deinterleave)
    elif mode in ['m+', 'm']:
        '''
        both of these two modes modify existing midi files
        m+: add at the end of the midi file,
        m: add from the beginning of the midi file
        '''
        if save_as_file:
            x = midi(name_of_midi)
        else:
            x = midi_io
        if instrument is not None:
            instrument_num = instrument
            if type(instrument) != int:
                instrument_num = instruments[instrument]
            instrument_num -= 1
            instrument_msg = mido.Message('program_change',
                                          program=instrument_num)
            x.tracks[1].insert(0, instrument_msg)
        tracklist = x.tracks[1:]
        track_modify = tracklist[track]
        interval_unit = x.ticks_per_beat * 4
        time1 *= interval_unit
        time1 = int(time1)
        if mode == 'm+':
            degrees = [x.degree for x in chordall.notes]
            duration = [
                int(x.duration * interval_unit) for x in chordall.notes
            ]
            interval2 = [int(x * interval_unit) for x in chordall.interval]
            has = []
            for t in range(len(duration)):
                distance = sum(interval2[:t])
                has.append((distance, t, 'note_on'))
                has.append((distance + duration[t], t, 'note_off'))
            sorthas = sorted(has, key=lambda x: x[0])
            for n in range(len(sorthas)):
                if n == 0:
                    track_modify.append(
                        Message(sorthas[n][2],
                                note=degrees[sorthas[n][1]],
                                velocity=chordall[sorthas[n][1] + 1].volume,
                                time=time1))
                else:
                    track_modify.append(
                        Message(sorthas[n][2],
                                note=degrees[sorthas[n][1]],
                                velocity=chordall[sorthas[n][1] + 1].volume,
                                time=sorthas[n][0] - sorthas[n - 1][0]))
        elif mode == 'm':
            file = write('tempmerge.mid',
                         chord1,
                         bpm,
                         track,
                         channel,
                         time1,
                         track_num,
                         instrument=instrument,
                         i=i,
                         save_as_file=save_as_file,
                         deinterleave=deinterleave)
            if save_as_file:
                tempmid = midi('tempmerge.mid')
            else:
                tempmid = file
            newtrack = tempmid.tracks[1:][track]
            aftertrack = merge([track_modify, newtrack])
            x.tracks[track + 1] = aftertrack
            if save_as_file:
                os.remove('tempmerge.mid')
        if save_as_file:
            x.save(name_of_midi)
        else:
            from io import BytesIO
            result_io = BytesIO()
            x.save(file=result_io)
            return result_io


MODIFY = 'modify'
NEW = 'new'


def detect_in_scale(x,
                    most_like_num=3,
                    get_scales=False,
                    search_all=True,
                    search_all_each_num=2,
                    major_minor_preference=True,
                    find_altered=True,
                    altered_max_number=1):
    if type(x) != chord:
        x = chord([trans_note(i) for i in x])
    whole_notes = x.names()
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
        x_len = len(x)
        results.sort(key=lambda s: x_len / len(s), reverse=True)
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


def detect_scale(x,
                 melody_tol=minor_seventh,
                 chord_tol=major_sixth,
                 get_off_overlap_notes=True,
                 average_degree_length=8,
                 melody_degree_tol=toNote('B4'),
                 most_like_num=3,
                 count_num=3,
                 get_scales=False,
                 not_split=False):
    # receive a piece of music and analyze what modes it is using,
    # return a list of most likely and exact modes the music has.

    # newly added on 2020/4/25, currently in development
    whole_notes = x.names()
    note_names = list(set(whole_notes))
    note_names = [standard[i] for i in note_names]
    note_names.sort()
    note_names.append(note_names[0] + octave)
    note_intervals = [
        note_names[i] - note_names[i - 1] for i in range(1, len(note_names))
    ]
    result_scale_types = detectScale[tuple(note_intervals)]
    if result_scale_types not in ['not found', ('12', )]:
        result_scale_types = result_scale_types[0]
        center_note = standard_reverse[note_names[0]]
        result_scale = scale(center_note, result_scale_types)
        if result_scale_types in modern_modes:
            inds = modern_modes.index(result_scale_types) - 1
            if inds != -1:
                result_scale = result_scale.inversion(7 - inds)
                result_scale.mode = 'major'
                result_scale_types = 'major'
        if result_scale_types == 'major':
            melody_notes = split_melody(
                x, 'notes', melody_tol, chord_tol, get_off_overlap_notes,
                average_degree_length,
                melody_degree_tol) if not not_split else x
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
            x, 'notes', melody_tol, chord_tol, get_off_overlap_notes,
            average_degree_length, melody_degree_tol) if not not_split else x
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


def get_chord_root_note(chord_name, get_chord_types=False):
    types = type(chord_name)
    if types == chord:
        chord_name = detect(chord_name)
        if type(chord_name) == list:
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
    if type(chords) != list:
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
        scale_degree = note_names.index(root_note) + 1
        current_function = chord_functions_roman_numerals[scale_degree]
        if chord_types == '' or chord_types == '5':
            original_chord = mode(scale_degree)
            third_type = original_chord[2].degree - original_chord[1].degree
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
    if type(chords) != list:
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


def chord_functions_analysis(x,
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
    if fixed_scale_type:
        scales = fixed_scale_type
    else:
        scales = x.detect_scale(get_scales=True)
        if scale_type:
            scales = [i for i in scales if i.mode == scale_type][0]
        else:
            scales = scales[0]
    result = chord_analysis(x, mode='chords')
    result = [i.standardize() for i in result]
    actual_chords = [detect(i, **detect_args) for i in result if len(i) > 1]
    actual_chords = [i[0] if type(i) == list else i for i in actual_chords]
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
    analysis_result = f'key: {scales[1].name} {scales.mode}{spaces}{chord_progressions}'
    if write_to_file:
        with open('chords functions analysis result.txt',
                  'w',
                  encoding='utf-8') as f:
            f.write(analysis_result)
        analysis_result += spaces + "Successfully write the chord analysis result as a text file, please see 'chords functions analysis result.txt'."
        return analysis_result
    else:
        return analysis_result


def split_melody(x,
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
    if mode == 'index':
        result = split_melody(x, 'notes', melody_tol, chord_tol,
                              get_off_overlap_notes, average_degree_length,
                              melody_degree_tol)
        melody = [t.number for t in result]

        return melody
    elif mode == 'hold':
        result = split_melody(x, 'index', melody_tol, chord_tol,
                              get_off_overlap_notes, average_degree_length,
                              melody_degree_tol)
        whole_interval = x.interval
        whole_notes = x.notes
        new_interval = []
        N = len(result) - 1
        for i in range(N):
            new_interval.append(sum(whole_interval[result[i]:result[i + 1]]))
        new_interval.append(sum(whole_interval[result[-1]:]))
        return chord([whole_notes[j] for j in result], interval=new_interval)

    elif mode == 'notes':
        x_notes = x.notes
        N = len(x)
        for k in range(N):
            x_notes[k].number = k
        temp = copy(x)
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
            whole_interval = [whole_interval[j.number] for j in whole_notes]
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
        melody = [x_notes[each.number] for each in melody]
        return melody


def split_chord(x,
                mode='index',
                melody_tol=minor_seventh,
                chord_tol=major_sixth,
                get_off_overlap_notes=True,
                average_degree_length=8,
                melody_degree_tol=toNote('B4')):
    melody_ind = split_melody(x, 'index', melody_tol, chord_tol,
                              get_off_overlap_notes, average_degree_length,
                              melody_degree_tol)
    N = len(x)
    chord_ind = [i for i in range(N) if i not in melody_ind]
    if mode == 'index':
        return chord_ind
    elif mode == 'notes':
        whole_notes = x.notes
        return [whole_notes[k] for k in chord_ind]
    elif mode == 'hold':
        whole_notes = x.notes
        new_interval = []
        whole_interval = x.interval
        M = len(chord_ind) - 1
        for i in range(M):
            new_interval.append(
                sum(whole_interval[chord_ind[i]:chord_ind[i + 1]]))
        new_interval.append(sum(whole_interval[chord_ind[-1]:]))
        return chord([whole_notes[j] for j in chord_ind],
                     interval=new_interval)


def split_all(x,
              mode='index',
              melody_tol=minor_seventh,
              chord_tol=major_sixth,
              get_off_overlap_notes=True,
              average_degree_length=8,
              melody_degree_tol=toNote('B4')):
    # split the main melody and chords part of a piece of music,
    # return both of main melody and chord part
    melody_ind = split_melody(x, 'index', melody_tol, chord_tol,
                              get_off_overlap_notes, average_degree_length,
                              melody_degree_tol)
    N = len(x)
    chord_ind = [i for i in range(N) if i not in melody_ind]
    if mode == 'index':
        return [melody_ind, chord_ind]
    elif mode == 'notes':
        whole_notes = x.notes
        return [[whole_notes[j] for j in melody_ind],
                [whole_notes[k] for k in chord_ind]]
    elif mode == 'hold':
        whole_notes = x.notes
        new_interval_1 = []
        whole_interval = x.interval
        chord_len = len(chord_ind) - 1
        for i in range(chord_len):
            new_interval_1.append(
                sum(whole_interval[chord_ind[i]:chord_ind[i + 1]]))
        new_interval_1.append(sum(whole_interval[chord_ind[-1]:]))
        new_interval_2 = []
        melody_len = len(melody_ind) - 1
        for j in range(melody_len):
            new_interval_2.append(
                sum(whole_interval[melody_ind[j]:melody_ind[j + 1]]))
        new_interval_2.append(sum(whole_interval[melody_ind[-1]:]))
        result_chord = chord([whole_notes[i] for i in chord_ind],
                             interval=new_interval_1)
        result_melody = chord([whole_notes[j] for j in melody_ind],
                              interval=new_interval_2)
        # shift is the start time that chord part starts after main melody starts,
        # or the start time that main melody starts after chord part starts,
        # depends on which starts earlier, if shift >= 0, chord part starts after main melody,
        # if shift < 0, chord part starts before main melody
        first_chord_ind = chord_ind[0]
        first_melody_ind = melody_ind[0]
        if first_chord_ind >= first_melody_ind:
            shift = sum(whole_interval[first_melody_ind:first_chord_ind])
        else:
            shift = -sum(whole_interval[first_chord_ind:first_melody_ind])
        return [result_melody, result_chord, shift]


def chord_analysis(x,
                   melody_tol=minor_seventh,
                   chord_tol=major_sixth,
                   get_off_overlap_notes=True,
                   average_degree_length=8,
                   melody_degree_tol=toNote('B4'),
                   mode='chord names',
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
    if not is_chord:
        chord_notes = split_chord(x, 'hold', melody_tol, chord_tol,
                                  get_off_overlap_notes, average_degree_length,
                                  melody_degree_tol)
    else:
        chord_notes = x
    if formated:
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
        result = [i if type(i) != list else i[0] for i in result]
        result_notes = [chord_notes[k[0] + 1:k[1] + 1] for k in chord_inds]
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
        else:
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
            return [chord_notes[k[0] + 1:k[1] + 1] for k in chord_inds]
        return chord_ls
    elif mode == 'chord names':
        result = [detect(each, **detect_args) for each in chord_ls]
        return [i if type(i) != list else i[0] for i in result]


def find_continuous(x, value, start=None, stop=None):
    if start is None:
        start = 0
    if stop is None:
        stop = len(x)
    inds = []
    appear = False
    for i in range(start, stop):
        if not appear:
            if x[i] == value:
                appear = True
                inds.append(i)
        else:
            if x[i] == value:
                inds.append(i)
            else:
                break
    return inds


def find_all_continuous(x, value, start=None, stop=None):
    if start is None:
        start = 0
    if stop is None:
        stop = len(x)
    result = []
    inds = []
    appear = False
    for i in range(start, stop):
        if x[i] == value:
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
        if result[-1][-1] >= len(x):
            del result[-1][-1]
    except:
        pass
    return result


def add_to_index(x, value, start=None, stop=None, step=1):
    if start is None:
        start = 0
    if stop is None:
        stop = len(x)
    inds = []
    counter = 0
    for i in range(start, stop, step):
        counter += x[i]
        inds.append(i)
        if counter == value:
            inds.append(i + 1)
            break
        elif counter > value:
            break
    if not inds:
        inds = [0]
    return inds


def add_to_last_index(x, value, start=None, stop=None, step=1):
    if start is None:
        start = 0
    if stop is None:
        stop = len(x)
    ind = 0
    counter = 0
    for i in range(start, stop, step):
        counter += x[i]
        ind = i
        if counter == value:
            ind += 1
            break
        elif counter > value:
            break
    return ind


def modulation(chord1, old_scale, new_scale):
    # change notes (including both of melody and chords) in the given piece
    # of music from a given scale to another given scale, and return
    # the new changing piece of music.
    return chord1.modulation(old_scale, new_scale)


def exp(form, obj_name='x', mode='tail'):
    # return a function that follows a mode of translating a given chord to the wanted result,
    # form is a chains of functions you want to perform on the variables.
    if mode == 'tail':
        try:
            func = eval(f'lambda x: x.{form}')
        except:
            return 'not a valid expression'
    elif mode == 'whole':
        try:
            func = eval(f'lambda {obj_name}: {form}')
        except:
            return 'not a valid expression'

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
            return trans(check_structure[0], pitch, duration,
                         interval)(','.join(check_structure[1:]))
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
        first_chord = trans(part1, pitch, duration, interval)
        if type(first_chord) == chord:
            if part2.isdigit() or (part2[0] == '-' and part2[1:].isdigit()):
                return first_chord / int(part2)
            elif part2[-1] == '!' and part2[:-1].isdigit():
                return first_chord @ int(part2[:-1])
            elif part2 in standard:
                first_chord_notenames = first_chord.names()
                if part2 in first_chord_notenames and part2 != first_chord_notenames[
                        0]:
                    return first_chord.inversion(
                        first_chord_notenames.index(part2))
                return chord([part2] + first_chord_notenames,
                             rootpitch=pitch,
                             duration=duration,
                             interval=interval)
            else:
                second_chord = trans(part2, pitch, duration, interval)
                if type(second_chord) == chord:
                    return chord(second_chord.names() + first_chord.names(),
                                 rootpitch=pitch,
                                 duration=duration,
                                 interval=interval)
    return 'not a valid chord representation or chord types not in database'


def toScale(obj, pitch=4):
    inds = obj.index(' ')
    tonic, scale_name = obj[:inds], obj[inds + 1:]
    return scale(note(tonic, pitch), scale_name)


C = trans
N = toNote
S = toScale


def notels(a):
    return [notedict[i] for i in a]


def torealnotes(a, mode=0):
    if mode == 0:
        result = a.split('Dg')
    else:
        result = a.split()
    return [[notedict[i] for i in j] for j in result]


def read12notesfile(path, mode=0):
    with open(path) as f:
        data = f.read()
        result = torealnotes(data, mode)
    return result


def torealnotes(a, combine=0, bychar=0, mode=0):
    if mode == 0:
        result = a.split('Dg')
    else:
        result = a.split()
    if combine == 0:
        if bychar == 0:
            return [notels(i.replace(' ', '')) for i in result]
        else:
            return [[notels(i) for i in j.split()] for j in result]
    else:
        return [notedict[i] for i in a]


def torealnotesfile(path,
                    name='torealnotes conversion.txt',
                    combine=0,
                    bychar=0,
                    mode=0):
    with open(path, "r") as f:
        data = f.read()
        with open(name, "w") as new:
            new.write(str(torealnotes(data, combine, bychar, mode)))


def tochords(a,
             pitch=4,
             combine=0,
             interval_unit=0.5,
             rest_unit=1,
             has_interval=0):
    if type(a[0]) != list:
        a = [a]
    if has_interval == 0:
        chordls = [
            chord([note(j, pitch)
                   for j in i], interval=interval_unit).rest(rest_unit)
            for i in a
        ]
    else:
        chordls = []
        for i in a:
            newchord = []
            N = len(i)
            newinterval = []
            for k in range(N):
                now = i[k]
                if now != 'interval':
                    newchord.append(note(now, pitch))
                    if k != N - 1 and i[k + 1] == 'interval':
                        newinterval.append(interval_unit + rest_unit)
                    else:
                        newinterval.append(interval_unit)
            chordls.append(chord(newchord, interval=newinterval))
    if combine == 0:
        return chordls
    else:
        return chord([j for i in chordls for j in i],
                     interval=[j for i in chordls for j in i.interval])


def tochordsfile(path,
                 pitch=4,
                 combine=0,
                 interval_unit=0.5,
                 rest_unit=1,
                 has_interval=0,
                 mode=0,
                 splitway=0,
                 combine1=0,
                 bychar=0):
    # mode == 0: open the real notes file and eval the nested by first checking if it is started with [[
    # mode == else: open the file written in 12notes language and translate to real notes
    # splitway == 0/1: corresponding to the mode == 0/1 in real notes translation
    with open(path) as f:
        data = f.read()
        if mode == 0:
            if data[:2] == '[[':
                data = eval(data)
                result = tochords(data, pitch, combine, interval_unit,
                                  rest_unit, has_interval)
            else:
                result = 'not a valid real notes file'
        else:
            data = torealnotes(data, combine1, bychar, splitway)
            result = tochords(data, pitch, combine, interval_unit, rest_unit,
                              has_interval)
    return result


def inversion_from(a, b, num=False, mode=0):
    N = len(b)
    for i in range(1, N):
        temp = b.inversion(i)
        if [x.name for x in temp.notes] == [y.name for y in a.notes]:
            return f'/{a[1].name}' if not num else f'{i} inversion'
    for j in range(1, N):
        temp = b.inversion_highest(j)
        if [x.name for x in temp.notes] == [y.name for y in a.notes]:
            return f'/{b[j].name}(top)' if not num else f'{j} inversion(highest)'
    return f'could not get chord {a.notes} from a single inversion of chord {b.notes}, you could try sort_from' if mode == 0 else None


def sort_from(a, b, getorder=False):
    names = [i.name for i in b]
    try:
        order = [names.index(j.name) + 1 for j in a]
        return f'{b.notes} sort as {order}' if not getorder else order
    except:
        return


def omitfrom(a, b, showls=False, alter_notes_show_degree=False):
    a_notes = a.names()
    b_notes = b.names()
    omitnotes = list(set(b_notes) - set(a_notes))
    if alter_notes_show_degree:
        b_first_note = b[1].degree
        omitnotes_degree = []
        for j in omitnotes:
            current = reverse_degree_match[b[b_notes.index(j) + 1].degree -
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


def changefrom(a,
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
        b = b.down(12 * (b[1].num - a[1].num))
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
            b_first_note = b[1].degree
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


def addfrom(a, b, default=True):
    # This function is used at the worst situation that no matches
    # from other chord transformations are found, and it is limited
    # to one note added.
    addnotes = omitfrom(b, a, True)
    if len(addnotes) == 1:
        if addnotes[0] == sorted(a.notes, key=lambda x: x.degree)[-1].name:
            return f'add {", ".join(addnotes)} on the top'
        else:
            return f'add {", ".join(addnotes)}'
    if default:
        return ''
    else:
        return f'add {", ".join(addnotes)}'


def inversion_way(a, b, inv_num=False, chordtype=None, only_msg=False):
    if samenotes(a, b):
        return f'{b[1].name}{chordtype}'
    if samenote_set(a, b):
        inversion_msg = inversion_from(
            a, b, mode=1) if not inv_num else inversion_from(
                a, b, num=True, mode=1)
        if inversion_msg is not None:
            if not only_msg:
                if chordtype is not None:
                    return f'{b[1].name}{chordtype}{inversion_msg}' if not inv_num else f'{b[1].name}{chordtype} {inversion_msg}'
                else:
                    return inversion_msg
            else:
                return inversion_msg
        else:
            sort_msg = sort_from(a, b, getorder=True)
            if sort_msg is not None:
                if not only_msg:
                    if chordtype is not None:
                        return f'{b[1].name}{chordtype} sort as {sort_msg}'
                    else:
                        return f'sort as {sort_msg}'
                else:
                    return f'sort as {sort_msg}'
            else:
                return f'a voicing of {b[1].name}{chordtype}'
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
        rootnote = a[1]
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
                         result), chordfrom, f'{chordfrom[1].name}{first[1]}')
                return result if not getgoodchord else (
                    result, chordfrom, f'{chordfrom[1].name}{first[1]}')
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
                    result = omitfrom(
                        a,
                        chordfrom,
                        alter_notes_show_degree=alter_notes_show_degree)
                    types = 'omit'
                elif len(a) == len(chordfrom):
                    result = changefrom(
                        a,
                        chordfrom,
                        alter_notes_show_degree=alter_notes_show_degree)
                    types = 'change'
                elif contains(chordfrom, a):
                    result = addfrom(a, chordfrom)
                    types = 'add'
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
                    bname = b[1].name + provide_name
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
            result = omitfrom(a,
                              chordfrom,
                              alter_notes_show_degree=alter_notes_show_degree)
        elif len(a) == len(chordfrom):
            result = changefrom(
                a, chordfrom, alter_notes_show_degree=alter_notes_show_degree)
        elif contains(chordfrom, a):
            result = addfrom(a, chordfrom)
        if result == '':
            return 'not good'
        bname = None
        if fromchord_name:
            if provide_name != None:
                bname = b[1].name + provide_name
            else:
                bname = detect(b)
            if type(bname) == list:
                bname = bname[0]
        return result if not getgoodchord else (result, chordfrom, bname)


def detect_variation(a,
                     mode='chord',
                     inv_num=False,
                     rootpitch=4,
                     change_from_first=False,
                     original_first=False,
                     same_note_special=True,
                     N=None,
                     alter_notes_show_degree=False):
    for each in range(1, N):
        each_current = a.inversion(each)
        each_detect = detect(each_current,
                             mode,
                             inv_num,
                             rootpitch,
                             change_from_first,
                             original_first,
                             same_note_special,
                             whole_detect=False,
                             return_fromchord=True,
                             alter_notes_show_degree=alter_notes_show_degree)
        if each_detect is not None:
            detect_msg, change_from_chord, chord_name_str = each_detect
            inv_msg = inversion_way(a, each_current, inv_num)
            result = f'{detect_msg} {inv_msg}'
            if any(x in detect_msg
                   for x in ['sort', '/']) and any(y in inv_msg
                                                   for y in ['sort', '/']):
                inv_msg = inversion_way(a, change_from_chord, inv_num)
                if inv_msg == 'not good':
                    inv_msg = find_similarity(
                        a,
                        change_from_chord,
                        alter_notes_show_degree=alter_notes_show_degree)
                result = f'{chord_name_str} {inv_msg}'
            return result
    for each2 in range(1, N):
        each_current = a.inversion_highest(each2)
        each_detect = detect(each_current,
                             mode,
                             inv_num,
                             rootpitch,
                             change_from_first,
                             original_first,
                             same_note_special,
                             whole_detect=False,
                             return_fromchord=True,
                             alter_notes_show_degree=alter_notes_show_degree)
        if each_detect is not None:
            detect_msg, change_from_chord, chord_name_str = each_detect
            inv_msg = inversion_way(a, each_current, inv_num)
            result = f'{detect_msg} {inv_msg}'
            if any(x in detect_msg
                   for x in ['sort', '/']) and any(y in inv_msg
                                                   for y in ['sort', '/']):
                inv_msg = inversion_way(a, change_from_chord, inv_num)
                if inv_msg == 'not good':
                    inv_msg = find_similarity(
                        a,
                        change_from_chord,
                        alter_notes_show_degree=alter_notes_show_degree)
                result = f'{chord_name_str} {inv_msg}'
            return result


def detect_split(a, N=None):
    if N < 6:
        splitind = 1
        lower = a.notes[0].name
        upper = detect(a.notes[splitind:])
        if type(upper) == list:
            upper = upper[0]
        return f'[{upper}]/{lower}'
    else:
        splitind = N // 2
        lower = detect(a.notes[:splitind])
        upper = detect(a.notes[splitind:])
        if type(lower) == list:
            lower = lower[0]
        if type(upper) == list:
            upper = upper[0]
        return f'[{upper}]/[{lower}]'


def interval_check(a, two_show_interval=True):
    if two_show_interval:
        TIMES, DIST = divmod((a.notes[1].degree - a.notes[0].degree), 12)
        if DIST == 0 and TIMES != 0:
            DIST = 12
        interval_name = INTERVAL[DIST][0]
        root_note_name = a[1].name
        if interval_name == 'perfect fifth':
            return f'{root_note_name}5 ({root_note_name} power chord) ({root_note_name} with perfect fifth)'
        return f'{root_note_name} with {interval_name}'
    else:
        if (a.notes[1].degree - a.notes[0].degree) % octave == 0:
            return f'{a.notes[0]} octave (or times of octave)'


def detect(a,
           mode='chord',
           inv_num=False,
           rootpitch=4,
           change_from_first=True,
           original_first=True,
           same_note_special=False,
           whole_detect=True,
           return_fromchord=False,
           two_show_interval=True,
           poly_chord_first=False,
           root_position_return_first=True,
           alter_notes_show_degree=False):
    # mode could be chord/scale
    if mode == 'chord':
        if type(a) != chord:
            a = chord(a, rootpitch=rootpitch)
        N = len(a)
        if N == 1:
            return f'note {a.notes[0]}'
        if N == 2:
            return interval_check(a, two_show_interval)
        a = a.standardize()
        N = len(a)
        if N == 1:
            return f'note {a.notes[0]}'
        if N == 2:
            return interval_check(a, two_show_interval)
        root = a[1].degree
        rootNote = a[1].name
        distance = tuple(i.degree - root for i in a[2:])
        findTypes = detectTypes[distance]
        if findTypes != 'not found':
            return [
                rootNote + i for i in findTypes
            ] if not root_position_return_first else rootNote + findTypes[0]
        original_detect = find_similarity(
            a,
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
            current = chord(a.inversion(i).names())
            root = current[1].degree
            distance = tuple(i.degree - root for i in current[2:])
            result1 = detectTypes[distance]
            if result1 != 'not found':
                inversion_result = inversion_way(a, current, inv_num,
                                                 result1[0])
                if 'sort' in inversion_result:
                    continue
                else:
                    return inversion_result if not return_fromchord else (
                        inversion_result, current,
                        f'{current[1].name}{result1[0]}')
            else:
                current = current.inoctave()
                root = current[1].degree
                distance = tuple(i.degree - root for i in current[2:])
                result1 = detectTypes[distance]
                if result1 != 'not found':
                    inversion_result = inversion_way(a, current, inv_num,
                                                     result1[0])
                    if 'sort' in inversion_result:
                        continue
                    else:
                        return inversion_result if not return_fromchord else (
                            inversion_result, current,
                            f'{current[1].name}{result1[0]}')
        for i in range(1, N):
            current = chord(a.inversion_highest(i).names())
            root = current[1].degree
            distance = tuple(i.degree - root for i in current[2:])
            result1 = detectTypes[distance]
            if result1 != 'not found':
                inversion_high_result = inversion_way(a, current, inv_num,
                                                      result1[0])
                if 'sort' in inversion_high_result:
                    continue
                else:
                    return inversion_high_result if not return_fromchord else (
                        inversion_high_result, current,
                        f'{current[1].name}{result1[0]}')
            else:
                current = current.inoctave()
                root = current[1].degree
                distance = tuple(i.degree - root for i in current[2:])
                result1 = detectTypes[distance]
                if result1 != 'not found':
                    inversion_high_result = inversion_way(
                        a, current, inv_num, result1[0])
                    if 'sort' in inversion_high_result:
                        continue
                    else:
                        return inversion_high_result if not return_fromchord else (
                            inversion_high_result, current,
                            f'{current[1].name}{result1[0]}')
        if poly_chord_first and N > 3:
            return detect_split(a, N)
        inversion_final = True
        possibles = [
            (find_similarity(a.inversion(j),
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
                a.inversion_highest(j),
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
                detect_var = detect_variation(a, mode, inv_num, rootpitch,
                                              change_from_first,
                                              original_first,
                                              same_note_special, N,
                                              alter_notes_show_degree)
                if detect_var is None:
                    result_change = detect(
                        a,
                        mode,
                        inv_num,
                        rootpitch,
                        not change_from_first,
                        original_first,
                        same_note_special,
                        False,
                        return_fromchord,
                        alter_notes_show_degree=alter_notes_show_degree)
                    if result_change is None:
                        return detect_split(a, N)
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
                current_invert = a.inversion(possibles[0][1])
            else:
                current_invert = a.inversion_highest(possibles[0][1])
            invfrom_current_invert = inversion_way(a, current_invert, inv_num)
            highest_msg = best[0][1]
            if any(x in highest_msg
                   for x in ['sort', '/']) and any(y in invfrom_current_invert
                                                   for y in ['sort', '/']):
                retry_msg = find_similarity(
                    a,
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
            detect_var = detect_variation(a, mode, inv_num, rootpitch,
                                          change_from_first, original_first,
                                          same_note_special, N,
                                          alter_notes_show_degree)
            if detect_var is None:
                result_change = detect(
                    a,
                    mode,
                    inv_num,
                    rootpitch,
                    not change_from_first,
                    original_first,
                    same_note_special,
                    False,
                    return_fromchord,
                    alter_notes_show_degree=alter_notes_show_degree)
                if result_change is None:
                    return detect_split(a, N)
                else:
                    return result_change
            else:
                return detect_var

    elif mode == 'scale':
        if type(a[0]) == int:
            try:
                scales = detectScale[tuple(a)][0]
            except:
                return 'cannot detect this scale'
        else:
            if type(a) in [chord, scale]:
                a = a.notes
            try:
                scales = detectScale[tuple(a[i].degree - a[i - 1].degree
                                           for i in range(1, len(a)))]
                if scales == 'not found':
                    return scales
                return scales[0]
            except:
                return 'cannot detect this scale'


def intervalof(a, cummulative=True, translate=False):
    if type(a) == scale:
        a = a.getScale()
    if type(a) != chord:
        a = chord(a)
    return a.intervalof(cummulative, translate)


def sums(*chordls):
    if len(chordls) == 1:
        chordls = chordls[0]
        start = chordls[0]
        for i in chordls[1]:
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
        check_chord_types = newchord[2].degree - newchord[1].degree
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


def negative_harmony(key, a=None, sort=False, get_map=False):
    notes_dict = [
        'C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F'
    ] * 2
    key_tonic = key[1].name
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
    if a:
        if type(a) == chord:
            temp = copy(a)
            notes = temp.notes
            for each in range(len(notes)):
                current = notes[each]
                if current.name in standard_dict:
                    current.name = standard_dict[current.name]
                notes[each] = note(map_dict[current.name], current.num)
            if sort:
                temp.notes.sort(key=lambda s: s.degree)
            return temp
        else:
            return 'requires a chord object'
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


def build(*tracks_list, bpm=80):
    if len(set([len(i) for i in tracks_list])) != 1:
        return 'every track should has the same number of variables'
    tracks = [i[1] for i in tracks_list]
    instruments_list = [i[0] for i in tracks_list]
    start_times = [i[2] for i in tracks_list]
    channels = None
    track_names = None
    tracks_len = len(tracks_list[0])
    if tracks_len >= 4:
        channels = [i[3] for i in tracks_list]
    if tracks_len >= 5:
        track_names = [i[4] for i in tracks_list]
    return P(tracks, instruments_list, bpm, start_times, track_names, channels)
