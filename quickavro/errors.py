# -*- coding: utf-8 -*-

class QuickAvroError(Exception):
    """
    Baseclass for all quickavro errors.
    """


class CodecNotSupported(QuickAvroError):
    """
    Raised when codec requested is not supported.
    """


class InvalidSchemaError(QuickAvroError):
    """
    Raised when unable to parse Avro schema.
    """


class SchemaNotFound(QuickAvroError):
    """
    Raised when schema is required but has not yet been provided. This
    could mean the schema was not read from the header or not
    explicitly set by the user when needed.
    """


class InvalidSyncData(QuickAvroError):
    """
    Raised when block sync marker does not match.
    """


class SnappyChecksumError(QuickAvroError):
    """
    Raised when Snappy CRC does not match.
    """
