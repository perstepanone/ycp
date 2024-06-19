# -*- coding: utf-8 -*-
"""Default options and configurations"""

import re
import os.path
from inspect import isfunction

from ..services.signals import SignalDispatcher
from ..gui.colorscheme import colorscheme_name_to_class
from ..services.shared import VideoManagerAware

# Use these priority constants to trigger events at specific points in time
# during processing of the signals "setopt" and "setopt.<some_setting_name>"
SIGNAL_PRIORITY_RAW = 2.0  # signal.value will be raw
SIGNAL_PRIORITY_SANITIZE = 1.0
SIGNAL_PRIORITY_BETWEEN = 0.6
SIGNAL_PRIORITY_SYNC = 0.2
SIGNAL_PRIORITY_AFTER_SYNC = 0.1

ALLOWED_SETTINGS = {
    # 'automatically_count_files': bool,
    # 'autosave_bookmarks': bool,
    # 'autoupdate_cumulative_size': bool,
    'bidi_support': bool,
    'binary_size_prefix': bool,
    # 'cd_bookmarks': bool,
    # 'cd_tab_case': str,
    # 'cd_tab_fuzzy': bool,
    # 'clear_filters_on_dir_change': bool,
    'collapse_preview': bool,
    'colorscheme': str,
    'column_ratios': (tuple, list),
    'confirm_on_delete': str,
    # 'dirname_in_tabs': bool,
    # 'display_size_in_main_column': bool,
    # 'display_size_in_status_bar': bool,
    "display_free_space_in_status_bar": bool,
    # 'display_tags_in_all_columns': bool,
    'draw_borders': str,
    'draw_borders_multipane': str,
    'draw_progress_bar_in_status_bar': bool,
    'filter_dead_tabs_on_startup': bool,
    'flushinput': bool,
    # 'freeze_files': bool,
    # 'global_inode_type_filter': str,
    # 'hidden_filter': str,
    'hint_collapse_threshold': int,
    # 'hostname_in_titlebar': bool,
    'size_in_bytes': bool,
    'idle_delay': int,
    # 'iterm2_font_width': int,
    # 'iterm2_font_height': int,
    'line_numbers': str,
    'max_console_history_size': (int, type(None)),
    'max_history_size': (int, type(None)),
    'metadata_deep_search': bool,
    'mouse_enabled': bool,
    'nested_app_warning': str,
    'one_indexed': bool,
    'open_all_images': bool,
    'padding_right': bool,
    'preview_directories': bool,
    'preview_files': bool,
    'preview_images': bool,
    'preview_images_method': str,
    'preview_max_size': int,
    'preview_script': (str, type(None)),
    'relative_current_zero': bool,
    'save_backtick_bookmark': bool,
    'save_console_history': bool,
    'save_tabs_on_exit': bool,
    'scroll_offset': int,
    'shorten_title': int,
    'show_cursor': bool,  # TODO: not working?
    # 'show_hidden_bookmarks': bool,
    'show_hidden': bool,
    'show_selection_in_titlebar': bool,
    'sort_case_insensitive': bool,
    'sort_directories_first': bool,
    'sort_reverse': bool,
    'sort': str,
    'sort_unicode': bool,
    'status_bar_on_top': bool,
    'tilde_in_titlebar': bool,
    'unicode_ellipsis': bool,
    'update_title': bool,
    # 'update_tmux_title': bool,
    'use_preview_script': bool,
    # 'vcs_aware': bool,
    # 'vcs_backend_bzr': str,
    # 'vcs_backend_git': str,
    # 'vcs_backend_hg': str,
    # 'vcs_backend_svn': str,
    # 'vcs_msg_length': int,
    'viewmode': str,
    # 'w3m_delay': float,
    # 'w3m_offset': int,
    'wrap_plaintext_previews': bool,
    'wrap_scroll': bool,
    'xterm_alt_key': bool,
    'sixel_dithering': str,
}

ALLOWED_VALUES = {
    'cd_tab_case': ['sensitive', 'insensitive', 'smart'],
    'confirm_on_delete': ['multiple', 'always', 'never'],
    'draw_borders': ['none', 'both', 'outline', 'separators'],
    'draw_borders_multipane': [None, 'none', 'both', 'outline',
                               'separators', 'active-pane'],
    'line_numbers': ['false', 'absolute', 'relative'],
    'nested_app_warning': ['true', 'false', 'error'],
    'one_indexed': [False, True],
    'preview_images_method': ['w3m', 'iterm2', 'terminology',
                              'sixel', 'urxvt', 'urxvt-full',
                              'kitty', 'ueberzug'],
    # 'vcs_backend_bzr': ['disabled', 'local', 'enabled'],
    'vcs_backend_git': ['enabled', 'disabled', 'local'],
    # 'vcs_backend_hg': ['disabled', 'local', 'enabled'],
    # 'vcs_backend_svn': ['disabled', 'local', 'enabled'],
    'viewmode': ['miller', 'multipane'],
}

DEFAULT_VALUES = {
    bool: False,
    type(None): None,
    str: "",
    int: 0,
    float: 0.0,
    list: [],
    tuple: tuple([]),
}


class Settings(SignalDispatcher, VideoManagerAware):

    def __init__(self):
        super().__init__()
        self.__dict__['_localsettings'] = {}
        self.__dict__['_localregexes'] = {}
        self.__dict__['_tagsettings'] = {}
        self.__dict__['_settings'] = {}
        for name in ALLOWED_SETTINGS:
            self.signal_bind('setopt.' + name, self._sanitize,
                             priority=SIGNAL_PRIORITY_SANITIZE)
            self.signal_bind('setopt.' + name, self._raw_set_with_signal,
                             priority=SIGNAL_PRIORITY_SYNC)
        for name, values in ALLOWED_VALUES.items():
            assert values
            assert name in ALLOWED_SETTINGS
            self._raw_set(name, values[0])

    def _sanitize(self, signal):
        name, value = signal.setting, signal.value
        if name == 'column_ratios':
            # TODO: cover more cases here
            if isinstance(value, tuple):
                signal.value = list(value)
            if not isinstance(value, list) or len(value) < 2:
                signal.value = [1, 1]
            else:
                signal.value = [int(i) if str(i).isdigit() else 1
                                for i in value]

        elif name == 'colorscheme':
            colorscheme_name_to_class(signal)

        elif name == 'preview_script':
            if isinstance(value, str):
                result = os.path.expanduser(value)
                if os.path.exists(result):
                    signal.value = result
                else:
                    self.app.notify(
                        "Preview script `{0}` doesn't exist!".format(result), bad=True)
                    signal.value = None

        elif name == 'use_preview_script':
            if self._settings.get('preview_script') is None and value and self.app.ui.is_on:
                self.app.notify("Preview script undefined or not found!",
                                bad=True)

    def set(self, name, value, path=None, tags=None):
        assert name in ALLOWED_SETTINGS, "No such setting: {0}!".format(name)
        if name not in self._settings:
            previous = None
        else:
            previous = self._settings[name]
        assert self._check_type(name, value)
        assert not (tags and path), "Can't set a setting for path and tag " \
                                    "at the same time!"
        kws = {
            "setting": name,
            "value": value,
            "previous": previous,
            "path": path,
            "tags": tags,
            "app": self.app,
        }
        self.signal_emit('setopt', **kws)
        self.signal_emit('setopt.' + name, **kws)

    def _get_default(self, name):
        if name == 'preview_script':
            if ycp.args.clean:  # FIXME: Validate bash file and references om it
                value = self.app.relpath('data/scope.sh')
            else:
                value = self.app.confpath('scope.sh')
                if not os.path.exists(value):
                    value = self.app.relpath('data/scope.sh')
        else:
            value = DEFAULT_VALUES[self.types_of(name)[0]]

        return value

    def get(self, name, path=None):
        assert name in ALLOWED_SETTINGS, "No such setting: {0}!".format(name)
        if path:
            localpath = path
        else:
            try:
                localpath = self.app.thisdir.path  # FIXME: Refactor functionality
            except AttributeError:
                localpath = None

        if localpath:
            for pattern, regex in self._localregexes.items():
                if name in self._localsettings[pattern] and \
                        regex.search(localpath):
                    return self._localsettings[pattern][name]

        if self._tagsettings and path:
            realpath = os.path.realpath(path)
            if realpath in self.app.tags:
                tag = self.app.tags.marker(realpath)
                if tag in self._tagsettings and name in self._tagsettings[tag]:
                    return self._tagsettings[tag][name]

        if name not in self._settings:
            value = self._get_default(name)
            self._raw_set(name, value)
            setattr(self, name, value)
        return self._settings[name]

    def __setattr__(self, name, value):
        if name.startswith('_'):
            self.__dict__[name] = value
        else:
            self.set(name, value, None)

    def __getattr__(self, name):
        if name.startswith('_'):
            return self.__dict__[name]
        return self.get(name, None)

    def __iter__(self):
        for setting in self._settings:
            yield setting

    @staticmethod
    def types_of(name):
        try:
            typ = ALLOWED_SETTINGS[name]
        except KeyError:
            return tuple()
        else:
            if isinstance(typ, tuple):
                return typ
            return (typ,)

    def _check_type(self, name, value):
        typ = ALLOWED_SETTINGS[name]
        if isfunction(typ):  # TODO: validate required attribute "typ"

            assert typ(value), \
                "Warning: The option `" + name + "' has an incorrect type!"
        else:
            assert isinstance(value, typ), \
                "Warning: The option `" + name + "' has an incorrect type!"" Got " \
                + str(type(value)) + ", expected " + str(typ) + "!" + \
                " Please check if your commands.py is up to date." \
                    if not self.app.ui.is_set_up else ""
        return True  # FIXME: Validate app attribute

    __getitem__ = __getattr__  # FIXME: private and protected attribute access №2
    __setitem__ = __setattr__


def _raw_set(self, name, value, path=None, tags=None):
    if path:
        if path not in self._localsettings:
            try:
                regex = re.compile(path)
            except re.error:  # Bad regular expression
                return
            self._localregexes[path] = regex
            self._localsettings[path] = {}
        self._localsettings[path][name] = value

        # make sure name is in _settings, so __iter__ runs through
        # local settings too.
        if name not in self._settings:
            type_ = self.types_of(name)[0]
            value = DEFAULT_VALUES[type_]
            self._settings[name] = value
    elif tags:
        for tag in tags:
            if tag not in self._tagsettings:
                self._tagsettings[tag] = {}
            self._tagsettings[tag][name] = value
    else:
        self._settings[name] = value


def _raw_set_with_signal(self, signal):
    self._raw_set(signal.setting, signal.value, signal.path, signal.tags)


class LocalSettings:

    def __init__(self, path, parent):
        self.__dict__['_parent'] = parent
        self.__dict__['_path'] = path

    def __setattr__(self, name, value):  # FIXME: private and protected attribute access
        if name.startswith('_'):
            self.__dict__[name] = value
        else:
            self._parent.set(name, value, self._path)

    def __getattr__(self, name):
        if name.startswith('_'):
            return self.__dict__[name]
        if name.startswith('signal_'):
            return getattr(self._parent, name)
        return self._parent.get(name, self._path)

    def __iter__(self):
        for setting in self._parent._settings:  # FIXME: Update reference
            yield setting

    __getitem__ = __getattr__  # FIXME: private and protected attribute access №2
    __setitem__ = __setattr__
