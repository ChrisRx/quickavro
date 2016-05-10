# -*- coding: utf-8 -*-

import os
import json

import _quickavro

from .constants import *
from .errors import *
from .utils import *


class BinaryEncoder(object):
    def __init__(self, schema=None, codec="null"):
        self._codec = None
        self._schema = None
        self._encoder = _quickavro.Encoder()
        self.sync_marker = os.urandom(SYNC_SIZE)
        if codec:
            self.codec = codec
        if schema:
            self.schema = schema

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
            raise SchemaNotSet("Schema not set")
        return self._schema

    @schema.setter
    def schema(self, schema):
        self._schema = schema
        self._encoder.set_schema(json.dumps(schema))

    def write(self, value):
        return self._encoder.write(value)

    def write_long(self, n):
        return self._encoder.write_long(n)

    def read(self, value):
        return self._encoder.read(value)

    def read_long(self, b):
        return self._encoder.read_long(b)

    def read_record(self, data):
        record, offset = self._encoder.read_record(data)
        return record, offset

    def read_block(self, block):
        # XXX this isn't right
        block_count, offset = self._encoder.read_long(block[:MAX_VARINT_SIZE])
        if block_count < 0:
            return None
        block = block[offset:]
        block_length, offset = self._encoder.read_long(block[:MAX_VARINT_SIZE])
        block = block[offset:block_length]
        return self.read(block)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
