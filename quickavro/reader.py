# -*- coding: utf-8 -*-

import _quickavro


class Reader(object):
    def __init__(self):
        self._reader = _quickavro.Reader()

    def read(self, schema, value):
        return self._reader.read(schema, value)
