#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import quickavro


current_dir = os.path.dirname(os.path.realpath(__file__))
avro_file = os.path.join(current_dir, 'example4.avro')

records = [
    {"name": "Larry", "age": 21},
    {"name": "Gary", "age": 34},
    {"name": "Barry", "age": 27},
    {"name": "Dark Larry", "age": 1134},
    {"name": "Larry", "age": None},
]

def main():
    with quickavro.FileWriter(avro_file, codec='deflate') as writer:
        writer.schema = {
          "type": "record",
          "name": "Person",
          "fields": [
            {"name": "name", "type": "string"},
            {"name": "age",  "type": ["int", "null"]}
          ]
        }
        # Write 1 block
        for record in records:
            writer.write_record(record)

    with quickavro.FileReader(avro_file) as reader:
        for record in reader.records():
            print("name: {name}, age: {age}".format(**record))


if __name__ == '__main__':
    main()
