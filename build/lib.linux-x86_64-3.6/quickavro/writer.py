# -*- coding: utf-8 -*-

from .constants import *
from .encoder import *
from .errors import *
from .utils import *

from ._compat import *


class FileWriter(BinaryEncoder):
    """
    The :class:`FileWriter` object implements :class:`quickavro.BinaryEncoder`
    and provides and interface to write Avro files.

    :param f: File-like object or path of file that :class:`FileWriter`
        will write into.
    :param codec: (optional) Compression codec used with
        :class:`FileWriter`.

    Example:

    .. code-block:: python

        with quickavro.FileWriter("test.avro) as writer:
            writer.schema = {
              "type": "record",
              "name": "Person",
              "fields": [
                {"name": "name", "type": "string"},
                {"name": "age",  "type": ["int", "null"]}
              ]
            }

            records = [
                {"name": "Larry", "age": 21},
                {"name": "Gary", "age": 34},
                {"name": "Barry", "age": 27},
                {"name": "Dark Larry", "age": 1134},
                {"name": "Larry of the Void", "age": None},
            ]

            for record in records:
                writer.write_record(record)
    """

    def __init__(self, f, codec="null"):
        super(FileWriter, self).__init__(codec=codec)
        if isinstance(f, basestring):
            self.f = open(f, 'wb')
        else:
            self.f = f

    def write_record(self, record):
        if self.block_size >= DEFAULT_SYNC_INTERVAL:
            self.f.write(self.flush())
        super(FileWriter, self).write_record(record)

    def flush(self):
        if self.block_count == 0:
            self.f.write(self.header)
            self.block_count += 1
        return self.write_block()

    def close(self):
        if self.block:
            self.f.write(self.flush())
        self.f.close()
