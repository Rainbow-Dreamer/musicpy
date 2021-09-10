import os
import sys

abs_path = os.path.abspath(os.path.dirname(__file__))
os.chdir(abs_path)
os.environ['PATH'] += os.pathsep + abs_path
os.chdir('../../..')
sys.path.append('.')

import musicpy.musicpy as mp

os.chdir('musicpy')

import simpleaudio
from pydub.playback import _play_with_simpleaudio as play_sound

os.chdir('sf2_loader/read_sf2_32bit')

import time
import numpy
import fluidsynth
from pydub import AudioSegment
from io import BytesIO
from copy import deepcopy as copy


def bar_to_real_time(bar, bpm, mode=0):
    # return time in ms
    return int(
        (60000 / bpm) * (bar * 4)) if mode == 0 else (60000 / bpm) * (bar * 4)


def real_time_to_bar(time, bpm):
    return (time / (60000 / bpm)) / 4


def velocity_to_db(vol):
    if vol == 0:
        return -100
    return mp.math.log(vol / 127, 10) * 20


def percentage_to_db(vol):
    if vol == 0:
        return -100
    return mp.math.log(abs(vol / 100), 10) * 20


def get_timestamps(current_chord,
                   bpm,
                   ignore_other_messages=False,
                   pan=None,
                   volume=None):
    for i in range(len(current_chord.notes)):
        current = current_chord.notes[i]
        if type(current) == mp.pitch_bend and current.start_time is None:
            current.start_time = sum(current_chord.interval[:i]) + 1
    noteon_part = [
        general_event(
            'noteon',
            bar_to_real_time(sum(current_chord.interval[:i]), bpm, 1) / 1000,
            current_chord.notes[i]) for i in range(len(current_chord.notes))
        if type(current_chord.notes[i]) == mp.note
    ]
    noteoff_part = [
        general_event(
            'noteoff',
            bar_to_real_time(
                sum(current_chord.interval[:i]) +
                current_chord.notes[i].duration, bpm, 1) / 1000,
            current_chord.notes[i]) for i in range(len(current_chord.notes))
        if type(current_chord.notes[i]) == mp.note
    ]
    pitch_bend_part = [
        general_event('pitch_bend',
                      bar_to_real_time(i.start_time - 1, bpm, 1) / 1000, i)
        for i in current_chord.notes if type(i) == mp.pitch_bend
    ]
    result = noteon_part + noteoff_part + pitch_bend_part
    if not ignore_other_messages:
        other_messages_part = [
            general_event('message',
                          bar_to_real_time(i.time / 4, bpm, 1) / 1000, i)
            for i in current_chord.other_messages
        ]
        result += other_messages_part
    if pan:
        pan_part = [
            general_event(
                'message',
                bar_to_real_time(i.start_time - 1, bpm, 1) / 1000,
                mp.controller_event(controller_number=10, parameter=i.value))
            for i in pan
        ]
        result += pan_part
    if volume:
        volume_part = [
            general_event(
                'message',
                bar_to_real_time(i.start_time - 1, bpm, 1) / 1000,
                mp.controller_event(controller_number=7, parameter=i.value))
            for i in volume
        ]
        result += volume_part
    result.sort(key=lambda s: (s.start_time, s.event_type))
    return result


class effect:
    def __init__(self, func, name=None, *args, unknown_args=None, **kwargs):
        self.func = func
        if name is None:
            name = 'effect'
        self.name = name
        self.parameters = [args, kwargs]
        if unknown_args is None:
            unknown_args = {}
        self.unknown_args = unknown_args

    def process(self, sound, *args, unknown_args=None, **kwargs):
        if args or kwargs or unknown_args:
            return self.func(*args, **kwargs, **unknown_args)
        else:
            return self.func(sound, *self.parameters[0], **self.parameters[1],
                             **self.unknown_args)

    def process_unknown_args(self, **kwargs):
        for each in kwargs:
            if each in self.unknown_args:
                self.unknown_args[each] = kwargs[each]

    def __call__(self, *args, unknown_args=None, **kwargs):
        temp = copy(self)
        temp.parameters[0] = args + temp.parameters[0][len(args):]
        temp.parameters[1].update(kwargs)
        if unknown_args is None:
            unknown_args = {}
        temp.unknown_args.update(unknown_args)
        return temp

    def new(self, *args, unknown_args=None, **kwargs):
        temp = copy(self)
        temp.parameters = [args, kwargs]
        temp.parameters[1].update(kwargs)
        if unknown_args is None:
            unknown_args = {}
        temp.unknown_args = unknown_args
        return temp

    def __repr__(self):
        return f'[effect]\nname: {self.name}\nparameters: {self.parameters} unknown arguments: {self.unknown_args}'


class effect_chain:
    def __init__(self, *effects):
        self.effects = list(effects)

    def __call__(self, sound):
        sound.effects = self.effects
        return sound

    def __repr__(self):
        return f'[effect chain]\neffects:\n' + '\n\n'.join(
            [str(i) for i in self.effects])


class general_event:
    def __init__(self, event_type, start_time, value=None, other=None):
        self.event_type = event_type
        self.start_time = start_time
        if self.start_time < 0:
            self.start_time = 0
        self.value = value
        self.other = other

    def __repr__(self):
        return f'[general event] type: {self.event_type}  start_time: {self.start_time}s  value: {self.value}  other: {self.other}'


class sf2_loader:
    def __init__(self, file=None):
        self.file = []
        self.synth = fluidsynth.Synth()
        self.sfid_list = []
        self.sfid = 1
        if file:
            self.file.append(file)
            self.sfid = self.synth.sfload(file)
            self.sfid_list.append(copy(self.sfid))
        self.current_track = 0
        self.current_sfid = copy(self.sfid)
        self.current_bank_num = 0
        self.current_preset_num = 0
        if file:
            self.program_select()
        self.audio_array = []
        self.instruments = []
        self.instruments_ind = []

    def __repr__(self):
        return f'''[soundfont loader]
loaded soundfonts: {self.file}
soundfonts id: {self.sfid_list}
current track: {self.current_track}
current soundfont id: {self.current_sfid}
current soundfont name: {os.path.basename(self.file[self.sfid_list.index(self.current_sfid)]) if self.file else ""}
current bank number: {self.current_bank_num}
current preset number: {self.current_preset_num}
current preset name: {self.get_current_instrument()}'''

    def program_select(self,
                       track=None,
                       sfid=None,
                       bank_num=None,
                       preset_num=None,
                       correct=True):
        current_track = copy(self.current_track)
        current_sfid = copy(self.current_sfid)
        current_bank_num = copy(self.current_bank_num)
        current_preset_num = copy(self.current_preset_num)
        if track is None:
            track = self.current_track
        if sfid is None:
            sfid = self.current_sfid
        if bank_num is None:
            bank_num = self.current_bank_num
        else:
            self.instruments.clear()
        if preset_num is None:
            preset_num = self.current_preset_num
        select_status = self.synth.program_select(track, sfid, bank_num,
                                                  preset_num)
        if not (correct and select_status == -1):
            self.current_track = track
            self.current_sfid = sfid
            self.current_bank_num = bank_num
            self.current_preset_num = preset_num
        else:
            self.synth.program_select(current_track, current_sfid,
                                      current_bank_num, current_preset_num)
        return select_status

    def __lt__(self, preset_num):
        if type(preset_num) == tuple and len(preset_num) == 2:
            self.program_select(bank_num=preset_num[1])
            self < preset_num[0]
        else:
            if type(preset_num) == str:
                if not self.instruments:
                    self.instruments, self.instruments_ind = self.get_all_instrument_names(
                        get_ind=True)
                if preset_num in self.instruments:
                    current_ind = self.instruments_ind[self.instruments.index(
                        preset_num)]
                    self.program_select(preset_num=current_ind)
            else:
                self.program_select(preset_num=preset_num)

    def __mod__(self, value):
        self.program_select(track=value[0],
                            bank_num=value[1],
                            preset_num=value[2])

    def get_current_instrument(self, num=0):
        try:
            result = self.synth.channel_info(num)[3]
        except:
            result = ''
        return result

    def preset_name(self, sfid=None, bank_num=None, preset_num=None):
        if sfid is None:
            sfid = self.current_sfid
        if bank_num is None:
            bank_num = self.current_bank_num
        if preset_num is None:
            preset_num = self.current_preset_num
        return self.synth.sfpreset_name(sfid, bank_num, preset_num)

    def get_instrument_name(self,
                            track=None,
                            sfid=None,
                            bank_num=None,
                            preset_num=None,
                            num=0):
        current_track = copy(self.current_track)
        current_sfid = copy(self.current_sfid)
        current_bank_num = copy(self.current_bank_num)
        current_preset_num = copy(self.current_preset_num)
        select_status = self.program_select(track, sfid, bank_num, preset_num)
        result = self.synth.channel_info(num)[3]
        self.program_select(current_track, current_sfid, current_bank_num,
                            current_preset_num)
        if select_status != -1:
            return result

    def get_all_instrument_names(self,
                                 track=None,
                                 sfid=None,
                                 bank_num=None,
                                 num=0,
                                 max_num=128,
                                 get_ind=False,
                                 mode=0):
        current_track = copy(self.current_track)
        current_sfid = copy(self.current_sfid)
        current_bank_num = copy(self.current_bank_num)
        current_preset_num = copy(self.current_preset_num)
        preset_num = 0
        select_status = self.program_select(track, sfid, bank_num, preset_num)
        result = []
        ind = []
        if select_status != -1:
            result.append(self.synth.channel_info(num)[3])
            ind.append(preset_num)

        for i in range(max_num - 1):
            preset_num += 1
            select_status = self.program_select(track, sfid, bank_num,
                                                preset_num)
            if select_status != -1:
                result.append(self.synth.channel_info(num)[3])
                ind.append(preset_num)
        self.program_select(current_track, current_sfid, current_bank_num,
                            ind[0] if mode == 1 else current_preset_num)
        return result if not get_ind else (result, ind)

    def change_preset(self, preset):
        if type(preset) == str:
            if not self.instruments:
                self.instruments, self.instruments_ind = self.get_all_instrument_names(
                    get_ind=True)
            if preset in self.instruments:
                current_ind = self.instruments_ind[self.instruments.index(
                    preset)]
                self.program_select(preset_num=current_ind)
        else:
            self.program_select(preset_num=preset)

    def change_bank(self, bank):
        self.program_select(bank_num=bank, correct=False)

    def change_track(self, track):
        self.program_select(track=track)

    def change_sfid(self, sfid):
        self.program_select(sfid=sfid, correct=False)

    def change_soundfont(self, name):
        if name in self.file:
            ind = self.file.index(name)
            self.change_sfid(self.sfid_list[ind])
        else:
            names = [os.path.basename(i) for i in self.file]
            if name in names:
                ind = names.index(name)
                self.change_sfid(self.sfid_list[ind])

    def export_note(self,
                    note_name,
                    duration=2,
                    decay=1,
                    volume=100,
                    track=0,
                    start_time=0,
                    sample_width=2,
                    channels=2,
                    frame_rate=44100,
                    name=None,
                    format='wav',
                    get_audio=False,
                    effects=None,
                    bpm=80):
        self.audio_array = []
        if type(note_name) != mp.note:
            current_note = mp.N(note_name)
        else:
            current_note = note_name
        note_name = current_note.degree
        if start_time > 0:
            self.audio_array = numpy.append(
                self.audio_array,
                self.synth.get_samples(int(frame_rate * start_time)))
        self.synth.noteon(track, note_name, volume)
        self.audio_array = numpy.append(
            self.audio_array,
            self.synth.get_samples(int(frame_rate * duration)))
        self.synth.noteoff(track, note_name)
        self.audio_array = numpy.append(
            self.audio_array, self.synth.get_samples(int(frame_rate * decay)))
        current_samples = fluidsynth.raw_audio_string(self.audio_array)
        current_audio = AudioSegment.from_raw(BytesIO(current_samples),
                                              sample_width=sample_width,
                                              channels=channels,
                                              frame_rate=frame_rate)
        self.synth.system_reset()
        self.program_select()
        self.synth.get_samples(int(frame_rate * 1))
        if effects:
            current_audio = process_effect(current_audio, effects, bpm=bpm)
        elif check_effect(current_note):
            current_audio = process_effect(current_audio,
                                           current_note.effects,
                                           bpm=bpm)
        if name is None:
            name = f'{current_note}.{format}'
        if not get_audio:
            current_audio.export(name, format=format)
        else:
            return current_audio

    def export_chord(self,
                     current_chord,
                     decay=0.5,
                     track=0,
                     start_time=0,
                     piece_start_time=0,
                     sample_width=2,
                     channels=2,
                     frame_rate=44100,
                     name=None,
                     format='wav',
                     bpm=80,
                     get_audio=False,
                     fixed_decay=False,
                     effects=None,
                     pan=None,
                     volume=None,
                     length=None,
                     extra_length=None):
        if type(decay) != list:
            current_decay = [decay * i for i in current_chord.get_duration()
                             ] if not fixed_decay else [
                                 decay for i in range(len(current_chord.notes))
                             ]
        else:
            current_decay = decay
        whole_length = bar_to_real_time(current_chord.bars(), bpm, 1) / 1000
        temp = current_chord.copy()
        whole_length_with_decay = mp.chord(temp.notes, [
            temp.notes[i].duration + current_decay[i]
            for i in range(len(temp.notes))
        ], temp.interval).bars()
        whole_length_with_decay = bar_to_real_time(whole_length_with_decay,
                                                   bpm, 1) / 1000

        if piece_start_time != 0:
            current_chord = copy(current_chord)
            current_chord.apply_start_time_to_changes(-piece_start_time)
        self.audio_array = []
        current_timestamps = get_timestamps(current_chord,
                                            bpm,
                                            pan=pan,
                                            volume=volume)
        current_timestamps_length = len(current_timestamps)
        current_length = 0
        if length:
            current_whole_length = length * 1000
        else:
            current_whole_length = (start_time +
                                    whole_length_with_decay) * 1000
            if extra_length:
                current_whole_length += extra_length * 1000
        current_silent_audio = AudioSegment.silent(
            duration=current_whole_length)

        for i in range(current_timestamps_length):
            current = current_timestamps[i]
            each = current.value
            if current.event_type == 'noteon' and hasattr(each, 'effects'):
                if hasattr(each, 'decay_length'):
                    current_note_decay = each.decay_length
                else:
                    current_note_decay = current_decay[len([
                        j for j in current_timestamps[:i]
                        if j.event_type == 'noteon'
                    ])]
                current_note_audio = self.export_note(
                    each,
                    duration=bar_to_real_time(each.duration, bpm, 1) / 1000,
                    decay=current_note_decay,
                    volume=each.volume,
                    track=track,
                    start_time=0,
                    sample_width=sample_width,
                    channels=channels,
                    frame_rate=frame_rate,
                    format=format,
                    get_audio=True,
                    effects=each.effects,
                    bpm=bpm)
                current_silent_audio = current_silent_audio.overlay(
                    current_note_audio,
                    position=(start_time + current.start_time) * 1000)

        self.audio_array = []
        if start_time > 0:
            self.audio_array = numpy.append(
                self.audio_array,
                self.synth.get_samples(int(frame_rate * start_time)))
        for k in range(current_timestamps_length):
            current = current_timestamps[k]
            each = current.value
            if current.event_type == 'noteon':
                if not hasattr(each, 'effects'):
                    self.synth.noteon(track, each.degree, each.volume)
            elif current.event_type == 'noteoff':
                if not hasattr(each, 'effects'):
                    self.synth.noteoff(track, each.degree)
            elif current.event_type == 'pitch_bend':
                self.synth.pitch_bend(track, each.value)
            elif current.event_type == 'message':
                if type(each) == mp.controller_event:
                    self.synth.cc(each.channel, each.controller_number,
                                  each.parameter)
                elif type(each) == mp.program_change:
                    self.synth.program_change(each.channel, each.program)
            if k != current_timestamps_length - 1:
                append_time = current_timestamps[
                    k + 1].start_time - current.start_time
                self.audio_array = numpy.append(
                    self.audio_array,
                    self.synth.get_samples(int(frame_rate * append_time)))
                current_length += append_time

        remain_times = whole_length_with_decay - whole_length
        if remain_times > 0:
            self.audio_array = numpy.append(
                self.audio_array,
                self.synth.get_samples(int(frame_rate * remain_times)))

        current_samples = fluidsynth.raw_audio_string(self.audio_array)
        current_audio = AudioSegment.from_raw(BytesIO(current_samples),
                                              sample_width=sample_width,
                                              channels=channels,
                                              frame_rate=frame_rate)
        current_silent_audio = current_silent_audio.overlay(current_audio)
        self.synth.system_reset()
        self.program_select()
        self.synth.get_samples(int(frame_rate * 1))
        if effects:
            current_silent_audio = process_effect(current_silent_audio,
                                                  effects,
                                                  bpm=bpm)
        elif check_effect(current_chord):
            current_silent_audio = process_effect(current_silent_audio,
                                                  current_chord.effects,
                                                  bpm=bpm)

        if name is None:
            name = f'Untitled.{format}'
        if not get_audio:
            current_silent_audio.export(name, format=format)
        else:
            return current_silent_audio

    def export_piece(self,
                     current_chord,
                     decay=0.5,
                     track=0,
                     sample_width=2,
                     channels=2,
                     frame_rate=44100,
                     name=None,
                     format='wav',
                     get_audio=False,
                     fixed_decay=False,
                     effects=None,
                     clear_program_change=True,
                     length=None,
                     extra_length=None,
                     track_lengths=None,
                     track_extra_lengths=None):
        decay_is_list = False
        decay_type = type(decay)
        if decay_type == list or decay_type == tuple:
            decay_is_list == True
        bpm = current_chord.tempo
        current_chord.normalize_tempo()
        if clear_program_change:
            current_chord.clear_program_change()
        if length:
            whole_duration = length * 1000
        else:
            whole_duration = current_chord.eval_time(bpm, mode='number') * 1000
            if extra_length:
                whole_duration += extra_length * 1000
        silent_audio = AudioSegment.silent(duration=whole_duration)
        for i in range(len(current_chord.tracks)):
            each = current_chord.tracks[i]
            current_start_time = bar_to_real_time(current_chord.start_times[i],
                                                  bpm, 1)
            current_pan = current_chord.pan[i]
            current_volume = current_chord.volume[i]
            current_instrument = current_chord.instruments_numbers[i]
            # instrument of a track of the piece type could be preset_num or [preset_num, bank_num, (track), (sfid)]
            if type(current_instrument) == int:
                current_instrument = [
                    current_instrument - 1, self.current_bank_num
                ]
            else:
                current_instrument = [current_instrument[0] - 1
                                      ] + current_instrument[1:]

            current_track = copy(self.current_track)
            current_sfid = copy(self.current_sfid)
            current_bank_num = copy(self.current_bank_num)
            current_preset_num = copy(self.current_preset_num)

            self.program_select(track=(current_instrument[2] if
                                       len(current_instrument) > 2 else None),
                                sfid=(current_instrument[3] if
                                      len(current_instrument) > 3 else None),
                                bank_num=current_instrument[1],
                                preset_num=current_instrument[0])

            current_audio = self.export_chord(
                each, decay if not decay_is_list else decay[i], track, 0,
                current_chord.start_times[i], sample_width, channels,
                frame_rate, None, format, bpm, True, fixed_decay, each.effects,
                current_pan, current_volume,
                None if not track_lengths else track_lengths[i],
                None if not track_extra_lengths else track_extra_lengths[i])
            silent_audio = silent_audio.overlay(current_audio,
                                                position=current_start_time)

            self.program_select(current_track, current_sfid, current_bank_num,
                                current_preset_num)

        self.synth.system_reset()
        self.program_select()
        self.synth.get_samples(int(frame_rate * 1))
        if effects:
            silent_audio = process_effect(silent_audio, effects, bpm=bpm)
        elif check_effect(current_chord):
            silent_audio = process_effect(silent_audio,
                                          current_chord.effects,
                                          bpm=bpm)

        if name is None:
            name = f'Untitled.{format}'
        if not get_audio:
            silent_audio.export(name, format=format)
        else:
            return silent_audio

    def export_midi_file(self,
                         current_chord,
                         decay=0.5,
                         track=0,
                         sample_width=2,
                         channels=2,
                         frame_rate=44100,
                         name=None,
                         format='wav',
                         get_audio=False,
                         fixed_decay=False,
                         effects=None,
                         clear_program_change=True,
                         instruments=None,
                         length=None,
                         extra_length=None,
                         track_lengths=None,
                         track_extra_lengths=None,
                         **read_args):
        current_chord = mp.read(current_chord,
                                mode='all',
                                to_piece=True,
                                **read_args)
        if instruments:
            current_chord.change_instruments(instruments)
        result = self.export_piece(current_chord, decay, track, sample_width,
                                   channels, frame_rate, name, format, True,
                                   fixed_decay, effects, clear_program_change,
                                   length, extra_length, track_lengths,
                                   track_extra_lengths)

        if name is None:
            name = f'Untitled.{format}'
        if not get_audio:
            result.export(name, format=format)
        else:
            return result

    def play_note(self,
                  note_name,
                  duration=2,
                  decay=1,
                  volume=100,
                  track=0,
                  start_time=0,
                  sample_width=2,
                  channels=2,
                  frame_rate=44100,
                  name=None,
                  format='wav',
                  effects=None,
                  bpm=80):
        current_audio = self.export_note(note_name, duration, decay, volume,
                                         track, start_time, sample_width,
                                         channels, frame_rate, name, format,
                                         True, effects, bpm)
        simpleaudio.stop_all()
        play_sound(current_audio)

    def play_chord(self,
                   current_chord,
                   decay=0.5,
                   track=0,
                   start_time=0,
                   piece_start_time=0,
                   sample_width=2,
                   channels=2,
                   frame_rate=44100,
                   name=None,
                   format='wav',
                   bpm=80,
                   fixed_decay=False,
                   effects=None,
                   pan=None,
                   volume=None,
                   length=None,
                   extra_length=None):
        current_audio = self.export_chord(current_chord, decay, track,
                                          start_time, piece_start_time,
                                          sample_width, channels, frame_rate,
                                          name, format, bpm, True, fixed_decay,
                                          effects, pan, volume, length,
                                          extra_length)
        simpleaudio.stop_all()
        play_sound(current_audio)

    def play_piece(self,
                   current_chord,
                   decay=0.5,
                   track=0,
                   sample_width=2,
                   channels=2,
                   frame_rate=44100,
                   name=None,
                   format='wav',
                   fixed_decay=False,
                   effects=None,
                   clear_program_change=True,
                   length=None,
                   extra_length=None,
                   track_lengths=None,
                   track_extra_lengths=None):
        current_audio = self.export_piece(current_chord, decay, track,
                                          sample_width, channels, frame_rate,
                                          name, format, True, fixed_decay,
                                          effects, clear_program_change,
                                          length, extra_length, track_lengths,
                                          track_extra_lengths)
        simpleaudio.stop_all()
        play_sound(current_audio)

    def play_midi_file(self,
                       current_chord,
                       decay=0.5,
                       track=0,
                       sample_width=2,
                       channels=2,
                       frame_rate=44100,
                       name=None,
                       format='wav',
                       fixed_decay=False,
                       effects=None,
                       clear_program_change=True,
                       instruments=None,
                       length=None,
                       extra_length=None,
                       track_lengths=None,
                       track_extra_lengths=None,
                       **read_args):
        current_audio = self.export_midi_file(
            current_chord, decay, track, sample_width, channels, frame_rate,
            name, format, True, fixed_decay, effects, clear_program_change,
            instruments, length, extra_length, track_lengths,
            track_extra_lengths, **read_args)
        simpleaudio.stop_all()
        play_sound(current_audio)

    def export_sound_modules(self,
                             track=None,
                             sfid=None,
                             bank_num=None,
                             preset_num=None,
                             start='A0',
                             stop='C8',
                             duration=6,
                             decay=1,
                             volume=127,
                             sample_width=2,
                             channels=2,
                             frame_rate=44100,
                             format='wav',
                             folder_name='Untitled',
                             effects=None,
                             bpm=80,
                             name=None,
                             show_full_path=False):
        try:
            os.mkdir(folder_name)
            os.chdir(folder_name)
        except:
            os.chdir(folder_name)
        current_track = copy(self.current_track)
        current_sfid = copy(self.current_sfid)
        current_bank_num = copy(self.current_bank_num)
        current_preset_num = copy(self.current_preset_num)
        self.program_select(track, sfid, bank_num, preset_num)
        if type(start) != mp.note:
            start = mp.N(start)
        if type(stop) != mp.note:
            stop = mp.N(stop)
        current_sf2 = self.file[self.sfid_list.index(self.current_sfid)]
        if not show_full_path:
            current_sf2 = os.path.basename(current_sf2)
        for i in range(start.degree, stop.degree + 1):
            current_note = str(mp.degree_to_note(i))
            if name is None:
                current_name = None
            else:
                if type(name) == list:
                    current_name = name[i] + f'.{format}'
                else:
                    current_name = name(str(current_note)) + f'.{format}'
            print(
                f'exporting {current_note} of {current_sf2}, bank {self.current_bank_num}, preset {self.current_preset_num}'
            )
            self.export_note(current_note,
                             duration=duration,
                             decay=decay,
                             volume=volume,
                             track=self.current_track,
                             sample_width=sample_width,
                             channels=channels,
                             frame_rate=frame_rate,
                             format=format,
                             effects=effects,
                             bpm=bpm,
                             name=current_name)
        print('exporting finished')
        self.program_select(current_track, current_sfid, current_bank_num,
                            current_preset_num)

    def reload(self, file):
        self.file = [file]
        self.synth = fluidsynth.Synth()
        self.sfid = self.synth.sfload(file)
        self.sfid_list = [copy(self.sfid)]
        self.program_select(preset_num=0)
        self.current_track = 0
        self.current_sfid = copy(self.sfid)
        self.current_bank_num = 0
        self.current_preset_num = 0
        self.audio_array = []

    def load(self, file):
        self.file.append(file)
        current_sfid = self.synth.sfload(file)
        self.sfid_list.append(current_sfid)
        if len(self.file) == 1:
            self.program_select()

    def unload(self, ind):
        if ind > 0:
            ind -= 1
        del self.file[ind]
        current_sfid = self.sfid_list[ind]
        self.synth.sfunload(current_sfid)
        del self.sfid_list[ind]


def process_effect(sound, effects, **kwargs):
    current_args = kwargs
    for each in effects:
        each.process_unknown_args(**current_args)
        sound = each.process(sound)
    return sound


def set_effect(sound, *effects):
    if len(effects) == 1:
        current_effect = effects[0]
        types = type(current_effect)
        if types != effect:
            if types == effect_chain:
                effects = current_effect.effects
            else:
                effects = list(current_effect)
        else:
            effects = list(effects)
    else:
        effects = list(effects)
    sound.effects = effects
    return sound


def check_effect(sound):
    return hasattr(sound, 'effects') and type(
        sound.effects) == list and sound.effects


def adsr_func(sound, attack, decay, sustain, release):
    change_db = percentage_to_db(sustain)
    result_db = sound.dBFS + change_db
    if attack > 0:
        sound = sound.fade_in(attack)
    if decay > 0:
        sound = sound.fade(to_gain=result_db, start=attack, duration=decay)
    else:
        sound = sound[:attack].append(sound[attack:] + change_db)
    if release > 0:
        sound = sound.fade_out(release)
    return sound


reverse = effect(lambda s: s.reverse(), 'reverse')
offset = effect(lambda s, bar, bpm: s[bar_to_real_time(bar, bpm, 1):],
                'offset',
                unknown_args={'bpm': None})
fade_in = effect(lambda s, duration: s.fade_in(duration), 'fade in')
fade_out = effect(lambda s, duration: s.fade_out(duration), 'fade out')
fade = effect(
    lambda s, duration1, duration2=0: s.fade_in(duration1).fade_out(duration2),
    'fade')
adsr = effect(adsr_func, 'adsr')
