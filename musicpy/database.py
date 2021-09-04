from .match import match

perfect_unison = diminished_second = P1 = d2 = 0
minor_second = augmented_unison = m2 = A1 = 1
major_second = diminished_third = M2 = d3 = 2
minor_third = augmented_second = m3 = A2 = 3
major_third = diminished_fourth = M3 = d4 = 4
perfect_fourth = augmented_third = P4 = A3 = 5
diminished_fifth = augmented_fourth = tritone = d5 = A4 = 6
perfect_fifth = diminished_sixth = P5 = d6 = 7
minor_sixth = augmented_fifth = m6 = A5 = 8
major_sixth = diminished_seventh = M6 = d7 = 9
minor_seventh = augmented_sixth = m7 = A6 = 10
major_seventh = diminished_octave = M7 = d8 = 11
perfect_octave = octave = augmented_seventh = diminished_ninth = P8 = A7 = d9 = 12
minor_ninth = augmented_octave = m9 = A8 = 13
major_ninth = diminished_tenth = M9 = d10 = 14
minor_tenth = augmented_ninth = m10 = A9 = 15
major_tenth = diminished_eleventh = M10 = d11 = 16
perfect_eleventh = augmented_tenth = P11 = A10 = 17
diminished_twelfth = augmented_eleventh = d12 = A11 = 18
perfect_twelfth = tritave = diminished_thirteenth = P12 = d13 = 19
minor_thirteenth = augmented_twelfth = m13 = A12 = 20
major_thirteenth = diminished_fourteenth = M13 = d14 = 21
minor_fourteenth = augmented_thirteenth = m14 = A13 = 22
major_fourteenth = diminished_fifteenth = M14 = d15 = 23
perfect_fifteenth = double_octave = augmented_fourteenth = P15 = A14 = 24
minor_sixteenth = augmented_fifteenth = m16 = A15 = 25
major_sixteenth = diminished_seventeenth = M16 = d17 = 26
minor_seventeenth = augmented_sixteenth = m17 = A16 = 27
major_seventeenth = M17 = 28

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
    17: 'perfect eleventh',
    20: 'minor thirteenth',
    21: 'major thirteenth'
}
NAME_OF_INTERVAL = {
    'perfect unison': 0,
    'minor second': 1,
    'major second': 2,
    'minor third': 3,
    'major third': 4,
    'perfect fourth': 5,
    'diminished fifth': 6,
    'perfect fifth': 7,
    'minor sixth': 8,
    'major sixth': 9,
    'minor seventh': 10,
    'major seventh': 11,
    'perfect octave': 12,
    'minor ninth': 13,
    'major ninth': 14,
    'perfect eleventh': 17,
    'minor thirteenth': 20,
    'major thirteenth': 21
}
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

scaleTypes = match({
    ('major', ): [2, 2, 1, 2, 2, 2, 1],
    ('minor', ): [2, 1, 2, 2, 1, 2, 2],
    ('melodic minor', ): [2, 1, 2, 2, 2, 2, 1],
    ('harmonic minor', ): [2, 1, 2, 2, 1, 3, 1],
    ('lydian', ): [2, 2, 2, 1, 2, 2, 1],
    ('dorian', ): [2, 1, 2, 2, 2, 1, 2],
    ('phrygian', ): [1, 2, 2, 2, 1, 2, 2],
    ('mixolydian', ): [2, 2, 1, 2, 2, 1, 2],
    ('locrian', ): [1, 2, 2, 1, 2, 2, 2],
    ('whole tone', ): [2, 2, 2, 2, 2, 2],
    ('12', ): [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ('major pentatonic', ): [2, 2, 3, 2, 3],
    ('minor pentatonic', ): [3, 2, 2, 3, 2]
})
modern_modes = [
    'major', 'dorian', 'phrygian', 'lydian', 'mixolydian', 'minor', 'locrian'
]
# you can sort the chord types from most commonly used to least commonly used
# to get better chord detection results
chordTypes = match({
    ('major', 'M', 'maj', 'majorthird'): ((4, 7), ),
    ('minor', 'm', 'minorthird', 'min', '-'): ((3, 7), ),
    ('maj7', 'M7', 'major7th', 'majorseventh'): ((4, 7, 11), ),
    ('m7', 'min7', 'minor7th', 'minorseventh', '-7'): ((3, 7, 10), ),
    ('7', 'seven', 'seventh', 'dominant seventh', 'dom7', 'dominant7', 'germansixth'):
    ((4, 7, 10), ),
    ('minormajor7', 'minor major 7', 'mM7'): ((3, 7, 11), ),
    ('dim', 'o'): ((3, 6), ),
    ('dim7', 'o7'): ((3, 6, 9), ),
    ('half-diminished7', 'ø7', 'ø', 'half-diminished', 'half-dim', 'm7b5'):
    ((3, 6, 10), ),
    ('aug', 'augmented', '+', 'aug3', '+3'): ((4, 8), ),
    ('aug7', 'augmented7', '+7'): ((4, 8, 10), ),
    ('augmaj7', 'augmented-major7', '+maj7', 'augM7'): ((4, 8, 11), ),
    ('aug6', 'augmented6', '+6', 'italian-sixth'): ((4, 10), ),
    ('frenchsixth', ): ((4, 6, 10), ),
    ('aug9', '+9'): ((4, 8, 10, 14), ),
    ('sus', 'sus4'): ((5, 7), ),
    ('sus2', ): ((2, 7), ),
    ('9', 'dominant9', 'dominant-ninth', 'ninth'): ((4, 7, 10, 14), ),
    ('maj9', 'major-ninth', 'major9th', 'M9'): ((4, 7, 11, 14), ),
    ('m9', 'minor9', 'minor9th', '-9'): ((3, 7, 10, 14), ),
    ('augmaj9', '+maj9', '+M9', 'augM9'): ((4, 8, 11, 14), ),
    ('add6', '6', 'sixth'): ((4, 7, 9), ),
    ('m6', 'minorsixth'): ((3, 7, 9), ),
    ('add2', '+2'): ((2, 4, 7), ),
    ('add9', ): ((4, 7, 14), ),
    ('madd2', 'm+2'): ((2, 3, 7), ),
    ('madd9', ): ((3, 7, 14), ),
    ('7sus4', '7sus'): ((5, 7, 10), ),
    ('7sus2', ): ((2, 7, 10), ),
    ('maj7sus4', 'maj7sus', 'M7sus4'): ((5, 7, 11), ),
    ('maj7sus2', 'M7sus2'): ((2, 7, 11), ),
    ('9sus4', '9sus'): ((5, 7, 10, 14), ),
    ('9sus2', ): ((2, 7, 10, 14), ),
    ('maj9sus4', 'maj9sus', 'M9sus', 'M9sus4'): ((5, 7, 11, 14), ),
    ('13sus4', '13sus'): ((5, 7, 10, 14, 21), (7, 10, 14, 17, 21)),
    ('13sus2', ): ((2, 7, 10, 17, 21), ),
    ('maj13sus4', 'maj13sus', 'M13sus', 'M13sus4'):
    ((5, 7, 11, 14, 21), (7, 11, 14, 17, 21)),
    ('maj13sus2', 'M13sus2'): ((2, 7, 11, 17, 21), ),
    ('add4', '+4'): ((4, 5, 7), ),
    ('madd4', 'm+4'): ((3, 5, 7), ),
    ('maj7b5', 'M7b5'): ((4, 6, 11), ),
    ('maj7#11', 'M7#11'): ((4, 7, 11, 18), ),
    ('maj9#11', 'M9#11'): ((4, 7, 11, 14, 18), ),
    ('69', '6/9', 'add69'): ((4, 7, 9, 14), ),
    ('m69', 'madd69'): ((3, 7, 9, 14), ),
    ('6sus4', '6sus'): ((5, 7, 9), ),
    ('6sus2', ): ((2, 7, 9), ),
    ('5', 'power chord'): ((7, ), ),
    ('5(+octave)', 'power chord(with octave)'): ((7, 12), ),
    ('maj11', 'M11', 'eleventh', 'major 11', 'major eleventh'):
    ((4, 7, 11, 14, 17), ),
    ('m11', 'minor eleventh', 'minor 11'): ((3, 7, 10, 14, 17), ),
    ('11', 'dominant11', 'dominant 11'): ((4, 7, 10, 14, 17), ),
    ('13', 'dominant13', 'dominant 13'): ((4, 7, 10, 14, 17, 21), ),
    ('maj13', 'major 13', 'M13'): ((4, 7, 11, 14, 17, 21), ),
    ('m13', 'minor 13'): ((3, 7, 10, 14, 17, 21), ),
    ('maj13#11', 'M13#11'): ((4, 7, 11, 14, 18, 21), ),
    ('13#11', ): ((4, 7, 10, 14, 18, 21), ),
    ('fifth_9th', ): ((7, 14), ),
    ('minormajor9', 'minor major 9', 'mM9'): ((3, 7, 11, 14), ),
    ('dim(Maj7)', ): ((3, 6, 11), )
})
standard_reverse = {j: i for i, j in standard2.items()}
detectScale = scaleTypes.reverse()
detectTypes = chordTypes.reverse()
notedict = {
    'C': 'C',
    'c': 'C#',
    'D': 'D',
    'd': 'D#',
    'E': 'E',
    'F': 'F',
    'f': 'F#',
    'G': 'G',
    'g': 'G#',
    'A': 'A',
    'a': 'A#',
    'B': 'B',
    ' ': 'interval'
}

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

instruments = {
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

reverse_instruments = {j: i for i, j in instruments.items()}

mode_check_parameters = [['major', [1, 3, 5], 1], ['dorian', [2, 4, 7], 2],
                         ['phrygian', [3, 5, 4], 3], ['lydian', [4, 6, 7], 4],
                         ['mixolydian', [5, 7, 4], 5], ['minor', [6, 1, 3], 6],
                         ['locrian', [7, 2, 4], 7]]

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
    '0': 36,
    '1': 42,
    '2': 40,
    '3': 38,
    '4': 46,
    '5': 44,
    '6': 39,
    '7': 35
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
