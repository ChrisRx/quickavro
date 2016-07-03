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


static void Encoder_dealloc(Encoder* self) {
    if (self->schema) {
        avro_schema_decref(self->schema);
    }
    if (self->iface) {
        avro_value_iface_decref(self->iface);
    }
    if (self->reader) {
        avro_reader_free(self->reader);
    }
    if (self->writer) {
        avro_writer_free(self->writer);
    }
    if (self->buffer) {
        avro_free(self->buffer, self->buffer_length);
    }

    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject* Encoder_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    Encoder* self;

    self = (Encoder*)type->tp_alloc(type, 0);
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
    int rval;

    if (!PyArg_ParseTuple(args, "s*", &buffer)) {
        Py_RETURN_NONE;
    }
    avro_value_t value;
    avro_reader_memory_set_source(self->reader, buffer.buf, buffer.len);
    avro_generic_value_new(self->iface, &value);
    PyObject* values = PyList_New(0);
    while ((rval = avro_value_read(self->reader, &value)) == 0) {
        PyObject* item = avro_to_python(&value);
        PyList_Append(values, item);
        avro_value_reset(&value);
        Py_DECREF(item);
    }
    avro_value_decref(&value);
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
            PyErr_SetString(PyExc_ValueError, "Varint is too long");
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
    size_t record_size;
    int rval;

    if (!PyArg_ParseTuple(args, "s*", &buffer)) {
        Py_RETURN_NONE;
    }
    avro_value_t value;
    avro_reader_memory_set_source(self->reader, buffer.buf, buffer.len);
    avro_generic_value_new(self->iface, &value);
    rval = avro_value_read(self->reader, &value);
    if (rval != 0) {
        PyErr_Format(PyExc_IOError, "%s", avro_strerror());
        return NULL;
    }
    PyObject* obj = avro_to_python(&value);
    rval = avro_value_sizeof(&value, &record_size);
    if (rval != 0) {
        PyErr_Format(PyExc_IOError, "%s", avro_strerror());
        return NULL;
    }
    avro_value_decref(&value);
    PyBuffer_Release(&buffer);
    return Py_BuildValue("(OO)", obj, PyLong_FromLong(record_size));
}

static PyObject* Encoder_set_schema(Encoder* self, PyObject* args) {
    char* json_str;
    avro_schema_error_t error;

    if (!PyArg_ParseTuple(args, "s", &json_str)) {
        PyErr_SetString(PyExc_ValueError, "Not provided valid arguments");
        return NULL;
    }
    int r = avro_schema_from_json(json_str, 0, &self->schema, &error);
    if (r != 0 || self->schema == NULL) {
        PyErr_Format(PyExc_IOError, "%s", avro_strerror());
        return NULL;
    }
    self->iface = avro_generic_class_from_schema(self->schema);
    return Py_BuildValue("i", 0);
}

static PyObject* Encoder_write(Encoder* self, PyObject* args) {
    PyObject* obj;
    int rval;

    if (!PyArg_ParseTuple(args, "O", &obj)) {
        Py_RETURN_NONE;
    }
    avro_value_t value;
    avro_generic_value_new(self->iface, &value);
    rval = python_to_avro(obj, &value);
    if (rval == 0) {
        rval = avro_value_write(self->writer, &value);
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
        rval = avro_value_write(self->writer, &value);
    }

    if (rval) {
        avro_value_decref(&value);
        return NULL;
    }
    PyObject* s = PyBytes_FromStringAndSize(self->buffer, avro_writer_tell(self->writer));
    avro_writer_reset(self->writer);
    avro_value_decref(&value);
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
    {"set_schema", (PyCFunction)Encoder_set_schema, METH_VARARGS, ""},
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
