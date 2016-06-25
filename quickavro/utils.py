# -*- coding: utf-8 -*-


import binascii
import struct

import _quickavro


def crc32(s):
    data = binascii.crc32(s) & 0xFFFFFFFF
    return struct.pack('>I', data)

def snappy_compress(data):
    """
    Compress str with snappy
    """
    return _quickavro.Snappy.compress(data)

def snappy_uncompress(data):
    """
    Uncompress str with snappy
    """
    return _quickavro.Snappy.uncompress(data)

def snappy_validate(data):
    """
    Validate snappy compressed str
    """
    return _quickavro.Snappy.validate(data)
