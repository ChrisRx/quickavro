# -*- coding: utf-8 -*-

import json
import zlib
import binascii
import struct

from .constants import *
from .encoder import *
from .errors import *
from .utils import *


class FileReader(BinaryEncoder):
    """
    The :class:`FileReader` object implements :class:`quickavro.BinaryEncoder`
    and provides and interface to read Avro files.

    :param f: File-like object or path of file that :class:`FileReader`
        will read from.

    Example:

    .. code-block:: python

        with quickavro.FileReader("test.avro") as reader:
            for record in reader.records():
                print(record)
    """

    def __init__(self, f):
        super(FileReader, self).__init__()
        if isinstance(f, basestring):
            self.f = open(f, 'rb')
        else:
            self.f = f
        header = self.read_header()
        metadata = header.get('meta')
        self.schema = json.loads(ensure_str(metadata.get('avro.schema')))
        self.codec = ensure_str(metadata.get('avro.codec'))
        self.sync_marker = header.get('sync')

    def close(self):
        self.f.close()

    def peek(self, size):
        cur = self.f.tell()
        data = self.f.read(size)
        self.f.seek(cur)
        return data

    def read_block(self):
        block_count = self.read_long()
        block_length = self.read_long()
        data = self.f.read(block_length)
        if not data:
            return None
        if self.codec == "deflate":
            data = zlib.decompress(data, -15)
        elif self.codec == "snappy":
            crc = data[-4:]
            data = snappy_uncompress(data[:-4])
            if crc != crc32(data):
                raise SnappyChecksumError("Snappy CRC32 check has failed.")
        self.block_count += 1
        return data

    def read_blocks(self):
        while True:
            block = self.read_block()
            if not block:
                break
            for record in self.read(block):
                yield record
            sync_marker = self.f.read(16)
            if sync_marker != self.sync_marker:
                break

    def read_header(self):
        header, offset = read_header(self.f.read(INITIAL_HEADER_SIZE))
        self.f.seek(offset)
        return header

    def read_long(self):
        data = self.peek(MAX_VARINT_SIZE)
        l, offset = super(FileReader, self).read_long(data)
        cur = self.f.tell()
        self.f.seek(cur+offset)
        return l

    def records(self):
        return self.read_blocks()
