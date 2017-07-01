# -*- coding: utf-8 -*-

import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
default_encoding = "UTF-8"

def with_metaclass(meta, *bases):
    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__
        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)
    return metaclass('temporary_class', None, {})

if PY3:
    basestring = (str, bytes)

    def ensure_bytes(s):
        if type(s) == str:
            return bytes(s, default_encoding)
        else:
            return bytes(s)

    def ensure_str(s):
        if type(s) == bytes:
            return s.decode(default_encoding)
        else:
            return s
else:
    range = xrange

    ensure_bytes = lambda s: s
    ensure_str = lambda s: s
