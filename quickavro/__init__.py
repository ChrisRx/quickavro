# -*- coding: utf-8 -*-

"""
quickavro
~~~~~~~~~~~~

quickavro is a library for working with the avro file format.

:copyright: (c) 2016 by Chris Marshall.
:license: Apache 2.0, see LICENSE for more details.

"""

__title__ = 'quickavro'
__version__ = '0.1.18'
__authors__ = ['Chris Marshall']
__license__ = 'Apache 2.0'
__all__ = ['BinaryEncoder', 'Enum', 'FileReader', 'FileWriter']

from .constants import (
    DEFAULT_SYNC_INTERVAL,
    HEADER_SCHEMA
)
from .errors import (
    CodecNotSupported,
    InvalidSchemaError
)
from .encoder import BinaryEncoder, Enum
from .reader import FileReader
from .writer import FileWriter
