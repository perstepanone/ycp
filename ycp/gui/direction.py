# -*- coding: utf-8 -*-

"""This class provides convenient methods for movement operations.

Direction objects are handled just like dicts but provide
methods like up() and down() which give you the correct value
for the vertical direction, even if only the "up" or "down" key
has been defined.


>>> d = Direction(down=5)
>>> d.down()
5
>>> d.up()
-5
>>> bool(d.horizontal())
False
"""

import math


class Direction(dict):

    """ Class defines moving cursor on pager`s columns
    """

    def __init__(self, dictionary=None, **keywords):
        if dictionary is not None:
            dict.__init__(self, dictionary)  # FIXME: Data structures
        else:
            dict.__init__(self, keywords)
        if 'to' in self:
            self['down'] = self['to']
            self['absolute'] = True

    def copy(self):
        return Direction(**self)

    def _get_bool(self, first, second, fallback=None):
        try:
            return self[first]
        except KeyError:
            try:
                return not self[second]
            except KeyError:
                return fallback

    def _get_direction(self, first, second, fallback=0):
        try:
            return self[first]
        except KeyError:
            try:
                return -self[second]
            except KeyError:
                return fallback

    def up(self):
        # FIXME: disable=invalid-unary-operand-type
        return -Direction.down(self)

    def down(self):
        return Direction._get_direction(self, 'down', 'up')

    def right(self):
        return Direction._get_direction(self, 'right', 'left')

    def absolute(self):
        return Direction._get_bool(self, 'absolute', 'relative')

    def left(self):
        # FIXME: disable=invalid-unary-operand-type
        return -Direction.right(self)

    def relative(self):
        return not Direction.absolute(self)

    def vertical_direction(self):
        down = Direction.down(self)
        return (down > 0) - (down < 0)

    def horizontal_direction(self):
        right = Direction.right(self)
        return (right > 0) - (right < 0)

    def vertical(self):
        return set(self) & set(['up', 'down'])  # FIXME: Data structures

    def horizontal(self):
        return set(self) & set(['left', 'right'])  # FIXME: Data structures

    def pages(self):
        return 'pages' in self and self['pages']

    def percentage(self):
        return 'percentage' in self and self['percentage']

    def cycle(self):
        return self.get('cycle') in (True, 'true', 'on', 'yes')

    def one_indexed(self):
        return ('one_indexed' in self
                and self.get('one_indexed') in (True, 'true', 'on', 'yes'))

    def multiply(self, n):
        for key in ('up', 'right', 'down', 'left'):
            try:
                self[key] *= n
            except KeyError:
                pass

    def set(self, n):
        for key in ('up', 'right', 'down', 'left'):
            if key in self:
                self[key] = n

    def move(self, direction, override=None, minimum=0,
             maximum=9999, current=0, pagesize=1, offset=0):
        """Calculates the new position in a given boundary.

        Example:
        >>> d = Direction(pages=True)
        >>> d.move(direction=3)
        3
        >>> d.move(direction=3, current=2)
        5
        >>> d.move(direction=3, pagesize=5)
        15
        >>> # Note: we start to count at zero.
        >>> d.move(direction=3, pagesize=5, maximum=10)
        9
        >>> d.move(direction=9, override=2)
        18
        """
        pos = direction
        if override is not None:
            if self.absolute():
                if self.one_indexed():
                    pos = override - 1
                else:
                    pos = override
            else:
                pos *= override
        if self.pages():
            pos *= pagesize
        elif self.percentage():
            pos *= maximum / 100
        if self.absolute():
            if pos < minimum:
                pos += maximum
        else:
            pos += current
        if self.cycle():
            cycles, pos = divmod(pos, (maximum + offset - minimum))
            self['_move_cycles'] = int(cycles)
            ret = minimum + pos
        else:
            ret = max(min(pos, maximum + offset - 1), minimum)
        if direction < 0:
            ret = int(math.ceil(ret))
        else:
            ret = int(ret)
        return ret

    def move_cycles(self):
        return self.get('_move_cycles', 0)

    def select(self, lst, current, pagesize, override=None, offset=1):
        dest = self.move(direction=self.down(), override=override,
                         current=current, pagesize=pagesize, minimum=0, maximum=len(lst) + 1)
        selection = lst[min(current, dest):max(current, dest) + offset]
        return dest + offset - 1, selection
