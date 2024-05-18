# -*- coding: utf-8 -*-


class TabManager:

    def __init__(self):
        self.tabslist = {}

    def get_tab_list(self):
        pass

    def tab_open(self):
        pass

    def tab_move(self, offset, narg=None):  # FIXME: Refactoring/delete this method
        if narg:
            return self.tab_open(narg)
        assert isinstance(offset, int)
        tablist = self.get_tab_list()
        current_index = tablist.index(self.current_tab)
        newtab = tablist[(current_index + offset) % len(tablist)]
        if newtab != self.current_tab:
            self.tab_open(newtab)
        return None


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
