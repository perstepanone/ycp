# -*- coding: utf-8 -*-

from os.path import basename
from bidi.algorithm import get_display

from gui.bar import Bar
from . import Widget


class TitleBar(Widget):

    def __init__(self, *args, **keywords):

        self.old_thisfile = None
        self.old_keybuffer = None
        self.old_wid = None
        self.result = None
        self.right_sumsize = 0
        self.throbber = ' '
        self.need_redraw = False
        super(Widget, self).__init__(self, *args, **keywords)
        self.app.signal_bind('tab.change', self.request_redraw, weak=True)

    def request_redraw(self):
        self.need_redraw = True

    def draw(self):
        if self.need_redraw or \
                self.app.thisfile != self.old_thisfile or \
                str(self.app.ui.keybuffer) != str(self.old_keybuffer) or \
                self.wid != self.old_wid:
            self.need_redraw = False
            self.old_wid = self.wid
            self.old_thisfile = self.app.thisfile
            self._calc_bar()
        self._print_result(self.result)
        if self.wid > 2:
            self.color('in_titlebar', 'throbber')
            self.addnstr(self.y, self.wid - self.right_sumsize, self.throbber, 1)

    def click(self, event):
        """Handle a MouseEvent"""
        direction = event.mouse_wheel_direction()
        if direction:
            self.app.tab_move(direction)
            self.need_redraw = True
            return True

        if not event.pressed(1) or not self.result:
            return False

        pos = self.wid - 1
        for tabname in reversed(self.app.get_tab_list()):
            tabtext = self._get_tab_text(tabname)
            pos -= len(tabtext)
            if event.x > pos:
                self.app.tab_open(tabname)
                self.need_redraw = True
                return True

        pos = 0
        for i, part in enumerate(self.result):
            pos += len(part)
            if event.x < pos:
                if self.settings.hostname_in_titlebar and i <= 2:
                    self.app.enter_dir("~")
                else:
                    if 'directory' in part.__dict__:
                        self.app.enter_dir(part.directory)
                return True
        return False

    def _calc_bar(self):
        bar = Bar('in_titlebar')
        self._get_left_part(bar)
        self._get_right_part(bar)
        try:
            bar.shrink_from_the_left(self.wid)
        except ValueError:
            bar.shrink_by_removing(self.wid)
        self.right_sumsize = bar.right.sumsize()
        self.result = bar.combine()

    def _get_left_part(self, bar):
        # TODO: Properly escape non-printable chars without breaking unicode
        if self.settings.hostname_in_titlebar:
            if self.app.username == 'root':
                clr = 'bad'
            else:
                clr = 'good'

            bar.add(self.app.username, 'hostname', clr, fixed=True)
            bar.add('@', 'hostname', clr, fixed=True)
            bar.add(self.app.hostname, 'hostname', clr, fixed=True)
            bar.add(' ', 'hostname', clr, fixed=True)

        if self.app.thisdir:
            pathway = self.app.thistab.pathway
            if self.settings.tilde_in_titlebar \
                    and (self.app.thisdir.path.startswith(self.app.home_path + "/") or
                         self.app.thisdir.path == self.app.home_path):
                pathway = pathway[self.app.home_path.count('/') + 1:]
                bar.add('~/', 'directory', fixed=True)

            for path in pathway:
                if path.is_link:
                    clr = 'link'
                else:
                    clr = 'directory'

                bidi_basename = get_display(path.basename)  # TODO: Test it
                bar.add(bidi_basename, clr, directory=path)
                bar.add('/', clr, fixed=True, directory=path)

            if self.app.thisfile is not None and \
                    self.settings.show_selection_in_titlebar:
                bidi_file_path = get_display(self.app.thisfile.relative_path)
                bar.add(bidi_file_path, 'file')
        else:
            path = self.app.thistab.path
            if self.settings.tilde_in_titlebar \
                    and (self.app.thistab.path.startswith(self.app.home_path + "/") or
                         self.app.thistab.path == self.app.home_path):
                path = path[len(self.app.home_path + "/"):]
                bar.add('~/', 'directory', fixed=True)

            clr = 'directory'
            bar.add(path, clr, directory=path)
            bar.add('/', clr, fixed=True, directory=path)

    def _get_right_part(self, bar):
        # TODO: fix that pressed keys are cut off when chaining CTRL keys
        kbuf = str(self.app.ui.keybuffer)
        self.old_keybuffer = kbuf
        bar.addright(' ', 'space', fixed=True)
        bar.addright(kbuf, 'keybuffer', fixed=True)
        bar.addright(' ', 'space', fixed=True)
        if len(self.app.tabs) > 1:
            for tabname in self.app.get_tab_list():
                tabtext = self._get_tab_text(tabname)
                clr = 'good' if tabname == self.app.current_tab else 'bad'
                bar.addright(tabtext, 'tab', clr, fixed=True)

    def _get_tab_text(self, tabname):
        result = ' ' + str(tabname)
        if self.settings.dirname_in_tabs:
            dirname = basename(self.app.tabs[tabname].path)
            if not dirname:
                result += ":/"
            elif len(dirname) > 15:
                result += ":" + dirname[:14] + self.ellipsis[self.settings.unicode_ellipsis]
            else:
                result += ":" + dirname  # FIXME : Rename/Replace attribute
        return result

    def _print_result(self, result):
        self.win.move(0, 0)
        for part in result:
            self.color(*part.lst)
            y, x = self.win.getyx()
            self.addstr(y, x, str(part))
        self.color_reset()
