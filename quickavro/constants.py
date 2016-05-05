# -*- coding: utf-8 -*-


MAGIC = b'Obj\x01'
SYNC_SIZE = 16

HEADER_SCHEMA = {
    'type': 'record',
    'name': 'org.apache.avro.file.Header',
    'fields': [
        {
            'name': 'magic',
            'type': {'type': 'fixed', 'name': 'magic', 'size': len(MAGIC)}
        },
        {
            'name': 'meta',
            'type': {'type': 'map', 'values': 'bytes'}
        },
        {
            'name': 'sync',
            'type': {'type': 'fixed', 'name': 'sync', 'size': SYNC_SIZE}
        },
    ]
}
