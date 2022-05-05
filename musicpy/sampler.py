import os
import threading
from musicpy import *
from io import BytesIO
import math
from pydub import AudioSegment
from pydub.generators import Sine, Triangle, Sawtooth, Square, WhiteNoise, Pulse
import sf2_loader as rs
import pickle

abs_path = os.path.abspath(os.path.dirname(__file__))


class esi:

    def __init__(self, samples, settings=None, name_mappings=None):
        self.samples = samples
        self.settings = settings
        self.name_mappings = name_mappings
        self.file_names = {os.path.splitext(i)[0]: i for i in self.samples}

    def __getitem__(self, ind):
        if self.name_mappings:
            if ind in self.name_mappings:
                return self.samples[self.name_mappings[ind]]
        if ind in self.samples:
            return self.samples[ind]
        if ind in self.file_names:
            return self.samples[self.file_names[ind]]


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


class sampler:

    def __init__(self, num=1, name=None, bpm=120):
        self.channel_num = num
        self.channel_names = []
        self.channel_sound_modules_name = []
        self.channel_sound_modules = []
        self.channel_dict = []
        self.name = name
        self.bpm = bpm
        self.current_playing = []
        self.piece_playing = []
        self.export_audio_fadeout_time_ratio = 0.5
        self.export_audio_fadeout_time = 500
        self.export_fadeout_use_ratio = False
        self.play_audio_fadeout_time_ratio = 0.5
        self.play_audio_fadeout_time = 500
        self.play_fadeout_use_ratio = False
        for i in range(self.channel_num):
            current_channel_name = f'Channel {i+1}'
            self.channel_names.append(current_channel_name)
            self.channel_sound_modules_name.append('not loaded')
            self.channel_sound_modules.append(None)
            self.channel_dict.append(copy(default_notedict))

    def add_new_channel(self, name=None):
        current_channel_name = f'Channel {self.channel_num+1}' if name is None else name
        self.channel_names.append(current_channel_name)
        self.channel_sound_modules_name.append('not loaded')
        self.channel_sound_modules.append(None)
        self.channel_dict.append(copy(default_notedict))
        self.channel_num += 1

    def delete_channel(self, i):
        del self.channel_names[i]
        del self.channel_sound_modules_name[i]
        del self.channel_sound_modules[i]
        del self.channel_dict[i]
        self.channel_num -= 1

    def clear_channel(self, i):
        current_ind = i
        if current_ind < self.channel_num:
            self.channel_names[current_ind] = f'Channel {current_ind+1}'
            self.channel_sound_modules_name[current_ind] = 'not loaded'
            self.channel_sound_modules[current_ind] = None
            self.channel_dict[current_ind] = copy(default_notedict)

    def clear_all_channels(self):
        self.stop_playing()
        self.channel_names.clear()
        self.channel_sound_modules_name = [
            'not loaded' for i in range(self.channel_num)
        ]
        self.channel_sound_modules.clear()
        self.channel_dict.clear()
        self.channel_num = 0

    def set_channel_name(self, i, name):
        self.channel_names[i] = name

    def unload(self, i, keep_notedict=False):
        current_ind = i
        if current_ind < self.channel_num:
            self.channel_sound_modules_name[current_ind] = 'not loaded'
            self.channel_sound_modules[current_ind] = None
            if not keep_notedict:
                self.channel_dict[current_ind] = copy(default_notedict)

    def __call__(self, obj, channel_num=0, bpm=None):
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
        return ' | '.join(
            [self.channel_names[i], self.channel_sound_modules_name[i]])

    def __delitem__(self, i):
        self.delete_channel(i)

    def load(self, current_ind, path=None, esi=None):
        if esi is not None:
            self.load_esi_file(current_ind, esi)
            return
        sound_path = path
        if os.path.isdir(sound_path):
            notedict = self.channel_dict[current_ind]
            self.channel_sound_modules[current_ind] = load_audiosegments(
                notedict, sound_path)
            self.channel_sound_modules_name[current_ind] = sound_path
        elif os.path.isfile(sound_path):
            self.channel_sound_modules[current_ind] = rs.sf2_loader(sound_path)
            self.channel_sound_modules_name[current_ind] = sound_path
        else:
            raise ValueError(f'cannot find the path {sound_path}')

    def export(self,
               obj,
               mode='wav',
               action='export',
               filename='Untitled.wav',
               channel_num=0,
               bpm=None,
               length=None,
               extra_length=None,
               track_lengths=None,
               track_extra_lengths=None,
               export_args={},
               show_msg=False,
               soundfont_args=None):
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
            if isinstance(result, chord):
                result = ['chord', result, channel_num]
            elif isinstance(result, piece):
                result = ['piece', result]
            else:
                return
        else:
            result = self.get_current_musicpy_chords(obj, channel_num)
        if result is None:
            return
        if soundfont_args is None:
            soundfont_args = default_soundfont_args
        types = result[0]
        current_chord = result[1]

        if types == 'chord':
            current_channel_num = result[2]
            current_bpm = self.bpm if bpm is None else bpm
            current_chord = copy(current_chord)
            current_chord.normalize_tempo(bpm=current_bpm)
            for each in current_chord:
                if isinstance(each, AudioSegment):
                    each.duration = real_time_to_bar(len(each), current_bpm)
                    each.volume = 127

            current_sound_modules = self.channel_sound_modules[
                current_channel_num]
            if show_msg:
                print(f'rendering track 1/1 channel {current_channel_num+1}')
            if isinstance(current_sound_modules, rs.sf2_loader):
                silent_audio = current_sound_modules.export_chord(
                    current_chord,
                    bpm=current_bpm,
                    start_time=current_chord.start_time,
                    get_audio=True,
                    effects=current_chord.effects
                    if check_effect(current_chord) else None,
                    length=length,
                    extra_length=extra_length,
                    **soundfont_args)
            else:
                apply_fadeout_obj = self.apply_fadeout(current_chord,
                                                       current_bpm)
                if length:
                    whole_duration = length * 1000
                else:
                    whole_duration = apply_fadeout_obj.eval_time(
                        current_bpm,
                        mode='number',
                        audio_mode=1,
                        start_time=current_chord.start_time) * 1000
                    if extra_length:
                        whole_duration += extra_length * 1000
                silent_audio = AudioSegment.silent(duration=whole_duration)
                silent_audio = self.channel_to_audio(
                    current_chord,
                    current_channel_num,
                    silent_audio,
                    current_bpm,
                    length=length,
                    extra_length=extra_length,
                    current_start_time=current_chord.start_time)
            if show_msg:
                print('rendering finished')
            try:
                if action == 'export':
                    silent_audio.export(filename, format=mode, **export_args)
                    if show_msg:
                        print('export finished')
                elif action == 'play':
                    play_audio(silent_audio)
                elif action == 'get':
                    return silent_audio
            except:
                return
        elif types == 'piece':
            current_chord = copy(current_chord)
            current_chord.normalize_tempo()
            current_chord.apply_start_time_to_changes(
                [-i for i in current_chord.start_times],
                msg=True,
                pan_volume=True)
            current_name = current_chord.name
            current_bpm = current_chord.bpm
            current_start_times = current_chord.start_times
            current_pan = current_chord.pan
            current_volume = current_chord.volume
            current_tracks = current_chord.tracks
            current_channels = current_chord.sampler_channels if current_chord.sampler_channels else [
                i for i in range(len(current_chord))
            ]
            for i in range(len(current_chord.tracks)):
                each_channel = current_chord.tracks[i]
                for each in each_channel:
                    if isinstance(each, AudioSegment):
                        each.duration = real_time_to_bar(
                            len(each), current_bpm)
                        each.volume = 127
                current_chord.tracks[i] = each_channel
            apply_fadeout_obj = self.apply_fadeout(current_chord, current_bpm)
            if length:
                whole_duration = length * 1000
            else:
                whole_duration = apply_fadeout_obj.eval_time(
                    current_bpm, mode='number', audio_mode=1) * 1000
                if extra_length:
                    whole_duration += extra_length * 1000
            silent_audio = AudioSegment.silent(duration=whole_duration)
            sound_modules_num = len(self.channel_sound_modules)
            track_number = len(current_chord)
            for i in range(track_number):
                current_channel_number = current_channels[i]
                if current_channel_number >= sound_modules_num:
                    print(
                        f'track {i+1} : cannot find channel {current_channel_number+1}'
                    )
                    continue
                if show_msg:
                    print(
                        f'rendering track {i+1}/{track_number} channel {current_channel_number+1}'
                    )
                current_sound_modules = self.channel_sound_modules[
                    current_channel_number]
                current_track = current_tracks[i]
                if isinstance(current_sound_modules, rs.sf2_loader):
                    current_instrument = current_chord.instruments_numbers[i]
                    current_channel = current_chord.channels[
                        i] if current_chord.channels else current_sound_modules.current_channel
                    current_sfid, current_bank, current_preset = current_sound_modules.channel_info(
                        current_channel)
                    if current_sfid == 0:
                        current_sound_modules.change_sfid(
                            current_sound_modules.sfid_list[0],
                            current_channel)
                        current_sfid, current_bank, current_preset = current_sound_modules.channel_info(
                            current_channel)
                    if isinstance(current_instrument, int):
                        current_instrument = [
                            current_instrument - 1, current_bank
                        ]
                    else:
                        current_instrument = [current_instrument[0] - 1
                                              ] + current_instrument[1:]
                    current_sound_modules.change(
                        channel=current_channel,
                        sfid=(current_instrument[2]
                              if len(current_instrument) > 2 else None),
                        bank=current_instrument[1],
                        preset=current_instrument[0],
                        mode=1)
                    silent_audio = silent_audio.overlay(
                        current_sound_modules.export_chord(
                            current_track,
                            bpm=current_bpm,
                            get_audio=True,
                            channel=current_channel,
                            effects=current_track.effects
                            if check_effect(current_track) else None,
                            pan=current_pan[i],
                            volume=current_volume[i],
                            length=None
                            if not track_lengths else track_lengths[i],
                            extra_length=None if not track_extra_lengths else
                            track_extra_lengths[i],
                            **soundfont_args),
                        position=bar_to_real_time(current_start_times[i],
                                                  current_bpm, 1))
                    current_sound_modules.change(current_channel,
                                                 current_sfid,
                                                 current_bank,
                                                 current_preset,
                                                 mode=1)
                else:
                    silent_audio = self.channel_to_audio(
                        current_tracks[i],
                        current_channels[i],
                        silent_audio,
                        current_bpm,
                        current_pan[i],
                        current_volume[i],
                        current_start_times[i],
                        length=None if not track_lengths else track_lengths[i],
                        extra_length=None
                        if not track_extra_lengths else track_extra_lengths[i])
            if check_effect(current_chord):
                silent_audio = process_effect(silent_audio,
                                              current_chord.effects,
                                              bpm=current_bpm)
            if show_msg:
                print('rendering finished')
            try:
                if action == 'export':
                    silent_audio.export(filename, format=mode, **export_args)
                    if show_msg:
                        print('export finished')
                elif action == 'play':
                    play_audio(silent_audio)
                elif action == 'get':
                    return silent_audio
            except:
                return

    def apply_fadeout(self, obj, bpm):
        temp = copy(obj)
        if isinstance(temp, chord):
            for each in temp.notes:
                if not isinstance(each, AudioSegment):
                    if self.export_fadeout_use_ratio:
                        current_fadeout_time = each.duration * self.export_audio_fadeout_time_ratio
                    else:
                        current_fadeout_time = real_time_to_bar(
                            self.export_audio_fadeout_time, bpm)
                    each.duration += current_fadeout_time
            return temp
        elif isinstance(temp, piece):
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
                         length=None,
                         extra_length=None):
        if len(self.channel_sound_modules) <= current_channel_num:
            return
        if not self.channel_sound_modules[current_channel_num]:
            return

        apply_fadeout_obj = self.apply_fadeout(current_chord, current_bpm)
        if length:
            whole_duration = length * 1000
        else:
            whole_duration = apply_fadeout_obj.eval_time(
                current_bpm, mode='number', audio_mode=1) * 1000
            if extra_length:
                whole_duration += extra_length * 1000
        current_silent_audio = AudioSegment.silent(duration=whole_duration)
        current_intervals = current_chord.interval
        current_durations = current_chord.get_duration()
        current_volumes = current_chord.get_volume()
        current_dict = self.channel_dict[current_channel_num]
        current_sounds = self.channel_sound_modules[current_channel_num]
        current_sound_path = self.channel_sound_modules_name[
            current_channel_num]
        current_start_time = bar_to_real_time(current_start_time, current_bpm,
                                              1)
        current_position = 0
        whole_length = len(current_chord)
        for i in range(whole_length):
            each = current_chord.notes[i]
            if isinstance(each, (note, AudioSegment)):
                interval = bar_to_real_time(current_intervals[i], current_bpm,
                                            1)
                duration = bar_to_real_time(
                    current_durations[i], current_bpm,
                    1) if not isinstance(each, AudioSegment) else len(each)
                volume = velocity_to_db(current_volumes[i])
                current_fadeout_time = int(
                    duration * self.export_audio_fadeout_time_ratio
                ) if self.export_fadeout_use_ratio else int(
                    self.export_audio_fadeout_time)
                if isinstance(each, AudioSegment):
                    current_sound = each[:duration]
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
                    current_sound = current_sound[:current_max_time]
                if check_effect(each):
                    current_sound = process_effect(current_sound,
                                                   each.effects,
                                                   bpm=current_bpm)

                if current_fadeout_time != 0 and not isinstance(
                        each, AudioSegment):
                    current_sound = current_sound.fade_out(
                        duration=current_max_fadeout_time)
                current_sound += volume
                current_silent_audio = current_silent_audio.overlay(
                    current_sound, position=current_position)
                current_position += interval
        if current_pan:
            pan_ranges = [
                bar_to_real_time(i.start_time, current_bpm, 1)
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
                bar_to_real_time(i.start_time, current_bpm, 1)
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
        if check_effect(current_chord):
            current_silent_audio = process_effect(current_silent_audio,
                                                  current_chord.effects,
                                                  bpm=current_bpm)
        silent_audio = silent_audio.overlay(current_silent_audio,
                                            position=current_start_time)
        return silent_audio

    def export_midi_file(self, obj, filename, channel_num=0, write_args={}):
        result = self.get_current_musicpy_chords(obj, channel_num)
        if result is None:
            return
        current_chord = result[1]
        write(current_chord, self.bpm, name=filename, **write_args)

    def get_current_musicpy_chords(self, current_chord, current_channel_num=0):
        current_bpm = self.bpm
        if isinstance(current_chord, note):
            current_chord = chord([current_chord])
        elif isinstance(current_chord, list) and all(
                isinstance(i, chord) for i in current_chord):
            current_chord = concat(current_chord, mode='|')
        if isinstance(current_chord, chord):
            return 'chord', current_chord, current_channel_num
        if isinstance(current_chord, track):
            has_effect = False
            if check_effect(current_chord):
                has_effect = True
                current_effects = copy(current_chord.effects)
            current_chord = build(current_chord,
                                  bpm=current_chord.bpm if current_chord.bpm
                                  is not None else current_bpm)
            if has_effect:
                current_chord.effects = current_effects
        if isinstance(current_chord, piece):
            current_bpm = current_chord.bpm
            current_start_times = current_chord.start_times
            return 'piece', current_chord

    def stop_playing(self):
        pygame.mixer.stop()
        pygame.mixer.music.stop()
        if self.current_playing:
            for each in self.current_playing:
                each.cancel()
            self.current_playing.clear()
        if self.piece_playing:
            for each in self.piece_playing:
                each.cancel()
            self.piece_playing.clear()

    def load_channel_settings(self, channel_num=0, text=None, path=None):
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

    def load_esi_file(self, channel_num, file_path):
        abs_path = os.getcwd()
        with open(file_path, 'rb') as file:
            current_esi = pickle.load(file)
        channel_settings = current_esi.settings
        current_samples = current_esi.samples
        filenames = list(current_samples.keys())
        sound_files_audio = [
            AudioSegment.from_file(
                BytesIO(current_samples[i]), format=os.path.splitext(i)[1]
                [1:]).set_frame_rate(44100).set_channels(2).set_sample_width(2)
            for i in filenames
        ]
        self.channel_dict[channel_num] = copy(default_notedict)
        if channel_settings is not None:
            self.load_channel_settings(channel_num, channel_settings)
        current_dict = self.channel_dict[channel_num]
        filenames = [os.path.splitext(i)[0] for i in filenames]
        result_audio = {
            filenames[i]: sound_files_audio[i]
            for i in range(len(filenames))
        }
        self.channel_sound_modules[channel_num] = {
            i: (result_audio[current_dict[i]]
                if current_dict[i] in result_audio else None)
            for i in current_dict
        }
        self.channel_sound_modules_name[channel_num] = file_path

    def reload_channel_sounds(self, current_ind):
        try:
            sound_path = self.channel_sound_modules_name[current_ind]
            notedict = self.channel_dict[current_ind]
            self.channel_sound_modules[current_ind] = load_audiosegments(
                notedict, sound_path)
        except Exception as e:
            print(str(e))

    def play_note_func(self, name, duration, volume, channel=0):
        note_sounds = self.channel_sound_modules[channel]
        if name in note_sounds:
            current_sound = note_sounds[name]
            if current_sound:
                current_sound = pygame.mixer.Sound(
                    buffer=current_sound.raw_data)
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

    def play(self,
             current_chord,
             channel_num=0,
             bpm=None,
             length=None,
             extra_length=None,
             track_lengths=None,
             track_extra_lengths=None,
             soundfont_args=None,
             wait=False):
        if not self.channel_sound_modules:
            return
        self.stop_playing()
        current_channel_num = channel_num
        current_bpm = self.bpm if bpm is None else bpm
        self.play_musicpy_sounds(current_chord, current_channel_num,
                                 current_bpm, length, extra_length,
                                 track_lengths, track_extra_lengths,
                                 soundfont_args)
        if wait:
            while pygame.mixer.get_busy():
                pygame.time.delay(10)

    def play_musicpy_sounds(self,
                            current_chord,
                            current_channel_num=None,
                            bpm=None,
                            length=None,
                            extra_length=None,
                            track_lengths=None,
                            track_extra_lengths=None,
                            soundfont_args=None):
        if isinstance(current_chord, note):
            current_chord = chord([current_chord])
        elif isinstance(current_chord, list) and all(
                isinstance(i, chord) for i in current_chord):
            current_chord = concat(current_chord, mode='|')
        if isinstance(current_chord, chord):
            if check_special(current_chord) or isinstance(
                    self.channel_sound_modules[current_channel_num],
                    rs.sf2_loader):
                self.export(current_chord,
                            action='play',
                            channel_num=current_channel_num,
                            bpm=bpm,
                            length=length,
                            extra_length=extra_length,
                            track_lengths=track_lengths,
                            track_extra_lengths=track_extra_lengths,
                            soundfont_args=soundfont_args)
            else:
                if current_chord.start_time == 0:
                    self.play_channel(current_chord, current_channel_num, bpm)
                else:
                    self.play_channel(current_chord,
                                      current_channel_num,
                                      bpm,
                                      start_time=bar_to_real_time(
                                          current_chord.start_time, bpm, 1))
        elif isinstance(current_chord, track):
            has_effect = False
            if check_effect(current_chord):
                has_effect = True
                current_effects = copy(current_chord.effects)
            current_chord = build(current_chord,
                                  bpm=current_chord.bpm
                                  if current_chord.bpm is not None else bpm)
            if has_effect:
                current_chord.effects = current_effects
        if isinstance(current_chord, piece):
            current_channel_nums = current_chord.sampler_channels if current_chord.sampler_channels else [
                i for i in range(len(current_chord))
            ]
            if check_special(current_chord) or any(
                    isinstance(self.channel_sound_modules[i], rs.sf2_loader)
                    for i in current_channel_nums):
                self.export(current_chord,
                            action='play',
                            bpm=bpm,
                            length=length,
                            extra_length=extra_length,
                            track_lengths=track_lengths,
                            track_extra_lengths=track_extra_lengths,
                            soundfont_args=soundfont_args)
                return
            current_tracks = current_chord.tracks
            bpm = current_chord.bpm
            current_start_times = current_chord.start_times
            for each in range(len(current_chord)):
                current_id = threading.Timer(
                    bar_to_real_time(current_start_times[each], bpm, 1) / 1000,
                    lambda each=each, bpm=bpm: self.play_channel(
                        current_tracks[each], current_channel_nums[each], bpm))
                current_id.start()
                self.piece_playing.append(current_id)

    def play_channel(self,
                     current_chord,
                     current_channel_num=0,
                     bpm=None,
                     start_time=0):
        if not self.channel_sound_modules[current_channel_num]:
            return
        current_intervals = current_chord.interval
        current_durations = current_chord.get_duration()
        current_volumes = current_chord.get_volume()
        current_time = start_time
        for i in range(len(current_chord)):
            each = current_chord.notes[i]
            if isinstance(each, note):
                duration = current_durations[i]
                volume = current_volumes[i]
                current_id = threading.Timer(
                    current_time / 1000,
                    lambda each=each, duration=duration, volume=volume: self.
                    play_note_func(f'{standardize_note(each.name)}{each.num}',
                                   duration, volume, current_channel_num))
                self.current_playing.append(current_id)
                current_id.start()
                current_time += bar_to_real_time(current_intervals[i], bpm, 1)

    def modules(self, ind):
        return self.channel_sound_modules[ind]

    def module_names(self, ind):
        return self.channel_sound_modules_name[ind]


class pitch:

    def __init__(self, path, note='C5', format=None):
        self.note = N(note) if isinstance(note, str) else note
        audio_load = False
        if not isinstance(path, AudioSegment):
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
                self.sounds.export('temp.wav', format='wav')
                import librosa
                self.audio = librosa.load('temp.wav',
                                          sr=self.sounds.frame_rate)[0]
                os.remove('temp.wav')
                audio_load = True
        else:
            self.sounds = path
            self.file_path = None
        self.sample_rate = self.sounds.frame_rate
        self.channels = self.sounds.channels
        if self.sounds.sample_width != 2:
            self.sounds = self.sounds.set_sample_width(2)
        self.sample_width = self.sounds.sample_width
        if not audio_load:
            import librosa
            if not isinstance(path, AudioSegment):
                self.audio = librosa.load(path, sr=self.sample_rate)[0]
            else:
                os.chdir(abs_path)
                path.export('temp.wav', format='wav')
                self.audio = librosa.load('temp.wav', sr=path.frame_rate)[0]
                os.remove('temp.wav')
            audio_load = True

    def pitch_shift(self, semitones=1, mode='librosa'):
        if mode == 'librosa':
            import librosa
            data_shifted = librosa.effects.pitch_shift(self.audio,
                                                       self.sample_rate,
                                                       n_steps=semitones)
            current_sound = BytesIO()
            import soundfile
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
            result = result.set_frame_rate(44100)
        return result

    def __add__(self, semitones):
        return self.pitch_shift(semitones)

    def __sub__(self, semitones):
        return self.pitch_shift(-semitones)

    def get(self, pitch):
        if not isinstance(pitch, note):
            pitch = N(pitch)
        semitones = pitch.degree - self.note.degree
        return self + semitones

    def set_note(self, pitch):
        if not isinstance(pitch, note):
            pitch = N(pitch)
        self.note = pitch

    def generate_dict(self, start='A0', end='C8', mode='librosa'):
        if not isinstance(start, note):
            start = N(start)
        if not isinstance(end, note):
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

    def play(self, wait=False):
        play_audio(self, wait=wait)

    def stop(self):
        pygame.mixer.stop()


class sound:

    def __init__(self, path, format=None):
        if not isinstance(path, AudioSegment):
            current_format = path[path.rfind('.') + 1:]
            try:
                self.sounds = AudioSegment.from_file(path,
                                                     format=current_format)

            except:
                with open(path, 'rb') as f:
                    current_data = f.read()
                current_file = BytesIO(current_data)
                self.sounds = AudioSegment.from_file(current_file,
                                                     format=current_format)
            self.file_path = path
        else:
            self.sounds = path
            self.file_path = None
        self.sample_rate = self.sounds.frame_rate
        self.channels = self.sounds.channels
        if self.sounds.sample_width != 2:
            self.sounds = self.sounds.set_sample_width(2)
        self.sample_width = self.sounds.sample_width

    def __len__(self):
        return len(self.sounds)

    def play(self, wait=False):
        play_audio(self, wait=wait)

    def stop(self):
        pygame.mixer.stop()


def play_audio(audio, mode=0, wait=False):
    if isinstance(audio, (pitch, sound)):
        current_audio = audio.sounds
    else:
        current_audio = audio
    if mode == 0:
        if current_audio.channels == 1:
            current_audio = current_audio.set_frame_rate(44100).set_channels(2)
        current_sound_object = pygame.mixer.Sound(
            buffer=current_audio.raw_data)
        current_sound_object.play()
    elif mode == 1:
        try:
            capture = rs.py.io.StdCaptureFD(out=True, in_=False)
        except:
            pass
        try:
            current_file = BytesIO()
            current_audio.export(current_file, format='wav')
            current_sound_object = pygame.mixer.Sound(file=current_file)
        except:
            current_path = os.getcwd()
            os.chdir(abs_path)
            current_audio.export('temp.wav', format='wav')
            current_sound_object = pygame.mixer.Sound(file='temp.wav')
            os.remove('temp.wav')
            os.chdir(current_path)
        current_sound_object.play()
        try:
            capture.reset()
        except:
            pass
    if wait:
        while pygame.mixer.get_busy():
            pygame.time.delay(10)


def stop():
    pygame.mixer.stop()
    pygame.mixer.music.stop()


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
                current_sound = AudioSegment.from_file(
                    current_sound_obj_path,
                    format=current_sound_format).set_frame_rate(
                        44100).set_channels(2)
                if current_sound.sample_width != 2:
                    current_sound = current_sound.set_sample_width(2)
                current_sounds[i] = current_sound
            except:
                with open(current_sound_obj_path, 'rb') as f:
                    current_data = f.read()
                current_sound = AudioSegment.from_file(
                    BytesIO(current_data),
                    format=current_sound_format).set_frame_rate(
                        44100).set_channels(2)
                if current_sound.sample_width != 2:
                    current_sound = current_sound.set_sample_width(2)
                current_sounds[i] = current_sound
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


def check_pan_or_volume(sound):
    return isinstance(sound, piece) and (any(i for i in sound.pan)
                                         or any(i for i in sound.volume))


def has_audio(sound):
    if isinstance(sound, chord):
        return any(isinstance(i, AudioSegment) for i in sound.notes)
    elif isinstance(sound, piece):
        return any(has_audio(i) for i in sound.tracks)


def check_special(sound):
    return check_effect_all(sound) or check_pan_or_volume(sound) or has_audio(
        sound)


def check_effect(sound):
    return hasattr(sound, 'effects') and isinstance(sound.effects,
                                                    list) and sound.effects


def check_effect_all(sound):
    if isinstance(sound, chord):
        return check_effect(sound) or any(check_effect(i) for i in sound)
    elif isinstance(sound, piece):
        return check_effect(sound) or any(
            check_effect_all(i) for i in sound.tracks)
    else:
        return check_effect(sound)


def process_effect(sound, effects, **kwargs):
    current_args = kwargs
    for each in effects:
        each.process_unknown_args(**current_args)
        sound = each.process(sound)
    return sound


def set_effect(sound, *effects):
    if len(effects) == 1:
        current_effect = effects[0]
        if not isinstance(current_effect, effect):
            if isinstance(current_effect, effect_chain):
                effects = current_effect.effects
            else:
                effects = list(current_effect)
        else:
            effects = list(effects)
    else:
        effects = list(effects)
    sound.effects = effects
    return sound


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


def sine(freq=440, duration=1000, volume=0):
    if isinstance(freq, (str, note)):
        freq = get_freq(freq)
    return Sine(freq).to_audio_segment(duration, volume)


def triangle(freq=440, duration=1000, volume=0):
    if isinstance(freq, (str, note)):
        freq = get_freq(freq)
    return Triangle(freq).to_audio_segment(duration, volume)


def sawtooth(freq=440, duration=1000, volume=0):
    if isinstance(freq, (str, note)):
        freq = get_freq(freq)
    return Sawtooth(freq).to_audio_segment(duration, volume)


def square(freq=440, duration=1000, volume=0):
    if isinstance(freq, (str, note)):
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
                  ] if not isinstance(volume, list) else volume
        volume = [percentage_to_db(i) for i in volume]
    for i in range(len(temp)):
        current_note = temp[i]
        if isinstance(current_note, note):
            if mode == 'sine':
                temp[i] = sine(get_freq(current_note),
                               bar_to_real_time(current_note.duration, bpm, 1),
                               volume[i])
            elif mode == 'triangle':
                temp[i] = triangle(
                    get_freq(current_note),
                    bar_to_real_time(current_note.duration, bpm, 1), volume[i])
            elif mode == 'sawtooth':
                temp[i] = sawtooth(
                    get_freq(current_note),
                    bar_to_real_time(current_note.duration, bpm, 1), volume[i])
            elif mode == 'square':
                temp[i] = square(
                    get_freq(current_note),
                    bar_to_real_time(current_note.duration, bpm, 1), volume[i])
            else:
                temp[i] = mode(get_freq(current_note),
                               bar_to_real_time(current_note.duration, bpm, 1),
                               volume[i])
    return temp


def audio(obj, sampler, channel_num=0, bpm=None):
    if isinstance(obj, note):
        obj = chord([obj])
    elif isinstance(obj, track):
        obj = build(obj, bpm=obj.bpm, name=obj.name)
    result = sampler.export(obj,
                            action='get',
                            channel_num=channel_num,
                            bpm=bpm)
    return result


def audio_chord(audio_list, interval=0, duration=1 / 4, volume=127):
    result = chord([])
    result.notes = audio_list
    result.interval = interval if isinstance(
        interval, list) else [interval for i in range(len(audio_list))]
    durations = duration if isinstance(
        duration, list) else [duration for i in range(len(audio_list))]
    volumes = volume if isinstance(
        volume, list) else [volume for i in range(len(audio_list))]
    for i in range(len(result.notes)):
        result.notes[i].duration = durations[i]
        result.notes[i].volume = volumes[i]
    return result


def make_esi(file_path,
             name='untitled.esi',
             settings=None,
             asfile=True,
             name_mappings=None):
    abs_path = os.getcwd()
    filenames = os.listdir(file_path)
    current_samples = {}
    current_settings = None
    if settings is not None:
        if asfile:
            with open(settings, encoding='utf-8-sig') as f:
                current_settings = f.read()
        else:
            current_settings = settings

    if not filenames:
        print('There are no sound files to make ESI files')
        return
    os.chdir(file_path)
    for t in filenames:
        with open(t, 'rb') as f:
            current_samples[t] = f.read()
    current_esi = esi(current_samples, current_settings, name_mappings)
    os.chdir(abs_path)
    with open(name, 'wb') as f:
        pickle.dump(current_esi, f)
    print(f'Successfully made ESI file: {name}')


def unzip_esi(file_path, folder_name=None):
    if folder_name is None:
        folder_name = os.path.basename(file_path)
        folder_name = folder_name[:folder_name.rfind('.')]
    if folder_name not in os.listdir():
        os.mkdir(folder_name)
    current_esi = load_esi(file_path, convert=False)
    os.chdir(folder_name)
    for each in current_esi.samples:
        print(f'Currently unzip file {each}')
        with open(each, 'wb') as f:
            f.write(current_esi.samples[each])
    print(f'Unzip {os.path.basename(file_path)} successfully')


def load_esi(file_path, convert=True):
    with open(file_path, 'rb') as file:
        current_esi = pickle.load(file)
    current_samples = current_esi.samples
    if convert:
        current_esi.samples = {
            i: AudioSegment.from_file(
                BytesIO(current_samples[i]), format=os.path.splitext(i)[1]
                [1:]).set_frame_rate(44100).set_channels(2).set_sample_width(2)
            for i in current_samples
        }
    return current_esi


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

default_soundfont_args = {'decay': 0.5, 'fixed_decay': True}

try:
    pygame.mixer.quit()
    pygame.mixer.init(44100, -16, 2, 1024)
    pygame.mixer.set_num_channels(1000)
except pygame.error:
    has_audio_interface = False
