# -*- coding: utf-8 -*-

import zlib

import _quickavro

from .constants import *
from .encoder import *
from .errors import *
from .utils import *


def write_header(schema, sync_marker, codec="null"):
    with BinaryEncoder(HEADER_SCHEMA, codec) as encoder:
        header = {
            "magic": MAGIC,
            "meta": {
                "avro.codec": codec,
                "avro.schema": json.dumps(schema)
            },
            "sync": sync_marker
        }
        return encoder.write(header)


class FileWriter(object):
    def __init__(self, f, codec="null"):
        if isinstance(f, basestring):
            self.f = open(f, 'w')
        else:
            self.f = f
        self._schema = None
        self._codec = None
        self.block = []
        self.block_count = 0
        self.block_size = 0
        self.last_sync = 0

        self.encoder = BinaryEncoder()

        if codec:
            self.codec = codec

    @property
    def sync_marker(self):
        return self.encoder.sync_marker

    def tell(self):
        return self.block_size

    def write_record(self, record):
        record = self.encoder.write(record)
        self.block.append(record)
        self.block_size += len(record)

    def write_sync(self):
        if self.block_count == 0:
            header = write_header(self.schema, self.sync_marker, self.codec)
            self.f.write(header)
            self.block_count += 1
        data = "".join(self.block)
        self.f.write(self.encoder.write_long(len(self.block)))
        if self.codec == 'deflate':
            data = zlib.compress(data)[2:-1]
            self.f.write(self.encoder.write_long(len(data)))
            self.f.write(data)
        elif self.codec == "snappy":
            data = snappy_compress(data)
            self.f.write(self.encoder.write_long(len(data)+4))
            self.f.write(data)
            crc = crc32(data)
            self.f.write(crc)
        else:
            self.f.write(self.encoder.write_long(len(data)))
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
        if codec not in {"deflate", "null", "snappy"}:
            raise CodecNotSupported()
        self._codec = codec

    @property
    def schema(self):
        if not self._schema:
            raise Exception("Schema not set")
        return self._schema

    @schema.setter
    def schema(self, schema):
        self._schema = schema
        self.encoder.schema = schema

    def close(self):
        if self.block:
            self.write_sync()
        self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
