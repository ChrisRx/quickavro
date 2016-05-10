# quickavro [![Build Status](https://drone.io/github.com/ChrisRx/quickavro/status.png)](https://drone.io/github.com/ChrisRx/quickavro/latest)

quickavro is a library for working with the [Avro](https://avro.apache.org) file format. The purpose of this library is to provide a high-performance interface in Python for reading/writing Avro files.  The performance of Avro has been historically very poor in Python, so quickavro will make use of a Python C extension that directly interacts with the Avro C API.

# Install

Another goal with this project was to make it easier to install the dependencies (libavro and libjansson), which you can see being called below before running the build and install make targets.

```Shell
make vendor
make
make install
```

# Usage

## Reading an avro file

```Python
import quickavro

with quickavro.FileReader("file.avro") as reader:
    for record in reader.records():
        print(record)
```

## Writing an avro file

```Python
import quickavro

records = [
    {"name": "Larry", "age": 21},
    {"name": "Gary", "age": 34},
    {"name": "Barry", "age": 27},
    {"name": "Dark Larry", "age": 1134},
    {"name": "Larry of the Void", "age": None},
]

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
        if writer.tell() >= quickavro.DEFAULT_SYNC_INTERVAL:
            writer.write_sync()
        writer.write_record(record)
```
