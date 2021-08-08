file_path = '../temp.mid'
read_result = None
set_bpm = None


def setup():
    global read_result
    all_tracks = read(file_path,
                      None,
                      mode='all',
                      get_off_drums=get_off_drums,
                      to_piece=True)
    tempo_changes = all_tracks.get_tempo_changes()
    all_tracks.clear_tempo()
    all_tracks = [(all_tracks.tempo, all_tracks.tracks[i],
                   all_tracks.start_times[i])
                  for i in range(len(all_tracks.tracks))]
    if clear_pitch_bend:
        for each in all_tracks:
            each[1].clear_pitch_bend(value=0)
    start_time_ls = [j[2] for j in all_tracks]
    first_track_ind = start_time_ls.index(min(start_time_ls))
    all_tracks.insert(0, all_tracks.pop(first_track_ind))
    if use_track_colors:
        color_num = len(all_tracks)
        import random
        if not use_default_tracks_colors:
            colors = []
            for i in range(color_num):
                current_color = tuple(
                    [random.randint(0, 255) for j in range(3)])
                while (colors == (255, 255, 255)) or (current_color in colors):
                    current_color = tuple(
                        [random.randint(0, 255) for j in range(3)])
                colors.append(current_color)
        else:
            colors = tracks_colors
            colors_len = len(colors)
            if colors_len < color_num:
                for k in range(color_num - colors_len):
                    current_color = tuple(
                        [random.randint(0, 255) for j in range(3)])
                    while (colors == (255, 255, 255)) or (current_color
                                                          in colors):
                        current_color = tuple(
                            [random.randint(0, 255) for j in range(3)])
                    colors.append(current_color)
    first_track = all_tracks[0]
    tempo, all_track_notes, first_track_start_time = first_track
    for i in range(len(all_tracks)):
        current = all_tracks[i]
        current_track = current[1]
        if use_track_colors:
            current_color = colors[i]
            for each in current_track:
                each.own_color = current_color
        if i > 0:
            all_track_notes &= (current_track,
                                current[2] - first_track_start_time)
    all_track_notes += tempo_changes
    all_track_notes.normalize_tempo(tempo, start_time=first_track_start_time)
    if clear_all_pitch_bend:
        all_track_notes = all_track_notes.only_notes()
    read_result = tempo, all_track_notes, first_track_start_time
