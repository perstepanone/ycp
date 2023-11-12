# -*- coding: utf-8 -*-

import mimetypes
import os
import pwd
import socket
import ycp
from gui.ui import UI, Tab
from collections import deque


class App:
    def __init__(self, ui=None, paths=None, bookmarks=None):
        self.ui = ui if ui is not None else UI()
        self.paths = paths
        self.bookmarks = bookmarks
        self.current_tab = 1
        self.tabs = {}
        self.restorable_tabs = deque([], ycp.MAX_RESTORABLE_TABS)
        self.default_linemodes = deque()
        self.loader = Loader()
        self.copy_buffer = set()
        self.metadata = MetadataManager()
        self.image_displayer = None
        self.run = None
        self.settings = None
        self.expectedtab = None

        try:
            self.username = pwd.getpwudid(os.getuid()).pw_name
        except KeyError:
            self.username = f'uid:{os.geteuid()}'
        self.hostname = socket.gethostname()
        self.home_path = os.path.expanduser('~')

        if not mimetypes.inited:
            pass
        self.mimetypes = mimetypes

    def initialize(self):
        """If ui/bookmarks are None, they will be initialized here."""

        # self.tabs =
        tab_list = self.get_tab_list()
        if tab_list:
            self.current_tab = tab_list[0]
            self.expectedtab = self.tabs[self.current_tab]
        else:
            self.current_tab = 1
            self.tabs = self.current_tab = self.expectedtab = Tab()

        # FIXME: add statement about clean option
        # TODO: add bookmarks/tags functionality

        self.ui.setup_curses()
        self.ui.initialize()

    def destroy(self):
        pass

    def block_input(self):
        pass

    def input_is_blocked(self):
        pass

    def exit(self):
        """Exit the program."""
        raise SystemExit

    def reset(self):
        pass

