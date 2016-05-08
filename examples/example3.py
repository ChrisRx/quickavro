#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time

import quickavro


current_dir = os.path.dirname(os.path.realpath(__file__))
avro_file = os.path.join(current_dir, 'example3.avro')

records = [
    {"name": "Larry", "age": 21},
    {"name": "Gary", "age": 34},
    {"name": "Barry", "age": 27},
    {"name": "Dark Larry", "age": 1134},
    {"name": "Larry", "age": None},
]

def generate_records(records, n):
    print("Generate {0} records ...".format(n))
    for i in range(n):
        yield records[i % len(records)]

def write_avro_file(n):
    with quickavro.FileWriter(avro_file) as writer:
        writer.schema = {
          "type": "record",
          "name": "Person",
          "fields": [
            {"name": "name", "type": "string"},
            {"name": "age",  "type": ["int", "null"]}
          ]
        }
        for record in generate_records(records, n):
            if writer.tell() >= quickavro.DEFAULT_SYNC_INTERVAL:
                writer.write_sync()
            writer.write_record(record)

def read_avro_file():
    with quickavro.FileReader(avro_file) as reader:
        record_count = 0
        for record in reader.records():
            record_count += 1
        print("Read {0} records back from file.".format(record_count))

def main():
    n = 1000000
    start_time = time.time()
    write_avro_file(n)
    print("Wrote {0} records in {1:.3f}".format(n, time.time()-start_time))
    start_time = time.time()
    read_avro_file()
    print("Read {0} records in {1:.3f}".format(n, time.time()-start_time))

if __name__ == '__main__':
    main()
