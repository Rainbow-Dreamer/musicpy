from musicpy import *
import pygame.midi
import time


def bar_to_real_time(bar, bpm, mode=0):
    # return time in ms
    return int(
        (60000 / bpm) * (bar * 4)) if mode == 0 else (60000 / bpm) * (bar * 4)


def real_time_to_bar(time, bpm):
    return (time / (60000 / bpm)) / 4


class midi_event:

    def __init__(self, value, time, mode=0, track=0, channel=None):
        '''
        mode:
        0: note on
        1: note off
        2: set instrument
        3: pitch bend
        4: tempo change
        5: controller event
        '''
        self.value = value
        self.time = time
        self.mode = mode
        self.track = track
        self.channel = channel

    def __repr__(self):
        return f'[note event] note: {self.current_note}  time: {self.time}s  mode: {self.mode}'


def play_send_midi(current_chord,
                   ports,
                   channel=0,
                   start_time=0,
                   bpm=120,
                   track_num=None,
                   set_instrument=False):
    pygame.midi.init()
    if isinstance(current_chord, note):
        current_chord = chord([current_chord])
    if isinstance(current_chord, chord):
        current_chord = P([current_chord],
                          channels=[channel],
                          start_times=[start_time],
                          bpm=bpm)
    elif isinstance(current_chord, track):
        current_chord = build(current_chord)
    if track_num is not None:
        if isinstance(track_num, int):
            track_num = [track_num for i in range(len(current_chord))]
    i = 0
    info_list = []
    while pygame.midi.get_device_info(i) != None:
        current_info = pygame.midi.get_device_info(i)
        info_list.append(current_info)
        i += 1
    port_list = [(each[1].decode('utf-8'), i)
                 for i, each in enumerate(info_list) if each[2] == 0]
    port_name_list = [i[0] for i in port_list]
    player_list = [
        pygame.midi.Output(port_list[port_name_list.index(i)][1])
        for i in ports if i in port_name_list
    ]
    if len(player_list) != len(ports):
        raise Exception('not all midi ports found')
    channels = current_chord.channels
    if not channels:
        channels = [0 for i in range(len(current_chord))]
    current_chord.normalize_tempo()
    event_list = []
    tempo_change_event = midi_event(value=current_chord.bpm,
                                    time=0,
                                    mode=4,
                                    track=0)
    event_list.append(tempo_change_event)
    for i, each in enumerate(current_chord.tracks):
        current_channel = channels[i]
        current_start_time = current_chord.start_times[i]
        if set_instrument and current_chord.instruments_numbers:
            current_instrument = current_chord.instruments_numbers[i] - 1
            event_list.append(
                midi_event(value=current_instrument,
                           time=0,
                           mode=2,
                           track=i,
                           channel=current_channel))
        for j, current in enumerate(each.notes):
            if isinstance(current, note):
                current_on_time = current_start_time + sum(each.interval[:j])
                current_off_time = current_on_time + current.duration
                event_list.append(
                    midi_event(value=current,
                               time=bar_to_real_time(current_on_time,
                                                     current_chord.bpm, 1) /
                               1000,
                               mode=0,
                               track=i))
                event_list.append(
                    midi_event(value=current,
                               time=bar_to_real_time(current_off_time,
                                                     current_chord.bpm, 1) /
                               1000,
                               mode=1,
                               track=i))
            elif isinstance(current, pitch_bend):
                if current.start_time is not None:
                    current_time = current.start_time
                else:
                    current_time = bar_to_real_time(
                        current_start_time + sum(each.interval[:j]),
                        current_chord.bpm, 1) / 1000
                event_list.append(
                    midi_event(value=current,
                               time=current_time,
                               mode=3,
                               track=i))
            elif isinstance(current, tempo):
                if current.start_time is not None:
                    current_time = current.start_time
                else:
                    current_time = bar_to_real_time(
                        current_start_time + sum(each.interval[:j]),
                        current_chord.bpm, 1) / 1000
                event_list.append(
                    midi_event(value=current.bpm,
                               time=current_time,
                               mode=4,
                               track=i))
    for each in current_chord.other_messages:
        if isinstance(each, controller_event):
            event_list.append(
                midi_event(value=each,
                           time=bar_to_real_time(each.time / 4,
                                                 current_chord.bpm, 1) / 1000,
                           mode=5,
                           track=each.track))
    event_list.sort(key=lambda s: s.time)
    if not event_list:
        return
    start_time = time.time()
    counter = 0
    length = len(event_list)
    while counter < length:
        past_time = time.time() - start_time
        current_event = event_list[counter]
        if past_time >= current_event.time:
            if track_num:
                current_track = track_num[current_event.track]
            else:
                current_track = current_event.track
            current_player = player_list[current_track]
            if current_event.mode == 0:
                current_note = current_event.value
                current_channel = current_note.channel if current_note.channel is not None else channels[
                    current_event.track]
                current_player.note_on(note=current_note.degree,
                                       velocity=current_event.value.volume,
                                       channel=current_channel)
            elif current_event.mode == 1:
                current_note = current_event.value
                current_channel = current_note.channel if current_note.channel is not None else channels[
                    current_event.track]
                current_player.note_off(note=current_note.degree,
                                        channel=current_channel)
            elif current_event.mode == 2:
                current_player.set_instrument(
                    instrument_id=current_event.value,
                    channel=current_event.channel)
            elif current_event.mode == 3:
                current_channel = current_event.value.channel if current_event.value.channel is not None else channels[
                    current_event.track]
                current_player.pitch_bend(value=current_event.value.value,
                                          channel=current_channel)
            elif current_event.mode == 4:
                current_player.write_short(0xFF, 0x51, current_event.value)
            elif current_event.mode == 5:
                current_player.write_short(
                    0xb0 | current_event.value.channel,
                    current_event.value.controller_number,
                    current_event.value.parameter)
            counter += 1
