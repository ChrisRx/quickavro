# -*- coding: utf-8 -*-

import os
import json
import zlib
import binascii
import struct

import _quickavro

from .constants import *


def crc32(s):
    data = binascii.crc32(s) & 0xFFFFFFFF
    return struct.pack('>I', data)

class Writer(object):
    def __init__(self, schema=None, codec="null"):
        if schema:
            self.schema = schema
            self._writer = _quickavro.Writer(json.dumps(schema))
        self.sync_marker = os.urandom(SYNC_SIZE)

    def write(self, value):
        return self._writer.write(value)

    def write_header(self, codec="null"):
        w = _quickavro.Writer(json.dumps(HEADER_SCHEMA))
        metadata = {
            "avro.codec": codec,
            "avro.schema": json.dumps(self.schema)
        }
        header = {
            "magic": MAGIC,
            "meta": metadata,
            "sync": self.sync_marker
        }
        return w.write(header)

    def write_long(self, n):
        return self._writer.write_long(n)


class FileWriter(Writer):
    def __init__(self, f, codec=None):
        super(FileWriter, self).__init__(None)
        if isinstance(f, basestring):
            self.f = open(f, 'w')
        else:
            self.f = f
        self._schema = None
        self._codec = None
        self.block = []
        self.block_count = 1
        self.block_size = 0
        self.last_sync = 0
        if codec:
            self.codec = codec

    def tell(self):
        return self.block_size

    def write_record(self, record):
        record = self.write(record)
        self.block.append(record)
        self.block_size += len(record)

    def write_sync(self):
        data = "".join(self.block)
        self.f.write(self.write_long(len(self.block)))
        if self.codec == 'deflate':
            data = zlib.compress(data)[2:-1]
            self.f.write(self.write_long(len(data)))
            self.f.write(data)
        elif self.codec == "snappy":
            data = _quickavro.Snappy.compress(data)
            self.f.write(self.write_long(len(data)+4))
            self.f.write(data)
            crc = crc32(data)
            self.f.write(crc)
        else:
            self.f.write(self.write_long(len(data)))
            self.f.write(data)
        self.f.write(self.sync_marker)
        self.block = []
        self.last_sync = self.f.tell()
        self.block_count += 1
        self.block_size = 0

    @property
    def codec(self):
        if not self._codec:
            return None
        return self._codec

    @codec.setter
    def codec(self, codec):
        self._codec = codec
        if self._schema:
            self._write_header(self._codec)

    @property
    def schema(self):
        if not self._schema:
            raise Exception("Schema not set")
        return self._schema

    @schema.setter
    def schema(self, schema, codec="null"):
        self._schema = schema
        self._writer = _quickavro.Writer(json.dumps(schema))
        if self._codec:
            codec = self._codec
        self._write_header(codec)

    def _write_header(self, codec="null"):
        if self.f.tell() != 0:
            self.f.seek(0)
        header = super(FileWriter, self).write_header(codec)
        self.f.write(header)

    def close(self):
        if self.block:
            self.write_sync()
        self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
