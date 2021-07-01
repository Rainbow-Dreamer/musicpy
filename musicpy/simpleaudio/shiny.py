# Simpleaudio Python Extension
# Copyright (C) 2015, Joe Hamilton
# MIT License (see LICENSE.txt)

import simpleaudio._simpleaudio as _sa
from time import sleep
import wave


class WaveObject(object):
    def __init__(self, audio_data, num_channels=2, bytes_per_sample=2,
                 sample_rate=44100):
        self.audio_data = audio_data
        self.num_channels = num_channels
        self.bytes_per_sample = bytes_per_sample
        self.sample_rate = sample_rate

    def play(self):
        return play_buffer(self.audio_data, self.num_channels,
                           self.bytes_per_sample, self.sample_rate)

    @classmethod
    def from_wave_file(cls, wave_file):
        wave_read = wave.open(wave_file, 'rb')
        wave_obj = cls.from_wave_read(wave_read)
        wave_read.close()
        return wave_obj

    @classmethod
    def from_wave_read(cls, wave_read):
        return cls(wave_read.readframes(wave_read.getnframes()),
                   wave_read.getnchannels(), wave_read.getsampwidth(),
                   wave_read.getframerate())

    def __str__(self):
        return "Wave Object: {} channel, {} bit, {} Hz".format(
            self.num_channels, self.bytes_per_sample * 8, self.sample_rate)


class PlayObject(object):
    def __init__(self, play_id):
        self.play_id = play_id

    def stop(self):
        _sa._stop(self.play_id)

    def wait_done(self):
        while self.is_playing():
            sleep(0.05)

    def is_playing(self):
        return _sa._is_playing(self.play_id)


def stop_all():
    _sa._stop_all()


def play_buffer(audio_data, num_channels, bytes_per_sample, sample_rate):
    play_id = _sa._play_buffer(audio_data, num_channels, bytes_per_sample,
                               sample_rate)
    return PlayObject(play_id)
