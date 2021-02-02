import traceback
from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
from tkinter import filedialog
import midiutil
import mido
import sys
import os
abs_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(abs_path)
os.chdir('..')
sys.path.append('.')
function_names = dir(__import__('musicpy')) + ['direct_play', 'print']
exec("from musicpy import *")
os.chdir('musicpy editor')
from io import BytesIO
import pygame
pygame.mixer.init(44100, -16, 1, 1024)
with open('config.py', encoding='utf-8-sig') as f:
    exec(f.read())
with open('musicpy editor for exe.py', encoding='utf-8-sig') as f:
    exec(f.read())
