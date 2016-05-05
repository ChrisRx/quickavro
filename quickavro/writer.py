# -*- coding: utf-8 -*-

import os
import json

import _quickavro

from .constants import *


class Writer(object):
    def __init__(self, schema):
        self.schema = schema
        self._writer = _quickavro.Writer(json.dumps(self.schema))
        #self.sync_marker = os.urandom(SYNC_SIZE)
        self.sync_marker = '\xa67\xc0#\xa8\xdc\xd1\xdf\xa7/\x8a\x1a\xf2\xd6\x06h'

    def write(self, value):
        return self._writer.write(value)

    def write_header(self, codec='null'):
        w = _quickavro.Writer(json.dumps(HEADER_SCHEMA))
        metadata = {
            "avro.codec": codec,
            "avro.schema": json.dumps(self.schema)
        }
        header = {
            'magic': MAGIC,
            'meta': metadata,
            'sync': self.sync_marker
        }
        return w.write(header)
