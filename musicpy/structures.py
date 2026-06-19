# structures.py — Re-export module for backward compatibility
# All classes have been decomposed into domain-focused modules.
# This file ensures existing imports continue to work:
#   from musicpy.structures import note, chord, scale, etc.

from copy import deepcopy as copy
from fractions import Fraction
from dataclasses import dataclass
import functools

if __name__ == 'musicpy.structures':
    from . import database
    from .primitives import (note, tempo, pitch_bend, pan, volume, event, beat,
                             rest_symbol, continue_symbol, rest)
    from .chord_class import chord, chord_type
    from .scale_class import scale, circle_of_fifths, circle_of_fourths
    from .piece_class import piece, track, drum, rhythm
    from .parsers import (_read_notes, _read_single_note, _parse_change_num,
                          _process_note, _process_settings,
                          _process_normalize_tempo,
                          _piece_process_normalize_tempo, copy_list,
                          process_note)
else:
    import database
    from primitives import (note, tempo, pitch_bend, pan, volume, event, beat,
                            rest_symbol, continue_symbol, rest)
    from chord_class import chord, chord_type
    from scale_class import scale, circle_of_fifths, circle_of_fourths
    from piece_class import piece, track, drum, rhythm
    from parsers import (_read_notes, _read_single_note, _parse_change_num,
                         _process_note, _process_settings,
                         _process_normalize_tempo,
                         _piece_process_normalize_tempo, copy_list,
                         process_note)

import musicpy as mp
