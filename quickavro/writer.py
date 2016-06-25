# -*- coding: utf-8 -*-

from .constants import *
from .encoder import *
from .errors import *
from .utils import *

from ._compat import *


class FileWriter(BinaryEncoder):
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
