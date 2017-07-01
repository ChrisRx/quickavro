# -*- coding: utf-8 -*-

VERSION = b'\x01'
MAGIC = b'Obj' + VERSION
SYNC_SIZE = 16
DEFAULT_SYNC_INTERVAL = 1000 * SYNC_SIZE

HEADER_SCHEMA = {
    'type': 'record',
    'name': 'org.apache.avro.file.Header',
    'fields': [
        {'name': 'magic', 'type': {'type': 'fixed', 'name': 'magic', 'size': len(MAGIC)}},
        {'name': 'meta', 'type': {'type': 'map', 'values': 'bytes'}},
        {'name': 'sync', 'type': {'type': 'fixed', 'name': 'sync', 'size': SYNC_SIZE}},
    ]
}

MAX_VARINT_SIZE = 10
INITIAL_HEADER_SIZE = 8192
