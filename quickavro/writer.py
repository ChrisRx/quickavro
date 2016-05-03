# -*- coding: utf-8 -*-

import _quickavro


class Writer(object):
    def __init__(self):
        self._writer = _quickavro.Writer()

    def write(self, schema, value):
        return self._writer.write(schema, value)
