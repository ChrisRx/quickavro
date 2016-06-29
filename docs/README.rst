quickavro |Build Status|
========================

quickavro is a Python library for working with the `Avro <https://avro.apache.org>`__ file format. The purpose of this library is to provide a high-performance interface in Python for reading/writing Avro files. The performance of Avro has been historically very poor in Python, so quickavro makes use of a Python C extension that directly interacts with the official Avro C API.  quickavro is currently alpha quality.

Documentation
=============

API documentation and examples can be found at
http://chrisrx.github.io/quickavro.

Install
=======

.. code:: bash

    $ pip install quickavro

It is important to note, however, that until `PyPi allows binary wheels for linux <https://github.com/pypa/pypi-legacy/issues/120>`__, ``setup.py`` will attempt to download and compile the dependencies when installing with ``pip install``.

Building from source
====================

quickavro depends upon several C libraries: 

- `Avro C <https://avro.apache.org/docs/current/api/c/>`__
- `Jansson <https://github.com/akheron/jansson>`__
- `Snappy <https://github.com/google/snappy>`__

They depend upon traditional build/config tools (cmake, autoconf, pkgconfig, etc), that sometimes make compiling this a nightmare so I ended up trying something a little different here and so far it is working well.

.. code:: Shell

    make vendor
    make
    make install

The ``vendor`` make target downloads and unpacks the source files for all the libraries, while the default make target ``build``, calls Python setuptools/distutils to staticly compile these and creates a `Wheel <http://pythonwheels.com/>`__ binary package. This removes the need for these libraries to be dynamically linked correctly and can trivially be packaged within the binary Wheel package without worries like if the header package has installed for the library.

.. |Build Status| image:: https://travis-ci.org/ChrisRx/quickavro.svg?branch=master
   :target: https://travis-ci.org/ChrisRx/quickavro
