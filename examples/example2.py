#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import quickavro


current_dir = os.path.dirname(os.path.realpath(__file__))
avro_file = os.path.join(current_dir, 'example2.avro')

records = [
    {"name": "Larry", "age": 21},
    {"name": "Gary", "age": 34},
    {"name": "Barry", "age": 27},
    {"name": "Dark Larry", "age": 1134},
    {"name": "Larry", "age": None},
]

def main():
    with open(avro_file, 'w') as f:
        writer = quickavro.FileWriter(f)
        writer.schema = {
          "type": "record",
          "name": "Person",
          "fields": [
            {"name": "name", "type": "string"},
            {"name": "age",  "type": ["int", "null"]}
          ]
        }
        # Must call FileWriter.write_sync() to flush record buffer when
        # not using with context
        for record in records:
            writer.write_record(record)
        writer.write_sync()

    with open(avro_file, 'r') as f:
        reader = quickavro.FileReader(f)

        for record in reader.records():
            print("name: {name}, age: {age}".format(**record))


if __name__ == '__main__':
    main()
