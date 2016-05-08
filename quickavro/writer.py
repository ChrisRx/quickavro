# -*- coding: utf-8 -*-

import os
import json

import _quickavro

from .constants import *


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
    def __init__(self, f):
        if isinstance(f, basestring):
            self.f = open(f, 'w')
        else:
            self.f = f
        self._schema = None
        self._codec = None
        super(FileWriter, self).__init__(None)
        self.block = []
        self.last_sync = 0

    def tell(self):
        return self.f.tell() - self.last_sync

    def write_record(self, record):
        record = self.write(record)
        self.block.append(record)
        #self.f.write(record)

    def write_sync(self):
        data = "".join(self.block)
        self.f.write(self.write_long(len(self.block)))
        self.f.write(self.write_long(len(data)))
        self.f.write(data)
        self.f.write(self.sync_marker)
        self.block = []
        self.last_sync = self.f.tell()

    @property
    def schema(self):
        if not self._schema:
            raise Exception("Schema not set")
        return self._schema

    @schema.setter
    def schema(self, schema, codec="null"):
        self._schema = schema
        self._writer = _quickavro.Writer(json.dumps(schema))
        self._write_header()

    def _write_header(self):
        if self.f.tell() != 0:
            self.f.seek(0)
        header = super(FileWriter, self).write_header()
        self.f.write(header)
        self.last_sync = self.f.tell()

    def close(self):
        if self.block:
            self.write_sync()
        self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
