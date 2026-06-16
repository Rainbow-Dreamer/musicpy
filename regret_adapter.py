"""
Regrets adapter for musicpy — bridges circular imports and custom serialization.
"""
import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Pre-load the dependency chain in correct order
import musicpy.structures   # Load base module first
import musicpy.database     # Load data module
import musicpy.musicpy      # Now the top-level module can resolve all refs

from musicpy.musicpy import (
    C, N, S, scale, to_dict, concat, chord_progression,
    get_chord, get_chord_by_interval, degree_to_note,
    note_to_degree, get_freq, standardize_note,
    build, track as make_track, trans, arpeggio,
)
from musicpy import algorithms as alg


def construct_chord(name):
    """Construct a chord from name and serialize to dict."""
    c = C(name)
    return to_dict(c)


def construct_note(name):
    """Construct a note from name and serialize to dict."""
    n = N(name)
    return _note_to_dict(n)


def construct_scale(root, mode):
    """Construct a scale from root and mode, return note names."""
    s = scale(root, mode)
    return [str(n) for n in s.notes]


def detect_chord(name):
    """Detect chord type from a chord name."""
    c = C(name)
    return alg.detect(c)


def transpose_chord(name, semitones):
    """Transpose a chord by semitones and serialize."""
    c = C(name)
    result = c.up(semitones)
    return to_dict(result)


def invert_chord(name, inversion_num):
    """Invert a chord and serialize. Note: inversion 0 is invalid in musicpy."""
    c = C(name)
    result = c.inversion(inversion_num)
    return to_dict(result)


def concat_chords(name1, name2):
    """Concatenate two chords and serialize."""
    c1 = C(name1)
    c2 = C(name2)
    result = concat(c1, c2)
    return to_dict(result)


def chord_progression_from_scale(root, mode):
    """Generate diatonic chord progression from scale using pick_chord_by_degree."""
    s = scale(root, mode)
    # Use the scale's pick_chord_by_degree method for each degree
    chords = []
    for i in range(1, 8):
        try:
            c = s.pick_chord_by_degree(i)
            chords.append(to_dict(c))
        except Exception:
            chords.append(None)
    return chords


def detect_scale_from_chord(name):
    """Detect which scales contain this chord."""
    c = C(name)
    return alg.detect_scale(c)


def negative_harmony_transform(name, root, mode):
    """Apply negative harmony transformation. Note: args are (scale, chord)."""
    c = C(name)
    s = scale(root, mode)
    result = alg.negative_harmony(s, c)
    return to_dict(result)


def _note_to_dict(n):
    """Convert a note object to a dict."""
    if hasattr(n, '__dict__'):
        d = {}
        for k, v in n.__dict__.items():
            if not k.startswith('_'):
                if isinstance(v, (int, float, str, bool, type(None))):
                    d[k] = v
                else:
                    d[k] = str(v)
        return d
    return str(n)
