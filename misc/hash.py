# -*- coding: utf-8 -*-

from os import listdir
from os.path import getsize, isdir
from hashlib import sha256


def hash_chunks(filepath, h=None):
    if not h:
        h = sha256()
    if isdir(filepath):
        h.update(filepath)
        yield h.hexdigest()
        for fp in listdir(filepath):
            for fp_chunk in hash_chunks(fp, h=h):
                yield fp_chunk
    elif getsize(filepath) == 0:
        yield h.hexdigest()
    else:
        with open(filepath, 'rb') as f:
            # Read the file in ~64KiB chunks (multiple of sha256's block
            # size that works well enough with HDDs and SSDs)
            for chunk in iter(lambda: f.read(h.block_size * 1024), b''):
                h.update(chunk)
                yield h.hexdigest()
