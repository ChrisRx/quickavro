#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import StringIO

import avro.schema
import avro.io

import quickavro

example_schema = """{
  "type": "record",
  "name": "Person",
  "fields": [
    {"name": "name", "type": "string"},
    {"name": "age",  "type": ["int", "null"]}
  ]
}"""

records = [
    {"name": "Larry", "age": 21},
    {"name": "Gary", "age": 34},
    {"name": "Barry", "age": 27},
    {"name": "Dark Larry", "age": 1134},
    {"name": "Larry", "age": None},
]

def get_records():
    schema = avro.schema.parse(example_schema)
    writer = avro.io.DatumWriter(schema)
    f = StringIO.StringIO()
    encoder = avro.io.BinaryEncoder(f)
    def serialize(record):
        writer.write(record, encoder)
    for record in records:
        serialize(record)
    return f.getvalue()

def main():
    print(repr(get_records()))
    w = quickavro.Writer()
    results = []
    for record in records:
        results.append(w.write(example_schema, record))
    print(repr("".join(results)))


if __name__ == '__main__':
    main()
