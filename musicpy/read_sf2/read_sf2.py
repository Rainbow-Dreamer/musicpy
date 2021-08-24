import os
import sys

abs_path = os.path.abspath(os.path.dirname(__file__))
os.chdir(abs_path)
os.environ['PATH'] += os.pathsep + abs_path
os.chdir('../..')
sys.path.append('.')

import musicpy.musicpy as mp

os.chdir('musicpy')

import simpleaudio
from pydub.playback import _play_with_simpleaudio as play_sound

os.chdir('read_sf2')

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
    return math.log(vol / 127, 10) * 20


def percentage_to_db(vol):
    if vol == 0:
        return -100
    return math.log(abs(vol / 100), 10) * 20


def process_effect(current_audio, other_effects):
    for each in other_effects:
        current_type = each.effect
        current_values = each.value
        if current_type == 'reverse':
            current_audio = current_audio.reverse()
        elif current_type == 'offset':
            current_audio = current_audio[current_values:]
        elif current_type == 'fade':
            fade_in_time, fade_out_time = current_values
            if fade_in_time > 0:
                current_audio = current_audio.fade_in(fade_in_time)
            if fade_out_time > 0:
                current_audio = current_audio.fade_out(fade_out_time)
        elif current_type == 'adsr':
            attack, decay, sustain, release = current_values
            change_db = percentage_to_db(sustain)
            result_db = current_audio.dBFS + change_db
            if attack > 0:
                current_audio = current_audio.fade_in(attack)
            if decay > 0:
                current_audio = current_audio.fade(to_gain=result_db,
                                                   start=attack,
                                                   duration=decay)
            else:
                current_audio = current_audio[:attack].append(
                    current_audio[attack:] + change_db)
            if release > 0:
                current_audio = current_audio.fade_out(release)
        return current_audio


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
            general_event('other',
                          bar_to_real_time(i.time / 4, bpm, 1) / 1000, i)
            for i in current_chord.other_messages
        ]
        result += other_messages_part
    if pan:
        pan_part = [
            general_event(
                'other',
                bar_to_real_time(i.start_time - 1, bpm, 1) / 1000,
                mp.controller_event(controller_number=10, parameter=i.value))
            for i in pan
        ]
        result += pan_part
    if volume:
        volume_part = [
            general_event(
                'other',
                bar_to_real_time(i.start_time - 1, bpm, 1) / 1000,
                mp.controller_event(controller_number=7, parameter=i.value))
            for i in volume
        ]
        result += volume_part
    result.sort(key=lambda s: s.start_time)
    return result


class effect:
    def __init__(self, effect, value=None):
        self.effect = effect
        self.value = value

    def __repr__(self):
        return f'[effect] type: {self.effect}  value: {self.value}'


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
    def __init__(self, file):
        self.file = [file]
        self.synth = fluidsynth.Synth()
        self.sfid = self.synth.sfload(file)
        self.current_track = 0
        self.current_sfid = copy(self.sfid)
        self.current_bank_num = 0
        self.current_preset_num = 0
        self.program_select()
        self.audio_array = []

    def program_select(self,
                       track=None,
                       sfid=None,
                       bank_num=None,
                       preset_num=None):
        if track is None:
            track = self.current_track
        if sfid is None:
            sfid = self.current_sfid
        if bank_num is None:
            bank_num = self.current_bank_num
        if preset_num is None:
            preset_num = self.current_preset_num
        select_status = self.synth.program_select(track, sfid, bank_num,
                                                  preset_num)
        self.current_track = track
        self.current_sfid = sfid
        self.current_bank_num = bank_num
        self.current_preset_num = preset_num
        return select_status

    def __lt__(self, preset_num):
        self.program_select(preset_num=preset_num)

    def __mod__(self, value):
        self.program_select(track=value[0],
                            bank_num=value[1],
                            preset_num=value[2])

    def get_current_instrument(self, num=0):
        return self.synth.channel_info(num)[3]

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
                                 track=0,
                                 sfid=None,
                                 bank_num=0,
                                 num=0,
                                 max_num=128):
        current_track = copy(self.current_track)
        current_sfid = copy(self.current_sfid)
        current_bank_num = copy(self.current_bank_num)
        current_preset_num = copy(self.current_preset_num)
        preset_num = 0
        select_status = self.program_select(track, sfid, bank_num, preset_num)
        result = [self.synth.channel_info(num)[3]]
        for preset_num in range(1, max_num):
            preset_num += 1
            select_status = self.program_select(track, sfid, bank_num,
                                                preset_num)
            if select_status != -1:
                result.append(self.synth.channel_info(num)[3])
        self.program_select(current_track, current_sfid, current_bank_num,
                            current_preset_num)
        return result

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
                    other_effects=None):
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
        if other_effects:
            current_audio = process_effect(current_audio, other_effects)
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
                     sample_width=2,
                     channels=2,
                     frame_rate=44100,
                     name=None,
                     format='wav',
                     bpm=80,
                     get_audio=False,
                     fixed_decay=False,
                     other_effects=None):
        if type(decay) != list:
            current_decay = [
                decay * i for i in current_chord.get_duration()
            ] if not fixed_decay else [
                decay for i in range(len(current_chord.get_duration()))
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

        self.audio_array = []
        current_timestamps = get_timestamps(current_chord, bpm)
        current_timestamps_length = len(current_timestamps)
        current_length = 0
        current_silent_audio = AudioSegment.silent(
            duration=(start_time + whole_length_with_decay) * 1000)

        for i in range(current_timestamps_length):
            current = current_timestamps[i]
            each = current.value
            if current.event_type == 'noteon' and hasattr(
                    each, 'other_effects'):
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
                    other_effects=each.other_effects)
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
                if not hasattr(each, 'other_effects'):
                    self.synth.noteon(track, each.degree, each.volume)
            elif current.event_type == 'noteoff':
                if not hasattr(each, 'other_effects'):
                    self.synth.noteoff(track, each.degree)
            elif current.event_type == 'pitch_bend':
                self.synth.pitch_bend(track, each.value)
            elif current.event_type == 'other':
                if type(current.value) == mp.controller_event:
                    self.synth.cc(each.channel, each.controller_number,
                                  each.parameter)
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
        if other_effects:
            current_silent_audio = process_effect(current_silent_audio,
                                                  other_effects)

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
                     start_time=0,
                     sample_width=2,
                     channels=2,
                     frame_rate=44100,
                     name=None,
                     format='wav',
                     get_audio=False,
                     fixed_decay=False,
                     other_effects=None):
        pass

    def export_midi_file(self,
                         current_chord,
                         decay=0.5,
                         track=0,
                         start_time=0,
                         sample_width=2,
                         channels=2,
                         frame_rate=44100,
                         name=None,
                         format='wav',
                         get_audio=False,
                         fixed_decay=False,
                         other_effects=None):
        pass

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
                  other_effects=None):
        current_audio = self.export_note(note_name, duration, decay, volume,
                                         track, start_time, sample_width,
                                         channels, frame_rate, name, format,
                                         True, other_effects)
        simpleaudio.stop_all()
        play_sound(current_audio)

    def play_chord(self,
                   current_chord,
                   decay=1,
                   track=0,
                   start_time=0,
                   sample_width=2,
                   channels=2,
                   frame_rate=44100,
                   name=None,
                   format='wav',
                   bpm=80,
                   fixed_decay=False,
                   other_effects=None):
        current_audio = self.export_chord(current_chord, decay, track,
                                          start_time, sample_width, channels,
                                          frame_rate, name, format, bpm, True,
                                          fixed_decay, other_effects)
        simpleaudio.stop_all()
        play_sound(current_audio)

    def play_piece(self,
                   current_chord,
                   decay=0.5,
                   track=0,
                   start_time=0,
                   sample_width=2,
                   channels=2,
                   frame_rate=44100,
                   name=None,
                   format='wav',
                   fixed_decay=False,
                   other_effects=None):
        current_audio = self.export_piece(current_chord, decay, track,
                                          start_time, sample_width, channels,
                                          frame_rate, name, format, True,
                                          fixed_decay, other_effects)
        simpleaudio.stop_all()
        play_sound(current_audio)

    def play_midi_file(self,
                       current_chord,
                       decay=0.5,
                       track=0,
                       start_time=0,
                       sample_width=2,
                       channels=2,
                       frame_rate=44100,
                       name=None,
                       format='wav',
                       fixed_decay=False,
                       other_effects=None):
        current_audio = self.export_midi_file(current_chord, decay, track,
                                              start_time, sample_width,
                                              channels, frame_rate, name,
                                              format, True, fixed_decay,
                                              other_effects)
        simpleaudio.stop_all()
        play_sound(current_audio)

    def export_sound_modules(self,
                             track=0,
                             sfid=None,
                             bank_num=0,
                             preset_num=0,
                             start='A0',
                             stop='C8',
                             duration=6,
                             decay=1,
                             volume=127,
                             sample_width=2,
                             channels=2,
                             frame_rate=44100,
                             format='wav',
                             folder_name='Untitled'):
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
        start = mp.N(start)
        stop = mp.N(stop)
        current_sf2 = self.file[sfid - 1]
        for i in range(start.degree, stop.degree + 1):
            current_note = str(mp.degree_to_note(i))
            print(
                f'exporting {current_note} of {current_sf2}, bank {bank_num}, presset {preset_num} ...'
            )
            self.export_note(current_note,
                             duration=duration,
                             decay=decay,
                             volume=volume,
                             track=track,
                             sample_width=sample_width,
                             channels=channels,
                             frame_rate=frame_rate,
                             format=format)
        print('exporting finished')
        self.program_select(current_track, current_sfid, current_bank_num,
                            current_preset_num)

    def reload(self, file):
        self.file = [file]
        self.synth = fluidsynth.Synth()
        self.sfid = self.synth.sfload(file)
        self.program_select(preset_num=0)
        self.current_track = 0
        self.current_sfid = copy(self.sfid)
        self.current_bank_num = 0
        self.current_preset_num = 0
        self.audio_array = []

    def load(self, file):
        self.file.append(file)
        self.synth.sfload(file)

    def unload(self, sfid):
        del self.file[sfid - 1]
        self.synth.sfunload(sfid)
