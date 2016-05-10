# -*- coding: utf-8 -*-

import os
import json

from _quickavro import Encoder

from .constants import *
from .errors import *
from .utils import *


class BinaryEncoder(Encoder):
    def __init__(self, schema=None, codec="null"):
        super(BinaryEncoder, self).__init__()
        self._codec = None
        self._schema = None
        self.sync_marker = os.urandom(SYNC_SIZE)
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
            raise CodecNotSupported("Codec {0} is not supported.".format(codec))
        self._codec = codec

    @property
    def schema(self):
        if not self._schema:
            raise SchemaNotSet("Schema not set")
        return self._schema

    @schema.setter
    def schema(self, schema):
        self._schema = schema
        self.set_schema(json.dumps(schema))

    def read_block(self, block):
        # XXX this isn't right
        block_count, offset = self.read_long(block[:MAX_VARINT_SIZE])
        if block_count < 0:
            return None
        block = block[offset:]
        block_length, offset = self.read_long(block[:MAX_VARINT_SIZE])
        block = block[offset:block_length]
        return self.read(block)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
