# -*- coding: utf-8 -*-


import os
from os.path import abspath, normpath, join, expanduser, isdir, dirname

from .. import PY3
from config import settings
from misc.history import History


class TabManager:

    def get_tab_list(self):
        pass


class Tab:
    def __init__(self):
        pass

    def open(self):
        pass

    def close(self):
        pass

    def restore(self):
        pass

    def move(self):
        pass

    def create(self):
        pass

    def shift(self):
        pass

    def switch(self):
        pass
