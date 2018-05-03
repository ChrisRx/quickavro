/*
 * Copyright 2016 Chris Marshall
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "encoderobject.h"
#include "compat.h"
#include "convert.h"
#include "quickavro.h"
#include <avro.h>


PyObject *AvroError;
PyObject *ReadError;
PyObject *SchemaError;
PyObject *WriteError;

static void Encoder_dealloc(Encoder* self) {
    if (self->reader_iface != NULL) {
        avro_value_iface_decref(self->reader_iface);
    }
    if (self->reader_schema != NULL) {
        avro_schema_decref(self->reader_schema);
    }
    if (self->writer_schema != NULL) {
        avro_schema_decref(self->writer_schema);
    }
    if (self->writer_iface != NULL) {
        avro_value_iface_decref(self->writer_iface);
    }
    if (self->resolver != NULL) {
        avro_value_iface_decref(self->resolver);
    }
    if (self->reader != NULL) {
        avro_reader_free(self->reader);
    }
    if (self->writer != NULL) {
        avro_writer_free(self->writer);
    }
    if (self->buffer != NULL) {
        avro_free(self->buffer, self->buffer_length);
    }

    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject* Encoder_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    Encoder* self;

    self = (Encoder*)type->tp_alloc(type, 0);
    self->buffer = NULL;
    self->resolver = NULL;
    self->reader = NULL;
    self->writer = NULL;
    self->reader_iface = NULL;
    self->reader_schema = NULL;
    self->writer_iface = NULL;
    self->writer_schema = NULL;
    self->reader_schema = NULL;
    return (PyObject*)self;
}

static int Encoder_init(Encoder* self, PyObject* args, PyObject* kwds) {
    self->reader = avro_reader_memory(NULL, 0);
    self->buffer = (char*)avro_malloc(INITIAL_BUFFER_SIZE);
    self->buffer_length = INITIAL_BUFFER_SIZE;
    self->writer = avro_writer_memory(self->buffer, self->buffer_length);
    return 0;
}

static PyObject* Encoder_read(Encoder* self, PyObject* args) {
    Py_buffer buffer;
    if (!PyArg_ParseTuple(args, "s*", &buffer)) {
        Py_RETURN_NONE;
    }
    PyObject* values = PyList_New(0);
    avro_value_t  writer_value;
    avro_value_t  reader_value;
    int rval;
    avro_reader_memory_set_source(self->reader, buffer.buf, buffer.len);
    if ((rval = avro_generic_value_new(self->reader_iface, &reader_value)) != 0) {
        PyErr_Format(ReadError, "%s", avro_strerror());
        return NULL;
    };
    if (self->writer_iface != NULL) {
        if ((rval = avro_resolved_writer_new_value(self->writer_iface, &writer_value)) != 0) {
            PyErr_Format(ReadError, "%s", avro_strerror());
            return NULL;
        }
        avro_resolved_writer_set_dest(&writer_value, &reader_value);
        while ((rval = avro_value_read(self->reader, &writer_value)) == 0) {
            PyObject* item = avro_to_python(&reader_value);
            PyList_Append(values, item);
            avro_value_reset(&reader_value);
            Py_DECREF(item);
        }
        avro_value_decref(&reader_value);
        avro_value_decref(&writer_value);
        PyBuffer_Release(&buffer);
        return values;
    }
    while ((rval = avro_value_read(self->reader, &reader_value)) == 0) {
        PyObject* item = avro_to_python(&reader_value);
        PyList_Append(values, item);
        avro_value_reset(&reader_value);
        Py_DECREF(item);
    }
    avro_value_decref(&reader_value);
    PyBuffer_Release(&buffer);
    return values;
}

static PyObject* Encoder_read_long(Encoder* self, PyObject* args) {
    Py_buffer buffer;

    if (!PyArg_ParseTuple(args, "s*", &buffer)) {
        Py_RETURN_NONE;
    }
    char* buf = buffer.buf;
    int64_t l;
    uint64_t value = 0;
    uint8_t b;
    int offset = 0;
    do {
        if (offset == MAX_VARINT_SIZE) {
            PyErr_SetString(ReadError, "Varint is too long");
            return NULL;
        }
        b = buf[offset];
        value |= (int64_t) (b & 0x7F) << (7 * offset);
        ++offset;
    } while (b & 0x80);
    l = ((value >> 1) ^ -(value & 1));
    PyBuffer_Release(&buffer);
    return Py_BuildValue("(OO)", PyLong_FromLong(l), PyLong_FromLong(offset));
}

static PyObject* Encoder_read_record(Encoder* self, PyObject* args) {
    Py_buffer buffer;
    PyObject *obj;
    size_t record_size;
    int rval;

    if (!PyArg_ParseTuple(args, "s*", &buffer)) {
        Py_RETURN_NONE;
    }
    avro_value_t reader_value;
    avro_value_t writer_value;
    avro_reader_memory_set_source(self->reader, buffer.buf, buffer.len);
    if ((rval = avro_generic_value_new(self->reader_iface, &reader_value)) != 0) {
        PyErr_Format(ReadError, "%s", avro_strerror());
        return NULL;
    };
    if (self->writer_iface != NULL) {
        if ((rval = avro_resolved_writer_new_value(self->writer_iface, &writer_value)) != 0) {
            PyErr_Format(ReadError, "%s", avro_strerror());
            return NULL;
        }
        avro_resolved_writer_set_dest(&writer_value, &reader_value);
        if ((rval = avro_value_read(self->reader, &writer_value)) != 0) {
            PyErr_Format(ReadError, "%s", avro_strerror());
            return NULL;
        }
        obj = avro_to_python(&reader_value);
        if ((rval = avro_value_sizeof(&reader_value, &record_size)) != 0) {
            PyErr_Format(ReadError, "%s", avro_strerror());
            return NULL;
        }
        avro_value_decref(&reader_value);
        avro_value_decref(&writer_value);
        PyBuffer_Release(&buffer);
        // TODO: refcount wrong, there are others
        // TODO: also check all the PyLong_ calls to make sure they
        // have the correct size types
        PyObject *ret = Py_BuildValue("(OO)", obj, PyLong_FromLong(record_size));
        Py_XDECREF(obj);
        return ret;
    }
    if ((rval = avro_value_read(self->reader, &reader_value)) != 0) {
        PyErr_Format(ReadError, "%s", avro_strerror());
        return NULL;
    }
    obj = avro_to_python(&reader_value);
    if ((rval = avro_value_sizeof(&reader_value, &record_size)) != 0) {
        PyErr_Format(ReadError, "%s", avro_strerror());
        return NULL;
    }
    avro_value_decref(&reader_value);
    PyBuffer_Release(&buffer);
    // TODO: refcount wrong, there are others
    // TODO: also check all the PyLong_ calls to make sure they
    // have the correct size types
    PyObject *ret = Py_BuildValue("(OO)", obj, PyLong_FromLong(record_size));
    Py_XDECREF(obj);
    return ret;
}

static PyObject* Encoder_set_schema(Encoder* self, PyObject* args, PyObject *kwargs) {
    char* json_str = NULL;
    char* reader_schema = NULL;
    avro_schema_error_t error;

    static char *kwlist[] = {"json_str", "reader_schema", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|s", kwlist, &json_str, &reader_schema)) {
        return NULL;
    }
    int r = avro_schema_from_json(json_str, 0, &self->writer_schema, &error);
    if (r != 0 || self->writer_schema == NULL) {
        self->writer_schema = NULL;
        PyErr_Format(SchemaError, "%s", avro_strerror());
        return NULL;
    }
    if (reader_schema != NULL) {
        int r = avro_schema_from_json(reader_schema, 0, &self->reader_schema, &error);
        if (r != 0 || self->reader_schema == NULL) {
            self->reader_schema = NULL;
            PyErr_Format(SchemaError, "%s", avro_strerror());
            return NULL;
        }
        self->writer_iface = avro_resolved_writer_new(self->writer_schema, self->reader_schema);
        if (self->writer_iface == NULL) {
            PyErr_Format(SchemaError, "%s", avro_strerror());
            return NULL;
        }
        self->resolver = avro_resolved_reader_new(self->writer_schema, self->reader_schema);
        if (self->resolver == NULL) {
            PyErr_Format(SchemaError, "%s", avro_strerror());
            return NULL;
        }
        self->reader_iface = avro_generic_class_from_schema(self->reader_schema);
    } else {
        self->reader_iface = avro_generic_class_from_schema(self->writer_schema);
        // ensure writer_iface is cleaned up if set_schema is set without
        // reader_schema
        if (self->writer_iface != NULL) {
            avro_value_iface_decref(self->writer_iface);
            self->writer_iface = NULL;
        }
        if (self->resolver != NULL) {
            avro_value_iface_decref(self->resolver);
            self->resolver = NULL;
        }
    }
    return Py_BuildValue("i", 0);
}

static PyObject* Encoder_write(Encoder* self, PyObject* args) {
    PyObject* obj;
    int rval;

    if (!PyArg_ParseTuple(args, "O", &obj)) {
        Py_RETURN_NONE;
    }
    avro_value_t reader_value;
    if ((rval = avro_generic_value_new(self->reader_iface, &reader_value)) != 0) {
        PyErr_Format(ReadError, "%s", avro_strerror());
        return NULL;
    };
    if (self->resolver != NULL) {
        avro_value_t resolved;
        if ((rval = python_to_avro(obj, &reader_value)) == 0) {
            rval = avro_value_write(self->writer, &reader_value);
        }
        if ((rval = avro_resolved_reader_new_value(self->resolver, &resolved)) != 0) {
            PyErr_Format(WriteError, "%s", avro_strerror());
            return NULL;
        }
        avro_resolved_reader_set_source(&resolved, &reader_value);
        size_t new_size;

        while (rval == ENOSPC) {
            new_size = self->buffer_length * 2;
            self->buffer = (char*)avro_realloc(self->buffer, self->buffer_length, new_size);
            if (!self->buffer) {
                PyErr_NoMemory();
                return NULL;
            }
            self->buffer_length = new_size;
            avro_writer_memory_set_dest(self->writer, self->buffer, self->buffer_length);
            rval = avro_value_write(self->writer, &resolved);
        }

        if (rval) {
            avro_value_decref(&resolved);
            avro_value_decref(&reader_value);
            return NULL;
        }
        PyObject* s = PyBytes_FromStringAndSize(self->buffer, avro_writer_tell(self->writer));
        avro_writer_reset(self->writer);
        avro_value_decref(&resolved);
        avro_value_decref(&reader_value);
        return s;
    }
    rval = python_to_avro(obj, &reader_value);
    if (rval == 0) {
        rval = avro_value_write(self->writer, &reader_value);
    }
    size_t new_size;

    while (rval == ENOSPC) {
        new_size = self->buffer_length * 2;
        self->buffer = (char*)avro_realloc(self->buffer, self->buffer_length, new_size);
        if (!self->buffer) {
            PyErr_NoMemory();
            return NULL;
        }
        self->buffer_length = new_size;
        avro_writer_memory_set_dest(self->writer, self->buffer, self->buffer_length);
        rval = avro_value_write(self->writer, &reader_value);
    }

    if (rval) {
        avro_value_decref(&reader_value);
        return NULL;
    }
    PyObject* s = PyBytes_FromStringAndSize(self->buffer, avro_writer_tell(self->writer));
    avro_writer_reset(self->writer);
    avro_value_decref(&reader_value);
    return s;
}

static PyObject* Encoder_write_long(Encoder* self, PyObject* args) {
    PyObject* obj;

    if (!PyArg_ParseTuple(args, "O", &obj)) {
        Py_RETURN_NONE;
    }
    int64_t l = PyLong_AsLongLong(obj);
    char* buf = (char*)malloc(sizeof(char)*MAX_VARINT_SIZE);
    uint8_t bytes_written = 0;
    uint64_t n = (l << 1) ^ (l >> 63);
    while (n & ~0x7F) {
        buf[bytes_written++] = (char)((((uint8_t) n) & 0x7F) | 0x80);
        n >>= 7;
    }
    buf[bytes_written++] = (char)n;
    PyObject* s = PyBytes_FromStringAndSize(buf, bytes_written);
    free(buf);
    return s;
}

static PyMethodDef Encoder_methods[] = {
    {"read", (PyCFunction)Encoder_read, METH_VARARGS, ""},
    {"read_long", (PyCFunction)Encoder_read_long, METH_VARARGS, ""},
    {"read_record", (PyCFunction)Encoder_read_record, METH_VARARGS, ""},
    {"set_schema", (PyCFunction)Encoder_set_schema, METH_VARARGS|METH_KEYWORDS, ""},
    {"write", (PyCFunction)Encoder_write, METH_VARARGS, ""},
    {"write_long", (PyCFunction)Encoder_write_long, METH_VARARGS, ""},
    {NULL}  /* Sentinel */
};

PyTypeObject EncoderType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_quickavro.Encoder",                           /* tp_name */
    sizeof(Encoder),                                /* tp_basicsize */
    0,                                              /* tp_itemsize */
    (destructor)Encoder_dealloc,                    /* tp_dealloc */
    0,                                              /* tp_print */
    0,                                              /* tp_getattr */
    0,                                              /* tp_setattr */
    0,                                              /* tp_compare */
    0,                                              /* tp_repr */
    0,                                              /* tp_as_number */
    0,                                              /* tp_as_sequence */
    0,                                              /* tp_as_mapping */
    0,                                              /* tp_hash */
    0,                                              /* tp_call */
    0,                                              /* tp_str */
    0,                                              /* tp_getattro */
    0,                                              /* tp_setattro */
    0,                                              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,       /* tp_flags */
    "Encoder objects",                              /* tp_doc */
    0,                                              /* tp_traverse */
    0,                                              /* tp_clear */
    0,                                              /* tp_richcompare */
    0,                                              /* tp_weaklistoffset */
    0,                                              /* tp_iter */
    0,                                              /* tp_iternext */
    Encoder_methods,                                /* tp_methods */
    0,                                              /* tp_members */
    0,                                              /* tp_getset */
    0,                                              /* tp_base */
    0,                                              /* tp_dict */
    0,                                              /* tp_descr_get */
    0,                                              /* tp_descr_set */
    0,                                              /* tp_dictoffset */
    (initproc)Encoder_init,                         /* tp_init */
    0,                                              /* tp_alloc */
    Encoder_new,                                    /* tp_new */
};
