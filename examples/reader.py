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

def get_records():
    schema = avro.schema.parse(example_schema)
    writer = avro.io.DatumWriter(schema)
    f = StringIO.StringIO()
    encoder = avro.io.BinaryEncoder(f)
    def serialize(record):
        writer.write(record, encoder)
    serialize({"name": "Larry", "age": 21})
    serialize({"name": "Gary", "age": 34})
    serialize({"name": "Barry", "age": 27})
    serialize({"name": "Dark Larry", "age": 1134})
    return f.getvalue()

def main():
    r = quickavro.Reader(example_schema)
    records = get_records()
    records = r.read(records)
    print("# of records: {0}".format(len(records)))
    for record in records:
        print("name: {name}, age: {age}".format(**record))


if __name__ == '__main__':
    main()
