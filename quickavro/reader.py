# -*- coding: utf-8 -*-

import json

import _quickavro

from .constants import *


def read_header(data):
    r = _quickavro.Reader(json.dumps(HEADER_SCHEMA))
    header, offset = r.read_record(data)
    if not header:
        return None, 0
    return header, offset


class Reader(object):
    def __init__(self, schema, codec='null'):
        self.schema = schema
        self.codec = codec
        self._reader = _quickavro.Reader(self.schema)

    def read(self, value):
        return self._reader.read(value)

    def read_long(self, b):
        return self._reader.read_long(b)

    def read_record(self, data):
        record, offset = self._reader.read_record(data)
        return record, offset

    def read_block(self, block):
        l, offset = self.read_long(block[:MAX_VARINT_SIZE])
        block = block[offset:]
        return self.read(block)


class FileReader(Reader):
    def __init__(self, f):
        if isinstance(f, basestring):
            self.f = open(f, 'r')
        else:
            self.f = f
        header = self._read_header()
        metadata = header.get('meta')
        schema = metadata.get('avro.schema')
        codec = metadata.get('avro.codec')
        super(FileReader, self).__init__(schema, codec)

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
        block = self.f.read(block_length)
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
            except MemoryError:
                break

    def close(self):
        self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
