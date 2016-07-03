# -*- coding: utf-8 -*-

import os
import json
import zlib

from _quickavro import Encoder

from .constants import *
from .errors import *
from .utils import *

from ._compat import *

def read_header(data):
    """
    Reads Avro binary file header

    :param data: bytes representing Avro file header.
    """
    with BinaryEncoder(HEADER_SCHEMA) as encoder:
        header, offset = encoder.read_record(data)
        if not header:
            raise InvalidSchemaError("Unable to read Avro header.")
        return header, offset

def write_header(schema, sync_marker, codec="null"):
    """
    Writes Avro binary file header

    :param schema: Dictionary to use as Avro schema.
    :param sync_marker: str used to verify blocks.
    :param codec: (optional) Compression codec.
    """
    with BinaryEncoder(HEADER_SCHEMA, codec) as encoder:
        header = {
            "magic": MAGIC,
            "meta": {
                "avro.codec": ensure_bytes(codec),
                "avro.schema": ensure_bytes(json.dumps(schema))
            },
            "sync": sync_marker
        }
        return encoder.write(header)


class BinaryEncoder(Encoder):
    """
    The object used to implement binary Avro encoding in quickavro. It
    is used internally and is exposed in the quickavro Python API.


    :param schema: (optional) Dictionary to use as Avro schema for this
        :class:`BinaryEncoder`.
    :param codec: (optional) Compression codec used with
        :class:`BinaryEncoder`.

    Example:

    .. code-block:: python

        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {
              "type": "record",
              "name": "Person",
              "fields": [
                {"name": "name", "type": "string"},
                {"name": "age",  "type": ["int", "null"]}
              ]
            }
            with open("test.avro, "wb") as f:
                f.write(encoder.header)
                for block in encoder.write_blocks(records):
                    f.write(block)
    """

    def __init__(self, schema=None, codec="null"):
        super(BinaryEncoder, self).__init__()
        self._codec = None
        self._schema = None
        self.sync_marker = os.urandom(SYNC_SIZE)
        self.codec = codec
        if schema:
            self.schema = schema
        self.block = []
        self.block_count = 0
        self.block_size = 0

    def close(self):
        pass

    @property
    def codec(self):
        return self._codec

    @codec.setter
    def codec(self, codec):
        if codec not in {"deflate", "null", "snappy"}:
            raise CodecNotSupported("Codec {0} is not supported.".format(codec))
        self._codec = codec

    @property
    def header(self):
        return write_header(self.schema, self.sync_marker, self.codec)

    def read_block(self, block):
        block_count, offset = self.read_long(block[:MAX_VARINT_SIZE])
        if block_count < 0:
            return None, None
        block = block[offset:]
        block_length, offset = self.read_long(block[:MAX_VARINT_SIZE])
        block, data = block[offset:block_length+offset], block[block_length+offset:]
        return block, data

    def read_blocks(self, data):
        if not self.schema:
            raise SchemaNotFound("Schema must be provided before attempting to read Avro data.")
        while True:
            block, data = self.read_block(data)
            if not block:
                break
            self.block_count += 1
            sync_marker, data = data[:SYNC_SIZE], data[SYNC_SIZE:]
            for record in self.read(block):
                yield record

    def read_header(self, data):
        data = memoryview(data)
        header, offset = read_header(data)
        data = data[offset:]
        return header, data

    @property
    def schema(self):
        if not self._schema:
            raise SchemaNotFound("Schema must be provided before attempting to read Avro data.")
        return self._schema

    @schema.setter
    def schema(self, schema):
        self._schema = schema
        self.set_schema(json.dumps(schema))

    def write_block(self):
        data = b"".join(self.block)
        block_count = self.write_long(len(self.block))
        if self.codec == 'deflate':
            data = zlib.compress(data)[2:-1]
        elif self.codec == 'snappy':
            crc = crc32(data)
            data = snappy_compress(data)
            data = data + crc
        block_length = self.write_long(len(data))
        self.block = []
        self.block_count += 1
        self.block_size = 0
        return block_count + block_length + data + self.sync_marker

    def write_blocks(self, records):
        for record in records:
            if self.block_size >= DEFAULT_SYNC_INTERVAL:
                yield self.write_block()
            self.write_record(record)
        if self.block:
            yield self.write_block()

    def write_record(self, record):
        # Ensure schema is set before allowing write_record
        self.schema
        record = self.write(record)
        self.block_size += len(record)
        self.block.append(record)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()


class enum(object):
    def __init__(self, name, index, value):
        self.name = name
        self.index = index
        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.__str__()


class MetaEnum(type):
    def __new__(cls, name, bases, attrs):
        symbols = attrs.get('symbols')
        if symbols is None:
            attrs['symbols'] = []
        for i, symbol in enumerate(symbols):
            attrs[symbol] = enum(name, i, symbol)
        attrs['name'] = name
        obj = super(MetaEnum, cls).__new__(cls, name, bases, attrs)
        obj.__class__.__name__ = 'enum'
        return obj

    @property
    def T(cls):
        return {"name": cls.name, "type": "enum", "symbols": cls.symbols}


class Enum(with_metaclass(MetaEnum)):
    symbols = []

    def __init__(self, name, values):
        if not name or not values:
            raise Exception("Must provide blah")
        self.name = name
        self.symbols = values.split(" ")
        for i, v in enumerate(self.symbols):
            setattr(self, v, enum(self.name, i, v))

    @property
    def T(self):
        return {"name": self.name, "type": "enum", "symbols": self.symbols}
