# -*- coding: utf-8 -*-

import shutil
from subprocess import check_output, CalledProcessError
from .. import PY3


def which(cmd):
    if PY3:
        return shutil.which(cmd)

    try:
        return check_output(["command", "-v", cmd])
    except CalledProcessError:
        return None
