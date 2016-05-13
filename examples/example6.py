#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import quickavro


current_dir = os.path.dirname(os.path.realpath(__file__))
avro_file = os.path.join(current_dir, 'example6.avro')

records = [
    {"name": "Larry", "age": 21},
    {"name": "Gary", "age": 34},
    {"name": "Barry", "age": 27},
    {"name": "Dark Larry", "age": 1134},
    {"name": "Larry", "age": None},
]

def main():
    with quickavro.BinaryEncoder() as encoder:
        encoder.schema = {
          "type": "record",
          "name": "Person",
          "fields": [
            {"name": "name", "type": "string"},
            {"name": "age",  "type": ["int", "null"]}
          ]
        }
        with open(avro_file, "w") as f:
            f.write(encoder.header)
            for block in encoder.write_blocks(records):
                f.write(block)


        # Read
        with open(avro_file, "r") as f:
            data = f.read()

        header, data = encoder.read_header(data)

        for record in encoder.read_blocks(data):
            print("name: {name}, age: {age}".format(**record))


if __name__ == '__main__':
    main()
