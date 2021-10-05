import traceback
from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog
import PIL.Image, PIL.ImageTk
import sys
import os
import midiutil
import mido
import keyboard
import time
import pyglet
from pyglet.window import mouse
from pyglet import shapes
import re
from yapf.yapflib.yapf_api import FormatCode
import simpleaudio
from io import BytesIO
from ast import literal_eval
import threading
import math
import array
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio as play_sound
from pydub.generators import Sine, Triangle, Sawtooth, Square, WhiteNoise, Pulse
import librosa
import soundfile
import sf2_loader
import py
import pygame
import pygame.midi

abs_path = os.path.dirname(sys.executable)
os.chdir(abs_path)
sys.path.append('.')
os.chdir('../..')
sys.path.append('musicpy')
musicpy_vars = dir(__import__('musicpy'))
exec("from musicpy import *")
os.chdir(abs_path)
with open('config.py', encoding='utf-8-sig') as f:
    exec(f.read())
with open('musicpy editor for exe.py', encoding='utf-8-sig') as f:
    exec(f.read())
