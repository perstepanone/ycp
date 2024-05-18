# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from datetime import datetime


class Row(ABC):
    """
    Supplies the file line contents for BrowserColumn.

        Attributes:
            mode (required!) - Name by which the row is referred to by the user
            uses_metadata - True if metadata should to be loaded for this linemode
            required_metadata -
                If any of these metadata fields are absent, fall back to
                the default linemode
    """

    def __init__(self,
                 mode,
                 uses_metadata,
                 required_metadata):
        self.mode = mode
        self.uses_metadata = uses_metadata
        self.required_metadata = required_metadata

    @property
    @abstractmethod
    def mode(self):
        raise NotImplementedError

    @mode.setter
    @abstractmethod
    def mode(self, mode):
        raise NotImplementedError

    def filetitle(self, vobj, metadata):
        """The left-aligned part of the line."""
        raise NotImplementedError

    def infostring(self, vobj, metadata):
        """The right-aligned part of the line.

                If `NotImplementedError' is raised (e.g. this method is just
                not implemented in the actual row), the caller should
                provide its own implementation (which in this case means
                displaying the hardlink count of the directories, size of the
                files and additionally a symlink marker for symlinks). Useful
                because only the caller (BrowserColumn) possesses the data
                necessary to display that information.

                """

        raise NotImplementedError


class DefaultRow(Row):

    def __init__(self,
                 mode,
                 uses_metadata=False,
                 required_metadata=None):
        super().__init__(mode, uses_metadata, required_metadata)
        if self.required_metadata is None:
            self.required_metadata = []

    @property
    @abstractmethod
    def mode(self):
        return "filename"

    def filetitle(self, vobj, metadata):
        return vobj.relative_path


class TitleRow(Row):

    def __init__(self,
                 mode="metatitle",
                 uses_metadata=True,
                 required_metadata=None):
        super().__init__(mode, uses_metadata, required_metadata)
        if required_metadata is None:
            required_metadata = ["title"]  # FIXME: Replace/delete attribute

    @property
    def mode(self):
        return self.mode

    def filetitle(self, vobj, metadata):
        name = metadata.title
        if metadata.year:
            return "%s - %s" % (metadata.year, name)
        return name

    def infostring(self, vobj, metadata):
        if metadata.authors:
            authorstring = metadata.authors
            if ',' in authorstring:
                authorstring = authorstring[0:authorstring.find(",")]
            return authorstring
        return ""


class PermissionsRow(Row):

    def __init__(self,
                 mode="permissions",
                 uses_metadata=False,
                 required_metadata=None
                 ):
        super().__init__(mode, uses_metadata, required_metadata)

    @property
    def mode(self):
        return self.mode

    def filetitle(self, vobj, metadata):
        return "%s %s %s %s" % (
            vobj.get_permission_string(), vobj.user, vobj.group, vobj.relative_path)

    def infostring(self, vobj, metadata):
        return ""


class FileInfoRow(Row):
    def __init__(self,
                 mode="fileinfo",
                 uses_metadata=False,
                 required_metadata=None
                 ):
        super().__init__(mode, uses_metadata, required_metadata)

    @property
    def mode(self):
        return self.mode

    def filetitle(self, vobj, metadata):
        return vobj.relative_path

    def infostring(self, vobj, metadata):
        if not vobj.is_directory:
            from subprocess import CalledProcessError
            try:
                pass  # fileinfo = spawn.check_output(["file", "-Lb", fobj.path]).strip() TODO: Refactoring this
            except CalledProcessError:
                return "unknown"
            # return fileinfo
        else:
            raise NotImplementedError


class MtimeRow(Row):

    def __init__(self,
                 mode="mtime",
                 uses_metadata=False,
                 required_metadata=None
                 ):
        super().__init__(mode, uses_metadata, required_metadata)

    @property
    def mode(self):
        return self.mode

    def filetitle(self, vobj, metadata):
        return vobj.relative_path

    def infostring(self, vobj, metadata):
        if vobj.stat is None:
            return '?'
        return datetime.fromtimestamp(vobj.stat.st_mtime).strftime("%Y-%m-%d %H:%M")


class SizeMtimeRow(Row):

    def __init__(self,
                 mode="sizemtime",
                 uses_metadata=False,
                 required_metadata=None
                 ):
        super().__init__(mode, uses_metadata, required_metadata)

    @property
    def mode(self):
        return self.mode

    def filetitle(self, vobj, metadata):
        return vobj.relative_path

    def infostring(self, vobj, metadata):
        if vobj.stat is None:
            return '?'
        if vobj.is_directory and not vobj.cumulative_size_calculated:
            if vobj.size is None:
                sizestring = ''  # FIXME: Replace/delete attribute
            else:
                sizestring = vobj.size  # FIXME: Replace/delete attribute
        else:
            pass  # sizestring = human_readable(fobj.size) # TODO: Refactoring this
        # return "%s %s" % (sizestring, datetime.fromtimestamp(vobj.stat.st_mtime).strftime("%Y-%m-%d %H:%M"))


class HumanReadableMtimeRow(Row):

    def __init__(self,
                 mode="humanreadablemtime",
                 uses_metadata=False,
                 required_metadata=None
                 ):
        super().__init__(mode, uses_metadata, required_metadata)

    @property
    def mode(self):
        return self.mode

    def filetitle(self, vobj, metadata):
        return vobj.relative_path

    def infostring(self, vobj, metadata):
        if vobj.stat is None:
            return '?'
        # return pass human_readable_time(fobj.stat.st_mtime) TODO: Refactoring this


class SizeHumanReadableMtimeRow(Row):

    def __init__(self,
                 mode="sizehumanreadablemtime",
                 uses_metadata=False,
                 required_metadata=None
                 ):
        super().__init__(mode, uses_metadata, required_metadata)

    @property
    def mode(self):
        return self.mode

    def filetitle(self, vobj, metadata):
        return vobj.relative_path

    def infostring(self, vobj, metadata):
        if vobj.stat is None:
            return '?'
        if vobj.is_directory and not vobj.cumulative_size_calculated:
            if vobj.size is None:
                sizestring = ''  # FIXME: Replace/delete attribute
            else:
                sizestring = vobj.size  # FIXME: Replace/delete attribute
        else:
            # sizestring = human_readable(vobj.size) TODO:Refactoring this
            return
            pass  # "%s %11s" % (sizestring, human_readable_time(vobj.stat.st_mtime)) TODO: Refactoring this
