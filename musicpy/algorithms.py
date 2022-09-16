if __name__ == '__main__' or __name__ == 'algorithms':
    from musicpy import *
else:
    from .musicpy import *
import random
from difflib import SequenceMatcher


def inversion_from(a, b, num=False, mode=0):
    N = len(b)
    for i in range(1, N):
        temp = b.inversion(i)
        if [x.name for x in temp.notes] == [y.name for y in a.notes]:
            return f'/{a[0].name}' if not num else f'{i} inversion'
    return f'could not get chord {a.notes} from a single inversion of chord {b.notes}, you could try sort from' if mode == 0 else None


def sort_from(a, b, getorder=False):
    names = [i.name for i in b]
    try:
        order = [names.index(j.name) + 1 for j in a]
        return f'{b.notes} sort as {order}' if not getorder else order
    except:
        return


def omit_from(a, b, showls=False, alter_notes_show_degree=False):
    a_notes = a.names()
    b_notes = b.names()
    omitnotes = list(set(b_notes) - set(a_notes))
    if alter_notes_show_degree:
        b_first_note = b[0].degree
        omitnotes_degree = []
        for j in omitnotes:
            current = reverse_degree_match[b[b_notes.index(j)].degree -
                                           b_first_note]
            if current == 'not found':
                omitnotes_degree.append(j)
            else:
                omitnotes_degree.append(current)
        omitnotes = omitnotes_degree
    if showls:
        result = omitnotes
    else:
        result = f"omit {', '.join(omitnotes)}"
        order_omit = chord([x for x in b_notes if x in a_notes])
        if order_omit.names() != a.names():
            result += ' ' + inversion_way(a, order_omit)
    return result


def change_from(a,
                b,
                octave_a=False,
                octave_b=False,
                same_degree=True,
                alter_notes_show_degree=False):
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
    anames = a.names()
    bnames = b.names()
    M = min(len(anotes), len(bnotes))
    changes = [(bnames[i], bnotes[i] - anotes[i]) for i in range(M)]
    changes = [x for x in changes if x[1] != 0]
    if any(abs(j[1]) != 1 for j in changes):
        changes = []
    else:
        if not alter_notes_show_degree:
            changes = [f'b{j[0]}' if j[1] > 0 else f'#{j[0]}' for j in changes]
        else:
            b_first_note = b[0].degree
            for i in range(len(changes)):
                note_name, note_change = changes[i]
                current_degree = reverse_degree_match[
                    bnotes[bnames.index(note_name)] - b_first_note]
                if current_degree == 'not found':
                    current_degree = note_name
                if note_change > 0:
                    changes[i] = f'b{current_degree}'
                else:
                    changes[i] = f'#{current_degree}'

    return ', '.join(changes)


def contains(a, b):
    '''
    if b contains a (notes), in other words,
    all of a's notes is inside b's notes
    '''
    return set(a.names()) < set(b.names()) and len(a) < len(b)


def inversion_way(a, b, inv_num=False, chordtype=None, only_msg=False):
    if samenotes(a, b):
        return f'{b[0].name}{chordtype}'
    if samenote_set(a, b):
        inversion_msg = inversion_from(
            a, b, mode=1) if not inv_num else inversion_from(
                a, b, num=True, mode=1)
        if inversion_msg is not None:
            if not only_msg:
                if chordtype is not None:
                    return f'{b[0].name}{chordtype}{inversion_msg}' if not inv_num else f'{b[0].name}{chordtype} {inversion_msg}'
                else:
                    return inversion_msg
            else:
                return inversion_msg
        else:
            sort_msg = sort_from(a, b, getorder=True)
            if sort_msg is not None:
                if not only_msg:
                    if chordtype is not None:
                        return f'{b[0].name}{chordtype} sort as {sort_msg}'
                    else:
                        return f'sort as {sort_msg}'
                else:
                    return f'sort as {sort_msg}'
            else:
                return f'a voicing of {b[0].name}{chordtype}'
    else:
        return 'not good'


def samenotes(a, b):
    return a.names() == b.names()


def samenote_set(a, b):
    return set(a.names()) == set(b.names())


def find_similarity(a,
                    b=None,
                    only_ratio=False,
                    fromchord_name=True,
                    getgoodchord=False,
                    listall=False,
                    ratio_and_chord=False,
                    ratio_chordname=False,
                    provide_name=None,
                    result_ratio=False,
                    get_types=False,
                    change_from_first=False,
                    same_note_special=True,
                    alter_notes_show_degree=False):
    result = ''
    types = None
    if b is None:
        wholeTypes = chordTypes.keynames()
        selfname = a.names()
        rootnote = a[0]
        possible_chords = [(chd(rootnote, i), i) for i in wholeTypes]
        lengths = len(possible_chords)
        if same_note_special:
            ratios = [(1 if samenote_set(a, x[0]) else SequenceMatcher(
                None, selfname, x[0].names()).ratio(), x[1])
                      for x in possible_chords]
        else:
            ratios = [(SequenceMatcher(None, selfname,
                                       x[0].names()).ratio(), x[1])
                      for x in possible_chords]
        alen = len(a)
        ratios_temp = [
            ratios[k] for k in range(len(ratios))
            if len(possible_chords[k][0]) >= alen
        ]
        if len(ratios_temp) != 0:
            ratios = ratios_temp
        ratios.sort(key=lambda x: x[0], reverse=True)
        if listall:
            return ratios
        if only_ratio:
            return ratios[0]
        first = ratios[0]
        highest = first[0]
        chordfrom = possible_chords[wholeTypes.index(first[1])][0]
        if ratio_and_chord:
            if ratio_chordname:
                return first, chordfrom
            return highest, chordfrom
        if highest > 0.6:
            if change_from_first:
                result = find_similarity(
                    a,
                    chordfrom,
                    fromchord_name=False,
                    alter_notes_show_degree=alter_notes_show_degree)
                cff_ind = 0
                while result == 'not good':
                    cff_ind += 1
                    try:
                        first = ratios[cff_ind]
                    except:
                        first = ratios[0]
                        highest = first[0]
                        chordfrom = possible_chords[wholeTypes.index(
                            first[1])][0]
                        result = ''
                        break
                    highest = first[0]
                    chordfrom = possible_chords[wholeTypes.index(first[1])][0]
                    if highest > 0.6:
                        result = find_similarity(
                            a,
                            chordfrom,
                            fromchord_name=False,
                            alter_notes_show_degree=alter_notes_show_degree)
                    else:
                        first = ratios[0]
                        highest = first[0]
                        chordfrom = possible_chords[wholeTypes.index(
                            first[1])][0]
                        result = ''
                        break
            if highest == 1:
                chordfrom_type = first[1]
                if samenotes(a, chordfrom):
                    result = f'{rootnote.name}{chordfrom_type}'
                    types = 'original'
                else:
                    if samenote_set(a, chordfrom):
                        result = inversion_from(a, chordfrom, mode=1)
                        types = 'inversion'
                        if result is None:
                            sort_message = sort_from(a,
                                                     chordfrom,
                                                     getorder=True)
                            if sort_message is None:
                                result = f'a voicing of the chord {rootnote.name}{chordfrom_type}'
                            else:
                                result = f'{rootnote.name}{chordfrom_type} sort as {sort_message}'
                        else:
                            result = f'{rootnote.name}{chordfrom_type} {result}'
                    else:
                        return 'not good'
                if get_types:
                    result = [result, types]
                if result_ratio:
                    return (highest, result) if not getgoodchord else (
                        (highest,
                         result), chordfrom, f'{chordfrom[0].name}{first[1]}')
                return result if not getgoodchord else (
                    result, chordfrom, f'{chordfrom[0].name}{first[1]}')
            else:
                if samenote_set(a, chordfrom):
                    result = inversion_from(a, chordfrom, mode=1)
                    types = 'inversion'
                    if result is None:
                        sort_message = sort_from(a, chordfrom, getorder=True)
                        types = 'inversion'
                        if sort_message is None:
                            return f'a voicing of the chord {rootnote.name}{chordfrom_type}'
                        else:
                            result = f'sort as {sort_message}'
                elif contains(a, chordfrom):
                    result = omit_from(
                        a,
                        chordfrom,
                        alter_notes_show_degree=alter_notes_show_degree)
                    types = 'omit'
                elif len(a) == len(chordfrom):
                    result = change_from(
                        a,
                        chordfrom,
                        alter_notes_show_degree=alter_notes_show_degree)
                    types = 'change'
                if result == '':
                    return 'not good'

                if fromchord_name:
                    from_chord_names = f'{rootnote.name}{first[1]}'
                    result = f'{from_chord_names} {result}'
                if get_types:
                    result = [result, types]
                if result_ratio:
                    return (highest,
                            result) if not getgoodchord else ((highest,
                                                               result),
                                                              chordfrom,
                                                              from_chord_names)
                return result if not getgoodchord else (result, chordfrom,
                                                        from_chord_names)

        else:
            return 'not good'
    else:
        if samenotes(a, b):
            if fromchord_name:
                if provide_name != None:
                    bname = b[0].name + provide_name
                else:
                    bname = detect(
                        b,
                        change_from_first=change_from_first,
                        same_note_special=same_note_special,
                        alter_notes_show_degree=alter_notes_show_degree)
                return bname if not getgoodchord else (bname, chordfrom, bname)
            else:
                return 'same'
        if only_ratio or listall:
            return SequenceMatcher(None, a.names(), b.names()).ratio()
        chordfrom = b
        if samenote_set(a, chordfrom):
            result = inversion_from(a, chordfrom, mode=1)
            if result is None:
                sort_message = sort_from(a, chordfrom, getorder=True)
                if sort_message is None:
                    return f'a voicing of the chord {rootnote.name}{chordfrom_type}'
                else:
                    result = f'sort as {sort_message}'
        elif contains(a, chordfrom):
            result = omit_from(a,
                               chordfrom,
                               alter_notes_show_degree=alter_notes_show_degree)
        elif len(a) == len(chordfrom):
            result = change_from(
                a, chordfrom, alter_notes_show_degree=alter_notes_show_degree)
        if result == '':
            return 'not good'
        bname = None
        if fromchord_name:
            if provide_name != None:
                bname = b[0].name + provide_name
            else:
                bname = detect(b,
                               change_from_first=change_from_first,
                               same_note_special=same_note_special,
                               alter_notes_show_degree=alter_notes_show_degree)
            if isinstance(bname, list):
                bname = bname[0]
        return result if not getgoodchord else (result, chordfrom, bname)


def detect_variation(current_chord,
                     inv_num=False,
                     change_from_first=False,
                     original_first=False,
                     same_note_special=True,
                     N=None,
                     alter_notes_show_degree=False):
    for each in range(1, N):
        each_current = current_chord.inversion(each)
        each_detect = detect(each_current,
                             inv_num,
                             change_from_first,
                             original_first,
                             same_note_special,
                             whole_detect=False,
                             return_fromchord=True,
                             alter_notes_show_degree=alter_notes_show_degree)
        if each_detect is not None:
            detect_msg, change_from_chord, chord_name_str = each_detect
            inv_msg = inversion_way(current_chord, each_current, inv_num)
            result = f'{detect_msg} {inv_msg}'
            if any(x in detect_msg
                   for x in ['sort', '/']) and any(y in inv_msg
                                                   for y in ['sort', '/']):
                inv_msg = inversion_way(current_chord, change_from_chord,
                                        inv_num)
                if inv_msg == 'not good':
                    inv_msg = find_similarity(
                        current_chord,
                        change_from_chord,
                        alter_notes_show_degree=alter_notes_show_degree)
                result = f'{chord_name_str} {inv_msg}'
            return result
    for each2 in range(1, N):
        each_current = current_chord.inversion_highest(each2)
        each_detect = detect(each_current,
                             inv_num,
                             change_from_first,
                             original_first,
                             same_note_special,
                             whole_detect=False,
                             return_fromchord=True,
                             alter_notes_show_degree=alter_notes_show_degree)
        if each_detect is not None:
            detect_msg, change_from_chord, chord_name_str = each_detect
            inv_msg = inversion_way(current_chord, each_current, inv_num)
            result = f'{detect_msg} {inv_msg}'
            if any(x in detect_msg
                   for x in ['sort', '/']) and any(y in inv_msg
                                                   for y in ['sort', '/']):
                inv_msg = inversion_way(current_chord, change_from_chord,
                                        inv_num)
                if inv_msg == 'not good':
                    inv_msg = find_similarity(
                        current_chord,
                        change_from_chord,
                        alter_notes_show_degree=alter_notes_show_degree)
                result = f'{chord_name_str} {inv_msg}'
            return result


def detect_split(current_chord, N=None, **detect_args):
    if N < 6:
        splitind = 1
        lower = current_chord.notes[0].name
        upper = detect(current_chord.notes[splitind:], **detect_args)
        if isinstance(upper, list):
            upper = upper[0]
        return f'[{upper}]/{lower}'
    else:
        splitind = N // 2
        lower = detect(current_chord.notes[:splitind], **detect_args)
        upper = detect(current_chord.notes[splitind:], **detect_args)
        if isinstance(lower, list):
            lower = lower[0]
        if isinstance(upper, list):
            upper = upper[0]
        return f'[{upper}]/[{lower}]'


def interval_check(current_chord):
    times, dist = divmod(
        (current_chord.notes[1].degree - current_chord.notes[0].degree), 12)
    if times > 0:
        dist = 12 + dist
    if dist in INTERVAL:
        interval_name = INTERVAL[dist]
    else:
        interval_name = INTERVAL[dist % 12]
    root_note_name = current_chord[0].name
    if interval_name == 'perfect fifth':
        return f'{root_note_name} with perfect fifth / {root_note_name}5 ({root_note_name} power chord)'
    return f'{root_note_name} with {interval_name}'


def detect(current_chord,
           inv_num=False,
           change_from_first=True,
           original_first=True,
           same_note_special=False,
           whole_detect=True,
           return_fromchord=False,
           poly_chord_first=False,
           root_position_return_first=True,
           alter_notes_show_degree=False):
    if not isinstance(current_chord, chord):
        current_chord = chord(current_chord)
    N = len(current_chord)
    if N == 1:
        return f'note {current_chord.notes[0]}'
    if N == 2:
        return interval_check(current_chord)
    current_chord = current_chord.standardize()
    N = len(current_chord)
    if N == 1:
        return f'note {current_chord.notes[0]}'
    if N == 2:
        return interval_check(current_chord)
    root = current_chord[0].degree
    rootNote = current_chord[0].name
    distance = tuple(i.degree - root for i in current_chord[1:])
    findTypes = detectTypes[distance]
    if findTypes != 'not found':
        return [
            rootNote + i for i in findTypes
        ] if not root_position_return_first else rootNote + findTypes[0]
    original_detect = find_similarity(
        current_chord,
        result_ratio=True,
        change_from_first=change_from_first,
        same_note_special=same_note_special,
        getgoodchord=return_fromchord,
        get_types=True,
        alter_notes_show_degree=alter_notes_show_degree)
    if original_detect != 'not good':
        if return_fromchord:
            original_ratio, original_msg = original_detect[0]
        else:
            original_ratio, original_msg = original_detect
        types = original_msg[1]
        original_msg = original_msg[0]
        if original_first:
            if original_ratio > 0.86 and types != 'change':
                return original_msg if not return_fromchord else (
                    original_msg, original_detect[1], original_detect[2])
        if original_ratio == 1:
            return original_msg if not return_fromchord else (
                original_msg, original_detect[1], original_detect[2])
    for i in range(1, N):
        current = chord(current_chord.inversion(i).names())
        root = current[0].degree
        distance = tuple(i.degree - root for i in current[1:])
        result1 = detectTypes[distance]
        if result1 != 'not found':
            inversion_result = inversion_way(current_chord, current, inv_num,
                                             result1[0])
            if 'sort' in inversion_result:
                continue
            else:
                return inversion_result if not return_fromchord else (
                    inversion_result, current,
                    f'{current[0].name}{result1[0]}')
        else:
            current = current.inoctave()
            root = current[0].degree
            distance = tuple(i.degree - root for i in current[1:])
            result1 = detectTypes[distance]
            if result1 != 'not found':
                inversion_result = inversion_way(current_chord, current,
                                                 inv_num, result1[0])
                if 'sort' in inversion_result:
                    continue
                else:
                    return inversion_result if not return_fromchord else (
                        inversion_result, current,
                        f'{current[0].name}{result1[0]}')
    for i in range(1, N):
        current = chord(current_chord.inversion_highest(i).names())
        root = current[0].degree
        distance = tuple(i.degree - root for i in current[1:])
        result1 = detectTypes[distance]
        if result1 != 'not found':
            inversion_high_result = inversion_way(current_chord, current,
                                                  inv_num, result1[0])
            if 'sort' in inversion_high_result:
                continue
            else:
                return inversion_high_result if not return_fromchord else (
                    inversion_high_result, current,
                    f'{current[0].name}{result1[0]}')
        else:
            current = current.inoctave()
            root = current[0].degree
            distance = tuple(i.degree - root for i in current[1:])
            result1 = detectTypes[distance]
            if result1 != 'not found':
                inversion_high_result = inversion_way(current_chord, current,
                                                      inv_num, result1[0])
                if 'sort' in inversion_high_result:
                    continue
                else:
                    return inversion_high_result if not return_fromchord else (
                        inversion_high_result, current,
                        f'{current[0].name}{result1[0]}')
    if poly_chord_first and N > 3:
        return detect_split(
            current_chord,
            N,
            inv_num=inv_num,
            change_from_first=change_from_first,
            original_first=original_first,
            same_note_special=same_note_special,
            whole_detect=whole_detect,
            return_fromchord=return_fromchord,
            poly_chord_first=poly_chord_first,
            root_position_return_first=root_position_return_first,
            alter_notes_show_degree=alter_notes_show_degree)
    inversion_final = True
    possibles = [
        (find_similarity(current_chord.inversion(j),
                         result_ratio=True,
                         change_from_first=change_from_first,
                         same_note_special=same_note_special,
                         getgoodchord=True,
                         alter_notes_show_degree=alter_notes_show_degree), j)
        for j in range(1, N)
    ]
    possibles = [x for x in possibles if x[0] != 'not good']
    if len(possibles) == 0:
        possibles = [
            (find_similarity(current_chord.inversion_highest(j),
                             result_ratio=True,
                             change_from_first=change_from_first,
                             same_note_special=same_note_special,
                             getgoodchord=True,
                             alter_notes_show_degree=alter_notes_show_degree),
             j) for j in range(1, N)
        ]
        possibles = [x for x in possibles if x[0] != 'not good']
        inversion_final = False
    if len(possibles) == 0:
        if original_detect != 'not good':
            return original_msg if not return_fromchord else (
                original_msg, original_detect[1], original_detect[2])
        if not whole_detect:
            return
        else:
            detect_var = detect_variation(current_chord, inv_num,
                                          change_from_first, original_first,
                                          same_note_special, N,
                                          alter_notes_show_degree)
            if detect_var is None:
                result_change = detect(
                    current_chord,
                    inv_num,
                    not change_from_first,
                    original_first,
                    same_note_special,
                    False,
                    return_fromchord,
                    alter_notes_show_degree=alter_notes_show_degree)
                if result_change is None:
                    return detect_split(
                        current_chord,
                        N,
                        inv_num=inv_num,
                        change_from_first=change_from_first,
                        original_first=original_first,
                        same_note_special=same_note_special,
                        whole_detect=whole_detect,
                        return_fromchord=return_fromchord,
                        poly_chord_first=poly_chord_first,
                        root_position_return_first=root_position_return_first,
                        alter_notes_show_degree=alter_notes_show_degree)
                else:
                    return result_change
            else:
                return detect_var
    possibles.sort(key=lambda x: x[0][0][0], reverse=True)
    best = possibles[0][0]
    highest_ratio, highest_msg = best[0]
    if original_detect != 'not good':
        if original_ratio > 0.6 and (original_ratio >= highest_ratio
                                     or 'sort' in highest_msg):
            return original_msg if not return_fromchord else (
                original_msg, original_detect[1], original_detect[2])
    if highest_ratio > 0.6:
        if inversion_final:
            current_invert = current_chord.inversion(possibles[0][1])
        else:
            current_invert = current_chord.inversion_highest(possibles[0][1])
        invfrom_current_invert = inversion_way(current_chord, current_invert,
                                               inv_num)
        highest_msg = best[0][1]
        if any(x in highest_msg
               for x in ['sort', '/']) and any(y in invfrom_current_invert
                                               for y in ['sort', '/']):
            retry_msg = find_similarity(
                current_chord,
                best[1],
                fromchord_name=return_fromchord,
                getgoodchord=return_fromchord,
                alter_notes_show_degree=alter_notes_show_degree)
            if not return_fromchord:
                invfrom_current_invert = retry_msg
            else:
                invfrom_current_invert, fromchord, chordnames = retry_msg
                current_invert = fromchord
                highest_msg = chordnames
            final_result = f'{best[2]} {invfrom_current_invert}'
        else:
            final_result = f'{highest_msg} {invfrom_current_invert}'
        return final_result if not return_fromchord else (final_result,
                                                          current_invert,
                                                          highest_msg)

    if not whole_detect:
        return
    else:
        detect_var = detect_variation(current_chord, inv_num,
                                      change_from_first, original_first,
                                      same_note_special, N,
                                      alter_notes_show_degree)
        if detect_var is None:
            result_change = detect(
                current_chord,
                inv_num,
                not change_from_first,
                original_first,
                same_note_special,
                False,
                return_fromchord,
                alter_notes_show_degree=alter_notes_show_degree)
            if result_change is None:
                return detect_split(
                    current_chord,
                    N,
                    inv_num=inv_num,
                    change_from_first=change_from_first,
                    original_first=original_first,
                    same_note_special=same_note_special,
                    whole_detect=whole_detect,
                    return_fromchord=return_fromchord,
                    poly_chord_first=poly_chord_first,
                    root_position_return_first=root_position_return_first,
                    alter_notes_show_degree=alter_notes_show_degree)
            else:
                return result_change
        else:
            return detect_var


def detect_scale_type(current_scale, mode='scale'):
    if mode == 'scale':
        interval = tuple(current_scale.interval)
    elif mode == 'interval':
        interval = tuple(current_scale)
    scales = detectScale[interval]
    if scales == 'not found':
        if mode == 'scale':
            current_notes = current_scale.getScale()
        elif mode == 'interval':
            current_notes = getchord_by_interval('C',
                                                 current_scale,
                                                 cummulative=False)
        result = detect_in_scale(current_notes,
                                 get_scales=True,
                                 match_len=True)
        if not result:
            return 'not found'
        else:
            return result[0].mode
    else:
        return scales[0]


def choose_melody(focused, now_focus, focus_ratio, focus_notes, remained_notes,
                  pick, avoid_dim_5, chordinner, newchord, choose_from_chord):
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
                    while any(
                        (firstmelody.degree - x.degree) % diminished_fifth == 0
                            for x in newchord.notes):
                        firstmelody = random.choice(pick)
            else:
                # pick up melody notes from chord inner notes
                firstmelody = random.choice(chordinner)
        else:
            firstmelody = random.choice(pick)
            if avoid_dim_5:
                while any(
                    (firstmelody.degree - x.degree) % diminished_fifth == 0
                        for x in newchord.notes):
                    firstmelody = random.choice(pick)
    return firstmelody


def random_composing(mode,
                     length,
                     difficulty='easy',
                     init_notes=None,
                     pattern=None,
                     focus_notes=None,
                     focus_ratio=0.7,
                     avoid_dim_5=True,
                     num=3,
                     left_hand_velocity=70,
                     right_hand_velocity=80,
                     left_hand_meter=4,
                     right_hand_meter=4,
                     choose_intervals=[1 / 8, 1 / 4, 1 / 2],
                     choose_durations=[1 / 8, 1 / 4, 1 / 2],
                     melody_interval_tol=perfect_fourth,
                     choose_from_chord=False):
    '''
    Composing a piece of music randomly from a given mode (here means scale),
    difficulty, number of start notes (or given notes) and an approximate length.
    length is the total approximate total number of notes you want the music to be.
    '''
    if pattern is not None:
        pattern = [int(x) for x in pattern]
    standard = mode.notes[:-1]
    # pick is the sets of notes from the required scales which used to pick up notes for melody
    pick = [x.up(2 * octave) for x in standard]
    focused = False
    if focus_notes != None:
        focused = True
        focus_notes = [pick[i - 1] for i in focus_notes]
        remained_notes = [j for j in pick if j not in focus_notes]
        now_focus = 0
    else:
        focus_notes = None
        remained_notes = None
        now_focus = 0
    # the chord part and melody part will be written separately,
    # but still with some relevations. (for example, avoiding dissonant intervals)
    # the draft of the piece of music would be generated first,
    # and then modify the details of the music (durations, intervals,
    # notes volume, rests and so on)
    basechord = mode.get_allchord(num=num)
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
            choose_more = [x for x in mode if x not in newchord]
            for g in range(left_hand_meter - newchord_len):
                current_choose = random.choice(choose_more)
                if current_choose.degree < newchord[-1].degree:
                    current_choose = current_choose.up(octave)
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
            firstmelody = choose_melody(focused, now_focus, focus_ratio,
                                        focus_notes, remained_notes, pick,
                                        avoid_dim_5, chordinner, newchord,
                                        choose_from_chord)
            firstmelody.volume = right_hand_velocity
            newmelody = [firstmelody]
            length_of_chord = sum(newchord.interval)
            intervals = [random.choice(choose_intervals)]
            firstmelody.duration = random.choice(choose_durations)
            while sum(intervals) <= length_of_chord:
                currentmelody = choose_melody(focused, now_focus, focus_ratio,
                                              focus_notes, remained_notes,
                                              pick, avoid_dim_5, chordinner,
                                              newchord, choose_from_chord)
                while abs(currentmelody.degree -
                          newmelody[-1].degree) > melody_interval_tol:
                    currentmelody = choose_melody(focused, now_focus,
                                                  focus_ratio, focus_notes,
                                                  remained_notes, pick,
                                                  avoid_dim_5, chordinner,
                                                  newchord, choose_from_chord)
                currentmelody.volume = right_hand_velocity
                newinter = random.choice(choose_intervals)
                intervals.append(newinter)
                currentmelody.duration = random.choice(choose_durations)
                newmelody.append(currentmelody)

            distance = [
                abs(x.degree - y.degree) for x in newmelody for y in newmelody
            ]
            if diminished_fifth in distance:
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


def fugue(mode,
          length,
          interval_bass=0.5,
          interval_melody=0.5,
          duration_bass=0.5,
          duration_melody=0.5):
    bassls = mode.notes[:-1]
    melodyls = [x.up(octave) for x in bassls]
    bassnotes = [random.choice(bassls) for j in range(length)]
    melodynotes = [random.choice(melodyls) for k in range(length)]
    bass = chord(bassnotes, duration_bass, interval_bass)
    melody = chord(melodynotes, duration_melody, interval_melody)
    return bass.add(melody, mode='head')


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
    return eval(
        f'''[{f"[{', '.join([f'n[a{i}]' for i in range(k)])}]"} {''.join([f'for a{i} in range(len(n)) ' if i == 0 else f"for a{i} in range(len(n)) if a{i} not in [{', '.join([f'a{t}' for t in range(i)])}] " for i in range(k)])}]''',
        locals())


def negative_harmony(key,
                     current_chord=None,
                     sort=False,
                     get_map=False,
                     keep_root=True):
    notes_dict = [
        'C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F'
    ] * 2
    key_tonic = key[0].name
    if key_tonic in standard_dict:
        key_tonic = standard_dict[key_tonic]
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
                    if current.name in standard_dict:
                        current.name = standard_dict[current.name]
                    current_note = closest_note(current,
                                                map_dict[current.name])
                    notes[each] = current.reset(name=current_note.name,
                                                num=current_note.num)
            if sort:
                temp.notes.sort(key=lambda s: s.degree)
            return temp
        else:
            raise ValueError('requires a chord object')
    else:
        temp = copy(key)
        if temp.notes[-1].degree - temp.notes[0].degree == octave:
            temp.notes = temp.notes[:-1]
        notes = temp.notes
        for each in range(len(notes)):
            current = notes[each]
            if current.name in standard_dict:
                current.name = standard_dict[current.name]
            notes[each] = current.reset(name=map_dict[current.name])
        if keep_root:
            root_note = key[0].name
            if root_note in standard_dict:
                root_note = standard_dict[root_note]
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
                 tuning=['E2', 'A2', 'D3', 'G3', 'B3', 'E4'],
                 duration=0.25,
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
    tuning = [N(i) for i in tuning]
    guitar_notes = [
        tuning[j].up(frets[j]) for j in range(6) if frets[j] is not None
    ]
    result = chord(guitar_notes, duration, interval)
    if return_chord:
        return result
    return detect(result.sortchord(), **detect_args)


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
    if current_scale.mode != 'major' and current_scale.mode in diatonic_modes:
        current_scale = current_scale.inversion(
            8 - diatonic_modes.index(current_scale.mode))
    chordtypes = list(chordTypes.dic.keys())
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
        current_chord_type = random.choice(chordtypes)[0]
        current_chord = chd(current_root, current_chord_type)
        while current_chord not in current_scale or current_chord_type == '5' or current_chord in result or (
                chord_length is not None
                and len(current_chord) < chord_length):
            current_chord_type = random.choice(chordtypes)[0]
            current_chord = chd(current_root, current_chord_type)
        result.append(current_chord)
    if chord_length is not None:
        result = [each[:chord_length + 1] for each in result]
    result = [each - octave * down_octave for each in result]
    return result


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
        standard_dict[i] if i not in standard2 else i for i in note_names
    ]
    first_note = whole_notes[0]
    results = []
    if find_altered:
        altered_scales = []
    for each in scaleTypes:
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
                                        k = k.up(octave)
                                    test_scale_exist[inds - 1] = k
                                    if chord(test_scale_exist).intervalof(
                                            cummulative=False
                                    ) not in scaleTypes.values():
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
        inversion_scales = [
            i for i in inversion_scales if i.mode != 'not found'
        ][:search_all_each_num]
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
                        results.insert(first_major_minor_ind + 1,
                                       results[first_major_minor_ind] - 3)
                    elif results[first_major_minor_ind].mode == 'minor':
                        results.insert(first_major_minor_ind + 1,
                                       results[first_major_minor_ind] + 3)

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
            i for i in results if len(i.getScale()) == len(current_chord)
        ]
    if get_scales:
        return results
    else:
        results = [f"{each.start.name} {each.mode}" for each in results]
        return results


def most_appear_notes_detect_scale(current_chord, most_appeared_note):
    third_degree_major = most_appeared_note.up(major_third).name
    third_degree_minor = most_appeared_note.up(minor_third).name
    if current_chord.count(third_degree_major) > current_chord.count(
            third_degree_minor):
        current_mode = 'major'
        if current_chord.count(most_appeared_note.up(
                augmented_fourth).name) > current_chord.count(
                    most_appeared_note.up(perfect_fourth).name):
            current_mode = 'lydian'
        else:
            if current_chord.count(most_appeared_note.up(
                    minor_seventh).name) > current_chord.count(
                        most_appeared_note.up(major_seventh).name):
                current_mode = 'mixolydian'
    else:
        current_mode = 'minor'
        if current_chord.count(
                most_appeared_note.up(major_sixth).name) > current_chord.count(
                    most_appeared_note.up(minor_sixth).name):
            current_mode = 'dorian'
        else:
            if current_chord.count(most_appeared_note.up(
                    minor_second).name) > current_chord.count(
                        most_appeared_note.up(major_second).name):
                current_mode = 'phrygian'
                if current_chord.count(
                        most_appeared_note.up(
                            diminished_fifth).name) > current_chord.count(
                                most_appeared_note.up(perfect_fifth).name):
                    current_mode = 'locrian'
    return scale(most_appeared_note.name, current_mode)


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
        most_appear_notes_detect_scale(current_chord, each)
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
                first_chord_info = first_chord.info(get_dict=True)
                if first_chord_info['type'] == 'chord':
                    if first_chord_info['chord type'].startswith('maj'):
                        major_scales = [result_scales[i] for i in major_inds]
                        major_scales = [
                            i for i in major_scales
                            if i.start.name == first_chord_info['root']
                        ] + [
                            i for i in major_scales
                            if i.start.name != first_chord_info['root']
                        ]
                        result_scales = major_scales + [
                            result_scales[j] for j in range(len(result_scales))
                            if j not in major_inds
                        ]
                    elif first_chord_info['chord type'].startswith('m'):
                        minor_scales = [result_scales[i] for i in minor_inds]
                        minor_scales = [
                            i for i in minor_scales
                            if i.start.name == first_chord_info['root']
                        ] + [
                            i for i in minor_scales
                            if i.start.name != first_chord_info['root']
                        ]
                        result_scales = minor_scales + [
                            result_scales[j] for j in range(len(result_scales))
                            if j not in minor_inds
                        ]

    if get_scales:
        return result_scales
    else:
        return f'most likely scales: {", ".join([f"{i.start.name} {i.mode}" for i in result_scales])}'


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
            scale(i[0], diatonic_modes[current_scale_names.index(i[0])])
            for i in scale_notes_counts
        ]
    else:
        current_tonic = [i[0] for i in scale_notes_counts[:most_appear_num]]
        current_ind = [current_scale_names.index(i) for i in current_tonic]
        current_mode = [diatonic_modes[i] for i in current_ind]
        result_scale = [
            scale(current_tonic[i], current_mode[i])
            for i in range(len(current_tonic))
        ]
    if get_scales:
        return result_scale
    else:
        return ', '.join([f"{i.start.name} {i.mode}" for i in result_scale])


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
                scale(i[0], diatonic_modes[current_scale_names.index(i[0])])
                for i in scale_notes_counts
            ]
        else:
            current_tonic = [
                i[0] for i in scale_notes_counts[:most_appear_num]
            ]
            current_ind = [current_scale_names.index(i) for i in current_tonic]
            current_mode = [diatonic_modes[i] for i in current_ind]
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
            result_scale[-1][0][1] = current_range[1]
    if get_scales:
        return result_scale
    else:
        return ', '.join([
            str(i[0]) + ' ' +
            ', '.join([f"{j.start.name} {j.mode}" for j in i[1]])
            for i in result_scale
        ])


def get_chord_root_note(chord_name,
                        get_chord_types=False,
                        to_standard=False,
                        **detect_args):
    types = type(chord_name)
    if types == chord:
        chord_name = detect(chord_name, **detect_args)
        if isinstance(chord_name, list):
            chord_name = chord_name[0]
    elif types == list:
        chord_name = chord_name[0]
    elif types == note:
        chord_name = str(chord_name)
    if chord_name in standard:
        if get_chord_types:
            return chord_name, ''
        else:
            return chord_name
    if chord_name.startswith('note '):
        result = chord_name.split('note ')[1][:2]
        if result in standard:
            if to_standard and result not in standard2:
                result = standard_dict[result]
        else:
            result = result[0]
            if result in standard:
                if to_standard and result not in standard2:
                    result = standard_dict[result]
        if get_chord_types:
            return result, ''
        return result
    if get_chord_types:
        situation = 0
    if chord_name[0] != '[':
        result = chord_name[:2]
        if get_chord_types:
            if '/' in chord_name:
                situation = 0
                part1, part2 = chord_name.split('/')
            else:
                situation = 1

    else:
        if chord_name[-1] == ']':
            inds = chord_name.rfind('[') - 1
        else:
            inds = chord_name.index('/')
        upper, lower = chord_name[:inds], chord_name[inds + 1:]
        if lower[0] != '[':
            result = upper[1:3]
            if get_chord_types:
                situation = 2
        else:
            result = lower[1:3]
            if get_chord_types:
                situation = 3
    if result in standard:
        if result not in standard2:
            result = standard_dict[result]
    else:
        result = result[0]
        if result in standard:
            if result not in standard2:
                result = standard_dict[result]
    if get_chord_types:
        if situation == 0:
            chord_types = part1.split(' ')[0][len(result):]
        elif situation == 1:
            chord_types = chord_name.split(' ')[0][len(result):]
        elif situation == 2:
            upper = upper[1:-1].split(' ')[0]
            chord_types = upper[len(result):]
        elif situation == 3:
            lower = lower[1:-1].split(' ')[0]
            chord_types = lower[len(result):]
        if chord_types == '':
            if 'with ' in chord_name:
                chord_types = 'with ' + chord_name.split('with ')[1]
            else:
                chord_types = 'major'
        return result, chord_types
    return result


def get_chord_type_location(current_chord, mode='functions'):
    if current_chord in chordTypes:
        chord_types = [
            i for i in list(chordTypes.keys()) if current_chord in i
        ][0]
        if mode == 'functions':
            for each, value in chord_function_dict.items():
                if each in chord_types:
                    return value
        elif mode == 'notations':
            for each, value in chord_notation_dict.items():
                if each in chord_types:
                    return value


def get_chord_functions(mode, chords, as_list=False, functions_interval=1):
    if not isinstance(chords, list):
        chords = [chords]
    note_names = mode.names()
    root_note_list = [
        get_chord_root_note(i, True)
        if '/' not in i else [get_chord_root_note(i.split('/', 1), True), i]
        for i in chords
    ]
    functions = []
    for each in root_note_list:
        if isinstance(each[0], tuple):
            current_note, inversion_note = each[1].split('/', 1)
            header = ''
            if inversion_note not in note_names:
                inversion_note, header = inversion_note[:-1], inversion_note[
                    -1]
            if inversion_note not in note_names:
                current_function = each[1]
            else:
                ind = note_names.index(inversion_note) + 1
                current_function = f'{get_chord_functions(mode, current_note)}/{header}{ind}'
        else:
            root_note, chord_types = each
            root_note_obj = note(root_note, 5)
            header = ''
            if root_note not in note_names:
                root_note, header = root_note[:-1], root_note[-1]
            scale_degree = note_names.index(root_note)
            current_function = chord_functions_roman_numerals[scale_degree + 1]
            if chord_types == '' or chord_types == '5':
                original_chord = mode(scale_degree)
                third_type = original_chord[1].degree - original_chord[0].degree
                if third_type == minor_third:
                    current_function = current_function.lower()
            else:
                if chord_types in chordTypes:
                    current_chord = chd(root_note, chord_types)
                    current_chord_names = current_chord.names()
                else:
                    if chord_types[5:] not in NAME_OF_INTERVAL:
                        current_chord_names = None
                    else:
                        current_chord_names = [
                            root_note_obj.name,
                            root_note_obj.up(
                                NAME_OF_INTERVAL[chord_types[5:]]).name
                        ]
                if chord_types in chord_function_dict:
                    to_lower, function_name = chord_function_dict[chord_types]
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
                            M3 = root_note_obj.up(major_third).name
                            m3 = root_note_obj.up(minor_third).name
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
        get_chord_root_note(i, True)
        if '/' not in i else [get_chord_root_note(i.split('/', 1), True), i]
        for i in chords
    ]
    notations = []
    for each in root_note_list:
        if isinstance(each[0], tuple):
            current_note, inversion_note = each[1].split('/', 1)
            current_notation = f'{get_chord_notations(current_note)}/{inversion_note}'
        else:
            root_note, chord_types = each
            current_notation = root_note
            root_note_obj = note(root_note, 5)
            if chord_types in chord_notation_dict:
                current_notation += chord_notation_dict[chord_types]
            else:
                notation_result = get_chord_type_location(chord_types,
                                                          mode='notations')
                if notation_result:
                    current_notation += notation_result
                else:
                    if chord_types in chordTypes:
                        current_chord = chd(root_note, chord_types)
                        current_chord_names = current_chord.names()
                    else:
                        if chord_types[5:] not in NAME_OF_INTERVAL:
                            current_chord_names = None
                        else:
                            current_chord_names = [
                                root_note_obj.name,
                                root_note_obj.up(
                                    NAME_OF_INTERVAL[chord_types[5:]]).name
                            ]
                    if current_chord_names:
                        M3 = root_note_obj.up(major_third).name
                        m3 = root_note_obj.up(minor_third).name
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
            get_scales=True
        )[0] if is_chord_analysis else detect_scale_function(
            current_chord,
            major_minor_preference=major_minor_preference,
            get_scales=True,
            is_chord=False)[0]
    if is_chord_analysis:
        result = chord_analysis(current_chord,
                                mode='chords',
                                **chord_analysis_args)
        result = [i.standardize() for i in result]
    else:
        result = current_chord
    if is_detect:
        actual_chords = [detect(i, **detect_args) for i in result]
        actual_chords = [
            i[0] if isinstance(i, list) else i for i in actual_chords
        ]
    else:
        actual_chords = current_chord
    if chord_mode == 'function':
        chord_progressions = get_chord_functions(
            mode=scales,
            chords=actual_chords,
            as_list=True,
            functions_interval=functions_interval)
        if full_chord_msg:
            chord_progressions = [
                f'{actual_chords[i]} {chord_progressions[i]}'
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
                delimiter.join(actual_chords[each_line_chords_number *
                                             i:each_line_chords_number *
                                             (i + 1)]) + delimiter
                for i in range(num)
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
    spaces = '\n' * space_lines
    analysis_result = f'key: {scales[0].name} {scales.mode}{spaces}{chord_progressions}'
    if write_to_file:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(analysis_result)
        analysis_result += spaces + f"Successfully write the chord analysis result as a text file, please see '{filename}'."
        return analysis_result
    else:
        return analysis_result


def split_melody(current_chord,
                 mode='index',
                 melody_tol=minor_seventh,
                 chord_tol=major_sixth,
                 get_off_overlap_notes=True,
                 average_degree_length=8,
                 melody_degree_tol=toNote('B4')):
    '''
    if mode == 'notes', return a list of main melody notes
    if mode == 'index', return a list of indexes of main melody notes
    if mode == 'chord', return a chord with main melody notes with original places
    '''
    if not isinstance(melody_degree_tol, note):
        melody_degree_tol = toNote(melody_degree_tol)
    if mode == 'notes':
        result = split_melody(current_chord, 'index', melody_tol, chord_tol,
                              get_off_overlap_notes, average_degree_length,
                              melody_degree_tol)
        current_chord_notes = current_chord.notes
        melody = [current_chord_notes[t] for t in result]
        return melody
    elif mode == 'chord':
        result = split_melody(current_chord, 'index', melody_tol, chord_tol,
                              get_off_overlap_notes, average_degree_length,
                              melody_degree_tol)
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

        play_together = find_all_continuous(whole_interval, 0)
        for each in play_together:
            max_ind = max(each, key=lambda t: whole_notes[t].degree)
            get_off = set(each) - {max_ind}
            for each_ind in get_off:
                whole_notes[each_ind] = None
        whole_notes = [x for x in whole_notes if x is not None]
        N = len(whole_notes) - 1
        start = 0
        if whole_notes[1].degree - whole_notes[0].degree >= chord_tol:
            start = 1
        i = start + 1
        melody = [whole_notes[start]]
        notes_num = 1
        melody_duration = [melody[0].duration]
        while i < N:
            current_note = whole_notes[i]
            next_note = whole_notes[i + 1]
            next_degree_diff = next_note.degree - current_note.degree
            recent_notes = add_to_index(melody_duration, average_degree_length,
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
                        melody_duration.append(current_note.duration)
                    else:
                        if abs(
                                next_degree_diff
                        ) < chord_tol and current_note.degree >= melody_degree_tol.degree:
                            melody.append(current_note)
                            notes_num += 1
                            melody_duration.append(current_note.duration)
                else:

                    if (melody[-1].degree - current_note.degree < chord_tol
                            and next_degree_diff < chord_tol
                            and all(k.degree - current_note.degree < chord_tol
                                    for k in melody[-2:])):
                        melody.append(current_note)
                        notes_num += 1
                        melody_duration.append(current_note.duration)
                    else:
                        if (abs(next_degree_diff) < chord_tol and
                                current_note.degree >= melody_degree_tol.degree
                                and all(
                                    k.degree - current_note.degree < chord_tol
                                    for k in melody[-2:])):
                            melody.append(current_note)
                            notes_num += 1
                            melody_duration.append(current_note.duration)
            i += 1
        melody_inds = [each.number for each in melody]
        whole_inds = melody_inds + other_messages_inds
        whole_inds.sort()
        return whole_inds


def split_chord(current_chord,
                mode='index',
                melody_tol=minor_seventh,
                chord_tol=major_sixth,
                get_off_overlap_notes=True,
                average_degree_length=8,
                melody_degree_tol=toNote('B4')):
    melody_ind = split_melody(current_chord, 'index', melody_tol, chord_tol,
                              get_off_overlap_notes, average_degree_length,
                              melody_degree_tol)
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


def split_all(current_chord,
              mode='index',
              melody_tol=minor_seventh,
              chord_tol=major_sixth,
              get_off_overlap_notes=True,
              average_degree_length=8,
              melody_degree_tol=toNote('B4')):
    '''
    split the main melody and chords part of a piece of music,
    return both of main melody and chord part
    '''
    melody_ind = split_melody(current_chord, 'index', melody_tol, chord_tol,
                              get_off_overlap_notes, average_degree_length,
                              melody_degree_tol)
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
        # shift is the start time that chord part starts after main melody starts,
        # or the start time that main melody starts after chord part starts,
        # depends on which starts earlier, if shift >= 0, chord part starts after main melody,
        # if shift < 0, chord part starts before main melody
        shift = result_chord.start_time - result_melody.start_time
        return [result_melody, result_chord, shift]


def chord_analysis(chords,
                   mode='chord names',
                   is_chord=False,
                   new_chord_tol=minor_seventh,
                   get_original_order=False,
                   formated=False,
                   formated_mode=1,
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
    if formated or (mode in ['inds', 'bars', 'bars start']):
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
    if formated:
        result = [detect(each, **detect_args) for each in chord_ls]
        result = [i if not isinstance(i, list) else i[0] for i in result]
        result_notes = [chord_notes[k[0]:k[1]] for k in chord_inds]
        result_notes = [
            each.sortchord() if all(j == 0
                                    for j in each.interval[:-1]) else each
            for each in result_notes
        ]
        if formated_mode == 0:
            chords_formated = '\n\n'.join([
                f'chord {i+1}: {result[i]}    notes: {result_notes[i]}'
                for i in range(len(result))
            ])
        elif formated_mode == 1:
            num = (len(result) // each_line_chords_number) + 1
            delimiter = ' ' * functions_interval + split_symbol + ' ' * functions_interval
            chords_formated = [
                delimiter.join(result[each_line_chords_number *
                                      i:each_line_chords_number * (i + 1)]) +
                delimiter for i in range(num)
            ]
            chords_formated[-1] = chords_formated[-1][:-len(delimiter)]
            chords_formated = ('\n' * space_lines).join(chords_formated)
        if output_as_file:
            with open('chord analysis result.txt', 'w', encoding='utf-8') as f:
                f.write(chords_formated)
            chords_formated += "\n\nSuccessfully write the chord analysis result as a text file, please see 'chord analysis result.txt'."
        return chords_formated
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
            inds.append(i + 1)
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
            ind += 1
            break
        elif counter > value:
            break
    return ind
