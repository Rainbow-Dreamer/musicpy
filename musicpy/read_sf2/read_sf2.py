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


class sf2_loader:
    def __init__(self, file):
        self.file = [file]
        self.synth = fluidsynth.Synth()
        self.sfid = self.synth.sfload(file)
        self.program_select()
        self.current_track = 0
        self.current_bank_num = 0
        self.current_preset_num = 0
        self.audio_array = []

    def program_select(self, track=0, sfid=None, bank_num=0, preset_num=0):
        if sfid is None:
            sfid = self.sfid
        select_status = self.synth.program_select(track, sfid, bank_num,
                                                  preset_num)
        self.current_track = track
        self.current_bank_num = bank_num
        self.current_preset_num = preset_num
        return select_status

    def __lt__(self, preset_num):
        self.program_select(track=self.current_track,
                            bank_num=self.current_bank_num,
                            preset_num=preset_num)

    def __mod__(self, value):
        self.program_select(track=value[0],
                            bank_num=value[1],
                            preset_num=value[2])

    def get_current_instrument(self, num=0):
        return self.synth.channel_info(num)[3]

    def preset_name(self, sfid=None, bank_num=0, preset_num=0):
        if sfid is None:
            sfid = self.sfid
        return self.synth.sfpreset_name(sfid, bank_num, preset_num)

    def get_instrument_name(self,
                            track=0,
                            sfid=None,
                            bank_num=0,
                            preset_num=0,
                            num=0):
        current_track = copy(self.current_track)
        current_sfid = copy(self.sfid)
        current_bank_num = copy(self.current_bank_num)
        current_preset_num = copy(self.current_preset_num)
        select_status = self.program_select(track, sfid, bank_num, preset_num)
        result = self.synth.channel_info(num)[3]
        self.program_select(current_track, current_sfid, current_bank_num,
                            current_preset_num)
        if select_status != -1:
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
                    get_audio=False):
        self.audio_array = []
        current_note = mp.N(note_name)
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
        if name is None:
            name = f'{current_note}.{format}'
        if not get_audio:
            current_audio.export(name)
        else:
            return current_audio

    def export_chord(self,
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
                     get_audio=False,
                     fixed_decay=False):
        durations = [
            bar_to_real_time(i, bpm, 1) / 1000
            for i in current_chord.get_duration()
        ]
        intervals = [
            bar_to_real_time(i, bpm, 1) / 1000 for i in current_chord.interval
        ]
        volumes = current_chord.get_volume()
        if type(decay) != list:
            current_decay = [
                decay * (i / 2) for i in durations
            ] if not fixed_decay else [decay for i in range(len(durations))]
        else:
            current_decay = decay
        whole_length = bar_to_real_time(current_chord.bars(), bpm, 1) / 1000
        temp = current_chord.copy()
        whole_length_with_decay = mp.chord(temp.notes, [
            temp.notes[i].duration +
            real_time_to_bar(current_decay[i] * 1000, bpm)
            for i in range(len(temp.notes))
        ], temp.interval).bars()
        whole_length_with_decay = bar_to_real_time(whole_length_with_decay,
                                                   bpm, 1) / 1000

        self.audio_array = []
        noteoff_times = [
            sum(intervals[:i]) + durations[i]
            for i in range(len(current_chord.notes))
        ]
        noteoff_already = [False for i in range(len(noteoff_times))]
        if start_time > 0:
            self.audio_array = numpy.append(
                self.audio_array,
                self.synth.get_samples(int(frame_rate * start_time)))
        current_length = 0
        for k in range(len(current_chord.notes)):
            each = current_chord.notes[k]
            self.synth.noteon(track, each.degree, volumes[k])
            current_note_length = durations[k]
            current_interval = intervals[k]
            append_time = min(current_note_length, current_interval)
            self.audio_array = numpy.append(
                self.audio_array,
                self.synth.get_samples(int(frame_rate * append_time)))
            current_length += append_time
            for i in range(len(current_chord.notes)):
                if not noteoff_already[
                        i] and current_length >= noteoff_times[i]:
                    self.synth.noteoff(track, current_chord.notes[i].degree)
                    noteoff_already[i] = True
            if current_note_length < current_interval:
                remain_time = current_interval - current_note_length
                self.audio_array = numpy.append(
                    self.audio_array,
                    self.synth.get_samples(int(frame_rate * remain_time)))
                current_length += remain_time

        remain_times = whole_length - current_length
        if remain_times > 0:
            self.audio_array = numpy.append(
                self.audio_array,
                self.synth.get_samples(int(frame_rate * remain_times)))
        for k in range(len(noteoff_already)):
            if not noteoff_already[k]:
                self.synth.noteoff(track, current_chord.notes[k].degree)
                noteoff_already[k] = True

        self.audio_array = numpy.append(
            self.audio_array,
            self.synth.get_samples(
                int(frame_rate * (whole_length_with_decay - whole_length))))

        current_samples = fluidsynth.raw_audio_string(self.audio_array)
        current_audio = AudioSegment.from_raw(BytesIO(current_samples),
                                              sample_width=sample_width,
                                              channels=channels,
                                              frame_rate=frame_rate)

        if name is None:
            name = f'Untitled.{format}'
        if not get_audio:
            current_audio.export(name)
        else:
            return current_audio

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
                  format='wav'):
        current_audio = self.export_note(note_name,
                                         duration,
                                         decay,
                                         volume,
                                         track,
                                         start_time,
                                         sample_width,
                                         channels,
                                         frame_rate,
                                         name,
                                         format,
                                         get_audio=True)
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
                   bpm=80):
        current_audio = self.export_chord(current_chord,
                                          decay,
                                          track,
                                          start_time,
                                          sample_width,
                                          channels,
                                          frame_rate,
                                          name,
                                          format,
                                          bpm,
                                          get_audio=True)
        simpleaudio.stop_all()
        play_sound(current_audio)

    def get_all_instrument_names(self,
                                 track=0,
                                 sfid=None,
                                 bank_num=0,
                                 num=0,
                                 max_num=128):
        current_track = copy(self.current_track)
        current_sfid = copy(self.sfid)
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
        current_sfid = copy(self.sfid)
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
        self.current_bank_num = 0
        self.current_preset_num = 0
        self.audio_array = []

    def load(self, file):
        self.file.append(file)
        self.synth.sfload(file)

    def unload(self, sfid):
        del self.file[sfid - 1]
        self.synth.sfunload(sfid)
