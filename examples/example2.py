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
        # When not using context handling blocks must be done manually
        # by calling FileWriter.flush()
        for record in records:
            if writer.block_size >= quickavro.DEFAULT_SYNC_INTERVAL:
                writer.flush()
            writer.write_record(record)
        # Must call FileWriter.close() to flush record buffer when
        # not using with context
        writer.close()

    with open(avro_file, 'r') as f:
        reader = quickavro.FileReader(f)

        for record in reader.records():
            print("name: {name}, age: {age}".format(**record))


if __name__ == '__main__':
    main()
