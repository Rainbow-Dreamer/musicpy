try:
    from .read_sf2.read_sf2 import *
except:
    import os
    os.chdir('../..')
    from .read_sf2_32bit.read_sf2 import *
