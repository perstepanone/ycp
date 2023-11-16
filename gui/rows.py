# -*- coding: utf-8 -*-

from datetime import datetime
from misc.utils import spawn

DEFAULT_ROWMODE = "filename"


class Row:
    """
    Supplies the file line contents for BrowserColumn.

        Attributes:
            name (required!) - Name by which the linemode is referred to by the user
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

    def filetitle(self, vobj, metadata):
        """The left-aligned part of the line."""
        raise NotImplementedError

    def infostring(self, vobj, metadata):
        """The right-aligned part of the line.

                If `NotImplementedError' is raised (e.g. this method is just
                not implemented in the actual linemode), the caller should
                provide its own implementation (which in this case means
                displaying the hardlink count of the directories, size of the
                files and additionally a symlink marker for symlinks). Useful
                because only the caller (BrowserColumn) possesses the data
                necessary to display that information.

                """

        raise NotImplementedError


class DefaultRow(Row):

    def __init__(self,
                 mode="filename",
                 uses_metadata=False,
                 required_metadata=[]):
        super().__init__(mode, uses_metadata, required_metadata)

    def filetitle(self, vobj, metadata):
        return vobj.relative_path


class TitleRow(Row):

    def __init__(self,
                 mode="metatitle",
                 uses_metadata=True,
                 required_metadata=["title"]):
        super().__init__(mode, uses_metadata, required_metadata)

    def filetitle(self, fobj, metadata):
        name = metadata.title
        if metadata.year:
            return "%s - %s" % (metadata.year, name)
        return name

    def infostring(self, fobj, metadata):
        if metadata.authors:
            authorstring = metadata.authors
            if ',' in authorstring:
                authorstring = authorstring[0:authorstring.find(",")]
            return authorstring
        return ""


class PermissionsRow(Row):

    def __init__(self,
                 mode="permissions",
                 ):
        super().__init__(mode)

    def filetitle(self, fobj):
        return "%s %s %s %s" % (
            fobj.get_permission_string(), fobj.user, fobj.group, fobj.relative_path)

    def infostring(self):
        return ""


class FileInfoRow(Row):
    def __init__(self,
                 mode="fileinfo",
                 ):
        super().__init__(mode)

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        if not fobj.is_directory:
            from subprocess import CalledProcessError
            try:
                fileinfo = spawn.check_output(["file", "-Lb", fobj.path]).strip()
            except CalledProcessError:
                return "unknown"
            return fileinfo
        else:
            raise NotImplementedError


class MtimeRow(Row):

    def __init__(self,
                 mode="mtime",
                 ):
        super().__init__(mode)

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        if fobj.stat is None:
            return '?'
        return datetime.fromtimestamp(fobj.stat.st_mtime).strftime("%Y-%m-%d %H:%M")


class SizeMtimeRow(Row):

    def __init__(self,
                 mode="sizemtime",
                 ):
        super().__init__(mode)

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        if fobj.stat is None:
            return '?'
        if fobj.is_directory and not fobj.cumulative_size_calculated:
            if fobj.size is None:
                sizestring = ''
            else:
                sizestring = fobj.size
        else:
            sizestring = human_readable(fobj.size)
        return "%s %s" % (sizestring,
                          datetime.fromtimestamp(fobj.stat.st_mtime).strftime("%Y-%m-%d %H:%M"))


class HumanReadableMtimeRow(Row):

    def __init__(self,
                 mode="humanreadablemtime",
                 ):
        super().__init__(mode)

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        if fobj.stat is None:
            return '?'
        return human_readable_time(fobj.stat.st_mtime)


class SizeHumanReadableMtimeRow(Row):
    name = "sizehumanreadablemtime"

    def __init__(self,
                 mode="sizehumanreadablemtime",
                 ):
        super().__init__(mode)

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        if fobj.stat is None:
            return '?'
        if fobj.is_directory and not fobj.cumulative_size_calculated:
            if fobj.size is None:
                sizestring = ''
            else:
                sizestring = fobj.size
        else:
            sizestring = human_readable(fobj.size)
        return "%s %11s" % (sizestring, human_readable_time(fobj.stat.st_mtime))
