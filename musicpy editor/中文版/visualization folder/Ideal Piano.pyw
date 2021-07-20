screen_width, screen_height = screen_size
show_delay_time_actual = int(show_delay_time * 1000)
pressed = keyboard.is_pressed
pygame.mixer.init(frequency, size, channel, buffer)
pyglet.resource.path = [abs_path]
for each in [
        'background_image', 'piano_image', 'notes_image', 'go_back_image',
        'self_play_image', 'self_midi_image', 'play_midi_image',
        'piano_background_image'
]:
    each_value = eval(each)
    each_path = os.path.dirname(each_value)
    if each_path:
        pyglet.resource.path.append(each_path.replace('/', '\\'))
        exec(f"{each} = '{os.path.basename(each_value)}'")
pyglet.resource.reindex()
icon = pyglet.resource.image('piano.ico')
background = pyglet.resource.image(background_image)
if not background_size:
    ratio_background = screen_width / background.width
    background.width = screen_width
    background.height *= ratio_background
else:
    background.width, background.height = background_size

batch = pyglet.graphics.Batch()
bottom_group = pyglet.graphics.OrderedGroup(0)
piano_bg = pyglet.graphics.OrderedGroup(1)
piano_key = pyglet.graphics.OrderedGroup(2)
play_highlight = pyglet.graphics.OrderedGroup(3)

if not draw_piano_keys:
    bar_offset_x = 9
    image = pyglet.resource.image(piano_image)
    if not piano_size:
        ratio = screen_width / image.width
        image.width = screen_width
        image.height *= ratio
    else:
        image.width, image.height = piano_size
    image_show = pyglet.sprite.Sprite(image,
                                      x=0,
                                      y=0,
                                      batch=batch,
                                      group=piano_bg)
playing = pyglet.resource.image(notes_image)
playing.width /= notes_resize_num
playing.height /= notes_resize_num

if note_mode == 'dots':
    if not draw_piano_keys:
        plays = [
            pyglet.sprite.Sprite(playing,
                                 x=j[0] + dots_offset_x,
                                 y=j[1],
                                 group=play_highlight) for j in note_place
        ]
    else:
        plays = [
            pyglet.sprite.Sprite(playing,
                                 x=j[0] + dots_offset_x,
                                 y=j[1],
                                 group=play_highlight) for j in note_place
        ]
else:
    plays = []

window = pyglet.window.Window(*screen_size, caption='Ideal Piano')
window.set_icon(icon)

label = pyglet.text.Label('',
                          font_name=fonts,
                          font_size=fonts_size,
                          bold=bold,
                          x=label1_place[0],
                          y=label1_place[1],
                          color=message_color,
                          anchor_x=label_anchor_x,
                          anchor_y=label_anchor_y,
                          multiline=True,
                          width=1000)
label2 = pyglet.text.Label('',
                           font_name=fonts,
                           font_size=fonts_size,
                           bold=bold,
                           x=label2_place[0],
                           y=label2_place[1],
                           color=message_color,
                           anchor_x=label_anchor_x,
                           anchor_y=label_anchor_y)
label3 = pyglet.text.Label('',
                           font_name=fonts,
                           font_size=fonts_size,
                           bold=bold,
                           x=label3_place[0],
                           y=label3_place[1],
                           color=message_color,
                           anchor_x=label_anchor_x,
                           anchor_y=label_anchor_y)
if show_music_analysis:
    music_analysis_label = pyglet.text.Label(
        '',
        font_name=fonts,
        font_size=music_analysis_fonts_size,
        bold=bold,
        x=music_analysis_place[0],
        y=music_analysis_place[1],
        color=message_color,
        anchor_x=label_anchor_x,
        anchor_y=label_anchor_y,
        multiline=True,
        width=music_analysis_width)


def get_off_sort(a):
    each_chord = a.split('/')
    for i in range(len(each_chord)):
        current = each_chord[i]
        if 'sort as' in current:
            current = current[:current.index('sort as') - 1]
            if current[0] == '[':
                current += ']'
            each_chord[i] = current
    return '/'.join(each_chord)


def load(dic, path, file_format, volume):
    wavedict = {
        i: pygame.mixer.Sound(f'{path}/{dic[i]}.{file_format}')
        for i in dic
    }
    if volume != None:
        [wavedict[x].set_volume(volume) for x in wavedict]
    return wavedict


def configkey(q):
    return pressed(f'{config_key} + {q}')


def configshow(content):
    label.text = str(content)


def switchs(q, name):
    if configkey(q):
        globals()[name] = not globals()[name]
        configshow(f'{name} changes to {globals()[name]}')


mouse_pos = 0, 0
first_time = True
message_label = False
notedic = key_settings
func = None
midi_device_load = False
piano_height = white_key_y + white_key_height
piano_keys = []
initial_colors = []
if draw_piano_keys:
    piano_background = pyglet.resource.image(piano_background_image)
    if not piano_size:
        ratio = screen_width / piano_background.width
        piano_background.width = screen_width
        piano_background.height *= ratio
    else:
        piano_background.width, piano_background.height = piano_size
    piano_background_show = pyglet.sprite.Sprite(piano_background,
                                                 x=0,
                                                 y=0,
                                                 batch=batch,
                                                 group=piano_bg)
    for i in range(white_keys_number):
        current_piano_key = shapes.Rectangle(x=white_key_start_x +
                                             white_key_interval * i,
                                             y=white_key_y,
                                             width=white_key_width,
                                             height=white_key_height,
                                             color=white_key_color,
                                             batch=batch,
                                             group=piano_key)
        piano_keys.append(current_piano_key)
        initial_colors.append((current_piano_key.x, white_key_color))
    first_black_key = shapes.Rectangle(x=black_key_first_x,
                                       y=black_key_y,
                                       width=black_key_width,
                                       height=black_key_height,
                                       color=black_key_color,
                                       batch=batch,
                                       group=piano_key)
    piano_keys.append(first_black_key)
    initial_colors.append((first_black_key.x, black_key_color))
    current_start = black_key_start_x
    for j in range(black_keys_set_num):
        for k in black_keys_set:
            current_start += k
            piano_keys.append(
                shapes.Rectangle(x=current_start,
                                 y=black_key_y,
                                 width=black_key_width,
                                 height=black_key_height,
                                 color=black_key_color,
                                 batch=batch,
                                 group=piano_key))
            initial_colors.append((current_start, black_key_color))
        current_start += black_keys_set_interval
    piano_keys.sort(key=lambda s: s.x)
    initial_colors.sort(key=lambda s: s[0])
    initial_colors = [t[1] for t in initial_colors]
    note_place = [(each.x, each.y) for each in piano_keys]
    bar_offset_x = 0


@window.event
def on_draw():
    window.clear()
    background.blit(0, 0)
    if not draw_piano_keys:
        image_show.draw()
    if batch:
        batch.draw()
    if first_time:
        global mode_num
        global func
        init_show()
        func = mode_show
        not_first()
        pyglet.clock.schedule_interval(func, 1 / fps)
    else:
        label.draw()
        label2.draw()
        if message_label:
            label3.draw()


@window.event
def on_close():
    pygame.mixer.music.stop()
    whole_reset()


def whole_reset():
    global read_result
    global set_bpm
    global playls
    global startplay
    global lastshow
    global finished
    global sheetlen
    global wholenotes
    global musicsheet
    global unit_time
    global melody_notes
    global first_time
    read_result = None
    set_bpm = None
    playls.clear()
    startplay = 0
    lastshow = None
    finished = False
    sheetlen = None
    wholenotes.clear()
    musicsheet = None
    unit_time = None
    melody_notes.clear()
    first_time = True
    pyglet.clock.unschedule(func)


currentchord = chord([])
playnotes = []


def reset_click_mode():
    global click_mode
    click_mode = None


def not_first():
    global first_time
    first_time = not first_time


paused = False
pause_start = 0


def mode_show(dt):
    global startplay
    global lastshow
    global finished
    global playls
    global paused
    global pause_start
    global message_label
    global playnotes
    global show_music_analysis_list
    global sheetlen
    if not paused:
        currentime = time.time() - startplay
        if note_mode == 'bars drop':
            if bars_drop_time:
                j = 0
                while j < len(bars_drop_time):
                    next_bar_drop = bars_drop_time[j]
                    if currentime >= next_bar_drop[0]:
                        current_note = next_bar_drop[1]
                        places = note_place[current_note.degree - 21]
                        current_bar = shapes.Rectangle(
                            x=places[0] + bar_offset_x,
                            y=screen_height,
                            width=bar_width,
                            height=bar_unit * current_note.duration /
                            (bpm2 / 130),
                            color=current_note.own_color
                            if use_track_colors else
                            (bar_color if color_mode == 'normal' else
                             (random.randint(0, 255), random.randint(0, 255),
                              random.randint(0, 255))),
                            batch=batch,
                            group=bottom_group)
                        current_bar.opacity = 255 * (
                            current_note.volume /
                            127) if opacity_change_by_velocity else bar_opacity
                        current_bar.num = current_note.degree - 21
                        current_bar.hit_key = False
                        plays.append(current_bar)
                        del bars_drop_time[j]
                        continue
                    j += 1
        for k in range(sheetlen):
            nownote = playls[k]
            current_sound, start_time, stop_time, situation, number, current_note = nownote
            if situation != 2:
                if situation == 0:
                    if currentime >= start_time:
                        if not play_midi_file:
                            current_sound.play()
                        nownote[3] = 1
                        if show_music_analysis:
                            if show_music_analysis_list:
                                current_music_analysis = show_music_analysis_list[
                                    0]
                                if k == current_music_analysis[0]:
                                    music_analysis_label.text = current_music_analysis[
                                        1]
                                    del show_music_analysis_list[0]
                        if note_mode == 'bars':
                            places = note_place[current_note.degree - 21]
                            current_bar = shapes.Rectangle(
                                x=places[0] + bar_offset_x,
                                y=bar_y,
                                width=bar_width,
                                height=bar_unit * current_note.duration /
                                (bpm2 / 130),
                                color=current_note.own_color
                                if use_track_colors else
                                (bar_color if color_mode == 'normal' else
                                 (random.randint(0, 255),
                                  random.randint(0, 255),
                                  random.randint(0, 255))),
                                batch=batch,
                                group=play_highlight)
                            current_bar.opacity = 255 * (
                                current_note.volume / 127
                            ) if opacity_change_by_velocity else bar_opacity
                            plays.append(current_bar)
                elif situation == 1:
                    if currentime >= stop_time:
                        if not play_midi_file:
                            current_sound.fadeout(show_delay_time_actual)
                        nownote[3] = 2
                        if k == sheetlen - 1:
                            finished = True

        playnotes = [wholenotes[x[4]] for x in playls if x[3] == 1]
        if playnotes:
            playnotes.sort(key=lambda x: x.degree)
            if playnotes != lastshow:
                if note_mode == 'dots':
                    if lastshow:
                        for each in lastshow:
                            plays[each.degree - 21].batch = None
                    for i in playnotes:
                        plays[i.degree - 21].batch = batch
                elif draw_piano_keys and note_mode != 'bars drop':
                    if lastshow:
                        for each in lastshow:
                            piano_keys[each.degree -
                                       21].color = initial_colors[each.degree -
                                                                  21]
                    for i in playnotes:
                        piano_keys[
                            i.degree -
                            21].color = i.own_color if use_track_colors else (
                                bar_color if color_mode == 'normal' else
                                (random.randint(0, 255),
                                 random.randint(0, 255),
                                 random.randint(0, 255)))

                lastshow = playnotes
                if show_notes:
                    label.text = str(playnotes)
                if show_chord:
                    chordtype = detect(playnotes, detect_mode, inv_num,
                                       rootpitch, change_from_first,
                                       original_first, same_note_special,
                                       whole_detect, return_fromchord,
                                       two_show_interval, poly_chord_first,
                                       root_position_return_first,
                                       alter_notes_show_degree)
                    label2.text = str(
                        chordtype) if not sort_invisible else get_off_sort(
                            str(chordtype))

        if keyboard.is_pressed(pause_key):
            paused = True
            pause_start = time.time()
            message_label = True
            label3.text = f'paused, press {unpause_key} to unpause'
        if note_mode == 'bars':
            i = 0
            while i < len(plays):
                each = plays[i]
                each.y += bar_steps
                if each.y >= screen_height:
                    each.batch = None
                    del plays[i]
                    continue
                i += 1
        elif note_mode == 'bars drop':
            i = 0
            while i < len(plays):
                each = plays[i]
                each.y -= bar_steps
                if not each.hit_key and each.y <= bars_drop_place:
                    each.hit_key = True
                    if draw_piano_keys:
                        piano_keys[each.num].color = each.color
                if each.height + each.y <= piano_height:
                    each.batch = None
                    if draw_piano_keys:
                        piano_keys[each.num].color = initial_colors[each.num]
                    del plays[i]
                    continue
                i += 1

    else:
        if keyboard.is_pressed(unpause_key):
            paused = False
            message_label = False
            pause_stop = time.time()
            pause_time = pause_stop - pause_start
            startplay += pause_time
    if finished:
        label2.text = ''
        for each in plays:
            each.batch = None
        if show_music_analysis:
            music_analysis_label.text = ''
            show_music_analysis_list = copy(default_show_music_analysis_list)
        label.text = f'music playing finished,\npress {repeat_key} to listen again,\nor press {exit_key} to exit'
        if keyboard.is_pressed(repeat_key):
            if show_notes:
                label.text = 'reloading, please wait...'
            else:
                label.text = ''
            if note_mode == 'bars' or note_mode == 'bars drop':
                plays.clear()
                if note_mode == 'bars drop':
                    bars_drop_time.clear()
            if draw_piano_keys:
                for k in range(len(piano_keys)):
                    piano_keys[k].color = initial_colors[k]
            del playls
            playls = initialize(musicsheet, unit_time, musicsheet.start_time)
            startplay = time.time()
            lastshow = None
            playnotes.clear()
            finished = False
        if keyboard.is_pressed(exit_key):
            sys.exit(0)


if note_mode == 'bars drop':
    bars_drop_time = []
    distances = screen_height - piano_height
    bar_steps = (distances / bars_drop_interval) / adjust_ratio
else:
    bars_drop_interval = 0


def midi_file_play(dt):
    pygame.mixer.music.play()


def initialize(musicsheet, unit_time, start_time):
    global play_midi_file
    play_midi_file = False
    playls = []
    start = start_time * unit_time + bars_drop_interval
    if play_as_midi:
        play_midi_file = True
        pygame.mixer.music.load(path)
        pyglet.clock.schedule_once(midi_file_play, bars_drop_interval)
        for i in range(sheetlen):
            currentnote = musicsheet.notes[i]
            duration = unit_time * currentnote.duration
            interval = unit_time * musicsheet.interval[i]
            currentstart = start
            currentstop = start + duration
            playls.append([0, currentstart, currentstop, 0, i, currentnote])
            if note_mode == 'bars drop':
                bars_drop_time.append(
                    (currentstart - bars_drop_interval, currentnote))
            start += interval
    else:
        try:
            for i in range(sheetlen):
                currentnote = musicsheet.notes[i]
                currentwav = pygame.mixer.Sound(
                    f'{sound_path}/{currentnote}.{sound_format}')
                duration = unit_time * currentnote.duration
                interval = unit_time * musicsheet.interval[i]
                currentstart = start
                currentstop = start + duration
                note_volume = currentnote.volume / 127
                note_volume *= global_volume
                currentwav.set_volume(note_volume)
                playls.append(
                    [currentwav, currentstart, currentstop, 0, i, currentnote])
                if note_mode == 'bars drop':
                    bars_drop_time.append(
                        (currentstart - bars_drop_interval, currentnote))
                start += interval
        except Exception as e:
            print(str(e))
            pygame.mixer.music.load(path)
            play_midi_file = True
            playls.clear()
            if note_mode == 'bars drop':
                bars_drop_time.clear()
            start = start_time * unit_time + bars_drop_interval
            for i in range(sheetlen):
                currentnote = musicsheet.notes[i]
                duration = unit_time * currentnote.duration
                interval = unit_time * musicsheet.interval[i]
                currentstart = start
                currentstop = start + duration
                playls.append(
                    [0, currentstart, currentstop, 0, i, currentnote])
                if note_mode == 'bars drop':
                    bars_drop_time.append(
                        (currentstart - bars_drop_interval, currentnote))
                start += interval
            pyglet.clock.schedule_once(midi_file_play, bars_drop_interval)
    return playls


melody_notes = []

if show_music_analysis:
    with open(music_analysis_file, encoding='utf-8-sig') as f:
        data = f.read()
        lines = [i for i in data.split('\n\n') if i]
        music_analysis_list = []
        current_key = None
        bar_counter = 0
        for each in lines:
            if each:
                if each[:3] != 'key':
                    current = each.split('\n')
                    current_bar = current[0]
                    if current_bar[0] == '+':
                        bar_counter += eval(current_bar[1:])
                    else:
                        bar_counter = eval(current_bar) - 1
                    current_chords = '\n'.join(current[1:])
                    if current_key:
                        current_chords = f'{key_header}{current_key}\n' + current_chords
                    music_analysis_list.append([bar_counter, current_chords])
                else:
                    current_key = each.split('key: ')[1]


def init_show():
    global playls
    global startplay
    global lastshow
    global finished
    global sheetlen
    global wholenotes
    global musicsheet
    global unit_time
    global melody_notes
    global path
    global bpm2
    setup()
    path = file_path
    if read_result != 'error':
        bpm2, musicsheet, start_time = read_result
    sheetlen = len(musicsheet)
    pygame.mixer.set_num_channels(sheetlen)
    wholenotes = musicsheet.notes
    unit_time = 4 * 60 / bpm2

    # every object in playls has a situation flag at the index of 3,
    # 0 means has not been played yet, 1 means it has started playing,
    # 2 means it has stopped playing
    musicsheet.start_time = start_time
    playls = initialize(musicsheet, unit_time, start_time)
    startplay = time.time()
    lastshow = None
    finished = False
    func = mode_show


def update(dt):
    pass


pyglet.clock.schedule_interval(update, 1 / fps)
pyglet.app.run()
