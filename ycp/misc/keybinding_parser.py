# -*- coding: utf-8 -*-

# import copy
import curses.ascii

from .. import PY3

digits = set(range(ord('0'), ord('9') + 1))

ANYKEY, PASSIVE_ACTION, ALT_KEY, QUANT_KEY = range(9001, 9005)
EXCLUDE_FROM_ANYKEY = [27]

SPECIAL_KEYS = {
    'bs': curses.KEY_BACKSPACE,
    'backspace': curses.KEY_BACKSPACE,
    'backspace2': curses.ascii.DEL,
    'delete': curses.KEY_DC,
    's-delete': curses.KEY_SDC,
    'insert': curses.KEY_IC,
    'cr': ord("\n"),
    'enter': ord("\n"),
    'return': ord("\n"),
    'space': ord(" "),
    'esc': curses.ascii.ESC,
    'escape': curses.ascii.ESC,
    'down': curses.KEY_DOWN,
    'up': curses.KEY_UP,
    'left': curses.KEY_LEFT,
    'right': curses.KEY_RIGHT,
    'pagedown': curses.KEY_NPAGE,
    'pageup': curses.KEY_PPAGE,
    'home': curses.KEY_HOME,
    'end': curses.KEY_END,
    'tab': ord('\t'),
    's-tab': curses.KEY_BTAB,
    'lt': ord('<'),
    'gt': ord('>'),
}

VERY_SPECIAL_KEYS = {
    'any': ANYKEY,
    'alt': ALT_KEY,
    'bg': PASSIVE_ACTION,
    'allow_quantifiers': QUANT_KEY,
}


def special_keys_init():
    for key, val in tuple(SPECIAL_KEYS.items()):
        SPECIAL_KEYS['a-' + key] = (ALT_KEY, val)

    for char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_!{}':
        SPECIAL_KEYS['a-' + char] = (ALT_KEY, ord(char))

    for char in 'abcdefghijklmnopqrstuvwxyz_':
        SPECIAL_KEYS['c-' + char] = ord(char) - 96

    SPECIAL_KEYS['c-space'] = 0

    for n in range(64):
        SPECIAL_KEYS['f' + str(n)] = curses.KEY_F0 + n


special_keys_init()
SPECIAL_KEYS.update(VERY_SPECIAL_KEYS)
del VERY_SPECIAL_KEYS

REVERSED_SPECIAL_KEYS = dict(
    (v, k) for k, v in SPECIAL_KEYS.items())


def key_to_string(key):
    if key in range(33, 127):
        return chr(key)
    if key in REVERSED_SPECIAL_KEYS:
        return "<%s>" % REVERSED_SPECIAL_KEYS[key]
    return "<%s>" % str(key)


def construct_keybinding(iterable):
    """Does the reverse of parse_keybinding"""
    return ''.join(key_to_string(c) for c in iterable)


def parse_keybinding(obj):
    """Translate a keybinding to a sequence of integers

    >>> tuple(parse_keybinding("lol<CR>"))
    (108, 111, 108, 10)

    >>> out = tuple(parse_keybinding("x<A-Left>"))
    >>> out  # it's kind of dumb that you can't test for constants...
    (120, 9003, 260)
    >>> out[0] == ord('x')
    True
    >>> out[1] == ALT_KEY
    True
    >>> out[2] == curses.KEY_LEFT
    True
    """
    assert isinstance(obj, (tuple, int, str))
    if isinstance(obj, tuple):
        for char in obj:
            yield char
    elif isinstance(obj, int):
        yield obj
    elif isinstance(obj, str):
        in_brackets = False
        bracket_content = []
        for char in obj:
            if in_brackets:
                if char == '>':
                    in_brackets = False
                    string = ''.join(bracket_content).lower()
                    try:
                        keys = SPECIAL_KEYS[string]
                        for key in keys:
                            yield key
                    except KeyError:
                        if string.isdigit():
                            yield int(string)
                        else:
                            yield ord('<')
                            for bracket_char in bracket_content:
                                yield ord(bracket_char)
                            yield ord('>')
                    except TypeError:
                        yield keys  # TODO: to check type
                else:
                    bracket_content.append(char)
            else:
                if char == '<':
                    in_brackets = True
                    bracket_content = []
                else:
                    yield ord(char)
        if in_brackets:
            yield ord('<')
            for char in bracket_content:
                yield ord(char)


def _unbind_traverse(pointer, keys, pos=0):
    if keys[pos] not in pointer:
        return
    if len(keys) > pos + 1 and isinstance(pointer, dict):
        _unbind_traverse(pointer[keys[pos]], keys, pos=pos + 1)
        if not pointer[keys[pos]]:
            del pointer[keys[pos]]
    elif len(keys) == pos + 1:
        try:
            del pointer[keys[pos]]
        except KeyError:
            pass
        try:
            keys.pop()
        except IndexError:
            pass


class KeyBuffer:

    def __init__(self, keymap=None):
        self.pointer = None
        self.result = None
        self.quantifier = None
        self.finished_parsing_quantifier = None
        self.finished_parsing = None
        self.parse_error = None

        self.keys = []
        self.wildcards = []
        self.keymap = keymap  # FIXME: Naming
        self.clear()

    def add(self, key):
        self.keys.append(key)
        self.result = None
        if not self.finished_parsing_quantifier and key in digits:
            if self.quantifier is None:
                self.quantifier = 0
            self.quantifier = self.quantifier * 10 + key - 48  # (48 = ord(0))
        else:
            self.finished_parsing_quantifier = True

            moved = True
            if key in self.pointer:
                self.pointer = self.pointer[key]
            elif ANYKEY in self.pointer and \
                    key not in EXCLUDE_FROM_ANYKEY:
                self.wildcards.append(key)
                self.pointer = self.pointer[ANYKEY]
            else:
                moved = False

            if moved:
                if isinstance(self.pointer, dict):
                    if PASSIVE_ACTION in self.pointer:
                        self.result = self.pointer[PASSIVE_ACTION]
                else:
                    self.result = self.pointer
                    self.finished_parsing = True
            else:
                self.finished_parsing = True
                self.parse_error = True

    def clear(self):
        self.keys = []  # FIXME: Statement declaration
        self.wildcards = []
        self.pointer = self.keymap
        self.result = None
        self.quantifier = None
        self.finished_parsing_quantifier = False
        self.finished_parsing = False
        self.parse_error = False

        if self.keymap and QUANT_KEY in self.keymap:
            if self.keymap[QUANT_KEY] == 'false':
                self.finished_parsing_quantifier = True

    def __str__(self):
        return "".join(key_to_string(c) for c in self.keys)


class KeyLayout(dict):

    def __init__(self, keybuffer=None):
        super().__init__()
        self.keybuffer = keybuffer
        self.used_keylayout = None

    def use_layout(self, keylayout_name):
        self.keybuffer.keylayout = self.get(keylayout_name, {})
        if self.used_keylayout != keylayout_name:
            self.used_keylayout = keylayout_name
            self.keybuffer.clear()

    def _clean_input(self, context, keys):
        try:
            pointer = self[context]
        except KeyError:
            self[context] = pointer = {}
        if PY3:
            keys = keys.encode('utf-8').decode('latin-1')
        return list(parse_keybinding(keys)), pointer

    def bind(self, context, keys, leaf):
        keys, pointer = self._clean_input(context, keys)
        if not keys:
            return
        last_key = keys[-1]
        for key in keys[:-1]:
            try:
                if isinstance(pointer[key], dict):
                    pointer = pointer[key]
                else:
                    pointer[key] = pointer = {}
            except KeyError:
                pointer[key] = pointer = {}
        pointer[last_key] = leaf

    def copy(self, **kwargs):
        pass  # FIXME : Add functionality from module copy or inherited method

    def unbind(self, context, keys):
        keys, pointer = self._clean_input(context, keys)
        if not keys:
            return
        _unbind_traverse(pointer, keys)
