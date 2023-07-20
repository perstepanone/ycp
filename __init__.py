# -*- coding: utf-8 -*-
import os
from sys import version_info, exit


# Information
__license__ = 'GPL3'
__version__ = '0.0.0'
__release__ = False


def version_helper():
    if __release__:
        version_string = 'ycp {0}'.format(__version__)
    else:
        import subprocess
        version_string = 'ycp-master {0}'
        try:
            with subprocess.Popen(
                    ["git", "describe"],
                    universal_newlines=True,
                    cwd=YCPDIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
            ) as git_describe:
                (git_description, _) = git_describe.communicate()
            version_string = version_string.format(git_description.strip('\n'))
        except (OSError, subprocess.CalledProcessError, AttributeError):
            version_string = version_string.format(__version__)
    return version_string


# Constants
YCPDIR = os.path.dirname(__file__)
VERSION = version_helper()
PY3 = version_info[0] >= 3

# These variables are ignored if the corresponding
# XDG environment variable is non-empty and absolute
CACHEDIR = os.path.expanduser('~/.cache/ycp')
CONFDIR = os.path.expanduser('~/.config/ycp')
DATADIR = os.path.expanduser('~/.local/share/ycp')


def main() -> None:
    pass


if __name__ == "__main__":
    exit(main())
