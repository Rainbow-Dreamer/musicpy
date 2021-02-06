from collections import defaultdict

from Xlib import X, XK, display
from Xlib.ext import record
from Xlib.protocol import rq

from ._keyboard_event import KeyboardEvent, KEY_DOWN, KEY_UP, normalize_name


# from ._nixkeyboard import init

def cleanup_key(name):
    if name.startswith('XK_'):
        name = name[3:]

    if name.startswith('KP_'):
        is_keypad = True
        name = name[3:]
    else:
        is_keypad = False

    if name.endswith('_R'):
        name = 'right ' + name[:-2]
    if name.endswith('_L'):
        name = 'left ' + name[:-2]

    return normalize_name(name), is_keypad


keysym_to_keys = defaultdict(list)
name_to_keysyms = defaultdict(list)
for raw_name in dir(XK):
    if not raw_name.startswith('XK_'): continue
    keysym = getattr(XK, raw_name)
    name, is_keypad = cleanup_key(raw_name)
    keysym_to_keys[keysym].append((name, is_keypad))
    name_to_keysyms[name].append(keysym)

local_dpy = None
record_dpy = None
ctx = None


def init():
    # Adapted from https://github.com/python-xlib/python-xlib/blob/master/examples/record_demo.py
    global local_dpy
    global record_dpy
    local_dpy = display.Display()
    record_dpy = display.Display()

    if not record_dpy.has_extension("RECORD"):
        raise ImportError("RECORD extension not found")

    r = record_dpy.record_get_version(0, 0)
    # print("RECORD extension version %d.%d" % (r.major_version, r.minor_version))

    # Create a recording context; we only want key and mouse events
    global ctx
    ctx = record_dpy.record_create_context(
        0,
        [record.AllClients],
        [
            {
                'core_requests': (0, 0),
                'core_replies': (0, 0),
                'ext_requests': (0, 0, 0, 0),
                'ext_replies': (0, 0, 0, 0),
                'delivered_events': (0, 0),
                'device_events': (X.KeyPress, X.KeyPress),
                'errors': (0, 0),
                'client_started': False,
                'client_died': False,
            }
        ]
    )


def listen(callback):
    def handler(reply):
        if reply.category != record.FromServer:
            return
        if reply.client_swapped:
            print("* received swapped protocol data, cowardly ignored")
            return
        if not len(reply.data) or reply.data[0] < 2:
            # not an event
            return

        data = reply.data
        while len(data):
            raw_event, data = rq.EventField(None).parse_binary_value(data, record_dpy.display, None, None)

            event_type = {X.KeyPress: KEY_DOWN, X.KeyRelease: KEY_UP}.get(raw_event.type)
            if event_type:
                keysym = local_dpy.keycode_to_keysym(raw_event.detail, 0)
                # TODO: scan code is not correct.
                if not keysym:
                    event = KeyboardEvent(event_type=event_type, scan_code=raw_event.detail)
                else:
                    try:
                        name, is_keypad = keysym_to_keys[keysym][0]
                    except IndexError:
                        name, is_keypad = None, None
                    event = KeyboardEvent(event_type=event_type, scan_code=keysym, name=name, is_keypad=is_keypad)

                callback(event)

    try:
        # Enable the context; this only returns after a call to record_disable_context,
        # while calling the callback function in the meantime
        record_dpy.record_enable_context(ctx, handler)
    finally:
        # Finally free the context
        record_dpy.record_free_context(ctx)


def map_name(name):
    for keysym in name_to_keysyms[name]:
        yield keysym, ()
