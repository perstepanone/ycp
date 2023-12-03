# -*- coding: utf-8 -*-


"""Colorschemes define colors for specific contexts.

Generally, this works by passing a set of keywords (strings) to
the colorscheme.get() method to receive the tuple (fg, bg, attr).
fg, bg are the foreground and background colors and attr is the attribute.
The values are specified in ycp.gui.color.

A colorscheme must...

1. be inside either of these directories:
~/.config/ycp/colorschemes/
path/to/ycp/colorschemes/

2. be a subclass of ycp.gui.colorscheme.ColorScheme

3. implement a use(self, context) method which returns (fg, bg, attr).
context is a struct which contains all entries of CONTEXT_KEYS,
associated with either True or False.

Define which colorscheme in your settings (e.g. ~/.config/ycp/settings.conf):
set colorscheme yourschemename
"""

import os.path
from abc import abstractmethod
from curses import color_pair
from io import open

from .. import YCPDIR
from gui.color import get_color
from gui.context import Context
from misc.utils import allow_access_to_confdir, flatten
from functools import cache


class ColorSchemeError(Exception):
    pass


class ColorScheme(object):
    """This is the class that colorschemes must inherit from.

    it defines the get() method, which returns the color tuple
    which fits to the given keys.
    """

    @cache
    def get(self, *keys):
        """Returns the (fg, bg, attr) for the given keys.

        Using this function rather than use() will cache all
        colors for faster access.
        """
        context = Context(keys)
        color = self.use(context)
        if len(color) != 3 or not all(isinstance(value, int) for value in color):
            raise ValueError("Bad Value from colorscheme.  Need "
                             "a tuple of (foreground_color, background_color, attribute).")
        return color

    @cache
    def get_attr(self, *keys):
        """Returns the curses attribute for the specified keys

        Ready to use for curses.setattr()
        """
        fg, bg, attr = self.get(*flatten(keys))
        return attr | color_pair(get_color(fg, bg))

    @abstractmethod
    def use(self, context):
        """Use the colorscheme to determine the (fg, bg, attr) tuple.

        Override this method in your own colorscheme.
        """
        return 1, -1, 0


def _colorscheme_name_to_class(signal):
    # Find the colorscheme.  First look in ~/.config/ycp/colorschemes,
    # then at YCPDIR/colorschemes.  If the file contains a class
    # named Scheme, it is used.  Otherwise, an arbitrary other class
    # is picked.
    if isinstance(signal.value, ColorScheme):
        return

    if not signal.value:
        signal.value = 'default'

    scheme_name = signal.value
    usecustom = not args.clean

    def exists(colorscheme):
        return os.path.exists(colorscheme + '.py') or os.path.exists(colorscheme + '.pyc')

    def is_scheme(cls):
        try:
            return issubclass(cls, ColorScheme)
        except TypeError:
            return False

    # create ~/.config/ycp/colorschemes/__init__.py if it doesn't exist
    if usecustom:
        if os.path.exists(signal.app.confpath('colorschemes')):
            initpy = signal.app.confpath('colorschemes', '__init__.py')
            if not os.path.exists(initpy):
                with open(initpy, "a", encoding="utf-8"):
                    # Just create the file
                    pass

    if usecustom and exists(signal.app.confpath('colorschemes', scheme_name)):
        scheme_supermodule = 'colorschemes'
    elif exists(signal.app.relpath('colorschemes', scheme_name)):
        scheme_supermodule = 'ycp.colorschemes'
        usecustom = False
    else:
        scheme_supermodule = None  # found no matching file.

    if scheme_supermodule is None:
        if signal.previous and isinstance(signal.previous, ColorScheme):
            signal.value = signal.previous
        else:
            signal.value = ColorScheme()
        raise ColorSchemeError("Cannot locate colorscheme `%s'" % scheme_name)
    else:
        if usecustom:
            allow_access_to_confdir(args.confdir, True)
        scheme_module = getattr(
            __import__(scheme_supermodule, globals(), locals(), [scheme_name], 0), scheme_name)
        if usecustom:
            allow_access_to_confdir(args.confdir, False)
        if hasattr(scheme_module, 'Scheme') and is_scheme(scheme_module.Scheme):
            signal.value = scheme_module.Scheme()
        else:
            for var in scheme_module.__dict__.values():
                if var != ColorScheme and is_scheme(var):
                    signal.value = var()
                    break
            else:
                raise ColorSchemeError("The module contains no valid colorscheme!")


def get_all_colorschemes(app):
    colorschemes = set()
    # Load colorscheme names from main ycp/gui/colrschemes dir
    for item in os.listdir(os.path.join(YCPDIR, 'colorschemes')):
        if not item.startswith('__'):
            colorschemes.add(item.rsplit('.', 1)[0])
    # Load colorscheme names from ~/.config/ycp/colorschemes if dir exists
    confpath = app.confpath('colorschemes')
    if os.path.isdir(confpath):
        for item in os.listdir(confpath):
            if not item.startswith('__'):
                colorschemes.add(item.rsplit('.', 1)[0])
    return list(sorted(colorschemes))
