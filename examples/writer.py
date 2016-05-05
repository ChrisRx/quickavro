#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import StringIO
import json
import struct

import avro.datafile
import avro.io
import avro.schema

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

#def get_records():
    #schema = avro.schema.parse(example_schema)
    #writer = avro.io.DatumWriter(schema)
    #f = StringIO.StringIO()
    #filewriter = avro.datafile.DataFileWriter(open('omg.avro', 'w'), writer, schema)
    ##encoder = avro.io.BinaryEncoder(f)
    #def serialize(record):
        #writer.write(record, encoder)
    #for record in records:
        #filewriter.append(record)
        ##serialize(record)
    #filewriter.close()

def main():
    #print(repr(get_records()))
    print(repr(open('omg.avro', 'r').read()))
    w = quickavro.Writer(json.loads(example_schema))
    results = []
    header = w.write_header()
    results.append(header)
    #r = []
    #for record in records:
        #r.append(w.write(record))
    #r = "".join(r)
    #results.append(struct.pack('H', len(r)) + r)
    #results.append(w.sync_marker)
    print(repr("".join(results)))


if __name__ == '__main__':
    main()
