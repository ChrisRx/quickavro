# -*- coding: utf-8 -*-

import _quickavro

from .constants import *


class Reader(object):
    def __init__(self, schema):
        self._reader = _quickavro.Reader(schema)

    def read(self, value):
        return self._reader.read(value)

    def read_header(self, codec='null'):
        header = self.read(HEADER_SCHEMA)

