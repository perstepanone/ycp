# -*- coding: utf-8 -*-


import curses
from itertools import groupby

from ...config import settings
from ...misc.keybinding_parser import key_to_string
from ..displayable import Widget
from .column import BrowserColumn
from .pager import Pager
from ..displayable import DisplayableContainer


class View(Widget, DisplayableContainer):

    def __init__(self):
        self.draw_bookmarks = False
        self.need_clear = False
        self.draw_hints = False
        self.draw_info = False
        super(DisplayableContainer, self).__init__(self, win)
        self.app.signal_bind('move', self.request_clear)
        self.old_draw_borders = self.settings.draw_borders
        self.columns = None
        self.main_column = None
        self.pager = None

    def request_clear(self):
        self.need_clear = True

    def draw(self):
        if self.need_clear:
            self.win.erase()
            self.need_redraw = True
            self.need_clear = False
        for tab in self.app.tabs.values():
            directory = tab.thisdir
            if directory:
                directory.load_content_if_outdated()
                directory.use()
        DisplayableContainer.draw(self)
        if self.draw_bookmarks:
            self._draw_bookmarks()
        elif self.draw_hints:
            self._draw_hints()
        elif self.draw_info:
            self._draw_info(self.draw_info)

    def finalize(self):
        if self.pager is not None and self.pager.visible:
            try:
                self.app.ui.win.move(self.main_column.y, self.main_column.x)
            except curses.error:
                pass
        else:
            col_x = self.main_column.x
            col_y = self.main_column.y - self.main_column.scroll_begin
            if self.main_column.target:
                col_y += self.main_column.target.pointer
            try:
                self.app.ui.win.move(col_y, col_x)
            except curses.error:
                pass

    def _draw_bookmarks(self):  # FIXME: Refactor/rename this method
        self.columns[-1].clear_image(force=True)
        self.app.bookmarks.update_if_outdated()
        self.color_reset()
        self.need_clear = True

        sorted_bookmarks = sorted(
            (
                item for item in self.app.bookmarks
                if self.app.settings.show_hidden_bookmarks or '/.' not in item[1].path
            ),
            key=lambda t: t[0].lower(),
        )

        hei = min(self.hei - 1, len(sorted_bookmarks))
        ystart = self.hei - hei

        maxlen = self.wid
        self.addnstr(ystart - 1, 0, "mark  path".ljust(self.wid), self.wid)

        whitespace = " " * maxlen
        for line, items in zip(range(self.hei - 1), sorted_bookmarks):
            key, mark = items
            string = " " + key + "   " + mark.path
            self.addstr(ystart + line, 0, whitespace)
            self.addnstr(ystart + line, 0, string, self.wid)

        self.win.chgat(ystart - 1, 0, curses.A_UNDERLINE)

    def _draw_info(self, lines):
        self.columns[-1].clear_image(force=True)
        self.need_clear = True
        hei = min(self.hei - 1, len(lines))
        ystart = self.hei - hei
        i = ystart
        whitespace = " " * self.wid
        for line in lines:
            if i >= self.hei:
                break
            self.addstr(i, 0, whitespace)
            self.addnstr(i, 0, line, self.wid)
            i += 1

    def _draw_hints(self):
        self.columns[-1].clear_image(force=True)
        self.color_reset()
        self.need_clear = True
        hints = []

        def populate_hints(keymap, prefix=""):
            for k, v in keymap.items():  # FIXME: Refactor this attribute
                k = prefix + key_to_string(k)
                if isinstance(v, dict):
                    populate_hints(v, k)
                else:
                    text = v
                    if text.startswith('hint') or text.startswith('chain hint'):
                        continue
                    hints.append((key, text))

        populate_hints(self.app.ui.keybuffer.pointer)

        def sort_hints(hints):  # FIXME: Refactor or delete this method
            """Sort the hints by the action string but first group them by the
            first key.

            """

            # groupby needs the list to be sorted.
            hints.sort(key=lambda t: t[0])

            def group_hints(hints):
                def first_key(hint):
                    return hint[0][0]

                def action_string(hint):
                    return hint[1]

                return (sorted(group, key=action_string)
                        for _, group
                        in groupby(
                    hints,
                    key=first_key))

            grouped_hints = group_hints(hints)

            # If there are too many hints, collapse the sublists.
            if len(hints) > self.app.settings.hint_collapse_threshold:
                def first_key_in_group(group):
                    return group[0][0][0]

                grouped_hints = (
                    [(first_key_in_group(hint_group), "...")]
                    if len(hint_group) > 1
                    else hint_group
                    for hint_group in grouped_hints
                )

            # Sort by the first action in group.
            grouped_hints = sorted(grouped_hints, key=lambda g: g[0][1])

            def flatten(nested_list):
                return [item for inner_list in nested_list for item in inner_list]

            return flatten(grouped_hints)

        hints = sort_hints(hints)

        hei = min(self.hei - 1, len(hints))
        ystart = self.hei - hei
        self.addnstr(
            ystart - 1, 0, "key          command".ljust(self.wid), self.wid)
        try:
            self.win.chgat(ystart - 1, 0, curses.A_UNDERLINE)
        except curses.error:
            pass
        whitespace = " " * self.wid
        i = ystart
        for key, cmd in hints:
            string = " " + key.ljust(11) + " " + cmd
            self.addstr(i, 0, whitespace)
            self.addnstr(i, 0, string, self.wid)
            i += 1

    def click(self, event):
        if DisplayableContainer.click(self, event):
            return True
        direction = event.mouse_wheel_direction()
        if direction:
            self.main_column.scroll(direction)
        return False

    def resize(self, y, x, hei=None, wid=None):  # FIXME: Check up implementation
        DisplayableContainer.resize(self, y, x, hei, wid)

    def poke(self):  # FIXME: Check up implementation
        DisplayableContainer.poke(self)


class MillerView(View):

    def __init__(self):
        self.ratios = None
        self.preview = True
        self.is_collapsed = False
        self.stretch_ratios = None
        self.old_collapse = False
        super(View, self).__init__(self, win)
        self.columns = []

        self.rebuild()

        for option in ('preview_directories', 'preview_files'):
            self.settings.signal_bind('setopt.' + option,
                                      self._request_clear_if_has_borders, weak=True)

        self.settings.signal_bind('setopt.column_ratios', self.request_clear)
        self.settings.signal_bind('setopt.column_ratios', self.rebuild,
                                  priority=settings.SIGNAL_PRIORITY_AFTER_SYNC)

        self.old_draw_borders = self.settings.draw_borders

    def rebuild(self):
        for child in self.container:
            if isinstance(child, BrowserColumn):
                self.remove_child(child)
                child.destroy()

        self.pager = Pager(self.win, embedded=True)
        self.pager.visible = False
        self.add_child(self.pager)

        ratios = self.settings.column_ratios

        for column in self.columns:
            column.destroy()
            self.remove_child(column)
        self.columns = []

        ratios_sum = sum(ratios)
        self.ratios = tuple((x / ratios_sum) for x in ratios)

        last = 0.1 if self.settings.padding_right else 0
        if len(self.ratios) >= 2:
            self.stretch_ratios = self.ratios[:-2] + \
                ((self.ratios[-2] + self.ratios[-1] * 1.0 - last),
                 (self.ratios[-1] * last))

        offset = 1 - len(ratios)
        if self.preview:
            offset += 1

        for level in range(len(ratios)):
            column = BrowserColumn(self.win, level + offset)
            self.add_child(column)
            self.columns.append(column)

        try:
            self.main_column = self.columns[self.preview and -2 or -1]
        except IndexError:
            self.main_column = None
        else:
            self.main_column.display_infostring = True
            self.main_column.main_column = True

        self.resize(self.y, self.x, self.hei, self.wid)

    def _request_clear_if_has_borders(self):
        if self.settings.draw_borders:
            self.request_clear()

    def draw(self):
        if self.need_clear:
            self.win.erase()
            self.need_redraw = True  # FIXME: Replace or/and rename attribute
            self.need_clear = False
        for tab in self.app.tabs.values():
            directory = tab.thisdir
            if directory:
                directory.load_content_if_outdated()
                directory.use()
        DisplayableContainer.draw(self)
        if self.settings.draw_borders:
            draw_borders = self.settings.draw_borders.lower()
            # 'true' for backwards compat.
            if draw_borders in ['both', 'true']:
                border_types = ['separators', 'outline']
            else:
                border_types = [draw_borders]
            self._draw_borders(border_types)
        if self.draw_bookmarks:
            self._draw_bookmarks()
        elif self.draw_hints:
            self._draw_hints()
        elif self.draw_info:
            self._draw_info(self.draw_info)

    def _draw_borders(self, border_types):
        win = self.win

        self.color('in_browser', 'border')

        left_start = 0
        right_end = self.wid - 1

        for child in self.columns:
            if not child.has_preview():
                left_start = child.x + child.wid
            else:
                break

        # Shift the rightmost vertical line to the left to create a padding,
        # but only when padding_right is on, the preview column is collapsed
        # and we did not open the pager to "zoom" in to the file.
        if self.settings.padding_right and not self.pager.visible and self.is_collapsed:
            right_end = self.columns[-1].x - 1
            if right_end < left_start:
                right_end = self.wid - 1

        # Draw horizontal lines and the leftmost vertical line
        if 'outline' in border_types:
            try:
                win.hline(0, left_start, curses.ACS_HLINE,
                          right_end - left_start)
                win.hline(self.hei - 1, left_start,
                          curses.ACS_HLINE, right_end - left_start)
                win.vline(1, left_start, curses.ACS_VLINE, self.hei - 2)
            except curses.error:
                pass

        # Draw the vertical lines in the middle
        if 'separators' in border_types:
            for child in self.columns[:-1]:
                if not child.has_preview():
                    continue
                if child.main_column and self.pager.visible:
                    # If we "zoom in" with the pager, we have to
                    # skip the between main_column and pager.
                    break
                x = child.x + child.wid
                y = self.hei - 1
                try:
                    win.vline(1, x, curses.ACS_VLINE, y - 1)
                    if 'outline' in border_types:
                        self.addch(0, x, curses.ACS_TTEE, 0)
                        self.addch(y, x, curses.ACS_BTEE, 0)
                    else:
                        self.addch(0, x, curses.ACS_VLINE, 0)
                        self.addch(y, x, curses.ACS_VLINE, 0)
                except curses.error:
                    # in case it's off the boundaries
                    pass

        if 'outline' in border_types:
            # Draw the last vertical line
            try:
                win.vline(1, right_end, curses.ACS_VLINE, self.hei - 2)
            except curses.error:
                pass

        if 'outline' in border_types:
            self.addch(0, left_start, curses.ACS_ULCORNER)
            self.addch(self.hei - 1, left_start, curses.ACS_LLCORNER)
            self.addch(0, right_end, curses.ACS_URCORNER)
            self.addch(self.hei - 1, right_end, curses.ACS_LRCORNER)

    def _collapse(self):
        # Should the last column be cut off? (Because there is no preview)
        if not self.settings.collapse_preview or not self.preview \
                or not self.stretch_ratios:
            return False
        result = not self.columns[-1].has_preview()
        target = self.columns[-1].target
        if not result and target and target.is_file:
            if self.app.settings.preview_script and \
                    self.app.settings.use_preview_script:
                try:
                    result = not self.app.previews[target.realpath]['foundpreview']
                except KeyError:
                    return self.old_collapse

        self.old_collapse = result
        return result

    def resize(self, y, x, hei=None, wid=None):
        """Resize all the columns according to the given ratio"""
        View.resize(self, y, x, hei, wid)

        border_type = self.settings.draw_borders.lower()
        if border_type in ['outline', 'both', 'true']:
            pad = 1
        else:
            pad = 0
        left = pad
        self.is_collapsed = self._collapse()
        if self.is_collapsed:
            generator = enumerate(self.stretch_ratios)
        else:
            generator = enumerate(self.ratios)

        last_i = len(self.ratios) - 1

        for i, ratio in generator:
            wid = int(ratio * self.wid)

            cut_off = self.is_collapsed and not self.settings.padding_right
            if i == last_i:
                if not cut_off:
                    wid = int(self.wid - left + 1 - pad)
                else:
                    self.columns[i].resize(
                        pad, max(0, left - 1), hei - pad * 2, 1)
                    self.columns[i].visible = False
                    continue

            if i == last_i - 1:
                self.pager.resize(pad, left, hei - pad * 2,
                                  max(1, self.wid - left - pad))

                if cut_off:
                    self.columns[i].resize(
                        pad, left, hei - pad * 2, max(1, self.wid - left - pad))
                    continue

            try:
                self.columns[i].resize(
                    pad, left, hei - pad * 2, max(1, wid - 1))
            except KeyError:
                pass

            left += wid

    def open_pager(self):
        self.pager.visible = True
        self.pager.focused = True
        self.need_clear = True
        self.pager.open()
        try:
            self.columns[-1].visible = False
            self.columns[-2].visible = False
        except IndexError:
            pass

    def close_pager(self):
        self.pager.visible = False
        self.pager.focused = False
        self.need_clear = True
        self.pager.close()
        try:
            self.columns[-1].visible = True
            self.columns[-2].visible = True
        except IndexError:
            pass

    def poke(self):
        View.poke(self)

        # Show the preview column when it has a preview but has
        # been hidden (e.g. because of padding_right = False)
        if not self.columns[-1].visible and self.columns[-1].has_preview() \
                and not self.pager.visible:
            self.columns[-1].visible = True

        if self.preview and self.is_collapsed != self._collapse():
            if self.app.settings.preview_files:
                # force clearing the image when resizing preview column
                self.columns[-1].clear_image(force=True)
            self.resize(self.y, self.x, self.hei, self.wid)

        if self.old_draw_borders != self.settings.draw_borders:
            self.resize(self.y, self.x, self.hei, self.wid)
            self.old_draw_borders = self.settings.draw_borders


class MultipaneView(View):

    def __init__(self):
        super(View, self).__init__(self, win)
        self.app.signal_bind('tab.layoutchange', self._layoutchange_handler)
        self.app.signal_bind('tab.change', self._tabchange_handler)
        self.rebuild()

        self.old_draw_borders = self._draw_borders_setting()

    def _draw_borders_setting(self):
        # If draw_borders_multipane has not been set, it defaults to `None`
        # and we fallback to using draw_borders. Important to note:
        # `None` is different from the string "none" referring to no borders
        if self.settings.draw_borders_multipane is not None:
            return self.settings.draw_borders_multipane
        else:
            return self.settings.draw_borders

    def _layoutchange_handler(self):
        if self.app.ui.browser == self:
            self.rebuild()

    def _tabchange_handler(self, signal):
        if self.app.ui.browser == self:
            if signal.old:
                signal.old.need_redraw = True
            if signal.new:
                signal.new.need_redraw = True

    def rebuild(self):
        self.columns = []

        for child in self.container:
            self.remove_child(child)
            child.destroy()
        for name, tab in self.app.tabs.items():
            column = BrowserColumn(self.win, 0, tab=tab)
            column.main_column = True
            column.display_infostring = True
            if name == self.app.current_tab:
                self.main_column = column
            self.columns.append(column)
            self.add_child(column)
        self.resize(self.y, self.x, self.hei, self.wid)

    def draw(self):
        if self.need_clear:
            self.win.erase()
            self.need_redraw = True  # FIXME: Rename or/and replace attribute
            self.need_clear = False

        View.draw(self)

        if self._draw_borders_setting():
            draw_borders = self._draw_borders_setting()
            # 'true' for backwards compat.
            if draw_borders in ['both', 'true']:
                border_types = ['separators', 'outline']
            else:
                border_types = [draw_borders]
            self._draw_borders(border_types)
        if self.draw_bookmarks:
            self._draw_bookmarks()
        elif self.draw_hints:
            self._draw_hints()
        elif self.draw_info:
            self._draw_info(self.draw_info)

    def _draw_border_rectangle(self, left_start, right_end):
        win = self.win
        win.hline(0, left_start, curses.ACS_HLINE, right_end - left_start)
        win.hline(self.hei - 1, left_start,
                  curses.ACS_HLINE, right_end - left_start)
        win.vline(1, left_start, curses.ACS_VLINE, self.hei - 2)
        win.vline(1, right_end, curses.ACS_VLINE, self.hei - 2)
        # Draw the four corners
        self.addch(0, left_start, curses.ACS_ULCORNER)
        self.addch(self.hei - 1, left_start, curses.ACS_LLCORNER)
        self.addch(0, right_end, curses.ACS_URCORNER)
        self.addch(self.hei - 1, right_end, curses.ACS_LRCORNER)

    def _draw_borders(self, border_types):
        win = self.win
        self.color('in_browser', 'border')

        left_start = 0
        right_end = self.wid - 1

        # Draw the outline borders
        if 'active-pane' not in border_types:
            if 'outline' in border_types:
                try:
                    self._draw_border_rectangle(left_start, right_end)
                except curses.error:
                    pass

            # Draw the column separators
            if 'separators' in border_types:
                for child in self.columns[:-1]:
                    x = child.x + child.wid
                    y = self.hei - 1
                    try:
                        win.vline(1, x, curses.ACS_VLINE, y - 1)
                        if 'outline' in border_types:
                            self.addch(0, x, curses.ACS_TTEE, 0)
                            self.addch(y, x, curses.ACS_BTEE, 0)
                        else:
                            self.addch(0, x, curses.ACS_VLINE, 0)
                            self.addch(y, x, curses.ACS_VLINE, 0)
                    except curses.error:
                        pass
        else:
            bordered_column = self.main_column
            left_start = max(bordered_column.x, 0)
            right_end = min(left_start + bordered_column.wid, self.wid - 1)
            try:
                self._draw_border_rectangle(left_start, right_end)
            except curses.error:
                pass

    def resize(self, y, x, hei=None, wid=None):
        View.resize(self, y, x, hei, wid)

        border_type = self._draw_borders_setting()
        if border_type in ['outline', 'both', 'true', 'active-pane']:
            # 'true' for backwards compat., no height pad needed for 'separators'
            pad = 1
        else:
            pad = 0
        column_width = int((wid - len(self.columns) + 1) / len(self.columns))
        left = 0
        top = 0
        for column in self.columns:
            column.resize(top + pad, left, hei - pad * 2, max(1, column_width))
            left += column_width + 1
            column.need_redraw = True
        self.need_redraw = True  # FIXME: Rename or/and replace attribute

    def poke(self):
        View.poke(self)

        if self.old_draw_borders != self._draw_borders_setting():
            self.resize(self.y, self.x, self.hei, self.wid)
            self.old_draw_borders = self._draw_borders_setting()
