from copy import deepcopy as copy


class match:

    def __init__(self, current_dict):
        # keys and values should both be a list/tuple/set of data,
        # and they should have the same counts
        # if the key itself is given as a dict, then just use it
        if isinstance(current_dict, dict):
            self.dic = current_dict
        else:
            raise ValueError('a dictionary is required')

    def __call__(self, key, mode=0, index=None):
        # unlike __getitem__, this treat key as a whole to match(mode == 0)
        # when mode == 1, the same as __getitem__,
        # and you can set which index to return in the finding results,
        # if the index is set to None (as default), then return whole results.
        if mode == 0:
            result = self.dic[key]
            if index is None:
                return result
            else:
                return result[index]
        elif mode == 1:
            result = self[key[0]]
            if index is None:
                return result
            else:
                return result[index]

    def __getitem__(self, key):
        dic = self.dic
        for i in dic:
            if key in i:
                return dic[i]
        raise KeyError(key)

    def __contains__(self, obj):
        return any(obj in i for i in self.dic)

    def search_all(self, key):
        result = []
        dic = self.dic
        for i in dic:
            if key in i:
                result.append(dic[i])
        return result

    def keys(self):
        return self.dic.keys()

    def values(self):
        return self.dic.values()

    def items(self):
        return self.dic.items()

    def __iter__(self):
        return self.dic.__iter__()

    def keynames(self):
        return [x[0] for x in self.dic.keys()]

    def valuenames(self):
        return [x[0] for x in self.dic.values()]

    def reverse(self, mode=0):
        dic = self.dic
        return match({((tuple(j), ) if
                       (not isinstance(j, tuple) or mode == 1) else j): i
                      for i, j in dic.items()})

    def __repr__(self):
        return str(self.dic)

    def update(self, key, value=None):
        if isinstance(key, dict):
            self.dic.update(key)
        elif isinstance(key, match):
            self.dic.update(key.dic)
        else:
            if not isinstance(key, (list, tuple, set)):
                key = (key, )
            self.dic[tuple(key)] = value

    def delete(self, key):
        for i in self.dic:
            if key in i:
                del self.dic[i]
                return


class Interval:

    def __init__(self, number, quality, name=None, direction=1):
        self.number = number
        self.quality = quality
        self.name = name
        self.direction = direction
        self.value = self.get_value()

    def __repr__(self):
        return f'{"-" if self.direction == -1 else ""}{self.quality}{self.number}'

    def get_value(self):
        if len(self.quality) > 1 and len(set(self.quality)) == 1:
            current_quality = self.quality[0]
        else:
            current_quality = self.quality
        if current_quality not in quality_dict:
            raise ValueError(
                f'quality {self.quality} is not a valid quality, should be one of {list(quality_dict.keys())} or multiples of each'
            )
        if self.number not in interval_number_dict:
            raise ValueError(
                f'number {self.number} is not a valid number, should be one of {list(interval_number_dict.keys())}'
            )
        times = len(self.quality)
        quality_number = quality_dict[current_quality]
        if current_quality == 'd' and self.number % 7 in [1, 4, 5]:
            quality_number += 1
        if quality_number != 0:
            quality_number_sign = int(quality_number / abs(quality_number))
        else:
            quality_number_sign = 0
        current_value = interval_number_dict[
            self.number] + quality_number + quality_number_sign * (times - 1)
        current_value *= self.direction
        return current_value

    def change_direction(self, direction):
        self.direction = direction
        self.value = self.get_value()

    def __add__(self, other):
        import musicpy as mp
        if isinstance(other, mp.note):
            current_pitch_name = other.name.upper()[0]
            current_pitch_name_ind = standard_pitch_name.index(
                current_pitch_name)
            new_other_name = standard_pitch_name[(current_pitch_name_ind +
                                                  self.direction *
                                                  (self.number - 1)) %
                                                 len(standard_pitch_name)]
            result = mp.degree_to_note(other.degree + self.value)
            result.name = mp.relative_note(result.name, new_other_name)
        else:
            result = self.value + other
        return result

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self.value - other

    def __rsub__(self, other):
        import musicpy as mp
        if isinstance(other, mp.note):
            current_pitch_name = other.name.upper()[0]
            current_pitch_name_ind = standard_pitch_name.index(
                current_pitch_name)
            new_other_name = standard_pitch_name[(current_pitch_name_ind -
                                                  self.direction *
                                                  (self.number - 1)) %
                                                 len(standard_pitch_name)]
            result = mp.degree_to_note(other.degree - self.value)
            result.name = mp.relative_note(result.name, new_other_name)
        else:
            result = other - self.value
        return result

    def __neg__(self):
        result = copy(self)
        result.change_direction(-result.direction)
        return result

    def __gt__(self, other):
        return self.value > other

    def __ge__(self, other):
        return self.value >= other

    def __lt__(self, other):
        return self.value < other

    def __le__(self, other):
        return self.value <= other

    def __eq__(self, other):
        if isinstance(other, Interval):
            return self.value == other.value
        else:
            return self.value == other

    def __mul__(self, other):
        return self.value * other

    def __rmul__(self, other):
        return other * self.value

    def __truediv__(self, other):
        return self.value / other

    def __rtruediv__(self, other):
        return other / self.value

    def __floordiv__(self, other):
        return self.value // other

    def __rfloordiv__(self, other):
        return other // self.value

    def __mod__(self, other):
        return self.value % other.value

    def __rmod__(self, other):
        return other % self.value

    def __divmod__(self, other):
        return divmod(self.value, other.value)

    def __rdivmod__(self, other):
        return divmod(other, self.value)

    def __hash__(self):
        return id(self)

    def sharp(self, unit=1):
        if unit == 0:
            return self
        if unit > 1:
            result = self
            for i in range(unit):
                result = result.sharp()
            return result
        current_interval_number_mod = self.number % 7
        if current_interval_number == 1:
            current_quality = ['P', 'A']
        elif current_interval_number_mod in [1, 4, 5]:
            current_quality = ['d', 'P', 'A']
        elif current_interval_number_mod in [0, 2, 3, 6]:
            current_quality = ['d', 'm', 'M', 'A']
        if self.quality not in current_quality and self.quality[
                0] == current_quality[0]:
            return Interval(self.number, self.quality[:-1])
        elif self.quality[0] == current_quality[-1]:
            return Interval(self.number, self.quality + current_quality[-1])
        elif self.quality in current_quality:
            current_quality_ind = current_quality.index(self.quality)
            return Interval(self.number,
                            current_quality[current_quality_ind + 1])

    def flat(self, unit=1):
        if unit == 0:
            return self
        if unit > 1:
            result = self
            for i in range(unit):
                result = result.flat()
            return result
        current_interval_number_mod = self.number % 7
        if current_interval_number == 1:
            current_quality = ['P', 'A']
        elif current_interval_number_mod in [1, 4, 5]:
            current_quality = ['d', 'P', 'A']
        elif current_interval_number_mod in [0, 2, 3, 6]:
            current_quality = ['d', 'm', 'M', 'A']
        if self.quality not in current_quality and self.quality[
                0] == current_quality[-1]:
            return Interval(self.number, self.quality[:-1])
        elif self.quality[0] == current_quality[0]:
            return Interval(self.number, self.quality + current_quality[0])
        elif self.quality in current_quality:
            current_quality_ind = current_quality.index(self.quality)
            return Interval(self.number,
                            current_quality[current_quality_ind - 1])


quality_dict = {'P': 0, 'M': 0, 'm': -1, 'd': -2, 'A': 1, 'dd': -3, 'AA': 2}

quality_name_dict = {
    'P': 'perfect',
    'M': 'major',
    'm': 'minor',
    'd': 'diminished',
    'A': 'augmented',
    'dd': 'doubly-diminished',
    'AA': 'doubly-augmented'
}

interval_number_dict = {
    1: 0,
    2: 2,
    3: 4,
    4: 5,
    5: 7,
    6: 9,
    7: 11,
    8: 12,
    9: 14,
    10: 16,
    11: 17,
    12: 19,
    13: 21,
    14: 23,
    15: 24,
    16: 26,
    17: 28
}

interval_number_name_list = [
    'unison', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh',
    'octave', 'ninth', 'tenth', 'eleventh', 'twelfth', 'thirteenth',
    'fourteenth', 'fifteenth', 'sixteenth', 'seventeenth'
]

interval_dict = {}
for i, each in enumerate(interval_number_name_list):
    current_interval_number = i + 1
    if current_interval_number == 1:
        current_quality = ['P', 'A', 'AA']
    else:
        current_interval_number_mod = current_interval_number % 7
        if current_interval_number_mod in [1, 4, 5]:
            current_quality = ['P', 'A', 'd', 'AA', 'dd']
        elif current_interval_number_mod in [0, 2, 3, 6]:
            current_quality = ['M', 'm', 'A', 'd', 'AA', 'dd']
    for each_quality in current_quality:
        current_interval_name = f'{quality_name_dict[each_quality]}_{each}'
        current_interval = Interval(number=current_interval_number,
                                    quality=each_quality,
                                    name=current_interval_name)
        interval_dict[current_interval_name] = current_interval
        interval_dict[str(current_interval)] = current_interval

globals().update(interval_dict)

tritone = d5
octave = perfect_octave = P8
tritave = P12
double_octave = P15

semitone = halfstep = 1
wholetone = wholestep = tone = 2

accidentals = ['b', '#', 'x', '♮']

INTERVAL = {
    0: 'perfect unison',
    1: 'minor second',
    2: 'major second',
    3: 'minor third',
    4: 'major third',
    5: 'perfect fourth',
    6: 'diminished fifth',
    7: 'perfect fifth',
    8: 'minor sixth',
    9: 'major sixth',
    10: 'minor seventh',
    11: 'major seventh',
    12: 'perfect octave',
    13: 'minor ninth',
    14: 'major ninth',
    15: 'minor third / augmented ninth',
    16: 'major third / major tenth',
    17: 'perfect eleventh',
    18: 'augmented eleventh',
    19: 'perfect twelfth',
    20: 'minor thirteenth',
    21: 'major thirteenth'
}
NAME_OF_INTERVAL = {j: i for i, j in INTERVAL.items()}

standard = {
    'C': 0,
    'C#': 1,
    'D': 2,
    'D#': 3,
    'E': 4,
    'F': 5,
    'F#': 6,
    'G': 7,
    'G#': 8,
    'A': 9,
    'A#': 10,
    'B': 11,
    'Bb': 10,
    'Eb': 3,
    'Ab': 8,
    'Db': 1,
    'Gb': 6
}

standard_lowercase = {
    'c': 0,
    'c#': 1,
    'd': 2,
    'd#': 3,
    'e': 4,
    'f': 5,
    'f#': 6,
    'g': 7,
    'g#': 8,
    'a': 9,
    'a#': 10,
    'b': 11,
    'bb': 10,
    'eb': 3,
    'ab': 8,
    'db': 1,
    'gb': 6
}

standard.update(standard_lowercase)

standard2 = {
    'C': 0,
    'C#': 1,
    'D': 2,
    'D#': 3,
    'E': 4,
    'F': 5,
    'F#': 6,
    'G': 7,
    'G#': 8,
    'A': 9,
    'A#': 10,
    'B': 11
}

standard_dict = {'Bb': 'A#', 'Eb': 'D#', 'Ab': 'G#', 'Db': 'C#', 'Gb': 'F#'}

standard_dict2 = {
    i: (i.upper() if not (len(i) == 2 and i[1] == 'b') else
        standard_dict[i[0].upper() + i[1]])
    for i in standard_lowercase
}

reverse_standard_dict = {j: i for i, j in standard_dict.items()}

standard_dict.update(standard_dict2)

reverse_standard_dict.update({
    i: reverse_standard_dict[standard_dict2[i]]
    for i in standard_dict2 if standard_dict2[i] in reverse_standard_dict
})

standard_pitch_name = ['C', 'D', 'E', 'F', 'G', 'A', 'B']

scaleTypes = match({
    ('major', ): [M2, M2, m2, M2, M2, M2, m2],
    ('minor', ): [M2, m2, M2, M2, m2, M2, M2],
    ('melodic minor', ): [M2, m2, M2, M2, M2, M2, m2],
    ('harmonic minor', ): [M2, m2, M2, M2, m2, m3, m2],
    ('lydian', ): [M2, M2, M2, m2, M2, M2, m2],
    ('dorian', ): [M2, m2, M2, M2, M2, m2, M2],
    ('phrygian', ): [m2, M2, M2, M2, m2, M2, M2],
    ('mixolydian', ): [M2, M2, m2, M2, M2, m2, M2],
    ('locrian', ): [m2, M2, M2, m2, M2, M2, M2],
    ('whole tone', ): [M2, M2, M2, M2, M2, M2],
    ('12', ): [m2, m2, m2, m2, m2, m2, m2, m2, m2, m2, m2, m2],
    ('major pentatonic', ): [M2, M2, m3, M2, m3],
    ('minor pentatonic', ): [m3, M2, M2, m3, M2]
})
diatonic_modes = [
    'major', 'dorian', 'phrygian', 'lydian', 'mixolydian', 'minor', 'locrian'
]
# you can sort the chord types from most commonly used to least commonly used
# to get better chord detection results
chordTypes = match({
    ('major', 'M', 'maj', 'majorthird'): (M3, P5),
    ('minor', 'm', 'minorthird', 'min', '-'): (m3, P5),
    ('maj7', 'M7', 'major7th', 'majorseventh'): (M3, P5, M7),
    ('m7', 'min7', 'minor7th', 'minorseventh', '-7'): (m3, P5, m7),
    ('7', 'seven', 'seventh', 'dominant seventh', 'dom7', 'dominant7'):
    (M3, P5, m7),
    ('germansixth', ): (M3, P5, A6),
    ('minormajor7', 'minor major 7', 'mM7'): (m3, P5, M7),
    ('dim', 'o'): (m3, d5),
    ('dim7', 'o7'): (m3, d5, d7),
    ('half-diminished7', 'ø7', 'ø', 'half-diminished', 'half-dim', 'm7b5'):
    (m3, d5, m7),
    ('aug', 'augmented', '+', 'aug3', '+3'): (M3, A5),
    ('aug7', 'augmented7', '+7'): (M3, A5, m7),
    ('augmaj7', 'augmented-major7', '+maj7', 'augM7'): (M3, A5, M7),
    ('aug6', 'augmented6', '+6', 'italian-sixth'): (M3, A6),
    ('frenchsixth', ): (M3, d5, A6),
    ('aug9', '+9'): (M3, A5, m7, M9),
    ('sus', 'sus4'): (P4, P5),
    ('sus2', ): (M2, P5),
    ('9', 'dominant9', 'dominant-ninth', 'ninth'): (M3, P5, m7, M9),
    ('maj9', 'major-ninth', 'major9th', 'M9'): (M3, P5, M7, M9),
    ('m9', 'minor9', 'minor9th', '-9'): (m3, P5, m7, M9),
    ('augmaj9', '+maj9', '+M9', 'augM9'): (M3, A5, M7, M9),
    ('add6', '6', 'sixth'): (M3, P5, M6),
    ('m6', 'minorsixth'): (m3, P5, M6),
    ('add2', '+2'): (M2, M3, P5),
    ('add9', ): (M3, P5, M9),
    ('madd2', 'm+2'): (M2, m3, P5),
    ('madd9', ): (m3, P5, M9),
    ('7sus4', '7sus'): (P4, P5, m7),
    ('7sus2', ): (M2, P5, m7),
    ('maj7sus4', 'maj7sus', 'M7sus4'): (P4, P5, M7),
    ('maj7sus2', 'M7sus2'): (M2, P5, M7),
    ('9sus4', '9sus'): (P4, P5, m7, M9),
    ('9sus2', ): (M2, P5, m7, M9),
    ('maj9sus4', 'maj9sus', 'M9sus', 'M9sus4'): (P4, P5, M7, M9),
    ('11', 'dominant11', 'dominant 11'): (M3, P5, m7, M9, P11),
    ('maj11', 'M11', 'eleventh', 'major 11', 'major eleventh'):
    (M3, P5, M7, M9, P11),
    ('m11', 'minor eleventh', 'minor 11'): (m3, P5, m7, M9, P11),
    ('13', 'dominant13', 'dominant 13'): (M3, P5, m7, M9, P11, M13),
    ('maj13', 'major 13', 'M13'): (M3, P5, M7, M9, P11, M13),
    ('m13', 'minor 13'): (m3, P5, m7, M9, P11, M13),
    ('13sus4', '13sus'): (P4, P5, m7, M9, M13),
    ('13sus2', ): (M2, P5, m7, P11, M13),
    ('maj13sus4', 'maj13sus', 'M13sus', 'M13sus4'): (P4, P5, M7, M9, M13),
    ('maj13sus2', 'M13sus2'): (M2, P5, M7, P11, M13),
    ('add4', '+4'): (M3, P4, P5),
    ('madd4', 'm+4'): (m3, P4, P5),
    ('maj7b5', 'M7b5'): (M3, d5, M7),
    ('maj7#11', 'M7#11'): (M3, P5, M7, A11),
    ('maj9#11', 'M9#11'): (M3, P5, M7, M9, A11),
    ('69', '6/9', 'add69'): (M3, P5, M6, M9),
    ('m69', 'madd69'): (m3, P5, M6, M9),
    ('6sus4', '6sus'): (P4, P5, M6),
    ('6sus2', ): (M2, P5, M6),
    ('5', 'power chord'): (P5, ),
    ('5(+octave)', 'power chord(with octave)'): (P5, P8),
    ('maj13#11', 'M13#11'): (M3, P5, M7, M9, A11, M13),
    ('13#11', ): (M3, P5, m7, M9, A11, M13),
    ('fifth_9th', ): (P5, M9),
    ('minormajor9', 'minor major 9', 'mM9'): (m3, P5, M7, M9),
    ('dim(Maj7)', ): (m3, d5, M7)
})
standard_reverse = {j: i for i, j in standard2.items()}
detectScale = scaleTypes.reverse()
detectTypes = chordTypes.reverse(mode=1)

degree_match = {
    '1': [perfect_unison],
    '2': [major_second, minor_second],
    '3': [minor_third, major_third],
    '4': [perfect_fourth],
    '5': [perfect_fifth],
    '6': [major_sixth, minor_sixth],
    '7': [minor_seventh, major_seventh],
    '9': [major_ninth, minor_ninth],
    '11': [perfect_eleventh],
    '13': [major_thirteenth, minor_thirteenth]
}

reverse_degree_match = match({tuple(j): i for i, j in degree_match.items()})

precise_degree_match = {
    '1': perfect_unison,
    'b2': minor_second,
    '2': major_second,
    'b3': minor_third,
    '3': major_third,
    '4': perfect_fourth,
    '#4': diminished_fifth,
    'b5': diminished_fifth,
    '5': perfect_fifth,
    '#5': minor_sixth,
    'b6': minor_sixth,
    '6': major_sixth,
    'b7': minor_seventh,
    '7': major_seventh,
    'b9': minor_ninth,
    '9': major_ninth,
    '#9': augmented_ninth,
    'b11': diminished_eleventh,
    '11': perfect_eleventh,
    '#11': augmented_eleventh,
    'b13': minor_thirteenth,
    '13': major_thirteenth,
    '#13': augmented_thirteenth
}

reverse_precise_degree_match = {
    perfect_unison: '1',
    minor_second: 'b2',
    major_second: '2',
    minor_third: 'b3',
    major_third: '3',
    perfect_fourth: '4',
    diminished_fifth: 'b5/#4',
    perfect_fifth: '5',
    minor_sixth: 'b6/#5',
    major_sixth: '6',
    minor_seventh: 'b7',
    major_seventh: '7',
    minor_ninth: 'b9',
    major_ninth: '9',
    augmented_ninth: '#9',
    diminished_eleventh: 'b11',
    perfect_eleventh: '11',
    augmented_eleventh: '#11',
    minor_thirteenth: 'b13',
    major_thirteenth: '13',
    augmented_thirteenth: '#13'
}

INSTRUMENTS = {
    'Acoustic Grand Piano': 1,
    'Bright Acoustic Piano': 2,
    'Electric Grand Piano': 3,
    'Honky-tonk Piano': 4,
    'Electric Piano 1': 5,
    'Electric Piano 2': 6,
    'Harpsichord': 7,
    'Clavi': 8,
    'Celesta': 9,
    'Glockenspiel': 10,
    'Music Box': 11,
    'Vibraphone': 12,
    'Marimba': 13,
    'Xylophone': 14,
    'Tubular Bells': 15,
    'Dulcimer': 16,
    'Drawbar Organ': 17,
    'Percussive Organ': 18,
    'Rock Organ': 19,
    'Church Organ': 20,
    'Reed Organ': 21,
    'Accordion': 22,
    'Harmonica': 23,
    'Tango Accordion': 24,
    'Acoustic Guitar (nylon)': 25,
    'Acoustic Guitar (steel)': 26,
    'Electric Guitar (jazz)': 27,
    'Electric Guitar (clean)': 28,
    'Electric Guitar (muted)': 29,
    'Overdriven Guitar': 30,
    'Distortion Guitar': 31,
    'Guitar harmonics': 32,
    'Acoustic Bass': 33,
    'Electric Bass (finger)': 34,
    'Electric Bass (pick)': 35,
    'Fretless Bass': 36,
    'Slap Bass 1': 37,
    'Slap Bass 2': 38,
    'Synth Bass 1': 39,
    'Synth Bass 2': 40,
    'Violin': 41,
    'Viola': 42,
    'Cello': 43,
    'Contrabass': 44,
    'Tremolo Strings': 45,
    'Pizzicato Strings': 46,
    'Orchestral Harp': 47,
    'Timpani': 48,
    'String Ensemble 1': 49,
    'String Ensemble 2': 50,
    'SynthStrings 1': 51,
    'SynthStrings 2': 52,
    'Choir Aahs': 53,
    'Voice Oohs': 54,
    'Synth Voice': 55,
    'Orchestra Hit': 56,
    'Trumpet': 57,
    'Trombone': 58,
    'Tuba': 59,
    'Muted Trumpet': 60,
    'French Horn': 61,
    'Brass Section': 62,
    'SynthBrass 1': 63,
    'SynthBrass 2': 64,
    'Soprano Sax': 65,
    'Alto Sax': 66,
    'Tenor Sax': 67,
    'Baritone Sax': 68,
    'Oboe': 69,
    'English Horn': 70,
    'Bassoon': 71,
    'Clarinet': 72,
    'Piccolo': 73,
    'Flute': 74,
    'Recorder': 75,
    'Pan Flute': 76,
    'Blown Bottle': 77,
    'Shakuhachi': 78,
    'Whistle': 79,
    'Ocarina': 80,
    'Lead 1 (square)': 81,
    'Lead 2 (sawtooth)': 82,
    'Lead 3 (calliope)': 83,
    'Lead 4 (chiff)': 84,
    'Lead 5 (charang)': 85,
    'Lead 6 (voice)': 86,
    'Lead 7 (fifths)': 87,
    'Lead 8 (bass + lead)': 88,
    'Pad 1 (new age)': 89,
    'Pad 2 (warm)': 90,
    'Pad 3 (polysynth)': 91,
    'Pad 4 (choir)': 92,
    'Pad 5 (bowed)': 93,
    'Pad 6 (metallic)': 94,
    'Pad 7 (halo)': 95,
    'Pad 8 (sweep)': 96,
    'FX 1 (rain)': 97,
    'FX 2 (soundtrack)': 98,
    'FX 3 (crystal)': 99,
    'FX 4 (atmosphere)': 100,
    'FX 5 (brightness)': 101,
    'FX 6 (goblins)': 102,
    'FX 7 (echoes)': 103,
    'FX 8 (sci-fi)': 104,
    'Sitar': 105,
    'Banjo': 106,
    'Shamisen': 107,
    'Koto': 108,
    'Kalimba': 109,
    'Bag pipe': 110,
    'Fiddle': 111,
    'Shanai': 112,
    'Tinkle Bell': 113,
    'Agogo': 114,
    'Steel Drums': 115,
    'Woodblock': 116,
    'Taiko Drum': 117,
    'Melodic Tom': 118,
    'Synth Drum': 119,
    'Reverse Cymbal': 120,
    'Guitar Fret Noise': 121,
    'Breath Noise': 122,
    'Seashore': 123,
    'Bird Tweet': 124,
    'Telephone Ring': 125,
    'Helicopter': 126,
    'Applause': 127,
    'Gunshot': 128
}

reverse_instruments = {j: i for i, j in INSTRUMENTS.items()}

mode_check_parameters = [['major', [1, 3, 5]], ['dorian', [2, 4, 7]],
                         ['phrygian', [3, 5, 4]], ['lydian', [4, 6, 7]],
                         ['mixolydian', [5, 7, 4]], ['minor', [6, 1, 3]],
                         ['locrian', [7, 2, 4]]]

chord_functions_roman_numerals = {
    1: 'I',
    2: 'II',
    3: 'III',
    4: 'IV',
    5: 'V',
    6: 'VI',
    7: 'VII',
}

roman_numerals_dict = match({
    ('I', 'i', '1'): 1,
    ('II', 'ii', '2'): 2,
    ('III', 'iii', '3'): 3,
    ('IV', 'iv', '4'): 4,
    ('V', 'v', '5'): 5,
    ('VI', 'vi', '6'): 6,
    ('VII', 'vii', '7'): 7
})

chord_function_dict = {
    'major': [0, ''],
    'minor': [1, ''],
    'maj7': [0, 'M7'],
    'm7': [1, '7'],
    '7': [0, '7'],
    'minormajor7': [1, 'M7'],
    'dim': [1, 'o'],
    'dim7': [1, 'o7'],
    'half-diminished7': [1, 'ø7'],
    'aug': [0, '+'],
    'aug7': [0, '+7'],
    'augmaj7': [0, '+M7'],
    'aug6': [0, '+6'],
    'frenchsixth': [0, '+6(french)'],
    'aug9': [0, '+9'],
    'sus': [0, 'sus4'],
    'sus2': [0, 'sus2'],
    '9': [0, '9'],
    'maj9': [0, 'M9'],
    'm9': [1, '9'],
    'augmaj9': [0, '+M9'],
    'add6': [0, 'add6'],
    'm6': [1, 'add6'],
    'add2': [0, 'add2'],
    'add9': [0, 'add9'],
    'madd2': [1, 'add2'],
    'madd9': [1, 'add9'],
    '7sus4': [0, '7sus4'],
    '7sus2': [0, '7sus2'],
    'maj7sus4': [0, 'M7sus4'],
    'maj7sus2': [0, 'M7sus2'],
    '9sus4': [0, '9sus4'],
    '9sus2': [0, '9sus2'],
    'maj9sus4': [0, 'M9sus4'],
    '13sus4': [0, '13sus4'],
    '13sus2': [0, '13sus2'],
    'maj13sus4': [0, 'M13sus4'],
    'maj13sus2': [0, 'M13sus2'],
    'add4': [0, 'add4'],
    'madd4': [1, 'add4'],
    'maj7b5': [0, 'M7b5'],
    'maj7#11': [0, 'M7#11'],
    'maj9#11': [0, 'M9#11'],
    '69': [0, '69'],
    'm69': [1, '69'],
    '6sus4': [1, '6sus4'],
    '6sus2': [1, '6sus2'],
    '5': [1, '5'],
    'maj11': [0, 'M11'],
    'm11': [1, '11'],
    '11': [0, '11'],
    '13': [0, '13'],
    'maj13': [0, 'M13'],
    'm13': [1, '13'],
    'maj13#11': [0, 'M13#11'],
    '13#11': [0, '13#11'],
    'fifth_9th': [0, '5/9'],
    'minormajor9': [1, 'M9']
}

chord_notation_dict = {
    'major': '',
    'minor': '-',
    'maj7': 'M7',
    'm7': '-7',
    '7': '7',
    'minormajor7': 'mM7',
    'dim': 'o',
    'dim7': 'o7',
    'half-diminished7': 'ø',
    'aug': '+',
    'aug7': '+7',
    'augmaj7': '+M7',
    'aug6': '+6',
    'frenchsixth': '+6(french)',
    'aug9': '+9',
    'sus': 'sus4',
    'sus2': 'sus2',
    '9': '9',
    'maj9': 'M9',
    'm9': [1, '9'],
    'augmaj9': '+M9',
    'add6': '6',
    'm6': 'm6',
    'add2': 'add2',
    'add9': 'add9',
    'madd2': 'madd2',
    'madd9': 'madd9',
    '7sus4': '7sus4',
    '7sus2': '7sus2',
    'maj7sus4': 'M7sus4',
    'maj7sus2': 'M7sus2',
    '9sus4': '9sus4',
    '9sus2': '9sus2',
    'maj9sus4': 'M9sus4',
    '13sus4': '13sus4',
    '13sus2': '13sus2',
    'maj13sus4': 'M13sus4',
    'maj13sus2': 'M13sus2',
    'add4': 'add4',
    'madd4': 'madd4',
    'maj7b5': 'M7b5',
    'maj7#11': 'M7#11',
    'maj9#11': 'M9#11',
    '69': '69',
    'm69': 'm69',
    '6sus4': '6sus4',
    '6sus2': '6sus2',
    '5': '5',
    'maj11': 'M11',
    'm11': 'm11',
    '11': '11',
    '13': '13',
    'maj13': 'M13',
    'm13': 'm13',
    'maj13#11': 'M13#11',
    '13#11': '13#11',
    'fifth_9th': '5/9',
    'minormajor9': 'M9'
}

drum_types = {
    27: 'High Q',
    28: 'Slap',
    29: 'Stratch Push',
    30: 'Stratch Pull',
    31: 'Sticks',
    32: 'Square Click',
    33: 'Metronome Click',
    34: 'Metronome Bell',
    35: 'Acoustic Bass Drum',
    36: 'Electric Bass Drum',
    37: 'Side Stick',
    38: 'Acoustic Snare',
    39: 'Hand Clap',
    40: 'Electric Snare',
    41: 'Low Floor Tom',
    42: 'Closed Hi-hat',
    43: 'High Floor Tom',
    44: 'Pedal Hi-hat',
    45: 'Low Tom',
    46: 'Open Hi-hat',
    47: 'Low-Mid Tom',
    48: 'Hi-Mid Tom',
    49: 'Crash Cymbal 1',
    50: 'High Tom',
    51: 'Ride Cymbal 1',
    52: 'Chinese Cymbal',
    53: 'Ride Bell',
    54: 'Tambourine',
    55: 'Splash Cymbal',
    56: 'Cowbell',
    57: 'Crash Cymbal 2',
    58: 'Vibra Slap',
    59: 'Ride Cymbal 2',
    60: 'High Bongo',
    61: 'Low Bongo',
    62: 'Mute High Conga',
    63: 'Open High Conga',
    64: 'Low Conga',
    65: 'High Timbale',
    66: 'Low Timbale',
    67: 'High Agogô',
    68: 'Low Agogô',
    69: 'Cabasa',
    70: 'Maracas',
    71: 'Short Whistle',
    72: 'Long Whistle',
    73: 'Short Guiro',
    74: 'Long Guiro',
    75: 'Claves',
    76: 'High Woodblock',
    77: 'Low Woodblock',
    78: 'Mute Cuica',
    79: 'Open Cuica',
    80: 'Mute Triangle',
    81: 'Open Triangle',
    82: 'Shaker',
    83: 'Jingle Bell',
    84: 'Belltree',
    85: 'Castanets',
    86: 'Mute Surdo',
    87: 'Open Surdo'
}

drum_mapping = {
    'K': 36,
    'H': 42,
    'S': 40,
    'S2': 38,
    'OH': 46,
    'PH': 44,
    'HC': 39,
    'K2': 35,
    'C': 57,
    'C2': 49,
    '0': -1,
    '-': -2
}

drum_mapping2 = {
    '0': 36,
    '1': 42,
    '2': 40,
    '3': 38,
    '4': 46,
    '5': 44,
    '6': 39,
    '7': 35,
    '8': 57,
    '9': 49,
    'x': -1,
    '-': -2
}

drum_set_dict = {
    1: 'Standard',
    9: 'Room Kit',
    17: 'Power Kit',
    25: 'Electronic Kit',
    26: 'TR-808 Kit',
    33: 'Jazz Kit',
    41: 'Brush Kit',
    49: 'Orchestra Kit',
    57: 'Sound FX Kit'
}
drum_set_dict_reverse = {j: i for i, j in drum_set_dict.items()}

drum_keywords = [
    'r', 'd', 'a', 't', 'l', 'n', 's', 'v', 'dl', 'di', 'dv', 'al', 'ai', 'av',
    'b'
]

guitar_standard_tuning = ['E2', 'A2', 'D3', 'G3', 'B3', 'E4']

choose_chord_progressions_list = [
    '6451', '3456', '4536', '14561451', '1564', '4156', '4565', '4563', '6341',
    '6345', '6415', '15634145'
]

default_choose_melody_rhythms = [('b b b 0 b b b b', 1)]

default_choose_drum_beats = [
    'K, H, S, H, K, H, S, H, K, H, S, H, K, K, S, H, t:2',
    'K;H, 0, OH, 0, K;S;H, 0, OH, 0, K;H, 0, OH, 0, K;S;H, 0, OH, S, t:1'
]

default_choose_bass_rhythm = [('b b b b', 1 / 2)]

default_choose_bass_playing_techniques = ['octaves', 'root']

non_standard_intervals = [major_sixth, minor_sixth, minor_second]
