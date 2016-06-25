quickavro examples
==================

Reading an avro file
--------------------

.. code-block:: python

    import quickavro

    with quickavro.FileReader("example.avro") as reader:
        for record in reader.records():
            print(record)

Writing an avro file
--------------------

.. code-block:: python

    import quickavro

    records = [
        {"name": "Larry", "age": 21},
        {"name": "Gary", "age": 34},
        {"name": "Barry", "age": 27},
        {"name": "Dark Larry", "age": 1134},
        {"name": "Larry of the Void", "age": None},
    ]

    with quickavro.FileWriter("example.avro") as writer:
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

Reading an avro file with BinaryEncoder
---------------------------------------

.. code-block:: python

    import quickavro

    with quickavro.BinaryEncoder() as encoder:
        encoder.schema = {
          "type": "record",
          "name": "Person",
          "fields": [
            {"name": "name", "type": "string"},
            {"name": "age",  "type": ["int", "null"]}
          ]
        }
        with open("example.avro", "r") as f:
            data = f.read()

        header, data = encoder.read_header(data)

        for record in encoder.read_blocks(data):
            print(record)

Writing an avro file with BinaryEncoder
---------------------------------------

.. code-block:: python

    import quickavro

    records = [
        {"name": "Larry", "age": 21},
        {"name": "Gary", "age": 34},
        {"name": "Barry", "age": 27},
        {"name": "Dark Larry", "age": 1134},
        {"name": "Larry of the Void", "age": None},
    ]

    with quickavro.BinaryEncoder() as encoder:
        encoder.schema = {
          "type": "record",
          "name": "Person",
          "fields": [
            {"name": "name", "type": "string"},
            {"name": "age",  "type": ["int", "null"]}
          ]
        }
        with open("example.avro", "w") as f:
            f.write(encoder.header)
            for block in encoder.write_blocks(records):
                f.write(block)


Using a deflate/snappy codec
----------------------------

.. code-block:: python

    import quickavro

    records = [
        {"name": "Larry", "age": 21},
        {"name": "Gary", "age": 34},
        {"name": "Barry", "age": 27},
        {"name": "Dark Larry", "age": 1134},
        {"name": "Larry of the Void", "age": None},
    ]

    with quickavro.BinaryEncoder(codec="deflate") as encoder:
        encoder.schema = {
          "type": "record",
          "name": "Person",
          "fields": [
            {"name": "name", "type": "string"},
            {"name": "age",  "type": ["int", "null"]}
          ]
        }
        with open("example.avro", "w") as f:
            f.write(encoder.header)
            for block in encoder.write_blocks(records):
                f.write(block)

    with quickavro.BinaryEncoder(codec="snappy") as encoder:
        encoder.schema = {
          "type": "record",
          "name": "Person",
          "fields": [
            {"name": "name", "type": "string"},
            {"name": "age",  "type": ["int", "null"]}
          ]
        }
        with open("example.avro", "w") as f:
            f.write(encoder.header)
            for block in encoder.write_blocks(records):
                f.write(block)


When not using context handling with :class:`quickavro.FileWriter`, blocks must be created manually by calling :meth:`quickavro.FileWriter.flush()` and then finally call :meth:`quickavro.FileWriter.close()` when finished:

.. code-block:: python

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
        for record in records:
            if writer.block_size >= quickavro.DEFAULT_SYNC_INTERVAL:
                # This ensures that blocks of records are created
                # correctly.
                writer.flush()
            writer.write_record(record)
        # This ensures that any records left in the current block are
        # written.
        writer.close()
