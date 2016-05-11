# -*- coding: utf-8 -*-

"""
quickavro
~~~~~~~~~~~~

quickavro is a library for working with the avro file format.

:copyright: (c) 2016 by Chris Marshall.
:license: Apache 2.0, see LICENSE for more details.

"""

__title__ = 'quickavro'
__version__ = '0.1.0'
__authors__ = ['Chris Marshall']
__license__ = 'Apache 2.0'
__all__ = ['BinaryEncoder', 'BlockEncoder', 'FileReader', 'FileWriter']

from .constants import (
    DEFAULT_SYNC_INTERVAL,
    HEADER_SCHEMA
)
from .errors import (
    CodecNotSupported,
    SchemaNotSet
)
from .encoder import BinaryEncoder, BlockEncoder
from .reader import FileReader
from .writer import FileWriter
