# -*- coding: utf-8 -*-
import os
import sys
import locale
from services.app import App
import click

# Information
__license__ = 'GPL3'
__version__ = '0.0.0'
__release__ = False

VERSION_MSG = [
    'ycp version: {0}'.format(__version__),
    'Python version: {0}'.format(' '.join(line.strip() for line in sys.version.splitlines())),
    'Locale: {0}'.format('.'.join(str(s) for s in locale.getlocale())),
]


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
PY3 = sys.version_info[0] >= 3

# These variables are ignored if the corresponding
# XDG environment variable is non-empty and absolute
CACHEDIR = os.path.expanduser('~/.cache/ycp')
CONFDIR = os.path.expanduser('~/.config/ycp')
DATADIR = os.path.expanduser('~/.local/share/ycp')

args = None


def main() -> None:
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        print("Warning: Unable to set locale.  Expect encoding problems.")

    level = 'YCP_LEVEL'
    if level in os.environ and os.environ[level].isdigit():
        os.environ[level] = str(int(os.environ[level]) + 1)
    else:
        os.environ[level] = '1'

    if 'SHELL' not in os.environ:
        os.environ['SHELL'] = 'sh'

    app = App()
    # TODO: Add opportunity to save config
    # TODO: Add some arguments in cli

    try:
        if not sys.stdin.isatty():
            sys.stderr.write("Error: Must run ranger from terminal\n")
            raise SystemExit(1)
        elif app.username == 'root':
            pass
        elif not args.debug:
            pass
        app.initialize()
        app.ui.initialize()
    except Exception:
        pass


if __name__ == "__main__":
    main()
    exit(sys.main())
