import pygame
import keyboard
import os
import time
import sys
import pyglet
import mido
import midiutil
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
abs_path = os.path.dirname(os.path.abspath(__file__))
if 'visualization folder' not in abs_path:
    abs_path += '/visualization folder'
os.chdir(abs_path)
sys.path.append(abs_path)
os.chdir('../../musicpy')
exec('from musicpy.musicpy import *', globals(), globals())
os.chdir(abs_path)    
with open('config.py', encoding='utf-8-sig') as f:
    exec(f.read(), globals(), globals())
import pygame.midi
with open('browse.py', encoding='utf-8-sig') as f:
    exec(f.read(), globals(), globals())
from pyglet.window import mouse
from pyglet import shapes
with open('Ideal Piano.pyw', encoding='utf-8-sig') as f:
    exec(f.read(), globals(), globals())
