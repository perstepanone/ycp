# -*- coding: utf-8 -*-


from datetime import datetime


def human_readable(byte_count, separator=' ', use_binary=None):
    """Convert a large number of bytes to an easily readable format.
    Output depends on the binary_size_prefix setting (which is False by default)
    and on the use_binary argument. The latter has priority over the former.

    >>> human_readable(54, use_binary=False)
    '54 B'
    >>> human_readable(1500, use_binary=False)
    '1.5 k'
    >>> human_readable(2 ** 20 * 1023, use_binary=False)
    '1.07 G'
    >>> human_readable(54, use_binary=True)
    '54 B'
    >>> human_readable(1500, use_binary=True)
    '1.46 Ki'
    >>> human_readable(2 ** 20 * 1023, use_binary=True)
    '1023 Mi'
    """

    # handle automatically_count_files false
    if byte_count is None:
        return ''
    if byte_count <= 0:
        return '0'
    if settings.size_in_bytes:  # FIXME: Add reference
        return format(byte_count, 'n')  # 'n' = locale-aware separator.

    # If you attempt to shorten this code, take performance into consideration.
    binary = settings.binary_size_prefix if use_binary is None else use_binary  # FIXME: Add reference
    if binary:
        prefixes = ('B', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi')
        unit = 1024
    else:
        prefixes = ('B', 'k', 'M', 'G', 'T', 'P')
        unit = 1000

    ind = 0
    while byte_count >= unit:
        byte_count /= unit
        ind += 1

    format_str = '%.3g%s%s' if byte_count < 1000 else '%.4g%s%s'  # e.g. 1023 requires '%.4g'
    return format_str % (byte_count, separator, prefixes[ind]) if ind < len(prefixes) else '>9000'


def human_readable_time(timestamp):
    """Convert a timestamp to an easily readable format.
    """
    # Hard to test because it's relative to ``now()``
    date = datetime.fromtimestamp(timestamp)
    datediff = datetime.now().date() - date.date()
    if datediff.days >= 365:
        return date.strftime("%-d %b %Y")
    elif datediff.days >= 7:
        return date.strftime("%-d %b")
    elif datediff.days >= 1:
        return date.strftime("%a")
    return date.strftime("%H:%M")
