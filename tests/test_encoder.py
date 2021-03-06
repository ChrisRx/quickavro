#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pytest

import quickavro

# from quickavro._quickavro import SchemaError
# from quickavro import SchemaError


# Default values.  not implemented in C? on read only?

@pytest.mark.usefixtures('tmpdir')
class TestEncoderBasic(object):
    def test_type_string(self):
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {"name": "name", "type": "string"}
            result = encoder.write("test")
            assert result == b"\x08test"

    def test_type_bytes(self):
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {"type": "bytes"}
            result = encoder.write(b"test")
            assert result == b"\x08test"

    def test_type_int32(self):
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {"type": "int"}
            result = encoder.write(10000)
            assert result == b"\xa0\x9c\x01"

    def test_type_int64(self):
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {"type": "long"}
            result = encoder.write(4294967295)
            assert result == b"\xfe\xff\xff\xff\x1f"

    def test_type_float(self):
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {"type": "float"}
            result = encoder.write(8311.125)
            assert result == b"\x80\xdc\x01F"

    def test_type_double(self):
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {"type": "double"}
            result = encoder.write(1928474837480108311.521837843)
            assert result == b"\xf1G\xae\xa5Q\xc3\xbaC"

    def test_type_boolean(self):
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {"type": "boolean"}
            result = encoder.write(True)
            assert result == b"\x01"

            result = encoder.write(False)
            assert result == b"\x00"

    def test_type_null(self):
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {"type": "null"}
            result = encoder.write(None)
            assert result == b""

    def test_type_record(self):
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {
                "type": "record",
                "name": "test",
                "fields": [
                    {"name": "name", "type": "string"},
                    {"name": "age", "type": "int"}
                ]
            }
            result = encoder.write({"name": "Larry", "age": 21})
            assert result == b"\nLarry*"

    def test_type_enum(self):
        # Test Avro enum encoding with quickavro custom Enum type
        Gender = quickavro.Enum("Gender", "F M")
            
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = Gender.T
            # result = encoder.write({"test": Gender.M}) Segfault
            result = encoder.write(Gender.F)
            assert result == b"\x00"
            result = encoder.write(Gender.M)
            assert result == b"\x02"

        # Test Avro enum encoding with string symbols matching a schema
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {
                "type": "enum",
                "name": "Gender",
                "symbols": ["F", "M"]
            }
            result = encoder.write("F")
            assert result == b"\x00"
            result = encoder.write("M")
            assert result == b"\x02"

    def test_type_fixed(self):
        with quickavro.BinaryEncoder() as encoder:
            value = b"\x01\x02\x03\x04\x05\x06\x07\x08"
            encoder.schema = {"name": "test", "type": "fixed", "size": len(value)}
            result = encoder.write(value)
            assert result == b"\x01\x02\x03\x04\x05\x06\x07\x08"

    def test_type_array(self):
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {"type": "array", "items": "string"}
            result = encoder.write(["test1", "test2"])
            assert result == b"\x04\ntest1\ntest2\x00"

    def test_type_union(self):
        TextAge = quickavro.Enum("TextAge", "AGE_ONE AGE_TWO")
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {
                "type": "record",
                "name": "test",
                "fields": [
                    {
                        "name": "ages",
                        "type": [
                            "int",
                            "null",
                            {
                                "type": "array",
                                "items": "int"
                            },{
                                "type": "enum",
                                "name": "TextAge",
                                "symbols": ["AGE_ONE", "AGE_TWO"]
                            }
                        ]
                    },
                ]
            }
            # encoder.schema = {"type": ["string", "null"]}
            result = encoder.write({"ages": 25})
            assert result == b"\x002"
            result = encoder.write({"ages": None})
            assert result == b"\x02"
            result = encoder.write({"ages": [16, 18, 21]})
            assert result == b"\x04\x06 $*\x00"
            result = encoder.write({"ages": "AGE_ONE"})
            assert result == b"\x06\x00"
            result = encoder.write({"ages": TextAge.AGE_TWO})
            assert result == b"\x06\x02"

    def test_type_union_fixed(self):
        with quickavro.BinaryEncoder() as encoder:
            value = b"\x01\x02\x03\x04\x05\x06\x07\x08"
            encoder.schema = {
                "type": "record",
                "name": "TestRecord",
                "fields": [
                    {
                        "name": "testfield",
                        "type": [
                            "null",
                            {"name": "testfixed", "type": "fixed", "size": len(value)}
                        ]
                    }
                ]
            }
            result = encoder.write({"testfield": None})
            assert result == b"\x00"
            result = encoder.write({})
            assert result == b"\x00"
            result = encoder.write({"testfield": value})
            assert result == b"\x02\x01\x02\x03\x04\x05\x06\x07\x08"

    def test_type_map(self):
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {
                "type": "map",
                "values": "string"
            }
            test_map = {"mykey": "myval"}
            result = encoder.write(test_map)
            assert result == b"\x02\nmykey\nmyval\x00"

    def test_type_link(self):
        with quickavro.BinaryEncoder() as encoder:
            encoder.schema = {
                "type": "record",
                "name": "chainlink",
                "fields": [
                    {"name": "linkid", "type": "int"},
                    {"name": "nextlink", "type": ["null", "chainlink"]}
                ]
            }

            chain = {"linkid": 1, "nextlink": {"linkid": 2}}
            result = encoder.write(chain)
            assert result == b"\x02\x02\x04\x00"


@pytest.mark.usefixtures('tmpdir')
class TestEncoderOther(object):
    def test_invalid_union(self):
        with quickavro.BinaryEncoder() as encoder:
            with pytest.raises(quickavro.SchemaError):
                encoder.schema = {
                    "type": "record",
                    "name": "test",
                    "fields": [
                        {"name": "age",  "type": ["invalid", "null"]}
                    ]
                }
                result = encoder.write({"age": 8011.125})
                assert result == b"\x08test"
