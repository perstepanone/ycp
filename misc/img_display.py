# -*- coding: utf-8 -*-

"""Interface for drawing images into the console

This module provides functions to draw images in the terminal using supported
implementations.
"""

import os


class ImgDisplayUnsupportedException(Exception):
    def __init__(self, message=None):
        if message is None:
            message = (
                '"{0}" does not appear to be a valid setting for'
                ' preview_images_method.'
            ).format(self.settings.preview_images_method)
        super(ImgDisplayUnsupportedException, self).__init__(message)


class ImageDisplayer:
    """Image display provider functions for drawing images in the terminal"""

    working_dir = os.environ.get('XDG_RUNTIME_DIR', os.path.expanduser("~") or None)

    def draw(self, path, start_x, start_y, width, height):
        """Draw an image at the given coordinates."""

    def clear(self, start_x, start_y, width, height):
        """Clear a part of terminal display."""

    def quit(self):
        """Cleanup and close"""
