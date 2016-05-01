# quickavro

quickavro is a library for working with the [Avro](https://avro.apache.org) file format. The purpose of this library is to provide a high-performance interface in Python for reading/writing Avro files.  The performance of Avro has been historically very poor in Python, so pyavro will make use of a Python C extension that directly interacts with the Avro C API.

# Install

Another goal with this project was to make it easier to install the dependencies (libavro and libjansson), which you can see being called below before running the build and install make targets.

```Shell
make vendor
make
make install
```
