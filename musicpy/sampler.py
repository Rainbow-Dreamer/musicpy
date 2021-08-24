import sys
import os
import threading
from ast import literal_eval

file_path = os.getcwd()
abs_path = os.path.abspath(os.path.dirname(__file__))
os.chdir(abs_path)
sys.path.append('musicpy')
sys.path.append('.')
from musicpy import *
from io import BytesIO
import math
import array
import simpleaudio
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio as play_sound
from pydub.generators import Sine, Triangle, Sawtooth, Square, WhiteNoise, Pulse
import librosa
import soundfile
from read_sf2 import read_sf2 as rs

os.chdir(file_path)

default_notedict = {
    'A0': 'A0',
    'A#0': 'A#0',
    'B0': 'B0',
    'C1': 'C1',
    'C#1': 'C#1',
    'D1': 'D1',
    'D#1': 'D#1',
    'E1': 'E1',
    'F1': 'F1',
    'F#1': 'F#1',
    'G1': 'G1',
    'G#1': 'G#1',
    'A1': 'A1',
    'A#1': 'A#1',
    'B1': 'B1',
    'C2': 'C2',
    'C#2': 'C#2',
    'D2': 'D2',
    'D#2': 'D#2',
    'E2': 'E2',
    'F2': 'F2',
    'F#2': 'F#2',
    'G2': 'G2',
    'G#2': 'G#2',
    'A2': 'A2',
    'A#2': 'A#2',
    'B2': 'B2',
    'C3': 'C3',
    'C#3': 'C#3',
    'D3': 'D3',
    'D#3': 'D#3',
    'E3': 'E3',
    'F3': 'F3',
    'F#3': 'F#3',
    'G3': 'G3',
    'G#3': 'G#3',
    'A3': 'A3',
    'A#3': 'A#3',
    'B3': 'B3',
    'C4': 'C4',
    'C#4': 'C#4',
    'D4': 'D4',
    'D#4': 'D#4',
    'E4': 'E4',
    'F4': 'F4',
    'F#4': 'F#4',
    'G4': 'G4',
    'G#4': 'G#4',
    'A4': 'A4',
    'A#4': 'A#4',
    'B4': 'B4',
    'C5': 'C5',
    'C#5': 'C#5',
    'D5': 'D5',
    'D#5': 'D#5',
    'E5': 'E5',
    'F5': 'F5',
    'F#5': 'F#5',
    'G5': 'G5',
    'G#5': 'G#5',
    'A5': 'A5',
    'A#5': 'A#5',
    'B5': 'B5',
    'C6': 'C6',
    'C#6': 'C#6',
    'D6': 'D6',
    'D#6': 'D#6',
    'E6': 'E6',
    'F6': 'F6',
    'F#6': 'F#6',
    'G6': 'G6',
    'G#6': 'G#6',
    'A6': 'A6',
    'A#6': 'A#6',
    'B6': 'B6',
    'C7': 'C7',
    'C#7': 'C#7',
    'D7': 'D7',
    'D#7': 'D#7',
    'E7': 'E7',
    'F7': 'F7',
    'F#7': 'F#7',
    'G7': 'G7',
    'G#7': 'G#7',
    'A7': 'A7',
    'A#7': 'A#7',
    'B7': 'B7',
    'C8': 'C8'
}

pygame.quit()
pygame.init()
pygame.mixer.init(44100, -16, 2, 4096)
pygame.mixer.set_num_channels(1000)


class sampler:
    def __init__(self, num=1, name=None, bpm=120):
        self.channel_num = num
        self.channel_names = []
        self.channel_sound_modules_name = []
        self.channel_sound_modules = []
        self.channel_sound_audiosegments = []
        self.channel_note_sounds_path = []
        self.channel_dict = []
        self.name = name
        self.bpm = bpm
        self.current_playing = []
        self.piece_playing = []
        self.export_fadeout_use_ratio = True
        self.export_audio_fadeout_time_ratio = 2
        self.export_audio_fadeout_time = 500
        self.play_audio_fadeout_time_ratio = 2
        self.play_audio_fadeout_time = 800
        self.play_fadeout_use_ratio = True
        for i in range(self.channel_num):
            current_channel_name = f'Channel {i+1}'
            self.channel_names.append(current_channel_name)
            self.channel_sound_modules_name.append('not loaded')
            self.channel_sound_modules.append(None)
            self.channel_sound_audiosegments.append(None)
            self.channel_note_sounds_path.append(None)
            self.channel_dict.append(copy(default_notedict))

    def add_new_channel(self, name=None):
        current_channel_name = f'Channel {self.channel_num+1}' if name is None else name
        self.channel_names.append(current_channel_name)
        self.channel_sound_modules_name.append('not loaded')
        self.channel_sound_modules.append(None)
        self.channel_sound_audiosegments.append(None)
        self.channel_note_sounds_path.append(None)
        self.channel_dict.append(copy(default_notedict))
        self.channel_num += 1

    def delete_channel(self, i):
        if i > 0:
            i -= 1
        del self.channel_names[i]
        del self.channel_sound_modules_name[i]
        del self.channel_sound_modules[i]
        del self.channel_sound_audiosegments[i]
        del self.channel_note_sounds_path[i]
        del self.channel_dict[i]
        self.channel_num -= 1

    def clear_channel(self, i):
        if i > 0:
            i -= 1
        elif i < 0:
            i += self.channel_num
        current_ind = i
        if current_ind < self.channel_num:
            self.channel_names[current_ind] = f'Channel {current_ind+1}'
            self.channel_sound_modules_name[current_ind] = 'not loaded'
            self.channel_sound_modules[current_ind] = None
            self.channel_sound_audiosegments[current_ind] = None
            self.channel_note_sounds_path[current_ind] = None
            self.channel_dict[current_ind] = copy(default_notedict)

    def clear_all_channels(self):
        self.stop_playing()
        self.channel_names.clear()
        self.channel_sound_modules_name = [
            'not loaded' for i in range(self.channel_num)
        ]
        self.channel_sound_modules.clear()
        self.channel_sound_audiosegments.clear()
        self.channel_note_sounds_path.clear()
        self.channel_dict.clear()
        self.channel_num = 0

    def set_channel_name(self, i, name):
        if i > 0:
            i -= 1
        self.channel_names[i] = name

    def __call__(self, obj, channel_num=1, bpm=None):
        return audio(obj, self, channel_num, bpm)

    def __len__(self):
        return len(self.channel_names)

    def __repr__(self):
        return '[Sampler]' + (' ' + self.name if self.name is not None else
                              '') + '\n' + '\n'.join([
                                  ' | '.join([
                                      self.channel_names[i],
                                      self.channel_sound_modules_name[i]
                                  ]) for i in range(self.channel_num)
                              ])

    def __getitem__(self, i):
        if i > 0:
            i -= 1
        return ' | '.join(
            [self.channel_names[i], self.channel_sound_modules_name[i]])

    def __delitem__(self, i):
        self.delete_channel(i)

    def load(self, current_ind, path=None, esi=None, ess=None):
        if current_ind > 0:
            current_ind -= 1
        if esi is not None and ess is not None:
            self.load_esi_file(current_ind, esi, ess)
            return
        sound_path = path
        notedict = self.channel_dict[current_ind]
        note_sounds = load(notedict, sound_path)
        note_sounds_path = load_sounds(notedict, sound_path)
        self.channel_sound_modules[current_ind] = note_sounds
        self.channel_note_sounds_path[current_ind] = note_sounds_path
        self.channel_sound_modules_name[current_ind] = sound_path
        self.channel_sound_audiosegments[current_ind] = load_audiosegments(
            notedict, sound_path)

    def export(self,
               obj,
               mode='wav',
               action='export',
               filename='Untitled.wav',
               channel_num=1,
               bpm=None):
        if channel_num > 0:
            channel_num -= 1
        if not self.channel_sound_modules:
            if action == 'export':
                print(
                    'You need at least 1 channel with loaded sound modules to export audio files'
                )
                return
            elif action == 'play':
                print(
                    'You need at least 1 channel with loaded sound modules to play'
                )
                return
            elif action == 'get':
                print('You need at least 1 channel with loaded sound modules')
                return
        if action == 'get':
            result = obj
            if type(result) == chord:
                result = ['chord', result, channel_num]
            elif type(result) == piece:
                result = ['piece', result]
            else:
                return
        else:
            result = self.get_current_musicpy_chords(obj, channel_num)
        if result is None:
            return
        types = result[0]
        current_chord = result[1]
        self.stop_playing()

        if types == 'chord':
            current_channel_num = result[2]
            current_bpm = self.bpm if bpm is None else bpm
            for each in current_chord:
                if type(each) == AudioSegment:
                    each.duration = real_time_to_bar(len(each), current_bpm)
                    each.volume = 127
            apply_fadeout_obj = self.apply_fadeout(current_chord, current_bpm)
            whole_duration = apply_fadeout_obj.eval_time(
                current_bpm, mode='number', audio_mode=1) * 1000
            current_start_times = 0
            current_chord = current_chord.only_notes(audio_mode=1)
            silent_audio = AudioSegment.silent(duration=whole_duration)
            silent_audio = self.channel_to_audio(current_chord,
                                                 current_channel_num,
                                                 silent_audio,
                                                 current_bpm,
                                                 mode=action)
            try:
                if action == 'export':
                    silent_audio.export(filename, format=mode)
                elif action == 'play':
                    play_audio(silent_audio)
                elif action == 'get':
                    return silent_audio
            except:
                return
        elif types == 'piece':
            current_name = current_chord.name
            current_bpm = current_chord.tempo
            current_start_times = current_chord.start_times
            current_pan = current_chord.pan
            current_volume = current_chord.volume
            current_tracks = current_chord.tracks
            current_channels = current_chord.channels if current_chord.channels else [
                i for i in range(len(current_chord))
            ]
            for i in range(len(current_chord.tracks)):
                each_channel = current_chord.tracks[i]
                each_channel = each_channel.only_notes(audio_mode=1)
                for each in each_channel:
                    if type(each) == AudioSegment:
                        each.duration = real_time_to_bar(
                            len(each), current_bpm)
                        each.volume = 127
                current_chord.tracks[i] = each_channel
            apply_fadeout_obj = self.apply_fadeout(current_chord, current_bpm)
            whole_duration = apply_fadeout_obj.eval_time(
                current_bpm, mode='number', audio_mode=1) * 1000
            silent_audio = AudioSegment.silent(duration=whole_duration)
            for i in range(len(current_chord)):
                silent_audio = self.channel_to_audio(current_tracks[i],
                                                     current_channels[i],
                                                     silent_audio,
                                                     current_bpm,
                                                     current_pan[i],
                                                     current_volume[i],
                                                     current_start_times[i],
                                                     mode=action)
            if check_adsr(current_chord):
                current_adsr = current_chord.adsr
                attack, decay, sustain, release = current_adsr
                change_db = percentage_to_db(sustain)
                result_db = silent_audio.dBFS + change_db
                if attack > 0:
                    silent_audio = silent_audio.fade_in(attack)
                if decay > 0:
                    silent_audio = silent_audio.fade(to_gain=result_db,
                                                     start=attack,
                                                     duration=decay)
                else:
                    silent_audio = silent_audio[:attack].append(
                        silent_audio[attack:] + change_db)
                if release > 0:
                    silent_audio = silent_audio.fade_out(release)
            if check_fade(current_chord):
                if current_chord.fade_in_time > 0:
                    silent_audio = silent_audio.fade_in(
                        current_chord.fade_in_time)
                if current_chord.fade_out_time > 0:
                    silent_audio = silent_audio.fade_out(
                        current_chord.fade_out_time)
            if check_offset(current_chord):
                silent_audio = silent_audio[
                    bar_to_real_time(current_chord.offset, current_bpm, 1):]
            if check_reverse(current_chord):
                silent_audio = silent_audio.reverse()
            try:
                if action == 'export':
                    silent_audio.export(filename, format=mode)
                elif action == 'play':
                    play_audio(silent_audio)
                elif action == 'get':
                    return silent_audio
            except:
                return

    def apply_fadeout(self, obj, bpm):
        temp = copy(obj)
        if type(temp) == chord:
            for each in temp.notes:
                if type(each) != AudioSegment:
                    if self.export_fadeout_use_ratio:
                        current_fadeout_time = each.duration * self.export_audio_fadeout_time_ratio
                    else:
                        current_fadeout_time = real_time_to_bar(
                            self.export_audio_fadeout_time, bpm)
                    each.duration += current_fadeout_time
            return temp
        elif type(temp) == piece:
            temp.tracks = [
                self.apply_fadeout(each, bpm) for each in temp.tracks
            ]
            return temp

    def channel_to_audio(self,
                         current_chord,
                         current_channel_num=0,
                         silent_audio=None,
                         current_bpm=None,
                         current_pan=None,
                         current_volume=None,
                         current_start_time=0,
                         mode='export'):
        if len(self.channel_sound_modules) <= current_channel_num:
            return
        if not self.channel_sound_modules[current_channel_num]:
            return

        apply_fadeout_obj = self.apply_fadeout(current_chord, current_bpm)
        whole_duration = apply_fadeout_obj.eval_time(
            current_bpm, mode='number', audio_mode=1) * 1000
        current_silent_audio = AudioSegment.silent(duration=whole_duration)
        current_intervals = current_chord.interval
        current_durations = current_chord.get_duration()
        current_volumes = current_chord.get_volume()
        current_dict = self.channel_dict[current_channel_num]
        current_sounds = self.channel_sound_audiosegments[current_channel_num]
        current_sound_path = self.channel_sound_modules_name[
            current_channel_num]
        current_start_time = bar_to_real_time(current_start_time, current_bpm,
                                              1)
        current_position = 0
        whole_length = len(current_chord)
        for i in range(whole_length):
            each = current_chord.notes[i]
            interval = bar_to_real_time(current_intervals[i], current_bpm, 1)
            duration = bar_to_real_time(
                current_durations[i], current_bpm,
                1) if type(each) != AudioSegment else len(each)
            volume = velocity_to_db(current_volumes[i])
            current_offset = 0
            if check_offset(each):
                current_offset = bar_to_real_time(each.offset, current_bpm, 1)
            current_fadeout_time = int(
                duration * self.export_audio_fadeout_time_ratio
            ) if self.export_fadeout_use_ratio else int(
                self.export_audio_fadeout_time)
            if type(each) == AudioSegment:
                current_sound = each[current_offset:duration]
            else:
                each_name = str(each)
                if each_name not in current_sounds:
                    each_name = str(~each)
                if each_name not in current_sounds:
                    current_position += interval
                    continue
                current_sound = current_sounds[each_name]
                if current_sound is None:
                    current_position += interval
                    continue
                current_max_time = min(len(current_sound),
                                       duration + current_fadeout_time)
                current_max_fadeout_time = min(len(current_sound),
                                               current_fadeout_time)
                current_sound = current_sound[current_offset:current_max_time]
            if check_adsr(each):
                current_adsr = each.adsr
                attack, decay, sustain, release = current_adsr
                change_db = percentage_to_db(sustain)
                result_db = current_sound.dBFS + change_db
                if attack > 0:
                    current_sound = current_sound.fade_in(attack)
                if decay > 0:
                    current_sound = current_sound.fade(to_gain=result_db,
                                                       start=attack,
                                                       duration=decay)
                else:
                    current_sound = current_sound[:attack].append(
                        current_sound[attack:] + change_db)
                if release > 0:
                    current_sound = current_sound.fade_out(release)
            if check_fade(each):
                if each.fade_in_time > 0:
                    current_sound = current_sound.fade_in(each.fade_in_time)
                if each.fade_out_time > 0:
                    current_sound = current_sound.fade_out(each.fade_out_time)
            if check_reverse(each):
                current_sound = current_sound.reverse()

            if current_fadeout_time != 0 and type(each) != AudioSegment:
                current_sound = current_sound.fade_out(
                    duration=current_max_fadeout_time)
            current_sound += volume
            current_silent_audio = current_silent_audio.overlay(
                current_sound, position=current_position)
            current_position += interval
        if current_pan:
            pan_ranges = [
                bar_to_real_time(i.start_time - 1, current_bpm, 1)
                for i in current_pan
            ]
            pan_values = [i.get_pan_value() for i in current_pan]
            audio_list = []
            for k in range(len(pan_ranges) - 1):
                current_audio = current_silent_audio[
                    pan_ranges[k]:pan_ranges[k + 1]].pan(pan_values[k])
                audio_list.append(current_audio)
            current_audio = current_silent_audio[pan_ranges[-1]:].pan(
                pan_values[-1])
            audio_list.append(current_audio)
            first_audio = audio_list[0]
            for each in audio_list[1:]:
                first_audio = first_audio.append(each, crossfade=0)
            current_silent_audio = first_audio

        if current_volume:
            volume_ranges = [
                bar_to_real_time(i.start_time - 1, current_bpm, 1)
                for i in current_volume
            ]
            volume_values = [
                percentage_to_db(i.value_percentage) for i in current_volume
            ]
            audio_list = []
            for k in range(len(volume_ranges) - 1):
                current_audio = current_silent_audio[
                    volume_ranges[k]:volume_ranges[k + 1]] + volume_values[k]
                audio_list.append(current_audio)
            current_audio = current_silent_audio[
                volume_ranges[-1]:] + volume_values[-1]
            audio_list.append(current_audio)
            first_audio = audio_list[0]
            for each in audio_list[1:]:
                first_audio = first_audio.append(each, crossfade=0)
            current_silent_audio = first_audio
        if check_adsr(current_chord):
            current_adsr = current_chord.adsr
            attack, decay, sustain, release = current_adsr
            change_db = percentage_to_db(sustain)
            result_db = current_silent_audio.dBFS + change_db
            if attack > 0:
                current_silent_audio = current_silent_audio.fade_in(attack)
            if decay > 0:
                current_silent_audio = current_silent_audio.fade(
                    to_gain=result_db, start=attack, duration=decay)
            else:
                current_silent_audio = current_silent_audio[:attack].append(
                    current_silent_audio[attack:] + change_db)
            if release > 0:
                current_silent_audio = current_silent_audio.fade_out(release)
        if check_fade(current_chord):
            if current_chord.fade_in_time > 0:
                current_silent_audio = current_silent_audio.fade_in(
                    current_chord.fade_in_time)
            if current_chord.fade_out_time > 0:
                current_silent_audio = current_silent_audio.fade_out(
                    current_chord.fade_out_time)
        if check_offset(current_chord):
            current_silent_audio = current_silent_audio[
                bar_to_real_time(current_chord.offset, current_bpm, 1):]
        if check_reverse(current_chord):
            current_silent_audio = current_silent_audio.reverse()
        silent_audio = silent_audio.overlay(current_silent_audio,
                                            position=current_start_time)
        return silent_audio

    def export_midi_file(self, obj, filename, channel_num=0):
        result = self.get_current_musicpy_chords(obj, channel_num)
        if result is None:
            return
        current_chord = result[1]
        self.stop_playing()
        write(filename, current_chord, self.bpm)

    def get_current_musicpy_chords(self, current_chord, current_channel_num=0):
        current_bpm = self.bpm
        if type(current_chord) == note:
            has_reverse = check_reverse(current_chord)
            has_offset = check_offset(current_chord)
            current_chord = chord([current_chord])
            if has_reverse:
                current_chord.reverse_audio = True
            if has_offset:
                current_chord.offset = has_offset
        elif type(current_chord) == list and all(
                type(i) == chord for i in current_chord):
            current_chord = concat(current_chord, mode='|')
        if type(current_chord) == chord:
            return 'chord', current_chord, current_channel_num
        if type(current_chord) == track:
            has_reverse = check_reverse(current_chord)
            has_offset = check_offset(current_chord)
            current_chord = build(
                current_chord,
                bpm=current_chord.tempo
                if current_chord.tempo is not None else current_bpm,
                name=current_chord.name)
            if has_reverse:
                current_chord.reverse_audio = True
            if has_offset:
                current_chord.offset = has_offset
        if type(current_chord) == piece:
            current_bpm = current_chord.tempo
            current_start_times = current_chord.start_times
            return 'piece', current_chord

    def stop_playing(self):
        pygame.mixer.stop()
        if self.current_playing:
            for each in self.current_playing:
                each.cancel()
            self.current_playing.clear()
        if self.piece_playing:
            for each in self.piece_playing:
                each.cancel()
            self.piece_playing.clear()
        try:
            simpleaudio.stop_all()
        except:
            pass
        try:
            pygame.mixer.music.stop()
        except:
            pass

    def load_channel_settings(self, channel_num=1, text=None, path=None):
        if text is None:
            with open(path, encoding='utf-8-sig') as f:
                data = f.read()
        else:
            data = text
        data = data.split('\n')
        current_dict = self.channel_dict[channel_num]
        for each in data:
            if ',' in each:
                current_key, current_value = each.split(',')
                current_dict[current_key] = current_value
        if text is None:
            self.reload_channel_sounds(channel_num)

    def load_esi_file(self, channel_num, file_path, split_file_path):
        abs_path = os.getcwd()
        with open(split_file_path, 'r', encoding='utf-8-sig') as f:
            unzip = f.read()
        unzip_ind, filenames = literal_eval(unzip)
        sound_files = []
        channel_settings = None
        with open(file_path, 'rb') as file:
            for each in range(len(filenames)):
                current_filename = filenames[each]
                current_length = unzip_ind[each]
                current = file.read(current_length)
                if current_filename[-4:] != '.txt':
                    sound_files.append(current)
                else:
                    channel_settings = current.decode('utf-8-sig').replace(
                        '\r', '')
        filenames = [i for i in filenames if i[-4:] != '.txt']
        sound_files_pygame = []
        for each in sound_files:
            with open('temp', 'wb') as f:
                f.write(each)
            sound_files_pygame.append(pygame.mixer.Sound('temp'))
        os.remove('temp')
        sound_files_audio = [
            AudioSegment.from_file(
                BytesIO(sound_files[i]),
                format=filenames[i][filenames[i].rfind('.') + 1:])
            for i in range(len(sound_files))
        ]
        self.channel_dict[channel_num] = copy(default_notedict)
        if channel_settings is not None:
            self.load_channel_settings(channel_num, channel_settings)
        current_dict = self.channel_dict[channel_num]
        filenames = [i[:i.rfind('.')] for i in filenames]
        result_pygame = {
            filenames[i]: sound_files_pygame[i]
            for i in range(len(sound_files))
        }
        result_audio = {
            filenames[i]: sound_files_audio[i]
            for i in range(len(sound_files))
        }
        note_sounds = {
            i: (result_pygame[current_dict[i]]
                if current_dict[i] in result_pygame else None)
            for i in current_dict
        }
        self.channel_sound_modules[channel_num] = note_sounds

        self.channel_sound_audiosegments[channel_num] = {
            i: (result_audio[current_dict[i]]
                if current_dict[i] in result_audio else None)
            for i in current_dict
        }

    def reload_channel_sounds(self, current_ind):
        try:
            sound_path = self.channel_sound_modules_name[current_ind]
            notedict = self.channel_dict[current_ind]
            note_sounds = load(notedict, sound_path)
            note_sounds_path = load_sounds(notedict, sound_path)
            self.channel_sound_modules[current_ind] = note_sounds
            self.channel_sound_audiosegments[current_ind] = load_audiosegments(
                notedict, sound_path)
            self.channel_note_sounds_path[current_ind] = note_sounds_path
        except Exception as e:
            print(str(e))

    def play_note_func(self, name, duration, volume, channel=0):
        note_sounds_path = self.channel_note_sounds_path[channel]
        note_sounds = self.channel_sound_modules[channel]
        if name in note_sounds:
            current_sound = note_sounds[name]
            if current_sound:
                current_sound.set_volume(volume / 127)
                duration_time = bar_to_real_time(duration, self.bpm, 1)
                current_sound.play()
                current_fadeout_time = int(
                    duration_time * self.play_audio_fadeout_time_ratio
                ) if self.play_fadeout_use_ratio else int(
                    self.play_audio_fadeout_time)
                current_id = threading.Timer(
                    duration_time / 1000,
                    lambda: current_sound.fadeout(current_fadeout_time)
                    if current_fadeout_time != 0 else current_sound.stop())
                current_id.start()
                self.current_playing.append(current_id)

    def play(self, current_chord, channel_num=1, bpm=None):
        if not self.channel_sound_modules:
            return
        self.stop_playing()
        if channel_num > 0:
            channel_num -= 1
        current_channel_num = channel_num
        current_bpm = self.bpm if bpm is None else bpm
        self.play_musicpy_sounds(current_chord, current_channel_num,
                                 current_bpm)

    def play_musicpy_sounds(self,
                            current_chord,
                            current_channel_num=None,
                            bpm=None):
        if type(current_chord) == note:
            has_reverse = check_reverse(current_chord)
            has_offset = check_offset(current_chord)
            current_chord = chord([current_chord])
            if has_reverse:
                current_chord.reverse_audio = True
            if has_offset:
                current_chord.offset = has_offset
        elif type(current_chord) == list and all(
                type(i) == chord for i in current_chord):
            current_chord = concat(current_chord, mode='|')
        if type(current_chord) == chord:
            if check_special(current_chord):
                self.export(current_chord,
                            action='play',
                            channel_num=current_channel_num)
            else:
                self.play_channel(current_chord, current_channel_num, bpm)
        elif type(current_chord) == track:
            has_reverse = check_reverse(current_chord)
            has_offset = check_offset(current_chord)
            current_chord = build(current_chord,
                                  bpm=current_chord.tempo
                                  if current_chord.tempo is not None else bpm,
                                  name=current_chord.name)
            if has_reverse:
                current_chord.reverse_audio = True
            if has_offset:
                current_chord.offset = has_offset
        if type(current_chord) == piece:
            if check_special(current_chord):
                self.export(current_chord, action='play')
                return
            current_tracks = current_chord.tracks
            current_channel_nums = current_chord.channels if current_chord.channels else [
                i for i in range(len(current_chord))
            ]
            bpm = current_chord.tempo
            current_start_times = current_chord.start_times
            for each in range(len(current_chord)):
                current_id = threading.Timer(
                    bar_to_real_time(current_start_times[each], bpm, 1) / 1000,
                    lambda each=each, bpm=bpm: self.play_channel(
                        current_tracks[each], current_channel_nums[each], bpm))
                current_id.start()
                self.piece_playing.append(current_id)

    def play_channel(self, current_chord, current_channel_num=0, bpm=None):
        if not self.channel_sound_modules[current_channel_num]:
            return
        current_chord = current_chord.only_notes()
        current_intervals = current_chord.interval
        current_durations = current_chord.get_duration()
        current_volumes = current_chord.get_volume()
        current_time = 0
        for i in range(len(current_chord)):
            each = current_chord.notes[i]
            if i == 0:
                self.play_note_func(f'{standardize_note(each.name)}{each.num}',
                                    current_durations[i], current_volumes[i],
                                    current_channel_num)
            else:
                duration = current_durations[i]
                volume = current_volumes[i]
                current_time += bar_to_real_time(current_intervals[i - 1], bpm,
                                                 1)
                current_id = threading.Timer(
                    current_time / 1000,
                    lambda each=each, duration=duration, volume=volume: self.
                    play_note_func(f'{standardize_note(each.name)}{each.num}',
                                   duration, volume, current_channel_num))
                self.current_playing.append(current_id)
                current_id.start()


class pitch:
    def __init__(self, path, note='C5', format=None):
        self.note = N(note) if type(note) == str else note
        audio_load = False
        if type(path) != AudioSegment:
            self.file_path = path
            current_format = path[path.rfind('.') +
                                  1:] if format is None else format
            try:
                self.sounds = AudioSegment.from_file(path,
                                                     format=current_format)

            except:
                with open(path, 'rb') as f:
                    current_data = f.read()
                current_file = BytesIO(current_data)
                self.sounds = AudioSegment.from_file(current_file,
                                                     format=current_format)
                os.chdir(abs_path)
                self.sounds.export('scripts/temp.wav', format='wav')
                self.audio = librosa.load('scripts/temp.wav',
                                          sr=self.sounds.frame_rate)[0]
                os.remove('scripts/temp.wav')
                audio_load = True

        else:
            self.sounds = path
            self.file_path = None
        self.sample_rate = self.sounds.frame_rate
        self.channels = self.sounds.channels
        self.sample_width = self.sounds.sample_width
        if not audio_load:
            self.audio = librosa.load(path, sr=self.sample_rate)[0]

    def pitch_shift(self, semitones=1, mode='librosa'):
        if mode == 'librosa':
            data_shifted = librosa.effects.pitch_shift(self.audio,
                                                       self.sample_rate,
                                                       n_steps=semitones)
            current_sound = BytesIO()
            soundfile.write(current_sound,
                            data_shifted,
                            self.sample_rate,
                            format='wav')
            result = AudioSegment.from_wav(current_sound)
        elif mode == 'pydub':
            new_sample_rate = int(self.sample_rate * (2**(semitones / 12)))
            result = self.sounds._spawn(
                self.sounds.raw_data,
                overrides={'frame_rate': new_sample_rate})
        return result

    def np_array_to_audio(self, np, sample_rate):
        current_sound = BytesIO()
        soundfile.write(current_sound, np, sample_rate, format='wav')
        result = AudioSegment.from_wav(current_sound)
        return result

    def __add__(self, semitones):
        return self.pitch_shift(semitones)

    def __sub__(self, semitones):
        return self.pitch_shift(-semitones)

    def get(self, pitch):
        if type(pitch) != note:
            pitch = N(pitch)
        semitones = pitch.degree - self.note.degree
        return self + semitones

    def set_note(self, pitch):
        if type(pitch) != note:
            pitch = N(pitch)
        self.note = pitch

    def generate_dict(self, start='A0', end='C8', mode='librosa'):
        if type(start) != note:
            start = N(start)
        if type(end) != note:
            end = N(end)
        degree = self.note.degree
        result = {}
        for i in range(end.degree - start.degree + 1):
            current_note_name = str(start + i)
            print(f'Converting note: {current_note_name} ...', flush=True)
            result[current_note_name] = self.pitch_shift(start.degree + i -
                                                         degree,
                                                         mode=mode)
        return result

    def export_sound_files(self,
                           path='.',
                           folder_name=None,
                           start='A0',
                           end='C8',
                           format='wav',
                           mode='librosa'):
        if folder_name is None:
            folder_name = 'Untitled'
        os.chdir(path)
        if folder_name not in os.listdir():
            os.mkdir(folder_name)
        os.chdir(folder_name)
        current_dict = self.generate_dict(start, end, mode=mode)
        for each in current_dict:
            print(f'Exporting {each} ...', flush=True)
            current_dict[each].export(f'{each}.{format}', format=format)
        print('finished')
        os.chdir(abs_path)

    def __len__(self):
        return len(self.sounds)

    def play(self):
        play_audio(self)

    def stop(self):
        simpleaudio.stop_all()


class sound:
    def __init__(self, path, format=None):
        if type(path) != AudioSegment:
            self.sounds = AudioSegment.from_file(
                path,
                format=path[path.rfind('.') +
                            1:] if format is None else format)
            self.file_path = path
        else:
            self.sounds = path
            self.file_path = None
        self.sample_rate = self.sounds.frame_rate
        self.channels = self.sounds.channels
        self.sample_width = self.sounds.sample_width

    def __len__(self):
        return len(self.sounds)

    def play(self):
        play_audio(self)

    def stop(self):
        simpleaudio.stop_all()


def play_audio(audio):
    if type(audio) in [pitch, sound]:
        play_sound(audio.sounds)
    else:
        play_sound(audio)


def stop(audio=None):
    if type(audio) in [pitch, sound]:
        audio.sounds.stop()
    else:
        simpleaudio.stop_all()


def load(dic, path):
    wavedict = {}
    files = os.listdir(path)
    filenames_only = [i[:i.rfind('.')] for i in files]
    current_path = path + '/'
    for i in dic:
        try:
            current_sound = pygame.mixer.Sound(
                current_path + files[filenames_only.index(dic[i])])
            wavedict[i] = current_sound
        except:
            wavedict[i] = None
    return wavedict


def load_audiosegments(current_dict, current_sound_path):
    current_sounds = {}
    current_sound_files = os.listdir(current_sound_path)
    current_sound_path += '/'
    current_sound_filenames = [i[:i.rfind('.')] for i in current_sound_files]
    for i in current_dict:
        current_sound_obj = current_dict[i]
        if current_sound_obj in current_sound_filenames:
            current_filename = current_sound_files[
                current_sound_filenames.index(current_sound_obj)]
            current_sound_obj_path = current_sound_path + current_filename
            current_sound_format = current_filename[current_filename.
                                                    rfind('.') + 1:]
            try:
                current_sounds[i] = AudioSegment.from_file(
                    current_sound_obj_path, format=current_sound_format)
            except:
                with open(current_sound_obj_path, 'rb') as f:
                    current_data = f.read()
                current_sounds[i] = AudioSegment.from_file(
                    BytesIO(current_data), format=current_sound_format)
        else:
            current_sounds[i] = None
    return current_sounds


def load_sounds(dic, current_path):
    files = os.listdir(current_path)
    current_sound_filenames = [i[:i.rfind('.')] for i in files]
    filenames_only = [i[:i.rfind('.')] for i in files]
    current_path += '/'
    wavedict = {}
    for i in dic:
        try:
            wavedict[i] = current_path + files[filenames_only.index(dic[i])]
        except:
            wavedict[i] = None
    return wavedict


def standardize_note(i):
    if i in standard_dict:
        i = standard_dict[i]
    return i


def velocity_to_db(vol):
    if vol == 0:
        return -100
    return math.log(vol / 127, 10) * 20


def percentage_to_db(vol):
    if vol == 0:
        return -100
    return math.log(abs(vol / 100), 10) * 20


def bar_to_real_time(bar, bpm, mode=0):
    # return time in ms
    return int(
        (60000 / bpm) * (bar * 4)) if mode == 0 else (60000 / bpm) * (bar * 4)


def real_time_to_bar(time, bpm):
    return (time / (60000 / bpm)) / 4


def reverse(sound):
    sound.reverse_audio = True
    return sound


def offset(sound, bar):
    sound.offset = bar
    return sound


def fade_in(sound, duration):
    sound.fade_in_time = duration
    if not hasattr(sound, 'fade_out_time'):
        sound.fade_out_time = 0
    return sound


def fade_out(sound, duration):
    sound.fade_out_time = duration
    if not hasattr(sound, 'fade_in_time'):
        sound.fade_in_time = 0
    return sound


def fade(sound, fade_in, fade_out=0):
    sound.fade_in_time = fade_in
    sound.fade_out_time = fade_out
    return sound


def adsr(sound, attack, decay, sustain, release):
    sound.adsr = [attack, decay, sustain, release]
    return sound


ADSR = adsr


def check_reverse(sound):
    return hasattr(sound, 'reverse_audio')


def check_offset(sound):
    return hasattr(sound, 'offset')


def check_reverse_all(sound):
    types = type(sound)
    if types == chord:
        return check_reverse(sound) or any(check_reverse(i) for i in sound)
    elif types == piece:
        return check_reverse(sound) or any(
            check_reverse_all(i) for i in sound.tracks)


def check_offset_all(sound):
    types = type(sound)
    if types == chord:
        return check_offset(sound) or any(check_offset(i) for i in sound)
    elif types == piece:
        return check_offset(sound) or any(
            check_offset_all(i) for i in sound.tracks)


def check_pan_or_volume(sound):
    return type(sound) == piece and (any(i for i in sound.pan)
                                     or any(i for i in sound.volume))


def check_fade(sound):
    return hasattr(sound, 'fade_in_time') or hasattr(sound, 'fade_out_time')


def check_fade_all(sound):
    types = type(sound)
    if types == chord:
        return check_fade(sound) or any(check_fade(i) for i in sound)
    elif types == piece:
        return check_fade(sound) or any(
            check_fade_all(i) for i in sound.tracks)


def check_adsr(sound):
    return hasattr(sound, 'adsr')


def check_adsr_all(sound):
    types = type(sound)
    if types == chord:
        return check_adsr(sound) or any(check_adsr(i) for i in sound)
    elif types == piece:
        return check_adsr(sound) or any(
            check_adsr_all(i) for i in sound.tracks)


def has_audio(sound):
    types = type(sound)
    if types == chord:
        return any(type(i) == AudioSegment for i in sound.notes)
    elif types == piece:
        return any(has_audio(i) for i in sound.tracks)


def check_special(sound):
    return check_pan_or_volume(sound) or check_reverse_all(
        sound) or check_offset_all(sound) or check_fade_all(
            sound) or check_adsr_all(sound) or has_audio(sound)


def sine(freq=440, duration=1000, volume=0):
    if type(freq) in [str, note]:
        freq = get_freq(freq)
    return Sine(freq).to_audio_segment(duration, volume)


def triangle(freq=440, duration=1000, volume=0):
    if type(freq) in [str, note]:
        freq = get_freq(freq)
    return Triangle(freq).to_audio_segment(duration, volume)


def sawtooth(freq=440, duration=1000, volume=0):
    if type(freq) in [str, note]:
        freq = get_freq(freq)
    return Sawtooth(freq).to_audio_segment(duration, volume)


def square(freq=440, duration=1000, volume=0):
    if type(freq) in [str, note]:
        freq = get_freq(freq)
    return Square(freq).to_audio_segment(duration, volume)


def white_noise(duration=1000, volume=0):
    return WhiteNoise().to_audio_segment(duration, volume)


def pulse(freq=440, duty_cycle=0.5, duration=1000, volume=0):
    return Pulse(freq, duty_cycle).to_audio_segment(duration, volume)


def get_wave(sound, mode='sine', bpm=120, volume=None):
    # volume: percentage, from 0% to 100%
    temp = copy(sound)
    if volume is None:
        volume = [velocity_to_db(i) for i in temp.get_volume()]
    else:
        volume = [volume for i in range(len(temp))
                  ] if type(volume) != list else volume
        volume = [percentage_to_db(i) for i in volume]
    for i in range(1, len(temp) + 1):
        current_note = temp[i]
        if type(current_note) == note:
            if mode == 'sine':
                temp[i] = sine(get_freq(current_note),
                               bar_to_real_time(current_note.duration, bpm, 1),
                               volume[i - 1])
            elif mode == 'triangle':
                temp[i] = triangle(
                    get_freq(current_note),
                    bar_to_real_time(current_note.duration, bpm, 1),
                    volume[i - 1])
            elif mode == 'sawtooth':
                temp[i] = sawtooth(
                    get_freq(current_note),
                    bar_to_real_time(current_note.duration, bpm, 1),
                    volume[i - 1])
            elif mode == 'square':
                temp[i] = square(
                    get_freq(current_note),
                    bar_to_real_time(current_note.duration, bpm, 1),
                    volume[i - 1])
            else:
                temp[i] = mode(get_freq(current_note),
                               bar_to_real_time(current_note.duration, bpm, 1),
                               volume[i - 1])
    return temp


def audio(obj, sampler, channel_num=1, bpm=None):
    if type(obj) == note:
        obj = chord([obj])
    elif type(obj) == track:
        obj = build(obj, bpm=obj.tempo, name=obj.name)
    result = sampler.export(obj,
                            action='get',
                            channel_num=channel_num,
                            bpm=bpm)
    return result


def audio_chord(audio_list, interval=0, duration=1 / 4, volume=127):
    result = chord([])
    result.notes = audio_list
    result.interval = interval if type(interval) == list else [
        interval for i in range(len(audio_list))
    ]
    durations = duration if type(duration) == list else [
        duration for i in range(len(audio_list))
    ]
    volumes = volume if type(volume) == list else [
        volume for i in range(len(audio_list))
    ]
    for i in range(len(result.notes)):
        result.notes[i].duration = durations[i]
        result.notes[i].volume = volumes[i]
    return result


def make_esi(file_path, name='untitled'):
    abs_path = os.getcwd()
    filenames = os.listdir(file_path)
    if not filenames:
        print('There are no sound files to make ESI files')
        return
    length_list = []
    with open(f'{name}.esi', 'wb') as file:
        os.chdir(file_path)
        for t in filenames:
            with open(t, 'rb') as f:
                each = f.read()
                length_list.append(len(each))
                file.write(each)
    os.chdir(abs_path)
    with open(f'{name}.ess', 'w', encoding='utf-8-sig') as f:
        f.write(
            str(length_list) + ',' +
            str([os.path.basename(i) for i in filenames]))
    print(
        f'Successfully made ESI file and ESS file: {name}.esi and {name}.ess')


def unzip_esi(file_path, split_file_path, folder_name=None):
    with open(split_file_path, 'r', encoding='utf-8-sig') as f:
        unzip = f.read()
    unzip_ind, filenames = literal_eval(unzip)
    if folder_name is None:
        folder_name = os.path.basename(file_path)
        folder_name = folder_name[:folder_name.rfind('.')]
    if folder_name not in os.listdir():
        os.mkdir(folder_name)
    with open(file_path, 'rb') as file:
        os.chdir(folder_name)
        for each in range(len(filenames)):
            current_filename = filenames[each]
            print(f'Currently unzip file {current_filename}')
            current_length = unzip_ind[each]
            with open(current_filename, 'wb') as f:
                f.write(file.read(current_length))
    print(f'Unzip {os.path.basename(file_path)} successfully')