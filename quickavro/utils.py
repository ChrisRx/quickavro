# -*- coding: utf-8 -*-


import binascii
import struct

import _quickavro


def crc32(s):
    data = binascii.crc32(s) & 0xFFFFFFFF
    return struct.pack('>I', data)

def snappy_compress(data):
    return _quickavro.Snappy.compress(data)

def snappy_uncompress(data):
    return _quickavro.Snappy.uncompress(data)
