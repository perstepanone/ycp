# -*- coding: utf-8 -*-

"""Shared objects contain singletons for shared use."""


class VideoManagerAware:
    """Subclass this to gain access to the global "App" object."""
    @staticmethod
    def app_set(app):
        VideoManagerAware.app = app


class SettingsAware:
    """Subclass this to gain access to the global "SettingObject" object."""
    @staticmethod
    def settings_set(settings):
        SettingsAware.settings = settings
