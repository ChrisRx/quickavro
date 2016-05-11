# -*- coding: utf-8 -*-

import json
import zlib
import binascii
import struct

import _quickavro

from .constants import *
from .encoder import *
from .errors import *
from .utils import *


class FileReader(BlockEncoder):
    def __init__(self, f):
        super(FileReader, self).__init__()
        if isinstance(f, basestring):
            self.f = open(f, 'r')
        else:
            self.f = f
        header = self._read_header()
        metadata = header.get('meta')
        self.schema = json.loads(metadata.get('avro.schema'))
        self.codec = metadata.get('avro.codec')
        self.sync_marker = header.get('sync')

    def _read_header(self):
        header, offset = read_header(self.f.read(2048))
        if header is None:
            raise Exception("Cannot do the thing with the header reading and such.")
        self.f.seek(offset)
        return header

    def _read_block(self):
        cur = self.f.tell()
        data = self.f.read(MAX_VARINT_SIZE)
        block_count, offset = self.read_long(data)
        if block_count < 0:
            return None
        self.f.seek(cur+offset)
        cur = self.f.tell()
        data = self.f.read(MAX_VARINT_SIZE)
        block_length, offset = self.read_long(data)
        self.f.seek(cur+offset)
        if self.codec == "deflate":
            block = self.f.read(block_length)
            if not block:
                return None
            block = zlib.decompress(block, -15)
        elif self.codec == "snappy":
            block = self.f.read(block_length-4)
            if not block:
                return None
            crc = self.f.read(4)
            assert crc == crc32(block)
            block = snappy_uncompress(block)
        else:
            block = self.f.read(block_length)
            if not block:
                return None
        self.block_count += 1
        return block

    def records(self):
        if self.f.tell() == 0:
            header_data = self._read_header()
        while True:
            try:
                block = self._read_block()
                if not block:
                    break
                for record in self.read(block):
                    yield record
                sync_marker = self.f.read(16)
                if sync_marker != self.sync_marker:
                    break
            except MemoryError as error:
                print(error)
                break

    def close(self):
        self.f.close()
