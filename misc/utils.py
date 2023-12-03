# -*- coding: utf-8 -*-

import os
import sys
from collections import deque


def allow_access_to_confdir(confdir, allow):
    from errno import EEXIST

    if allow:
        try:
            os.makedirs(confdir)
        except OSError as err:
            if err.errno != EEXIST:  # EEXIST means it already exists
                print("This configuration directory could not be created:")
                print(confdir)
                print("To run ranger without the need for configuration")
                print("files, use the --clean option.")
                raise SystemExit
        else:
            pass
        if confdir not in sys.path:
            sys.path[0:0] = [confdir]
    else:
        if sys.path[0] == confdir:
            del sys.path[0]


def flatten(lst):
    """Flatten an iterable.

    All contained tuples, lists, deques and sets are replaced by their
    elements and flattened as well.

    >>> l = [1, 2, [3, [4], [5, 6]], 7]
    >>> list(flatten(l))
    [1, 2, 3, 4, 5, 6, 7]
    >>> list(flatten(()))
    []
    """
    for elem in lst:
        if isinstance(elem, (tuple, list, set, deque)):
            for subelem in flatten(elem):
                yield subelem
        else:
            yield elem
