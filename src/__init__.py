# -*- coding: utf-8 -*-
import os
import sys
import locale
import pwd
import socket
import tempfile
import mimetypes
from collections import deque

from services.loader import Loader
from services.metadata import MetadataManager
from gui.ui import UI
from gui.tab import TabManager


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
MAX_RESTORABLE_TABS = 3
LEVEL = 'YCP_LEVEL'

# These variables are ignored if the corresponding
# XDG environment variable is non-empty and absolute
CACHEDIR = os.path.expanduser('~/.cache/ycp')
CONFDIR = os.path.expanduser('~/.config/ycp')
DATADIR = os.path.expanduser('~/.local/share/ycp')

args = None  # FIXME: arguments from console


class App:
    def __init__(self, ui=None, paths=None, bookmarks=None):
        self.ui = ui if ui is not None else UI()
        self.paths = paths
        self.bookmarks = bookmarks
        self.current_tab = 1
        self.tabs = TabManager()
        self.restorable_tabs = deque([], MAX_RESTORABLE_TABS)
        self.default_linemodes = deque()
        # self.loader = Loader()
        self.copy_buffer = set()
        # self.metadata = MetadataManager()
        self.image_displayer = None
        self.run = None
        self.settings = None
        self.expectedtab = None

        try:
            self.username = pwd.getpwuid(os.getuid()).pw_name
        except KeyError:
            self.username = f'uid:{os.geteuid()}'
        self.hostname = socket.gethostname()
        self.home_path = os.path.expanduser('~')

        if not mimetypes.inited:
            pass
        self.mimetypes = mimetypes

    def initialize(self):
        """If ui/bookmarks are None, they will be initialized here."""

        # self.tabs =
        tab_list = self.tabs.get_tab_list()
        if tab_list:
            self.current_tab = tab_list[0]
            self.expectedtab = self.tabs[self.current_tab]
        else:
            self.current_tab = 1
            self.tabs = self.current_tab = self.expectedtab  # TODO:Add reference to tab instance

        # FIXME: add statement about clean option
        # TODO: add bookmarks/tags functionality

        self.ui.setup_curses()
        self.ui.initialize()

    def destroy(self):
        pass

    def block_input(self):
        pass

    def input_is_blocked(self):
        pass

    def exit(self):
        """Exit the program."""
        raise SystemExit

    def reset(self):
        pass


def set_locale() -> None:
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        print("Warning: Unable to set locale.  Expect encoding problems.")


def set_level() -> None:
    if LEVEL in os.environ and os.environ[LEVEL].isdigit():
        os.environ[LEVEL] = str(int(os.environ[LEVEL]) + 1)
    else:
        os.environ[LEVEL] = '1'

    if 'SHELL' not in os.environ:
        os.environ['SHELL'] = 'sh'


def restore_saved_tabs(app: object) -> None:
    tabs_datapath = app.datapath('tabs')  # FIXME: Refactor references in function
    if app.settings.save_tabs_on_exit and os.path.exists(tabs_datapath) and not args.paths:
        try:
            with open(tabs_datapath, 'r', encoding="utf-8") as fobj:
                tabs_saved = fobj.read().partition('\0\0')
                startup_path = app.start_paths.pop(0)
                app.start_paths += tabs_saved[0].split('\0')
                # Remove dead entries if this behavior is defined in settings
                if app.settings.filter_dead_tabs_on_startup:
                    app.start_paths = list(filter(os.path.isdir, app.start_paths))
                try:
                    startup_path_tab_index = app.start_paths.index(startup_path)  # FIXME: Replace variable
                except ValueError:
                    app.start_paths.insert(0, startup_path)
            if tabs_saved[-1]:
                with open(tabs_datapath, 'w', encoding="utf-8") as fobj:
                    fobj.write(tabs_saved[-1])
            else:
                os.remove(tabs_datapath)
        except OSError as ex:
            pass  # FIXME: Add message to screen/logger


def main() -> bool:
    set_locale()
    set_level()

    app = App()
    # TODO: Add opportunity to save config
    # TODO: Add opportunity to tagging files
    # TODO: Add some arguments in cli

    profile = None
    exit_msg = ''
    exit_code = 0
    startup_path_tab_index = 0
    try:
        app = App()
        # FIXME: Settings load
        if args.list_unused_keys:  # FIXME: Console argument
            from misc.keybinding_parser import (SPECIAL_KEYS, VERY_SPECIAL_KEYS)

            maps = app.ui.keymaps['browser']
            for key in sorted(SPECIAL_KEYS.values(), key=str):
                if key not in maps:
                    print("<%s>" % SPECIAL_KEYS[key])
            for key in range(33, 127):
                if key not in maps:
                    print(chr(key))
            return 0

        if not sys.stdin.isatty():
            sys.stderr.write("Error: Must run ycp from terminal\n")
            raise SystemExit(1)
        elif app.username == 'root':
            pass
        elif not args.debug:  # FIXME: Reference
            pass
        if not args.clean:
            # Create data directory
            if not os.path.exists(DATADIR):
                os.makedirs(DATADIR)

        restore_saved_tabs(app)
        app.initialize()
        app.tabs.tab_move(startup_path_tab_index)
        app.ui.initialize()

        if int(os.environ[LEVEL]) > 1:
            warning = 'Warning:'
            nested_warning = "You're in a nested ycp instance!"
            warn_when_nested = app.settings.nested_ranger_warning.lower()
            if warn_when_nested == 'true':
                app.notify(' '.join((warning, nested_warning)), bad=False)  # FIXME: Add method
            elif warn_when_nested == 'error':
                app.notify(' '.join((warning.upper(), nested_warning + '!!')),
                           bad=True)

        if app.args.profile:
            import cProfile
            import pstats
            app.__app = app
            profile_file = tempfile.gettempdir() + '/ycp_profile'
            cProfile.run('ycp.__app.loop()', profile_file)  # FIXME: Update reference
            profile = pstats.Stats(profile_file, stream=sys.stderr)
        else:
            app.loop()

    except Exception:
        import traceback
        ex_traceback = traceback.format_exc()
        exit_msg += '\n'.join(VERSION_MSG) + '\n'
        try:
            exit_msg += "Current file: {0}\n".format(repr(app.thisfile.path))
        except Exception:
            pass
        exit_msg += '''
        {0}
        ycp crashed. Please report this traceback at:
        https://github.com/perstepanone/ycp/issues
        '''.format(ex_traceback)

        exit_code = 1

    except SystemExit as ex:
        if ex.code is not None:
            if not isinstance(ex.code, int):
                exit_msg = ex.code
                exit_code = 1
            else:
                exit_code = ex.code

    finally:
        if exit_msg:
            pass  # FIXME: Add logger
        try:
            app.ui.destroy()
        except (AttributeError, NameError):
            pass
        # If profiler is enabled print the stats
        if app.args.profile and profile:
            profile.strip_dirs().sort_stats('cumulative').print_callees()
        # print the exit message if any
        if exit_msg:
            sys.stderr.write(exit_msg)
        return exit_code
