#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pytest

import quickavro


records = [
    {"name": "Larry", "age": 21},
    {"name": "Gary", "age": 34},
    {"name": "Barry", "age": 27},
    {"name": "Dark Larry", "age": 1134},
    {"name": "Larry", "age": None},
]


@pytest.mark.usefixtures('tmpdir')
class TestQuickAvro(object):
    def test_filewriter(self, tmpdir):
        avro_file = os.path.join(str(tmpdir), "testfile1.avro")
        with quickavro.FileWriter(avro_file) as writer:
            writer.schema = {
              "type": "record",
              "name": "Person",
              "fields": [
                {"name": "name", "type": "string"},
                {"name": "age",  "type": ["int", "null"]}
              ]
            }
            for record in records:
                writer.write_record(record)
        
        with quickavro.FileReader(avro_file) as reader:
            for record, expected_record in zip(reader.records(), records):
                assert record.get('name') == expected_record.get('name')
                assert record.get('age') == expected_record.get('age')

    def test_record(self, tmpdir):
        Gender = quickavro.Enum("Gender", "F M")

        records = [
            {"name": "Larry", "age": 21},
            {"name": "Gary", "age": 34},
            {"name": "Barry", "age": 27},
            {"name": "Dark Larry", "age": 1134},
            {"name": "Larry", "age": None},
            {"name": "Larry"},
            {"name": "Larry", "gender": Gender.M},
            {"name": "Sherry", "gender": Gender.F},
        ]

        avro_file = os.path.join(str(tmpdir), "testfile1.avro")
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {
                "type": "record",
                "name": "test",
                "fields": [
                    {"name": "name", "type": "string"},
                    {"name": "age",  "type": ["int", "null"], "default": 1},
                    {"name": "gender", "type": [Gender.T, "null"]},
                ]
            }
            avro_file = encoder.header
            for block in encoder.write_blocks(records):
                avro_file += block

            header, data = encoder.read_header(avro_file)

            for record in encoder.read_blocks(data):
                print(record)
