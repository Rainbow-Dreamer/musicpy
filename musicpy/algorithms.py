if __name__ == '__main__' or __name__ == 'algorithms':
    from musicpy import *
else:
    from .musicpy import *
import random
from difflib import SequenceMatcher
import itertools


def inversion_from(a, b, num=False):
    N = len(b)
    for i in range(1, N):
        temp = b.inversion(i)
        if temp.names(standardize_note=True) == a.names(standardize_note=True):
            return a[0].name if not num else i


def sort_from(a, b):
    a_names = a.names(standardize_note=True)
    b_names = b.names(standardize_note=True)
    order = [b_names.index(j) + 1 for j in a_names]
    return order


def omit_from(a, b):
    a_notes = a.names(standardize_note=True)
    b_notes = b.names(standardize_note=True)
    omitnotes = [i for i in b_notes if i not in a_notes]
    b_first_note = b[0]
    omitnotes_degree = []
    for j in omitnotes:
        current_degree = get_pitch_interval(b_first_note, b[b_notes.index(j)])
        precise_degrees = list(database.reverse_precise_degree_match.keys())
        if current_degree not in precise_degrees:
            omitnotes_degree.append(j)
        else:
            current_precise_degree = precise_degrees[precise_degrees.index(
                current_degree)]
            omitnotes_degree.append(
                database.reverse_precise_degree_match[current_precise_degree])
    omitnotes = omitnotes_degree
    return omitnotes


def change_from(a, b, octave_a=False, octave_b=False, same_degree=True):
    '''
    how a is changed from b (flat or sharp some notes of b to get a)
    this is used only when two chords have the same number of notes
    in the detect chord function
    '''
    if octave_a:
        a = a.inoctave()
    if octave_b:
        b = b.inoctave()
    if same_degree:
        b = b.down(12 * (b[0].num - a[0].num))
    N = min(len(a), len(b))
    anotes = [x.degree for x in a.notes]
    bnotes = [x.degree for x in b.notes]
    anames = a.names(standardize_note=True)
    bnames = b.names(standardize_note=True)
    M = min(len(anotes), len(bnotes))
    changes = [(bnames[i], bnotes[i] - anotes[i]) for i in range(M)]
    changes = [x for x in changes if x[1] != 0]
    if any(abs(j[1]) != 1 for j in changes):
        changes = []
    else:
        b_first_note = b[0].degree
        for i, each in enumerate(changes):
            note_name, note_change = each
            if note_change != 0:
                b_root_note = b.notes[0]
                b_current_note = b.notes[bnames.index(note_name)]
                current_b_degree = get_pitch_interval(b_root_note,
                                                      b_current_note)
                precise_degrees = list(
                    database.reverse_precise_degree_match.keys())
                if current_b_degree not in precise_degrees:
                    current_degree = b_current_note.name
                else:
                    current_precise_degree = precise_degrees[
                        precise_degrees.index(current_b_degree)]
                    current_degree = database.reverse_precise_degree_match[
                        current_precise_degree]
                if note_change > 0:
                    changes[i] = f'b{current_degree}'
                else:
                    changes[i] = f'#{current_degree}'
    return changes


def contains(a, b):
    '''
    if b contains a (notes), in other words,
    all of a's notes is inside b's notes
    '''
    return set(a.names(standardize_note=True)) < set(
        b.names(standardize_note=True)) and len(a) < len(b)


def inversion_way(a, b):
    if samenotes(a, b):
        result = None
    elif samenote_set(a, b):
        inversion_msg = inversion_from(a, b, num=True)
        if inversion_msg is not None:
            result = inversion_msg
        else:
            sort_msg = sort_from(a, b)
            result = sort_msg
    else:
        result = None
    return result


def samenotes(a, b):
    return a.names(standardize_note=True) == b.names(standardize_note=True)


def samenote_set(a, b):
    return set(a.names(standardize_note=True)) == set(
        b.names(standardize_note=True))


def find_similarity(a,
                    b=None,
                    b_type=None,
                    change_from_first=True,
                    same_note_special=False,
                    similarity_ratio=0.6,
                    custom_mapping=None):
    current_chord_type = chord_type()
    current_chord_type.order = []
    if b is None:
        current_chord_types = database.chordTypes if custom_mapping is None else custom_mapping[
            2]
        wholeTypes = current_chord_types.keynames()
        selfname = a.names(standardize_note=True)
        root_note = a[0]
        root_note_standardize = note(standardize_note(root_note.name),
                                     root_note.num)
        possible_chords = [(get_chord(root_note_standardize,
                                      each,
                                      custom_mapping=current_chord_types,
                                      pitch_interval=False), each, i)
                           for i, each in enumerate(wholeTypes)]
        lengths = len(possible_chords)
        if same_note_special:
            ratios = [(1 if samenote_set(a, x[0]) else SequenceMatcher(
                None, selfname, x[0].names()).ratio(), x[1], x[2])
                      for x in possible_chords]
        else:
            ratios = [(SequenceMatcher(None, selfname,
                                       x[0].names()).ratio(), x[1], x[2])
                      for x in possible_chords]
        alen = len(a)
        ratios_temp = [
            ratios[k] for k in range(len(ratios))
            if len(possible_chords[k][0]) >= alen
        ]
        if len(ratios_temp) != 0:
            ratios = ratios_temp
        ratios.sort(key=lambda x: x[0], reverse=True)
        first = ratios[0]
        highest = first[0]
        chordfrom = get_chord(root_note,
                              wholeTypes[first[2]],
                              custom_mapping=current_chord_types)
        current_chord_type.highest_ratio = highest
        if highest >= similarity_ratio:
            if change_from_first:
                current_chord_type = find_similarity(
                    a=a,
                    b=chordfrom,
                    b_type=first[1],
                    similarity_ratio=similarity_ratio,
                    custom_mapping=custom_mapping)
                current_chord_type.highest_ratio = highest
                cff_ind = 0
                while current_chord_type.chord_type is None:
                    cff_ind += 1
                    try:
                        first = ratios[cff_ind]
                    except:
                        first = ratios[0]
                        highest = first[0]
                        chordfrom = get_chord(
                            root_note,
                            wholeTypes[first[2]],
                            custom_mapping=current_chord_types)
                        current_chord_type.chord_type = None
                        break
                    highest = first[0]
                    chordfrom = get_chord(root_note,
                                          wholeTypes[first[2]],
                                          custom_mapping=current_chord_types)
                    if highest >= similarity_ratio:
                        current_chord_type = find_similarity(
                            a=a,
                            b=chordfrom,
                            b_type=first[1],
                            similarity_ratio=similarity_ratio,
                            custom_mapping=custom_mapping)
                        current_chord_type.highest_ratio = highest
                    else:
                        first = ratios[0]
                        highest = first[0]
                        chordfrom = get_chord(
                            root_note,
                            wholeTypes[first[2]],
                            custom_mapping=current_chord_types)
                        current_chord_type.chord_type = None
                        break
            if not change_from_first:
                chordfrom_type = first[1]
                current_chord_type = find_similarity(
                    a=a,
                    b=chordfrom,
                    b_type=chordfrom_type,
                    similarity_ratio=similarity_ratio,
                    custom_mapping=custom_mapping)
                current_chord_type.highest_ratio = highest
            return current_chord_type
        else:
            return current_chord_type
    else:
        if b_type is None:
            raise ValueError('requires chord type name of b')
        chordfrom_type = b_type
        chordfrom = b

        if samenotes(a, chordfrom):
            chordfrom_type = detect(current_chord=chordfrom,
                                    change_from_first=change_from_first,
                                    same_note_special=same_note_special,
                                    get_chord_type=True,
                                    custom_mapping=custom_mapping)
            return chordfrom_type

        elif samenote_set(a, chordfrom):
            current_chord_type.root = chordfrom[0].name
            current_chord_type.chord_type = chordfrom_type
            current_inv_msg = inversion_way(a, chordfrom)
            current_chord_type.apply_sort_msg(current_inv_msg,
                                              change_order=True)
        elif contains(a, chordfrom):
            current_omit_msg = omit_from(a, chordfrom)
            current_chord_type.chord_speciality = 'root position'
            current_chord_type.omit = current_omit_msg
            current_chord_type.root = chordfrom[0].name
            current_chord_type.chord_type = chordfrom_type
            current_chord_type._add_order(0)
            current_custom_chord_types = custom_mapping[
                2] if custom_mapping is not None else None
            current_chord_omit = current_chord_type.to_chord(
                custom_mapping=current_custom_chord_types)
            if not samenotes(a, current_chord_omit):
                current_inv_msg = inversion_way(a, current_chord_omit)
                current_chord_type.apply_sort_msg(current_inv_msg,
                                                  change_order=True)
        elif len(a) == len(chordfrom):
            current_change_msg = change_from(a, chordfrom)
            if current_change_msg:
                current_chord_type.chord_speciality = 'altered chord'
                current_chord_type.altered = current_change_msg
                current_chord_type.root = chordfrom[0].name
                current_chord_type.chord_type = chordfrom_type
                current_chord_type._add_order(1)
        return current_chord_type


def detect_variation(current_chord,
                     change_from_first=True,
                     original_first=True,
                     same_note_special=False,
                     similarity_ratio=0.6,
                     N=None,
                     custom_mapping=None):
    current_custom_chord_types = custom_mapping[
        2] if custom_mapping is not None else None
    for each in range(1, N):
        each_current = current_chord.inversion(each)
        each_detect = detect(current_chord=each_current,
                             change_from_first=change_from_first,
                             original_first=original_first,
                             same_note_special=same_note_special,
                             similarity_ratio=similarity_ratio,
                             whole_detect=False,
                             get_chord_type=True,
                             custom_mapping=custom_mapping)
        if each_detect is not None:
            inv_msg = inversion_way(current_chord, each_current)
            if each_detect.voicing is not None:
                change_from_chord = each_detect.to_chord(
                    apply_voicing=False,
                    custom_mapping=current_custom_chord_types)
                inv_msg = inversion_way(current_chord, change_from_chord)
                if inv_msg is None:
                    result = find_similarity(a=current_chord,
                                             b=change_from_chord,
                                             b_type=each_detect.chord_type,
                                             similarity_ratio=similarity_ratio,
                                             custom_mapping=custom_mapping)
                else:
                    result = each_detect
                    result.apply_sort_msg(inv_msg, change_order=True)
            else:
                result = each_detect
                result.apply_sort_msg(inv_msg, change_order=True)
            return result
    for each2 in range(1, N):
        each_current = current_chord.inversion_highest(each2)
        each_detect = detect(current_chord=each_current,
                             change_from_first=change_from_first,
                             original_first=original_first,
                             same_note_special=same_note_special,
                             similarity_ratio=similarity_ratio,
                             whole_detect=False,
                             get_chord_type=True,
                             custom_mapping=custom_mapping)
        if each_detect is not None:
            inv_msg = inversion_way(current_chord, each_current)
            if each_detect.voicing is not None:
                change_from_chord = each_detect.to_chord(
                    apply_voicing=False,
                    custom_mapping=current_custom_chord_types)
                inv_msg = inversion_way(current_chord, change_from_chord)
                if inv_msg is None:
                    result = find_similarity(a=current_chord,
                                             b=change_from_chord,
                                             b_type=each_detect.chord_type,
                                             similarity_ratio=similarity_ratio,
                                             custom_mapping=custom_mapping)
                else:
                    result = each_detect
                    result.apply_sort_msg(inv_msg, change_order=True)
            else:
                result = each_detect
                result.apply_sort_msg(inv_msg, change_order=True)
            return result


def detect_split(current_chord, N=None, **detect_args):
    if N is None:
        N = len(current_chord)
    result = chord_type(chord_speciality='polychord')
    if N < 6:
        splitind = 1
        lower = chord_type(note_name=current_chord.notes[0].name, type='note')
        upper = detect(current_chord.notes[splitind:],
                       get_chord_type=True,
                       **detect_args)
        result.polychords = [lower, upper]
    else:
        splitind = N // 2
        lower = detect(current_chord.notes[:splitind],
                       get_chord_type=True,
                       **detect_args)
        upper = detect(current_chord.notes[splitind:],
                       get_chord_type=True,
                       **detect_args)
        result.polychords = [lower, upper]
    return result


def interval_check(current_chord, custom_mapping=None):
    times, dist = divmod(
        (current_chord.notes[1].degree - current_chord.notes[0].degree), 12)
    if times > 0:
        dist = 12 + dist
    current_interval_dict = database.INTERVAL if custom_mapping is None else custom_mapping[
        0]
    if dist in current_interval_dict:
        interval_name = current_interval_dict[dist]
    else:
        interval_name = current_interval_dict[dist % 12]
    root_note_name = current_chord[0].name
    return root_note_name, interval_name


def _detect_helper(current_chord_type,
                   get_chord_type=False,
                   show_degree=True,
                   custom_mapping=None):
    return current_chord_type.to_text(
        show_degree=show_degree,
        custom_mapping=custom_mapping if current_chord_type.type == 'chord'
        else None) if not get_chord_type else current_chord_type


@method_wrapper(chord)
def detect(current_chord,
           change_from_first=True,
           original_first=True,
           same_note_special=False,
           whole_detect=True,
           poly_chord_first=False,
           root_preference=False,
           show_degree=False,
           get_chord_type=False,
           original_first_ratio=0.86,
           similarity_ratio=0.6,
           custom_mapping=None,
           standardize_note=False):
    current_chord_type = chord_type()
    if not isinstance(current_chord, chord):
        current_chord = chord(current_chord)
    N = len(current_chord)
    if N == 1:
        current_chord_type.type = 'note'
        current_chord_type.note_name = str(current_chord.notes[0])
        return _detect_helper(current_chord_type=current_chord_type,
                              get_chord_type=get_chord_type,
                              show_degree=show_degree,
                              custom_mapping=custom_mapping)
    if N == 2:
        current_root_note_name, current_interval_name = interval_check(
            current_chord, custom_mapping=custom_mapping)
        current_chord_type.type = 'interval'
        current_chord_type.root = current_root_note_name
        current_chord_type.interval_name = current_interval_name
        return _detect_helper(current_chord_type=current_chord_type,
                              get_chord_type=get_chord_type,
                              show_degree=show_degree,
                              custom_mapping=custom_mapping)
    current_chord = current_chord.standardize(
        standardize_note=standardize_note)
    N = len(current_chord)
    if N == 1:
        current_chord_type.type = 'note'
        current_chord_type.note_name = str(current_chord.notes[0])
        return _detect_helper(current_chord_type=current_chord_type,
                              get_chord_type=get_chord_type,
                              show_degree=show_degree,
                              custom_mapping=custom_mapping)
    if N == 2:
        current_root_note_name, current_interval_name = interval_check(
            current_chord, custom_mapping=custom_mapping)
        current_chord_type.type = 'interval'
        current_chord_type.root = current_root_note_name
        current_chord_type.interval_name = current_interval_name
        return _detect_helper(current_chord_type=current_chord_type,
                              get_chord_type=get_chord_type,
                              show_degree=show_degree,
                              custom_mapping=custom_mapping)
    current_chord_type.order = []
    root = current_chord[0].degree
    root_note = current_chord[0].name
    distance = tuple(i.degree - root for i in current_chord[1:])
    current_detect_types = database.detectTypes if custom_mapping is None else custom_mapping[
        1]
    current_custom_chord_types = custom_mapping[
        2] if custom_mapping is not None else None
    if distance in current_detect_types:
        findTypes = current_detect_types[distance]
        current_chord_type.root = root_note
        current_chord_type.chord_type = findTypes[0]
        return _detect_helper(current_chord_type=current_chord_type,
                              get_chord_type=get_chord_type,
                              show_degree=show_degree,
                              custom_mapping=custom_mapping)

    if root_preference:
        current_chord_type_root_preference = detect_chord_by_root(
            current_chord,
            get_chord_type=True,
            custom_mapping=custom_mapping,
            inner=True)
        if current_chord_type_root_preference is not None:
            return _detect_helper(
                current_chord_type=current_chord_type_root_preference,
                get_chord_type=get_chord_type,
                show_degree=show_degree,
                custom_mapping=custom_mapping)

    current_chord_inoctave = current_chord.inoctave()
    root = current_chord_inoctave[0].degree
    distance = tuple(i.degree - root for i in current_chord_inoctave[1:])
    if distance in current_detect_types:
        result = current_detect_types[distance]
        current_chord_type.clear()
        current_invert_msg = inversion_way(current_chord,
                                           current_chord_inoctave)
        current_chord_type.root = current_chord_inoctave[0].name
        current_chord_type.chord_type = result[0]
        current_chord_type.apply_sort_msg(current_invert_msg,
                                          change_order=True)
        return _detect_helper(current_chord_type=current_chord_type,
                              get_chord_type=get_chord_type,
                              show_degree=show_degree,
                              custom_mapping=custom_mapping)

    current_chord_type = find_similarity(a=current_chord,
                                         change_from_first=change_from_first,
                                         same_note_special=same_note_special,
                                         similarity_ratio=similarity_ratio,
                                         custom_mapping=custom_mapping)

    if current_chord_type.chord_type is not None:
        if (original_first and current_chord_type.highest_ratio >=
                original_first_ratio) or current_chord_type.highest_ratio == 1:
            return _detect_helper(current_chord_type=current_chord_type,
                                  get_chord_type=get_chord_type,
                                  show_degree=show_degree,
                                  custom_mapping=custom_mapping)

    current_chord_type_inoctave = find_similarity(
        a=current_chord_inoctave,
        change_from_first=change_from_first,
        same_note_special=same_note_special,
        similarity_ratio=similarity_ratio,
        custom_mapping=custom_mapping)

    if current_chord_type_inoctave.chord_type is not None:
        if (original_first and current_chord_type_inoctave.highest_ratio >=
                original_first_ratio
            ) or current_chord_type_inoctave.highest_ratio == 1:
            current_invert_msg = inversion_way(current_chord,
                                               current_chord_inoctave)
            current_chord_type_inoctave.apply_sort_msg(current_invert_msg,
                                                       change_order=True)
            return _detect_helper(
                current_chord_type=current_chord_type_inoctave,
                get_chord_type=get_chord_type,
                show_degree=show_degree,
                custom_mapping=custom_mapping)

    for i in range(1, N):
        current = chord(current_chord.inversion(i).names())
        distance = current.intervalof()
        if distance not in current_detect_types:
            current = current.inoctave()
            distance = current.intervalof()
        if distance in current_detect_types:
            result = current_detect_types[distance]
            inversion_result = inversion_way(current_chord, current)
            if not isinstance(inversion_result, int):
                continue
            else:
                current_chord_type.clear()
                current_chord_type.chord_speciality = 'inverted chord'
                current_chord_type.inversion = inversion_result
                current_chord_type.root = current[0].name
                current_chord_type.chord_type = result[0]
                current_chord_type._add_order(2)
                return _detect_helper(current_chord_type=current_chord_type,
                                      get_chord_type=get_chord_type,
                                      show_degree=show_degree,
                                      custom_mapping=custom_mapping)
    for i in range(1, N):
        current = chord(current_chord.inversion_highest(i).names())
        distance = current.intervalof()
        if distance not in current_detect_types:
            current = current.inoctave()
            distance = current.intervalof()
        if distance in current_detect_types:
            result = current_detect_types[distance]
            inversion_high_result = inversion_way(current_chord, current)
            if not isinstance(inversion_high_result, int):
                continue
            else:
                current_chord_type.clear()
                current_chord_type.chord_speciality = 'inverted chord'
                current_chord_type.inversion = inversion_high_result
                current_chord_type.root = current[0].name
                current_chord_type.chord_type = result[0]
                current_chord_type._add_order(2)
                return _detect_helper(current_chord_type=current_chord_type,
                                      get_chord_type=get_chord_type,
                                      show_degree=show_degree,
                                      custom_mapping=custom_mapping)
    if poly_chord_first and N > 3:
        current_chord_type = detect_split(current_chord=current_chord,
                                          N=N,
                                          change_from_first=change_from_first,
                                          original_first=original_first,
                                          same_note_special=same_note_special,
                                          whole_detect=whole_detect,
                                          poly_chord_first=poly_chord_first,
                                          show_degree=show_degree,
                                          custom_mapping=custom_mapping)
        return _detect_helper(current_chord_type=current_chord_type,
                              get_chord_type=get_chord_type,
                              show_degree=show_degree,
                              custom_mapping=custom_mapping)
    inversion_final = True
    possibles = [(find_similarity(a=current_chord.inversion(j),
                                  change_from_first=change_from_first,
                                  same_note_special=same_note_special,
                                  similarity_ratio=similarity_ratio,
                                  custom_mapping=custom_mapping), j)
                 for j in range(1, N)]
    possibles = [x for x in possibles if x[0].chord_type is not None]
    if len(possibles) == 0:
        possibles = [(find_similarity(a=current_chord.inversion_highest(j),
                                      change_from_first=change_from_first,
                                      same_note_special=same_note_special,
                                      similarity_ratio=similarity_ratio,
                                      custom_mapping=custom_mapping), j)
                     for j in range(1, N)]
        possibles = [x for x in possibles if x[0].chord_type is not None]
        inversion_final = False
    if len(possibles) == 0:
        if current_chord_type.chord_type is not None:
            return _detect_helper(current_chord_type=current_chord_type,
                                  get_chord_type=get_chord_type,
                                  show_degree=show_degree,
                                  custom_mapping=custom_mapping)
        else:
            if not whole_detect:
                return
    else:
        possibles.sort(key=lambda x: x[0].highest_ratio, reverse=True)
        highest_chord_type, current_inversion = possibles[0]
        if current_chord_type.chord_type is not None:
            if current_chord_type.highest_ratio >= similarity_ratio and (
                    current_chord_type.highest_ratio >=
                    highest_chord_type.highest_ratio
                    or highest_chord_type.voicing is not None):
                return _detect_helper(current_chord_type=current_chord_type,
                                      get_chord_type=get_chord_type,
                                      show_degree=show_degree,
                                      custom_mapping=custom_mapping)
        if highest_chord_type.highest_ratio >= similarity_ratio:
            if inversion_final:
                current_invert = current_chord.inversion(current_inversion)
            else:
                current_invert = current_chord.inversion_highest(
                    current_inversion)
            invfrom_current_invert = inversion_way(current_chord,
                                                   current_invert)
            if highest_chord_type.voicing is not None and not isinstance(
                    invfrom_current_invert, int):
                current_root_position = highest_chord_type.get_root_position()
                current_chord_type = find_similarity(
                    a=current_chord,
                    b=C(current_root_position,
                        custom_mapping=current_custom_chord_types),
                    b_type=highest_chord_type.chord_type,
                    similarity_ratio=similarity_ratio,
                    custom_mapping=custom_mapping)
                current_chord_type.chord_speciality = 'chord voicings'
                current_chord_type.voicing = invfrom_current_invert
                current_chord_type._add_order(3)
            else:
                current_invert_msg = inversion_way(
                    current_chord,
                    highest_chord_type.to_chord(
                        apply_voicing=False,
                        custom_mapping=current_custom_chord_types))
                current_chord_type = highest_chord_type
                current_chord_type.apply_sort_msg(current_invert_msg,
                                                  change_order=True)
            return _detect_helper(current_chord_type=current_chord_type,
                                  get_chord_type=get_chord_type,
                                  show_degree=show_degree,
                                  custom_mapping=custom_mapping)

    if not whole_detect:
        return
    else:
        detect_var = detect_variation(current_chord=current_chord,
                                      change_from_first=change_from_first,
                                      original_first=original_first,
                                      same_note_special=same_note_special,
                                      similarity_ratio=similarity_ratio,
                                      N=N,
                                      custom_mapping=custom_mapping)
        if detect_var is None:
            current_chord_type = detect_split(
                current_chord=current_chord,
                N=N,
                change_from_first=change_from_first,
                original_first=original_first,
                same_note_special=same_note_special,
                whole_detect=whole_detect,
                poly_chord_first=poly_chord_first,
                show_degree=show_degree,
                custom_mapping=custom_mapping)
            return _detect_helper(current_chord_type=current_chord_type,
                                  get_chord_type=get_chord_type,
                                  show_degree=show_degree,
                                  custom_mapping=custom_mapping)
        else:
            current_chord_type = detect_var
            return _detect_helper(current_chord_type=current_chord_type,
                                  get_chord_type=get_chord_type,
                                  show_degree=show_degree,
                                  custom_mapping=custom_mapping)


def detect_chord_by_root(current_chord,
                         get_chord_type=False,
                         show_degree=False,
                         custom_mapping=None,
                         return_mode=0,
                         inner=False,
                         standardize_note=False):
    if not inner:
        current_chord = current_chord.standardize(
            standardize_note=standardize_note)
        if len(current_chord) < 3:
            return detect(current_chord,
                          get_chord_type=get_chord_type,
                          custom_mapping=custom_mapping)
    current_chord_types = []
    current_custom_chord_types = custom_mapping[
        2] if custom_mapping is not None else None
    current_match_chord = _detect_chord_by_root_helper(
        current_chord, custom_mapping=custom_mapping, inner=inner)
    if current_match_chord:
        current_chord_type = find_similarity(
            a=current_chord,
            b=C(f'{current_chord[0].name}{current_match_chord}',
                custom_mapping=current_custom_chord_types),
            b_type=current_match_chord,
            custom_mapping=custom_mapping)
        current_chord_types.append(current_chord_type)
    current_chord_inoctave = current_chord.inoctave()
    if not samenotes(current_chord_inoctave, current_chord):
        current_match_chord_inoctave = _detect_chord_by_root_helper(
            current_chord_inoctave, custom_mapping=custom_mapping, inner=inner)
        if current_match_chord_inoctave and current_match_chord_inoctave != current_match_chord:
            current_chord_type_inoctave = find_similarity(
                a=current_chord,
                b=C(f'{current_chord[0].name}{current_match_chord_inoctave}',
                    custom_mapping=current_custom_chord_types),
                b_type=current_match_chord_inoctave,
                custom_mapping=custom_mapping)
            current_chord_types.append(current_chord_type_inoctave)
    if return_mode == 0:
        if current_chord_types:
            current_chord_types = min(current_chord_types,
                                      key=lambda s: s.get_complexity())
            return current_chord_types if get_chord_type else current_chord_types.to_text(
                show_degree=show_degree)
    else:
        return current_chord_types if get_chord_type else [
            i.to_text(show_degree=show_degree) for i in current_chord_types
        ]


def _detect_chord_by_root_helper(current_chord,
                                 custom_mapping=None,
                                 inner=False):
    current_match_chord = None
    current_note_interval = current_chord.intervalof(translate=True)
    current_note_interval.sort()
    current_note_interval = tuple(current_note_interval)
    current_detect_types = database.detectTypes if not custom_mapping else custom_mapping[
        1]
    current_chord_types = database.chordTypes if not custom_mapping else custom_mapping[
        2]
    if not inner and current_note_interval in current_detect_types:
        return current_detect_types[current_note_interval][0]
    if not any(i in current_note_interval
               for i in database.non_standard_intervals):
        chord_type_intervals = list(current_chord_types.values())
        match_chords = [
            current_detect_types[i][0] for i in chord_type_intervals
            if all((each in i or each - database.octave in i)
                   for each in current_note_interval)
        ]
        if match_chords:
            match_chords.sort(key=lambda s: len(s))
            current_match_chord = match_chords[0]
    return current_match_chord


def detect_scale_type(current_scale, mode='scale'):
    if mode == 'scale':
        interval = tuple(current_scale.interval)
    elif mode == 'interval':
        interval = tuple(current_scale)
    if interval not in database.detectScale:
        if mode == 'scale':
            current_notes = current_scale.get_scale()
        elif mode == 'interval':
            current_notes = get_chord_by_interval('C',
                                                  current_scale,
                                                  cumulative=False)
        result = detect_in_scale(current_notes,
                                 get_scales=True,
                                 match_len=True)
        if not result:
            return None
        else:
            return result[0].mode
    else:
        scales = database.detectScale[interval]
        return scales[0]


def _random_composing_choose_melody(focused, now_focus, focus_ratio,
                                    focus_notes, remained_notes, pick,
                                    avoid_dim_5, chordinner, newchord,
                                    choose_from_chord):
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
                    while any((firstmelody.degree - x.degree) %
                              database.diminished_fifth == 0
                              for x in newchord.notes):
                        firstmelody = random.choice(pick)
            else:
                # pick up melody notes from chord inner notes
                firstmelody = random.choice(chordinner)
        else:
            firstmelody = random.choice(pick)
            if avoid_dim_5:
                while any((firstmelody.degree - x.degree) %
                          database.diminished_fifth == 0
                          for x in newchord.notes):
                    firstmelody = random.choice(pick)
    return firstmelody


def random_composing(current_scale,
                     length,
                     pattern=None,
                     focus_notes=None,
                     focus_ratio=0.7,
                     avoid_dim_5=True,
                     num=3,
                     left_hand_velocity=70,
                     right_hand_velocity=80,
                     left_hand_meter=4,
                     choose_intervals=[1 / 8, 1 / 4, 1 / 2],
                     choose_durations=[1 / 8, 1 / 4, 1 / 2],
                     melody_interval_tol=database.perfect_fourth,
                     choose_from_chord=False):
    '''
    compose a piece of music randomly from a given scale with custom preferences to some degrees in the scale
    '''
    if pattern is not None:
        pattern = [int(x) for x in pattern]
    standard = current_scale.notes[:-1]
    # pick is the sets of notes from the required scales which used to pick up notes for melody
    pick = [x.up(2 * database.octave) for x in standard]
    focused = False
    if focus_notes is not None:
        focused = True
        focus_notes = [pick[i - 1] for i in focus_notes]
        remained_notes = [j for j in pick if j not in focus_notes]
        now_focus = 0
    else:
        focus_notes = None
        remained_notes = None
        now_focus = 0
    # the chord part and melody part will be written separately,
    # but still with some revelations. (for example, avoiding dissonant intervals)
    # the draft of the piece of music would be generated first,
    # and then modify the details of the music (durations, intervals,
    # notes volume, rests and so on)
    basechord = current_scale.get_all_chord(num=num)
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
        newchord_len = len(newchord)
        if newchord_len < left_hand_meter:
            choose_more = [x for x in current_scale if x not in newchord]
            for g in range(left_hand_meter - newchord_len):
                current_choose = random.choice(choose_more)
                if current_choose.degree < newchord[-1].degree:
                    current_choose = current_choose.up(database.octave)
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
            firstmelody = _random_composing_choose_melody(
                focused, now_focus, focus_ratio, focus_notes, remained_notes,
                pick, avoid_dim_5, chordinner, newchord, choose_from_chord)
            firstmelody.volume = right_hand_velocity
            newmelody = [firstmelody]
            length_of_chord = sum(newchord.interval)
            intervals = [random.choice(choose_intervals)]
            firstmelody.duration = random.choice(choose_durations)
            while sum(intervals) <= length_of_chord:
                currentmelody = _random_composing_choose_melody(
                    focused, now_focus, focus_ratio, focus_notes,
                    remained_notes, pick, avoid_dim_5, chordinner, newchord,
                    choose_from_chord)
                while abs(currentmelody.degree -
                          newmelody[-1].degree) > melody_interval_tol:
                    currentmelody = _random_composing_choose_melody(
                        focused, now_focus, focus_ratio, focus_notes,
                        remained_notes, pick, avoid_dim_5, chordinner,
                        newchord, choose_from_chord)
                currentmelody.volume = right_hand_velocity
                newinter = random.choice(choose_intervals)
                intervals.append(newinter)
                currentmelody.duration = random.choice(choose_durations)
                newmelody.append(currentmelody)

            distance = [
                abs(x.degree - y.degree) for x in newmelody for y in newmelody
            ]
            if database.diminished_fifth in distance:
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


def perm(n, k=None):
    '''
    return all of the permutations of the elements in x
    '''
    if isinstance(n, int):
        n = list(range(1, n + 1))
    if isinstance(n, str):
        n = list(n)
    if k is None:
        k = len(n)
    result = list(itertools.permutations(n, k))
    return result


def negative_harmony(key,
                     current_chord=None,
                     sort=False,
                     get_map=False,
                     keep_root=True):
    notes_dict = [
        'C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F'
    ] * 2
    key_tonic = key[0].name
    if key_tonic in database.standard_dict:
        key_tonic = database.standard_dict[key_tonic]
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
    if current_chord:
        if isinstance(current_chord, chord):
            temp = copy(current_chord)
            notes = temp.notes
            for each in range(len(notes)):
                current = notes[each]
                if isinstance(current, note):
                    if current.name in database.standard_dict:
                        current.name = database.standard_dict[current.name]
                    current_note = closest_note(map_dict[current.name],
                                                current)
                    notes[each] = current.reset(name=current_note.name,
                                                num=current_note.num)
            if sort:
                temp.notes.sort(key=lambda s: s.degree)
            return temp
        else:
            raise ValueError('requires a chord object')
    else:
        temp = copy(key)
        if temp.notes[-1].degree - temp.notes[0].degree == database.octave:
            temp.notes = temp.notes[:-1]
        notes = temp.notes
        for each in range(len(notes)):
            current = notes[each]
            if current.name in database.standard_dict:
                current.name = database.standard_dict[current.name]
            notes[each] = current.reset(name=map_dict[current.name])
        if keep_root:
            root_note = key[0].name
            if root_note in database.standard_dict:
                root_note = database.standard_dict[root_note]
            root_note_ind = [i.name for i in notes].index(root_note)
            new_notes = [
                i.name
                for i in notes[root_note_ind + 1:] + notes[:root_note_ind + 1]
            ]
            new_notes.reverse()
            new_notes.append(new_notes[0])
        else:
            new_notes = [i.name for i in notes]
            new_notes.append(new_notes[0])
            new_notes.reverse()
        result = scale(notes=chord(new_notes))
        return result


def guitar_chord(frets,
                 return_chord=True,
                 tuning=database.guitar_standard_tuning,
                 duration=1 / 4,
                 interval=0,
                 **detect_args):
    '''
    the default tuning is the standard tuning E-A-D-G-B-E,
    you can set the tuning to whatever you want
    the parameter frets is a list contains the frets of each string of
    the guitar you want to press in this chord, sorting from 6th string
    to 1st string (which is from E2 string to E4 string in standard tuning),
    the fret of a string is an integer, if it is 0, then it means you
    play that string open (not press any fret on that string),
    if it is 3 for example, then it means you press the third fret on that
    string, if it is None, then that means you did not play that string
    (mute or just not touch that string)
    this function will return the chord types that form by the frets pressing
    at the strings on a guitar, or you can choose to just return the chord
    '''
    tuning = [N(i) if isinstance(i, str) else i for i in tuning]
    length = len(tuning)
    guitar_notes = [
        tuning[j].up(frets[j]) for j in range(length) if frets[j] is not None
    ]
    result = chord(guitar_notes, duration, interval)
    if return_chord:
        return result
    return detect(result.sortchord(), **detect_args)


def guitar_pattern(frets,
                   tuning=database.guitar_standard_tuning,
                   default_duration=1 / 8,
                   default_interval=1 / 8,
                   default_volume=100):
    tuning = [N(i) if isinstance(i, str) else i for i in tuning]
    length = len(tuning)
    current = [i.strip() for i in frets.split(',')]
    notes_result = []
    intervals = []
    start_time = 0
    current_string_ind = length - 1

    for each in current:
        if each == '':
            continue
        if each.startswith('s'):
            current_string_ind = length - int(each.split('s', 1)[1])
        else:
            has_settings = False
            duration = default_duration
            interval = default_interval
            volume = default_volume
            if '[' in each and ']' in each:
                has_settings = True
                each, current_settings = each.split('[', 1)
                current_settings = current_settings[:-1].split(';')
                current_settings_len = len(current_settings)
                if current_settings_len == 1:
                    duration = process_note(current_settings[0])
                else:
                    if current_settings_len == 2:
                        duration, interval = current_settings
                    else:
                        duration, interval, volume = current_settings
                        volume = parse_num(volume)
                    duration = process_note(duration)
                    interval = process_note(
                        interval) if interval != '.' else duration
            current_notes = each.split(';')
            current_length = len(current_notes)
            for i, each_note in enumerate(current_notes):
                has_same_time = True
                if i == current_length - 1:
                    has_same_time = False
                notes_result, intervals, start_time = _read_single_guitar_note(
                    each_note,
                    tuning,
                    length,
                    current_string_ind,
                    duration,
                    interval,
                    volume,
                    notes_result,
                    intervals,
                    start_time,
                    has_settings=has_settings,
                    has_same_time=has_same_time)
    current_chord = chord(notes_result,
                          interval=intervals,
                          start_time=start_time)
    return current_chord


def _read_single_guitar_note(each,
                             tuning,
                             length,
                             current_string_ind,
                             duration,
                             interval,
                             volume,
                             notes_result,
                             intervals,
                             start_time,
                             has_settings=False,
                             has_same_time=False):
    dotted_num = 0
    if each.endswith('.'):
        for k in range(len(each) - 1, -1, -1):
            if each[k] != '.':
                each = each[:k + 1]
                break
            else:
                dotted_num += 1
    if each == 'r':
        current_interval = duration if has_settings else (
            dotted(interval, dotted_num) if interval != 0 else 1 / 4)
        if not notes_result:
            start_time += current_interval
        elif intervals:
            intervals[-1] += current_interval
    elif each == '-':
        current_interval = duration if has_settings else (
            dotted(interval, dotted_num) if interval != 0 else 1 / 4)
        if notes_result:
            notes_result[-1].duration += current_interval
        if intervals:
            intervals[-1] += current_interval
    else:
        if ':' in each:
            current_string, current_fret = each.split(':')
            current_string = current_string.strip()
            current_fret = current_fret.strip()
            current_note_string_ind = length - int(current_string)
            current_note = tuning[current_note_string_ind].up(
                int(current_fret))
        else:
            current_fret = each
            current_note = tuning[current_string_ind].up(int(current_fret))
        current_note.duration = duration
        current_note.volume = volume
        if has_same_time:
            current_interval = 0
            if not has_settings:
                current_note.duration = dotted(current_note.duration,
                                               dotted_num)
        else:
            if has_settings:
                current_interval = interval
            else:
                current_interval = dotted(interval, dotted_num)
                current_note.duration = dotted(current_note.duration,
                                               dotted_num)
        notes_result.append(current_note)
        intervals.append(current_interval)
    return notes_result, intervals, start_time


@method_wrapper(chord)
def find_chords_for_melody(melody,
                           mode=None,
                           num=3,
                           chord_num=8,
                           get_pattern=False,
                           chord_length=None,
                           down_octave=1):
    if isinstance(melody, (str, list)):
        melody = chord(melody)
    possible_scales = detect_in_scale(melody, num, get_scales=True)
    if not possible_scales:
        raise ValueError('cannot find a scale suitable for this melody')
    current_scale = possible_scales[0]
    if current_scale.mode != 'major' and current_scale.mode in database.diatonic_modes:
        current_scale = current_scale.inversion(
            8 - database.diatonic_modes.index(current_scale.mode))
    database.chordTypes = list(database.chordTypes.dic.keys())
    result = []
    if get_pattern:
        choose_patterns = [
            '6451', '1645', '6415', '1564', '4565', '4563', '6545', '6543',
            '4536', '6251'
        ]
        roots = [
            current_scale[i]
            for i in [int(k) for k in random.choice(choose_patterns)]
        ]
        length = len(roots)
        counter = 0
    for i in range(chord_num):
        if not get_pattern:
            current_root = random.choice(current_scale.notes[:6])
        else:
            current_root = roots[counter]
            counter += 1
            if counter >= length:
                counter = 0
        current_chord_type = random.choice(database.chordtypes)[0]
        current_chord = get_chord(current_root, current_chord_type)
        while current_chord not in current_scale or current_chord_type == '5' or current_chord in result or (
                chord_length is not None
                and len(current_chord) < chord_length):
            current_chord_type = random.choice(database.chordtypes)[0]
            current_chord = get_chord(current_root, current_chord_type)
        result.append(current_chord)
    if chord_length is not None:
        result = [each[:chord_length + 1] for each in result]
    result = [each - database.octave * down_octave for each in result]
    return result


@method_wrapper(chord)
def detect_in_scale(current_chord,
                    most_like_num=3,
                    get_scales=False,
                    search_all=True,
                    search_all_each_num=2,
                    major_minor_preference=True,
                    find_altered=True,
                    altered_max_number=1,
                    match_len=False):
    '''
    detect the most possible scales that a set of notes are in,
    this algorithm can also detect scales with altered notes based on
    existing scale definitions
    '''
    current_chord = current_chord.remove_duplicates()
    if not isinstance(current_chord, chord):
        current_chord = chord([trans_note(i) for i in current_chord])
    whole_notes = current_chord.names()
    note_names = list(set(whole_notes))
    note_names = [
        database.standard_dict[i] if i not in database.standard2 else i
        for i in note_names
    ]
    first_note = whole_notes[0]
    results = []
    if find_altered:
        altered_scales = []
    for each in database.scaleTypes:
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
                                        k = k.up(database.octave)
                                    test_scale_exist[inds - 1] = k
                                    if chord(test_scale_exist).intervalof(
                                            cumulative=False
                                    ) not in database.scaleTypes.values():
                                        altered_msg.append(f'{header}{inds}')
                                        altered_scales.append(
                                            f"{current_scale.start.name} {current_scale.mode} {', '.join(altered_msg)}"
                                        )
    if search_all:
        current_chord_len = len(current_chord)
        results.sort(key=lambda s: current_chord_len / len(s), reverse=True)
    if results:
        first_note_scale = results[0]
        inversion_scales = [
            first_note_scale.inversion(i)
            for i in range(2, len(first_note_scale))
        ]
        inversion_scales = [i for i in inversion_scales
                            if i.mode is not None][:search_all_each_num]
        results += inversion_scales
        if major_minor_preference:
            major_or_minor_inds = [
                i for i in range(len(results))
                if results[i].mode in ['major', 'minor']
            ]
            if len(major_or_minor_inds) > 1:
                results.insert(1, results.pop(major_or_minor_inds[1]))
            else:
                if len(major_or_minor_inds) > 0:
                    first_major_minor_ind = major_or_minor_inds[0]
                    if results[first_major_minor_ind].mode == 'major':
                        results.insert(
                            first_major_minor_ind + 1,
                            results[first_major_minor_ind].relative_key())
                    elif results[first_major_minor_ind].mode == 'minor':
                        results.insert(
                            first_major_minor_ind + 1,
                            results[first_major_minor_ind].relative_key())

    results = results[:most_like_num]
    if find_altered:
        for i, each in enumerate(altered_scales):
            current_start, current_mode = each.split(' ', 1)
            current_mode, current_altered = current_mode.rsplit(' ', 1)
            current_scale = scale(current_start, mode=current_mode)
            altered_scales[i] = scale(notes=current_scale.notes,
                                      mode=f'{current_mode} {current_altered}')
        results.extend(altered_scales)
    if match_len:
        results = [
            i for i in results if len(i.get_scale()) == len(current_chord)
        ]
    if get_scales:
        return results
    else:
        results = [f"{each.start.name} {each.mode}" for each in results]
        return results


def _most_appear_notes_detect_scale(current_chord, most_appeared_note):
    third_degree_major = most_appeared_note.up(database.major_third).name
    third_degree_minor = most_appeared_note.up(database.minor_third).name
    if current_chord.count(third_degree_major) > current_chord.count(
            third_degree_minor):
        current_mode = 'major'
        if current_chord.count(
                most_appeared_note.up(
                    database.augmented_fourth).name) > current_chord.count(
                        most_appeared_note.up(database.perfect_fourth).name):
            current_mode = 'lydian'
        else:
            if current_chord.count(
                    most_appeared_note.up(
                        database.minor_seventh).name) > current_chord.count(
                            most_appeared_note.up(
                                database.major_seventh).name):
                current_mode = 'mixolydian'
    else:
        current_mode = 'minor'
        if current_chord.count(
                most_appeared_note.up(
                    database.major_sixth).name) > current_chord.count(
                        most_appeared_note.up(database.minor_sixth).name):
            current_mode = 'dorian'
        else:
            if current_chord.count(
                    most_appeared_note.up(
                        database.minor_second).name) > current_chord.count(
                            most_appeared_note.up(database.major_second).name):
                current_mode = 'phrygian'
                if current_chord.count(
                        most_appeared_note.up(database.diminished_fifth).name
                ) > current_chord.count(
                        most_appeared_note.up(database.perfect_fifth).name):
                    current_mode = 'locrian'
    return scale(most_appeared_note.name, current_mode)


@method_wrapper(chord)
def detect_scale(current_chord,
                 get_scales=False,
                 most_appear_num=5,
                 major_minor_preference=True,
                 is_chord=True):
    '''
    Receive a piece of music and analyze what modes it is using,
    return a list of most likely and exact modes the music has.

    newly added on 2020/4/25, currently in development
    '''
    if not is_chord:
        original_chord = current_chord
        current_chord = concat(current_chord, mode='|')
    current_chord = current_chord.only_notes()
    counts = current_chord.count_appear(sort=True)
    most_appeared_note = [N(each[0]) for each in counts[:most_appear_num]]
    result_scales = [
        _most_appear_notes_detect_scale(current_chord, each)
        for each in most_appeared_note
    ]
    if major_minor_preference:
        major_minor_inds = [
            i for i in range(len(result_scales))
            if result_scales[i].mode in ['major', 'minor']
        ]
        result_scales = [result_scales[i] for i in major_minor_inds] + [
            result_scales[i]
            for i in range(len(result_scales)) if i not in major_minor_inds
        ]
        if major_minor_inds:
            major_minor_inds = [
                i for i in range(len(result_scales))
                if result_scales[i].mode in ['major', 'minor']
            ]
            major_inds = [
                i for i in major_minor_inds if result_scales[i].mode == 'major'
            ]
            minor_inds = [
                i for i in major_minor_inds if result_scales[i].mode == 'minor'
            ]
            current_chord_analysis = chord_analysis(
                current_chord,
                is_chord=True,
                get_original_order=True,
                mode='chords') if is_chord else original_chord
            if current_chord_analysis:
                first_chord = current_chord_analysis[0]
                first_chord_info = first_chord.info()
                if first_chord_info.type == 'chord' and first_chord_info.chord_type:
                    if first_chord_info.chord_type.startswith('maj'):
                        major_scales = [result_scales[i] for i in major_inds]
                        major_scales = [
                            i for i in major_scales
                            if i.start.name == first_chord_info.root
                        ] + [
                            i for i in major_scales
                            if i.start.name != first_chord_info.root
                        ]
                        result_scales = major_scales + [
                            result_scales[j] for j in range(len(result_scales))
                            if j not in major_inds
                        ]
                    elif first_chord_info.chord_type.startswith('m'):
                        minor_scales = [result_scales[i] for i in minor_inds]
                        minor_scales = [
                            i for i in minor_scales
                            if i.start.name == first_chord_info.root
                        ] + [
                            i for i in minor_scales
                            if i.start.name != first_chord_info.root
                        ]
                        result_scales = minor_scales + [
                            result_scales[j] for j in range(len(result_scales))
                            if j not in minor_inds
                        ]

    if get_scales:
        return result_scales
    else:
        return f'most likely scales: {", ".join([f"{i.start.name} {i.mode}" for i in result_scales])}'


@method_wrapper(chord)
def detect_scale2(current_chord,
                  get_scales=False,
                  most_appear_num=3,
                  major_minor_preference=True,
                  is_chord=True):
    '''
    Receive a piece of music and analyze what modes it is using,
    return a list of most likely and exact modes the music has.
    
    This algorithm uses different detect factors from detect_scale function,
    which are the appearance rate of the notes in the tonic chord.
    '''
    if not is_chord:
        current_chord = concat(current_chord, mode='|')
    current_chord = current_chord.only_notes()
    counts = current_chord.count_appear(sort=True)
    counts_dict = {i[0]: i[1] for i in counts}
    appeared_note = [N(each[0]) for each in counts]
    note_scale_count = [
        (i, sum([counts_dict[k]
                 for k in scale(i, 'major').names()]) / len(current_chord))
        for i in appeared_note
    ]
    note_scale_count.sort(key=lambda s: s[1], reverse=True)
    most_appeared_note, current_key_rate = note_scale_count[0]
    current_scale = scale(most_appeared_note, 'major')
    current_scale_names = current_scale.names()
    current_scale_num = len(current_scale_names)
    tonic_chords = [[
        current_scale_names[i],
        current_scale_names[(i + 2) % current_scale_num],
        current_scale_names[(i + 4) % current_scale_num]
    ] for i in range(current_scale_num)]
    scale_notes_counts = [(current_scale_names[k],
                           sum([counts_dict[i] for i in tonic_chords[k]]))
                          for k in range(current_scale_num)]
    scale_notes_counts.sort(key=lambda s: s[1], reverse=True)
    if major_minor_preference:
        scale_notes_counts = [
            i for i in scale_notes_counts
            if i[0] in [current_scale_names[0], current_scale_names[5]]
        ]
        result_scale = [
            scale(i[0],
                  database.diatonic_modes[current_scale_names.index(i[0])])
            for i in scale_notes_counts
        ]
    else:
        current_tonic = [i[0] for i in scale_notes_counts[:most_appear_num]]
        current_ind = [current_scale_names.index(i) for i in current_tonic]
        current_mode = [database.diatonic_modes[i] for i in current_ind]
        result_scale = [
            scale(current_tonic[i], current_mode[i])
            for i in range(len(current_tonic))
        ]
    if get_scales:
        return result_scale
    else:
        return ', '.join([f"{i.start.name} {i.mode}" for i in result_scale])


@method_wrapper(chord)
def detect_scale3(current_chord,
                  get_scales=False,
                  most_appear_num=3,
                  major_minor_preference=True,
                  unit=5,
                  key_accuracy_tol=0.9,
                  is_chord=True):
    '''
    Receive a piece of music and analyze what modes it is using,
    return a list of most likely and exact modes the music has.
    
    This algorithm uses the same detect factors as detect_scale2 function,
    but detect the key of the piece in units, which makes modulation detections possible.
    '''
    if not is_chord:
        current_chord = concat(current_chord, mode='|')
    current_chord = current_chord.only_notes()
    result_scale = []
    total_bars = current_chord.bars()
    current_key = None
    current_key_range = [0, 0]
    for i in range(math.ceil(total_bars / unit)):
        current_range = [unit * i, unit * (i + 1)]
        if current_range[1] >= total_bars:
            current_range[1] = total_bars
        current_part = current_chord.cut(*current_range)
        if not current_part:
            current_key_range[1] = current_range[1]
            if result_scale:
                result_scale[-1][0][1] = current_range[1]
            continue
        counts = current_part.count_appear(sort=True)
        counts_dict = {i[0]: i[1] for i in counts}
        appeared_note = [N(each[0]) for each in counts]
        note_scale_count = [
            (i, sum([counts_dict[k]
                     for k in scale(i, 'major').names()]) / len(current_part))
            for i in appeared_note
        ]
        note_scale_count.sort(key=lambda s: s[1], reverse=True)
        most_appeared_note, current_key_rate = note_scale_count[0]
        if current_key_rate < key_accuracy_tol:
            current_key_range[1] = current_range[1]
            if result_scale:
                result_scale[-1][0][1] = current_range[1]
            continue
        current_scale = scale(most_appeared_note, 'major')
        current_scale_names = current_scale.names()
        current_scale_num = len(current_scale_names)
        tonic_chords = [[
            current_scale_names[i],
            current_scale_names[(i + 2) % current_scale_num],
            current_scale_names[(i + 4) % current_scale_num]
        ] for i in range(current_scale_num)]
        scale_notes_counts = [(current_scale_names[k],
                               sum([counts_dict[i] for i in tonic_chords[k]]))
                              for k in range(current_scale_num)]
        scale_notes_counts.sort(key=lambda s: s[1], reverse=True)
        if major_minor_preference:
            scale_notes_counts = [
                i for i in scale_notes_counts
                if i[0] in [current_scale_names[0], current_scale_names[5]]
            ]
            current_result_scale = [
                scale(i[0],
                      database.diatonic_modes[current_scale_names.index(i[0])])
                for i in scale_notes_counts
            ]
        else:
            current_tonic = [
                i[0] for i in scale_notes_counts[:most_appear_num]
            ]
            current_ind = [current_scale_names.index(i) for i in current_tonic]
            current_mode = [database.diatonic_modes[i] for i in current_ind]
            current_result_scale = [
                scale(current_tonic[i], current_mode[i])
                for i in range(len(current_tonic))
            ]
        if not current_key:
            current_key = current_result_scale
        if not result_scale:
            result_scale.append([current_key_range, current_result_scale])
        if set(current_result_scale) != set(current_key):
            current_key_range = current_range
            current_key = current_result_scale
            result_scale.append([current_key_range, current_result_scale])
        else:
            current_key_range[1] = current_range[1]
            if result_scale:
                result_scale[-1][0][1] = current_range[1]
    if get_scales:
        return result_scale
    else:
        return ', '.join([
            str(i[0]) + ' ' +
            ', '.join([f"{j.start.name} {j.mode}" for j in i[1]])
            for i in result_scale
        ])


def get_chord_root_note(current_chord,
                        get_chord_types=False,
                        to_standard=False):
    if current_chord.type == 'note':
        result = N(current_chord.note_name).name
    else:
        if current_chord.chord_speciality == 'polychord':
            result = get_chord_root_note(current_chord.polychords[0],
                                         to_standard=to_standard)
        else:
            result = current_chord.root
    current_chord_type = current_chord.chord_type
    if current_chord_type is None:
        current_chord_type = ''
    if to_standard:
        result = database.standard_dict.get(result, result)
    if get_chord_types:
        return result, current_chord_type
    else:
        return result


def get_chord_type_location(current_chord, mode='functions'):
    if current_chord in database.chordTypes:
        chord_types = [
            i for i in list(database.chordTypes.keys()) if current_chord in i
        ][0]
        if mode == 'functions':
            for each, value in database.chord_function_dict.items():
                if each in chord_types:
                    return value
        elif mode == 'notations':
            for each, value in database.chord_notation_dict.items():
                if each in chord_types:
                    return value


def get_note_degree_in_scale(root_note, current_scale):
    header = ''
    note_names = current_scale.names()
    if root_note not in note_names:
        current_scale_standard = current_scale.standard()
        root_note = database.standard_dict.get(root_note, root_note)
        if any(get_accidental(i) == 'b' for i in current_scale_standard):
            root_note = N(root_note).flip_accidental().name
        scale_degree = [i[0] for i in current_scale_standard].index(root_note)
        scale_degree_diff = N(root_note).degree - N(
            standardize_note(current_scale_standard[scale_degree])).degree
        if scale_degree_diff == -1:
            header = 'b'
        elif scale_degree_diff == 1:
            header = '#'
    else:
        scale_degree = note_names.index(root_note)
    return scale_degree, header


def get_chord_functions(chords,
                        current_scale,
                        as_list=False,
                        functions_interval=1):
    if not isinstance(chords, list):
        chords = [chords]
    note_names = current_scale.names()
    root_note_list = [
        get_chord_root_note(i, get_chord_types=True) for i in chords
        if i.type == 'chord'
    ]
    functions = []
    for i, each in enumerate(root_note_list):
        current_chord_type = chords[i]
        if current_chord_type.inversion is not None or current_chord_type.non_chord_bass_note is not None:
            current_note = current_chord_type.root
            current_chord_type.order = [2, 4]
            inversion_note = current_chord_type.to_text().rsplit('/', 1)[1]
            current_chord_type.inversion = None
            current_chord_type.non_chord_bass_note = None
            current_inversion_note_degree, current_inversion_note_header = get_note_degree_in_scale(
                inversion_note, current_scale)
            current_function = f'{get_chord_functions(current_chord_type, current_scale)}/{current_inversion_note_header}{current_inversion_note_degree+1}'
        else:
            root_note, chord_types = each
            root_note_obj = note(root_note, 5)
            scale_degree, header = get_note_degree_in_scale(
                root_note, current_scale)
            current_function = database.chord_functions_roman_numerals[
                scale_degree + 1]
            if chord_types == '' or chord_types == '5':
                original_chord = current_scale(scale_degree)
                third_type = original_chord[1].degree - original_chord[0].degree
                if third_type == database.minor_third:
                    current_function = current_function.lower()
            else:
                if chord_types in database.chordTypes:
                    current_chord = get_chord(root_note, chord_types)
                    current_chord_names = current_chord.names()
                else:
                    if chord_types[5:] not in database.NAME_OF_INTERVAL:
                        current_chord_names = None
                    else:
                        current_chord_names = [
                            root_note_obj.name,
                            root_note_obj.up(database.NAME_OF_INTERVAL[
                                chord_types[5:]]).name
                        ]
                if chord_types in database.chord_function_dict:
                    to_lower, function_name = database.chord_function_dict[
                        chord_types]
                    if to_lower:
                        current_function = current_function.lower()
                    current_function += function_name
                else:
                    function_result = get_chord_type_location(chord_types,
                                                              mode='functions')
                    if function_result:
                        to_lower, function_name = function_result
                        if to_lower:
                            current_function = current_function.lower()
                        current_function += function_name
                    else:
                        if current_chord_names:
                            M3 = root_note_obj.up(database.major_third).name
                            m3 = root_note_obj.up(database.minor_third).name
                            if m3 in current_chord_names:
                                current_function = current_function.lower()
                            if len(current_chord_names) >= 3:
                                current_function += '?'
                        else:
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
    if not isinstance(chords, list):
        chords = [chords]
    root_note_list = [
        get_chord_root_note(i, get_chord_types=True) for i in chords
        if i.type == 'chord'
    ]
    notations = []
    for i, each in enumerate(root_note_list):
        current_chord_type = chords[i]
        if current_chord_type.inversion is not None or current_chord_type.non_chord_bass_note is not None:
            current_note = current_chord_type.root
            current_chord_type.order = [2, 4]
            inversion_note = current_chord_type.to_text().rsplit('/', 1)[1]
            current_chord_type.inversion = None
            current_chord_type.non_chord_bass_note = None
            current_notation = f'{get_chord_notations(current_chord_type)}/{inversion_note}'
        else:
            root_note, chord_types = each
            current_notation = root_note
            root_note_obj = note(root_note, 5)
            if chord_types in database.chord_notation_dict:
                current_notation += database.chord_notation_dict[chord_types]
            else:
                notation_result = get_chord_type_location(chord_types,
                                                          mode='notations')
                if notation_result:
                    current_notation += notation_result
                else:
                    if chord_types in database.chordTypes:
                        current_chord = get_chord(root_note, chord_types)
                        current_chord_names = current_chord.names()
                    else:
                        if chord_types[5:] not in database.NAME_OF_INTERVAL:
                            current_chord_names = None
                        else:
                            current_chord_names = [
                                root_note_obj.name,
                                root_note_obj.up(database.NAME_OF_INTERVAL[
                                    chord_types[5:]]).name
                            ]
                    if current_chord_names:
                        M3 = root_note_obj.up(database.major_third).name
                        m3 = root_note_obj.up(database.minor_third).name
                        if m3 in current_chord_names:
                            current_notation += '-'
                        if len(current_chord_names) >= 3:
                            current_notation += '?'
                    else:
                        current_notation += '?'
        notations.append(current_notation)
    if as_list:
        return notations
    return (' ' * functions_interval + split_symbol +
            ' ' * functions_interval).join(notations)


@method_wrapper(chord)
def chord_functions_analysis(current_chord,
                             functions_interval=1,
                             function_symbol='-',
                             split_symbol='|',
                             chord_mode='function',
                             fixed_scale_type=None,
                             return_scale_degrees=False,
                             write_to_file=False,
                             filename='chords functions analysis result.txt',
                             each_line_chords_number=15,
                             space_lines=2,
                             full_chord_msg=False,
                             is_chord_analysis=True,
                             detect_scale_function=detect_scale2,
                             major_minor_preference=True,
                             is_detect=True,
                             detect_args={},
                             chord_analysis_args={}):
    '''
    analysis the chord functions of a chord instance
    '''
    if is_chord_analysis:
        current_chord = current_chord.only_notes()
    else:
        if isinstance(current_chord, chord):
            current_chord = [current_chord]
    if fixed_scale_type:
        scales = fixed_scale_type
    else:
        scales = detect_scale_function(
            current_chord,
            major_minor_preference=major_minor_preference,
            get_scales=True,
            is_chord=is_chord_analysis)[0]
    if is_chord_analysis:
        result = chord_analysis(current_chord,
                                mode='chords',
                                **chord_analysis_args)
        result = [i.standardize() for i in result]
    else:
        result = current_chord
    if is_detect:
        actual_chords = [
            detect(i, get_chord_type=True, **detect_args) for i in result
        ]
    else:
        actual_chords = current_chord
    if chord_mode == 'function':
        chord_progressions = get_chord_functions(
            chords=actual_chords,
            current_scale=scales,
            as_list=True,
            functions_interval=functions_interval)
        if full_chord_msg:
            chord_progressions = [
                f'{actual_chords[i].to_text()} {chord_progressions[i]}'
                for i in range(len(chord_progressions))
            ]
        if return_scale_degrees:
            return chord_progressions
        if write_to_file:
            num = (len(chord_progressions) // each_line_chords_number) + 1
            delimiter = ' ' * functions_interval + function_symbol + ' ' * functions_interval
            chord_progressions = [
                delimiter.join(chord_progressions[each_line_chords_number *
                                                  i:each_line_chords_number *
                                                  (i + 1)]) + delimiter
                for i in range(num)
            ]
            chord_progressions[-1] = chord_progressions[-1][:-len(delimiter)]
            chord_progressions = ('\n' * space_lines).join(chord_progressions)
        else:
            chord_progressions = f' {function_symbol} '.join(
                chord_progressions)
    elif chord_mode == 'notation':
        if full_chord_msg:
            num = (len(actual_chords) // each_line_chords_number) + 1
            delimiter = ' ' * functions_interval + split_symbol + ' ' * functions_interval
            chord_progressions = [
                delimiter.join([
                    j.to_text()
                    for j in actual_chords[each_line_chords_number *
                                           i:each_line_chords_number * (i + 1)]
                ]) + delimiter for i in range(num)
            ]
            chord_progressions[-1] = chord_progressions[-1][:-len(delimiter)]
            chord_progressions = ('\n' * space_lines).join(chord_progressions)
        elif not write_to_file:
            chord_progressions = get_chord_notations(
                chords=actual_chords,
                as_list=True,
                functions_interval=functions_interval,
                split_symbol=split_symbol)
            if return_scale_degrees:
                return chord_progressions
            chord_progressions = f' {split_symbol} '.join(chord_progressions)
        else:
            chord_progressions = get_chord_notations(actual_chords, True,
                                                     functions_interval,
                                                     split_symbol)
            if return_scale_degrees:
                return chord_progressions
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
    else:
        raise ValueError("chord mode must be 'function' or 'notation'")
    spaces = '\n' * space_lines
    analysis_result = f'key: {scales[0].name} {scales.mode}{spaces}{chord_progressions}'
    if write_to_file:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(analysis_result)
        analysis_result += spaces + f"Successfully write the chord analysis result as a text file, please see '{filename}'."
        return analysis_result
    else:
        return analysis_result


@method_wrapper(chord)
def split_melody(current_chord,
                 mode='chord',
                 melody_tol=database.minor_seventh,
                 chord_tol=database.major_sixth,
                 get_off_overlap_notes=True,
                 get_off_same_time=True,
                 average_degree_length=8,
                 melody_degree_tol='B4'):
    '''
    split the melody part of a chord instance
    if mode == 'notes', return a list of main melody notes
    if mode == 'index', return a list of indexes of main melody notes
    if mode == 'chord', return a chord with main melody notes with original places
    '''
    if melody_degree_tol is not None and not isinstance(
            melody_degree_tol, note):
        melody_degree_tol = to_note(melody_degree_tol)
    if mode == 'notes':
        result = split_melody(current_chord=current_chord,
                              mode='index',
                              melody_tol=melody_tol,
                              chord_tol=chord_tol,
                              get_off_overlap_notes=get_off_overlap_notes,
                              get_off_same_time=get_off_same_time,
                              average_degree_length=average_degree_length,
                              melody_degree_tol=melody_degree_tol)
        current_chord_notes = current_chord.notes
        melody = [current_chord_notes[t] for t in result]
        return melody
    elif mode == 'chord':
        result = split_melody(current_chord=current_chord,
                              mode='index',
                              melody_tol=melody_tol,
                              chord_tol=chord_tol,
                              get_off_overlap_notes=get_off_overlap_notes,
                              get_off_same_time=get_off_same_time,
                              average_degree_length=average_degree_length,
                              melody_degree_tol=melody_degree_tol)
        return current_chord.pick(result)

    elif mode == 'index':
        current_chord_notes = current_chord.notes
        current_chord_interval = current_chord.interval
        whole_length = len(current_chord)
        for k in range(whole_length):
            current_chord_notes[k].number = k
        other_messages_inds = [
            i for i in range(whole_length)
            if not isinstance(current_chord_notes[i], note)
        ]
        temp = current_chord.only_notes()
        N = len(temp)
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
            whole_interval = [
                current_chord_interval[j.number] for j in whole_notes
            ]
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
        if get_off_same_time:
            play_together = find_all_continuous(whole_interval, 0)
            for each in play_together:
                max_ind = max(each, key=lambda t: whole_notes[t].degree)
                get_off = set(each) - {max_ind}
                for each_ind in get_off:
                    whole_notes[each_ind] = None
                    whole_interval[each_ind] = None
            whole_notes = [x for x in whole_notes if x is not None]
            whole_interval = [x for x in whole_interval if x is not None]
        N = len(whole_notes) - 1
        start = 0
        if whole_notes[1].degree - whole_notes[0].degree >= chord_tol:
            start = 1
        i = start + 1
        melody = [whole_notes[start]]
        notes_num = 1
        melody_interval = [whole_interval[start]]
        while i < N:
            current_note = whole_notes[i]
            next_note = whole_notes[i + 1]
            current_note_interval = whole_interval[i]
            next_degree_diff = next_note.degree - current_note.degree
            recent_notes = add_to_index(melody_interval, average_degree_length,
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
                        melody_interval.append(current_note_interval)
                    else:
                        if abs(next_degree_diff) < chord_tol and not (
                                melody_degree_tol is not None
                                and current_note.degree <
                                melody_degree_tol.degree):
                            melody.append(current_note)
                            notes_num += 1
                            melody_interval.append(current_note_interval)
                else:

                    if (melody[-1].degree - current_note.degree < chord_tol
                            and next_degree_diff < chord_tol
                            and all(k.degree - current_note.degree < chord_tol
                                    for k in melody[-2:])):
                        melody.append(current_note)
                        notes_num += 1
                        melody_interval.append(current_note_interval)
                    else:
                        if (abs(next_degree_diff) < chord_tol
                                and not (melody_degree_tol is not None
                                         and current_note.degree <
                                         melody_degree_tol.degree) and
                                all(k.degree - current_note.degree < chord_tol
                                    for k in melody[-2:])):
                            melody.append(current_note)
                            notes_num += 1
                            melody_interval.append(current_note_interval)
            i += 1
        melody_inds = [each.number for each in melody]
        whole_inds = melody_inds + other_messages_inds
        whole_inds.sort()
        return whole_inds


@method_wrapper(chord)
def split_chord(current_chord, mode='chord', **args):
    '''
    split the chord part of a chord instance
    '''
    melody_ind = split_melody(current_chord=current_chord,
                              mode='index',
                              **args)
    N = len(current_chord)
    whole_notes = current_chord.notes
    other_messages_inds = [
        i for i in range(N) if not isinstance(whole_notes[i], note)
    ]
    chord_ind = [
        i for i in range(N)
        if (i not in melody_ind) or (i in other_messages_inds)
    ]
    if mode == 'index':
        return chord_ind
    elif mode == 'notes':
        return [whole_notes[k] for k in chord_ind]
    elif mode == 'chord':
        return current_chord.pick(chord_ind)


@method_wrapper(chord)
def split_all(current_chord, mode='chord', **args):
    '''
    split the main melody and chords part of a piece of music,
    return both of main melody and chord part
    '''
    melody_ind = split_melody(current_chord=current_chord,
                              mode='index',
                              **args)
    N = len(current_chord)
    whole_notes = current_chord.notes
    chord_ind = [
        i for i in range(N)
        if (i not in melody_ind) or (not isinstance(whole_notes[i], note))
    ]
    if mode == 'index':
        return [melody_ind, chord_ind]
    elif mode == 'notes':
        return [[whole_notes[j] for j in melody_ind],
                [whole_notes[k] for k in chord_ind]]
    elif mode == 'chord':
        result_chord = current_chord.pick(chord_ind)
        result_melody = current_chord.pick(melody_ind)
        return [result_melody, result_chord]


@method_wrapper(chord)
def chord_analysis(chords,
                   mode='chord names',
                   is_chord=False,
                   new_chord_tol=database.minor_seventh,
                   get_original_order=False,
                   formatted=False,
                   formatted_mode=1,
                   output_as_file=False,
                   each_line_chords_number=5,
                   functions_interval=1,
                   split_symbol='|',
                   space_lines=2,
                   detect_args={},
                   split_chord_args={}):
    '''
    analysis the chord progressions of a chord instance
    '''
    chords = chords.only_notes()
    if not is_chord:
        chord_notes = split_chord(chords, 'chord', **split_chord_args)
    else:
        chord_notes = chords
    if formatted or (mode in ['inds', 'bars', 'bars start']):
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
                if len(current_chord) == 2:
                    if next_note.degree > min(
                        [k.degree for k in current_chord]):
                        current_chord.append(next_note)
                    else:
                        chord_ls.append(chord(current_chord).sortchord())
                        if get_original_order:
                            chord_inds.append(
                                [i + 1 - len(current_chord), i + 1])
                        current_chord = []
                        current_chord.append(next_note)
                else:
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
    if formatted:
        result = [detect(each, **detect_args) for each in chord_ls]
        result = [i if not isinstance(i, list) else i[0] for i in result]
        result_notes = [chord_notes[k[0]:k[1]] for k in chord_inds]
        result_notes = [
            each.sortchord() if all(j == 0
                                    for j in each.interval[:-1]) else each
            for each in result_notes
        ]
        if formatted_mode == 0:
            chords_formatted = '\n\n'.join([
                f'chord {i+1}: {result[i]}    notes: {result_notes[i]}'
                for i in range(len(result))
            ])
        elif formatted_mode == 1:
            num = (len(result) // each_line_chords_number) + 1
            delimiter = ' ' * functions_interval + split_symbol + ' ' * functions_interval
            chords_formatted = [
                delimiter.join(result[each_line_chords_number *
                                      i:each_line_chords_number * (i + 1)]) +
                delimiter for i in range(num)
            ]
            chords_formatted[-1] = chords_formatted[-1][:-len(delimiter)]
            chords_formatted = ('\n' * space_lines).join(chords_formatted)
        if output_as_file:
            with open('chord analysis result.txt', 'w', encoding='utf-8') as f:
                f.write(chords_formatted)
            chords_formatted += "\n\nSuccessfully write the chord analysis result as a text file, please see 'chord analysis result.txt'."
        return chords_formatted
    if mode == 'chords':
        if get_original_order:
            return [chord_notes[k[0]:k[1]] for k in chord_inds]
        return chord_ls
    elif mode == 'chord names':
        result = [detect(each, **detect_args) for each in chord_ls]
        return [i if not isinstance(i, list) else i[0] for i in result]
    elif mode == 'inds':
        return [[i[0], i[1]] for i in chord_inds]
    elif mode == 'bars':
        inds = [[i[0], i[1]] for i in chord_inds]
        return [chord_notes.count_bars(k[0], k[1]) for k in inds]
    elif mode == 'bars start':
        inds = [[i[0], i[1]] for i in chord_inds]
        return [chord_notes.count_bars(k[0], k[1])[0] for k in inds]


def find_continuous(current_chord, value, start=None, stop=None):
    if start is None:
        start = 0
    if stop is None:
        stop = len(current_chord)
    inds = []
    appear = False
    for i in range(start, stop):
        if not appear:
            if current_chord[i] == value:
                appear = True
                inds.append(i)
        else:
            if current_chord[i] == value:
                inds.append(i)
            else:
                break
    return inds


def find_all_continuous(current_chord, value, start=None, stop=None):
    if start is None:
        start = 0
    if stop is None:
        stop = len(current_chord)
    result = []
    inds = []
    appear = False
    for i in range(start, stop):
        if current_chord[i] == value:
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
        if result[-1][-1] >= len(current_chord):
            del result[-1][-1]
    except:
        pass
    return result


def add_to_index(current_chord, value, start=None, stop=None, step=1):
    if start is None:
        start = 0
    if stop is None:
        stop = len(current_chord)
    inds = []
    counter = 0
    for i in range(start, stop, step):
        counter += current_chord[i]
        inds.append(i)
        if counter == value:
            inds.append(i + step)
            break
        elif counter > value:
            break
    if not inds:
        inds = [0]
    return inds


def add_to_last_index(current_chord, value, start=None, stop=None, step=1):
    if start is None:
        start = 0
    if stop is None:
        stop = len(current_chord)
    ind = 0
    counter = 0
    for i in range(start, stop, step):
        counter += current_chord[i]
        ind = i
        if counter == value:
            ind += step
            break
        elif counter > value:
            break
    return ind


def humanize(current_chord,
             timing_range=[-1 / 128, 1 / 128],
             velocity_range=[-10, 10]):
    '''
    add random dynamic changes in given ranges to timing and velocity of notes to a piece
    '''
    temp = copy(current_chord)
    if isinstance(temp, piece):
        temp.tracks = [
            humanize(each, timing_range, velocity_range)
            for each in temp.tracks
        ]
        return temp
    elif isinstance(temp, chord):
        if velocity_range:
            for each in temp.notes:
                each.volume += random.uniform(*velocity_range)
                if each.volume < 0:
                    each.volume = 0
                elif each.volume > 127:
                    each.volume = 127
                each.volume = int(each.volume)
        if timing_range:
            places = [0] + [
                sum(temp.interval[:i]) for i in range(1,
                                                      len(temp.notes) + 1)
            ]
            places = [places[0]] + [
                each + random.choices([random.uniform(*timing_range), 0])[0]
                for each in places[1:]
            ]
            temp.interval = [
                abs(places[i] - places[i - 1]) for i in range(1, len(places))
            ]
        return temp


def write_pop(
        scale_type,
        length=[10, 20],
        melody_ins=1,
        chord_ins=1,
        bpm=120,
        scale_type2=None,
        choose_chord_notes_num=[4],
        default_chord_durations=1 / 2,
        inversion_highest_num=2,
        choose_chord_intervals=[1 / 8],
        choose_melody_durations=[1 / 8, 1 / 16, beat(1 / 8, 1)],
        choose_start_times=[0],
        choose_chord_progressions=None,
        current_choose_chord_progressions_list=None,
        melody_chord_octave_diff=2,
        choose_melody_rhythms=None,
        with_drum_beats=True,
        drum_ins=1,
        with_bass=True,
        bass_octave=2,
        choose_bass_rhythm=database.default_choose_bass_rhythm,
        choose_bass_techniques=database.default_choose_bass_playing_techniques
):
    '''
    write a pop/dance song with melody, chords, bass and drum in a given key,
    currently in development
    '''
    if isinstance(length, list):
        length = random.randint(*length)
    if isinstance(bpm, list):
        bpm = random.randint(*bpm)
    if isinstance(melody_ins, list):
        melody_ins = random.choice(melody_ins)
    if isinstance(chord_ins, list):
        chord_ins = random.choice(chord_ins)
    melody_octave = scale_type[0].num + melody_chord_octave_diff
    if 'minor' in scale_type.mode:
        scale_type = scale_type.relative_key()

    if choose_chord_progressions is None:
        choose_chord_progressions = random.choice(
            database.choose_chord_progressions_list
            if current_choose_chord_progressions_list is None else
            current_choose_chord_progressions_list)
    choose_chords = scale_type % (choose_chord_progressions,
                                  default_chord_durations, 0,
                                  random.choice(choose_chord_notes_num))
    for i in range(len(choose_chords)):
        each = choose_chords[i]
        if each[0] == scale_type[4]:
            each = C(f'{scale_type[4].name}',
                     each[0].num,
                     duration=default_chord_durations) @ [1, 2, 3, 1.1]
            choose_chords[i] = each

    if inversion_highest_num is not None:
        choose_chords = [i ^ inversion_highest_num for i in choose_chords]
    chord_num = len(choose_chords)
    length_count = 0
    chord_ind = 0
    melody = chord([])
    chords_part = chord([])
    if with_bass:
        bass_part = chord([])
        current_bass_techniques = None
        if choose_bass_techniques is not None:
            current_bass_techniques = random.choice(choose_bass_techniques)
    while length_count < length:
        current_chord = choose_chords[chord_ind]
        current_chord_interval = random.choice(choose_chord_intervals)
        if isinstance(current_chord_interval, beat):
            current_chord_interval = current_chord_interval.get_duration()
        current_chord = current_chord.set(interval=current_chord_interval)
        current_chord_length = current_chord.bars(mode=0)
        chords_part |= current_chord
        length_count = chords_part.bars(mode=0)
        if with_bass:
            current_chord_tonic = note(
                scale_type[int(choose_chord_progressions[chord_ind]) - 1].name,
                bass_octave)
            if choose_bass_rhythm is None:
                current_bass_part = chord([current_chord_tonic]) % (
                    current_chord_length, current_chord_length)
            else:
                current_bass_part = get_chords_from_rhythm(
                    chord([current_chord_tonic]),
                    rhythm(*random.choice(choose_bass_rhythm)))
                if current_bass_techniques:
                    if current_bass_techniques == 'octaves':
                        if len(current_bass_part) > 1:
                            for i in range(len(current_bass_part)):
                                if i % 2 != 0:
                                    current_bass_part[i] += 12
            bass_part |= current_bass_part
        while melody.bars(mode=0) < length_count:
            if scale_type2:
                current_melody = copy(random.choice(scale_type2.notes))
            else:
                current_melody = copy(
                    random.choice(current_chord.notes + scale_type.notes))
                current_melody.num = melody_octave
            current_chord_duration = random.choice(choose_melody_durations)
            if isinstance(current_chord_duration, beat):
                current_chord_duration = current_chord_duration.get_duration()
            current_melody.duration = current_chord_duration
            melody.notes.append(current_melody)
            melody.interval.append(copy(current_melody.duration))
        chord_ind += 1
        if chord_ind >= chord_num:
            chord_ind = 0
    chords_part.set_volume(70)
    result = piece(tracks=[melody, chords_part],
                   instruments=[melody_ins, chord_ins],
                   bpm=bpm,
                   start_times=[0, random.choice(choose_start_times)],
                   track_names=['melody', 'chords'],
                   channels=[0, 1])
    result.choose_chord_progressions = choose_chord_progressions
    if with_drum_beats:
        current_drum_beats = drum(
            random.choice(database.default_choose_drum_beats))
        current_drum_beat_repeat_num = math.ceil(
            length / current_drum_beats.notes.bars())
        current_drum_beats *= current_drum_beat_repeat_num
        current_drum_beats.notes.set_volume(70)
        result.append(
            track(content=current_drum_beats.notes,
                  instrument=drum_ins,
                  start_time=result.start_times[1],
                  track_name='drum',
                  channel=9))
    if with_bass:
        bass_part.set_volume(80)
        result.append(
            track(content=bass_part,
                  instrument=34,
                  start_time=result.start_times[1],
                  track_name='bass',
                  channel=2))
    return result
