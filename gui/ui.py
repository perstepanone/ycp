# -*- coding: utf-8 -*-

import threading
import os
import curses

from gui.displayable import DisplayableContainer
from mouse_event import MouseEvent, _setup_mouse

ESCAPE_ICON_TITLE = '\033]1;'


# TODO: add mice support
class UI(DisplayableContainer):
    def __init__(self, app=None):
        self.is_setup = False
        self.is_on = False
        self.termsize = None
        self.keybuffer = KeyBuffer()
        self.keymaps = KeyMaps(self.keybuffer)
        self.redrawlock = threading.Event()
        self.redrawlock.set()

        self.titlebar = None
        self._viewmode = None
        self.procmngr = None
        self.status = None
        self.console = None
        self.pager = None
        self.browser = None
        # TODO: add multiplexer support
        self._draw_title = None
        if app is not None:
            self.app = app

    def setup_curses(self):
        # os.environ['ESCDELAY'] = '25'
        try:
            self.win = curses.initscr()
        except curses.error as ex:
            if ex.args[0] == "setupterm: could not find terminal":
                os.environ['TERM'] = 'linux'
                self.win = curses.initscr()
        self.keymaps.use_keymap('browser')
        super().__init__(self, None)

    def initialize(self):
        """initialize curses, then call setup (at the first time) and resize."""
        self.win.leaveok(0)
        self.win.keypad(1)
        self.load_mode = False

        curses.cbreak()
        curses.noecho()
        curses.halfdelay(20)

        try:
            curses.curs_set(int(bool(self.settings.show_cursor)))
        except curses.error:
            pass
        curses.start_color()
        try:
            curses.use_default_colors()
        except curses.error:
            pass

        self.settings.signal_bind('setopt.mouse_enabled', _setup_mouse)
        self.settings.signal_bind('setopt.freeze_files', self.redraw_statusbar)
        _setup_mouse({"value": self.settings.mouse_enabled})

        if not self.is_setup:
            self.is_setup = True
            self.setup()
            self.win.addstr("loading...")
            self.win.refresh()
            self._draw_title = curses.tigetflag("hs")

        self.update_size()
        self.is_on = True

    def suspend(self):
        """Turn off curses"""
        if self.app.image_displayer:
            self.app.image_displayer.quit()

        self.win.keypad(0)
        curses.nocbreak()
        curses.echo()
        try:
            curses.curs_set(1)
        except curses.error:
            pass
        if self.settings.mouse_enabled:
            _setup_mouse({"value": False})
        curses.endwin()
        self.is_on = False

    @property
    def load_mode(self):
        return self.load_mode

    @load_mode.setter
    def load_mode(self, boolean):
        boolean = bool(boolean)
        if boolean != self.load_mode:
            self.load_mode = boolean

            if boolean:
                # don't wait for key presses in the load mode
                curses.cbreak()
                self.win.nodelay(1)
            else:
                self.win.nodelay(0)
                # Sanitize halfdelay setting
                halfdelay = min(255, max(1, self.settings.idle_delay // 100))
                curses.halfdelay(halfdelay)

    def destroy(self):
        DisplayableContainer.destroy(self)
        self.suspend()

    def handle_mouse(self):
        """Handles mouse input"""
        pass

    def handle_key(self, key):
        self.hint()

        if key < 0:
            self.keybuffer.clear()

        elif not DisplayableContainer.press(self, key):
            self.keymaps.use_keymap("browser")
            self.press(key)

    def press(self, key):
        keybuffer = self.keybufer
        self.status.clear_message()

        keybuffer.add(key)
        self.app.hide_bookmarks()
        self.browser.draw_hints = not keybuffer.finished_parsing \
                                  and keybuffer.finished_parsing_quantifier

        if keybuffer.result is not None:
            try:
                self.app.execute_console(
                    keybuffer.result,
                    wildcards=keybuffer.wildcards,
                    quantifier=keybuffer.quantifier,
                )
            finally:
                if keybuffer.finished_parsing:
                    keybuffer.clear()
        elif keybuffer.finished_parsing:
            keybuffer.clear()
            return False
        return True

    def handle_keys(self, *keys):
        for key in keys:
            self.handle_key(key)

    def handle_input(self):
        key = self.win.getch()
        if key == curses.KEY_ENTER:
            key = ord("\n")
        if key == 27 or (128 <= key < 256):
            # Handle special keys like ALT+X or unicode here:
            keys = [key]
            previous_load_mode = self.load_mode
            self.set_load_mode(True)
            for _ in range(4):
                getkey = self.win.getch()
                if getkey != -1:
                    keys.append(getkey)
            if len(keys) == 1:
                keys.append(-1)
            elif keys[0] == 27:
                keys[0] = ALT_KEY
            if self.settings.xterm_alt_key:
            # if len(keys) == 2 and keys[1] in range(127, 256):
            #     if keys[0] == 195:
            #         keys = [ALT_KEY, keys[1] - 64]
            #     elif keys[0] == 194:
            #         keys = [ALT_KEY, keys[1] - 128] #TODO: uncommenting this
            self.handle_keys(*keys)
            self.set_load_mode(previous_load_mode)
            if self.settings.flushinput and not self.console.visible:
                curses.flushinp()
        else:
            # Handle simple key presses, CTRL+X, etc here:
            if key >= 0:
                if self.settings.flushinput and not self.console.visible:
                    curses.flushinp()
                if key == curses.KEY_MOUSE:
                    self.handle_mouse()
                elif key == curses.KEY_RESIZE:
                    self.update_size()
                else:
                    if not self.app.input_is_blocked():
                        self.handle_key(key)
            elif key == -1 and not os.isatty(sys.stdin.fileno()):
                # STDIN has been closed
                self.app.exit()

    def setup(self):
        """Build up the UI by initializing widgets."""
        from widgets.titlebar import TitleBar
        from widgets.console import Console
        from widgets.statusbar import StatusBar
        from widgets.procmanager import ProcManager
        from widgets.pager import Pager

        self.titlebar = TitleBar(self.win)
        self.add_child(self.titlebar)

        self.settings.signal_bind('setopt.viewmode', self._set_viewmode)
        self._viewmode = None
        # The following line sets self.browser implicitly through the signal
        self.viewmode = self.settings.viewmode
        self.add_child(self.browser)  # TODO:Refactor this

        self.procmngr = ProcManager(self.win)
        self.taskview.visible = False
        self.add_child(self.taskview)

        self.status = StatusBar(self.win, self.browser.main_column)
        self.add_child(self.status)

        self.console = Console(self.win)
        self.add_child(self.console)
        self.console.visible = False

        self.pager = Pager(self.win)
        self.pager.visible = False
        self.add_child(self.pager)

    def redraw(self):
        """Redraw all widgets"""
        self.redrawlock.wait()
        self.redrawlock.clear()
        self.poke()

        # determine which widgets are shown
        if self.console.wait_for_command_input or self.console.question_queue:
            self.console.focused = True
            self.console.visible = True
            self.status.visible = False
        else:
            self.console.focused = False
            self.console.visible = False
            self.status.visible = True

        self.draw()
        self.finalize()
        self.redrawlock.set()

    def redraw_window(self):
        """Redraw the window. This only calls self.win.redrawwin()."""
        self.win.erase()
        self.win.redrawwin()
        self.win.refresh()
        self.win.redrawwin()
        self.need_redraw = True

    def update_size(self):
        """resize all widgets"""
        self.termsize = self.win.getmaxyx()
        y, x = self.termsize

        self.browser.resize(self.settings.status_bar_on_top and 2 or 1, 0, y - 2, x)
        self.procmngr.resize(1, 0, y - 2, x)
        self.pager.resize(1, 0, y - 2, x)
        self.titlebar.resize(0, 0, 1, x)
        self.status.resize(self.settings.status_bar_on_top and 1 or y - 1, 0, 1, x)
        self.console.resize(y - 1, 0, 1, x)

    def draw(self):
        """Draw all objects in the container"""
        self.win.touchwin()
        DisplayableContainer.draw(self)
        # if self._draw_title and self.settings.update_title:   #TODO: Refactor this
        #     cwd = self.fm.thisdir.path
        #     if self.settings.tilde_in_titlebar \
        #        and (cwd == self.fm.home_path
        #             or cwd.startswith(self.fm.home_path + "/")):
        #         cwd = '~' + cwd[len(self.fm.home_path):]
        #     if self.settings.shorten_title:
        #         split = cwd.rsplit(os.sep, self.settings.shorten_title)
        #         if os.sep in split[0]:
        #             cwd = os.sep.join(split[1:])
        #     try:
        #         fixed_cwd = cwd.encode('utf-8', 'surrogateescape'). \
        #             decode('utf-8', 'replace')
        #         titlecap = curses.tigetstr('tsl')
        #         escapes = (
        #             [titlecap.decode("latin-1")]
        #             if titlecap is not None
        #             else [] + [ESCAPE_ICON_TITLE]
        #         )
        #         belcap = curses.tigetstr('fsl')
        #         bel = belcap.decode('latin-1') if belcap is not None else ""
        #         fmt_tups = [(e, fixed_cwd, bel) for e in escapes]
        #     except UnicodeError:
        #         pass
        #     else:
        #         for fmt_tup in fmt_tups:
        #             sys.stdout.write("%sranger:%s%s" % fmt_tup)
        #             sys.stdout.flush()

        self.win.refresh()

    def finalize(self):
        """Finalize every object in container and refresh the window"""
        DisplayableContainer.finalize(self)
        self.win.refresh()

    def draw_images(self):
        if self.pager.visible:
            self.pager.draw_image()
        elif self.browser.pager:
            if self.browser.pager.visible:
                self.browser.pager.draw_image()
            else:
                self.browser.columns[-1].draw_image()

    def close_pager(self):
        if self.console.visible:
            self.console.focused = True
        self.pager.close()
        self.pager.visible = False
        self.pager.focused = False
        self.browser.visible = True

    def open_pager(self):
        self.browser.columns[-1].clear_image(force=True)
        if self.console.focused:
            self.console.focused = False
        self.pager.open()
        self.pager.visible = True
        self.pager.focused = True
        self.browser.visible = False
        return self.pager

    def open_embedded_pager(self):
        self.browser.open_pager()
        for column in self.browser.columns:
            if column == self.browser.main_column:
                break
            column.level_shift(amount=1)
        return self.browser.pager

    def close_embedded_pager(self):
        self.browser.close_pager()
        for column in self.browser.columns:
            column.level_restore()

    def open_console(self, string='', prompt=None, position=None):
        self.change_mode('normal')
        if self.console.open(string, prompt=prompt, position=position):
            self.status.msg = None

    def close_console(self):
        self.console.close()
        self.close_pager()

    def open_taskview(self):  # TODO: Rename method
        self.browser.columns[-1].clear_image(force=True)
        self.pager.close()
        self.pager.visible = False
        self.pager.focused = False
        self.console.visible = False
        self.browser.visible = False
        self.taskview.visible = True
        self.taskview.focused = True

    def redraw_main_column(self):
        self.browser.main_column.need_redraw = True

    def redraw_statusbar(self):
        self.status.need_redraw = True

    def close_taskview(self):  # TODO: Rename method
        self.taskview.visible = False
        self.browser.visible = True
        self.taskview.focused = False

    def throbber(self, string='.', remove=False):
        if remove:
            self.titlebar.throbber = type(self.titlebar).throbber
        else:
            self.titlebar.throbber = string

    def hint(self, text=None):
        self.status.hint = text

    def get_pager(self):
        if self.browser.pager and self.browser.pager.visible:
            return self.browser.pager
        return self.pager

    @property
    def _viewmode(self):
        return self._viewmode

    @_viewmode.setter
    def _viewmode(self, value, signal=None):
        if isinstance(value, signal):
            value = value.value
        if value == '':
            value = self.ALLOWED_VIEWMODES[0]
        if value in self.ALLOWED_VIEWMODES:
            if self._viewmode != value:
                self._viewmode = value
                new_browser = self._viewmode_to_class(value)(self.win)

                if self.browser is None:
                    self.add_child(new_browser)
                else:
                    old_size = self.browser.y, self.browser.x, self.browser.hei, self.browser.wid
                    self.replace_child(self.browser, new_browser)
                    self.browser.destroy()
                    new_browser.resize(*old_size)

                self.browser = new_browser
                self.redraw_window()
        else:
            raise ValueError("Attempting to set invalid viewmode `%s`, should "
                             "be one of `%s`." % (value, "`, `".join(self.ALLOWED_VIEWMODES)))

    def change_mode(self, mode=None):
        """:change_mode <mode>

        Change mode to "visual" (selection) or "normal" mode.
        """
        if mode is None:
            self.fm.notify('Syntax: change_mode <mode>', bad=True)
            return
        if mode == self.mode:  # pylint: disable=access-member-before-definition
            return
        if mode == 'visual':
            self._visual_pos_start = self.thisdir.pointer
            self._visual_move_cycles = 0
            self._previous_selection = set(self.thisdir.marked_items)
            self.mark_files(val=not self._visual_reverse, movedown=False)
        elif mode == 'normal':
            if self.mode == 'visual':  # pylint: disable=access-member-before-definition
                self._visual_pos_start = None
                self._visual_move_cycles = None
                self._previous_selection = None
        else:
            return
        self.mode = mode
        self.ui.status.request_redraw()

    def move(self):
        pass

    def move_parent(self):
        pass

    def select_file(self):
        pass

    def scroll(self):
        pass

    def get_preview(self):
        pass

    def update_preview(self):
        pass
