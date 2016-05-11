# -*- coding: utf-8 -*-

import os
import json
import zlib

from _quickavro import Encoder

from .constants import *
from .errors import *
from .utils import *


def read_header(data):
    with BinaryEncoder(HEADER_SCHEMA) as encoder:
        header, offset = encoder.read_record(data[:2048])
        if not header:
            return None, 0
        return header, offset

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
    def header(self):
        return write_header(self.schema, self.sync_marker, self.codec)

    @property
    def codec(self):
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

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()


class BlockEncoder(BinaryEncoder):
    def __init__(self, schema=None, codec="null"):
        super(BlockEncoder, self).__init__(schema, codec)
        self.block = []
        self.block_count = 0
        self.block_size = 0
        self.read_buffer = ""

    def read_header(self, data):
        header, offset = read_header(data)
        data = data[offset:]
        return header, data

    def read_block(self, block):
        block_count, offset = self.read_long(block[:MAX_VARINT_SIZE])
        if block_count < 0:
            return None, None
        block = block[offset:]
        block_length, offset = self.read_long(block[:MAX_VARINT_SIZE])
        block, data = block[offset:block_length+offset], block[block_length+offset:]
        return self.read(block), data

    def read_blocks(self, data):
        if not self.schema:
            raise SchemaNotSet("Nope")
        while True:
            block, data = self.read_block(data)
            if not block:
                break
            self.block_count += 1
            sync_marker, data = data[:SYNC_SIZE], data[SYNC_SIZE:]
            for record in block:
                yield record

    def write_record(self, record):
        record = self.write(record)
        self.block.append(record)
        self.block_size += len(record)

    def write_block(self):
        data = "".join(self.block)
        bc = self.write_long(len(self.block))
        if self.codec == 'deflate':
            data = zlib.compress(data)[2:-1]
            bl = self.write_long(len(data))
        elif self.codec == 'snappy':
            data = snappy_compress(data)
            crc = crc32(data)
            data = data + crc
            bl = self.write_long(len(data))
        else:
            bl = self.write_long(len(data))
        self.block = []
        self.block_count += 1
        self.block_size = 0
        return bc + bl + data + self.sync_marker

    def write_blocks(self, records):
        for record in records:
            if self.block_size >= DEFAULT_SYNC_INTERVAL:
                yield self.write_block()
            self.write_record(record)
        if self.block:
            yield self.write_block()
