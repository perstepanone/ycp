# -*- coding: utf-8 -*-

from ...misc.accumulator import Accumulator

from ..displayable import Widget


class TaskManager(Widget, Accumulator):

    def __init__(self, win):
        self.old_lst = None
        super(Widget, self).__init__(self, win)
        super(Accumulator, self).__init__(self)
        self.scroll_begin = 0

    def draw(self):
        base_clr = ['in_taskview']
        lst = self.get_list()

        if self.old_lst != lst:
            self.old_lst = lst
            self.need_redraw = True  # FIXME: Rename or/and replace attribute

        if self.need_redraw:
            self.win.erase()
            if not self.pointer_is_synced():
                self.sync_index()

            if self.hei <= 0:
                return

            self.addstr(0, 0, "Task View")
            self.color_at(0, 0, self.wid, tuple(base_clr), 'title')

            if lst:
                for i in range(self.hei - 1):
                    i += self.scroll_begin
                    try:
                        obj = lst[i]
                    except IndexError:
                        break

                    y = i + 1
                    clr = list(base_clr)

                    if self.pointer == i:
                        clr.append('selected')

                    descr = obj.get_description()
                    if obj.progressbar_supported and 0 <= obj.percent <= 100:
                        self.addstr(y, 0, "%3.2f%% - %s" % (obj.percent, descr), self.wid)
                        wid = int((self.wid / 100) * obj.percent)
                        self.color_at(y, 0, self.wid, tuple(clr))
                        self.color_at(y, 0, wid, tuple(clr), 'loaded')
                    else:
                        self.addstr(y, 0, descr, self.wid)
                        self.color_at(y, 0, self.wid, tuple(clr))

            else:
                if self.hei > 1:
                    self.addstr(1, 0, "No task in the queue.")
                    self.color_at(1, 0, self.wid, tuple(base_clr), 'error')

            self.color_reset()

    def finalize(self):
        y = self.y + 1 + self.pointer - self.scroll_begin
        self.app.ui.win.move(y, self.x)

    def task_remove(self, i=None):
        if i is None:
            i = self.pointer

        if self.app.loader.queue:
            self.app.loader.remove(index=i)

    def task_move(self, to, i=None):  # FIXME: Invalid name
        if i is None:
            i = self.pointer

        self.app.loader.move(pos_src=i, pos_dest=to)

    def press(self, key):
        self.app.ui.keymaps.use_keymap('taskview')
        self.app.ui.press(key)

    def get_list(self):
        return self.app.loader.queue
