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

#include "readerobject.h"
#include "compat.h"
#include "convert.h"
#include "quickavro.h"
#include <avro.h>


static void Reader_dealloc(Reader* self) {
    if (self->schema) {
        avro_schema_decref(self->schema);
    }
    if (self->iface) {
        avro_value_iface_decref(self->iface);
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject* Reader_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    Reader* self;

    self = (Reader*)type->tp_alloc(type, 0);
    return (PyObject*)self;
}

static int Reader_init(Reader* self, PyObject* args, PyObject* kwds) {
    char* json_str;
    avro_schema_error_t error;

    if (!PyArg_ParseTuple(args, "s", &json_str)) {
        PyErr_SetString(PyExc_ValueError, "Not provided valid arguments");
        return -1;
    }
    int r = avro_schema_from_json(json_str, 0, &self->schema, &error);
    if (r != 0 || self->schema == NULL) {
        printf("Oh no, schema no work\n");
        return -1;
    }
    self->iface = avro_generic_class_from_schema(self->schema);
    self->reader = avro_reader_memory(NULL, 0);
    return 0;
}

static PyObject* Reader_read(Reader* self, PyObject* args) {
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
        PyList_Append(values, avro_to_python(&value));
        avro_value_reset(&value);
    }
    avro_value_decref(&value);
    PyBuffer_Release(&buffer);
    return values;
}

static PyObject* Reader_read_long(Reader* self, PyObject* args) {
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

static PyObject* Reader_read_record(Reader* self, PyObject* args) {
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

static PyMethodDef Reader_methods[] = {
    {"read", (PyCFunction)Reader_read, METH_VARARGS, ""},
    {"read_long", (PyCFunction)Reader_read_long, METH_VARARGS, ""},
    {"read_record", (PyCFunction)Reader_read_record, METH_VARARGS, ""},
    {NULL}  /* Sentinel */
};

PyTypeObject ReaderType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_quickavro.Reader",                            /* tp_name */
    sizeof(Reader),                                 /* tp_basicsize */
    0,                                              /* tp_itemsize */
    (destructor)Reader_dealloc,                     /* tp_dealloc */
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
    "Reader objects",                               /* tp_doc */
    0,                                              /* tp_traverse */
    0,                                              /* tp_clear */
    0,                                              /* tp_richcompare */
    0,                                              /* tp_weaklistoffset */
    0,                                              /* tp_iter */
    0,                                              /* tp_iternext */
    Reader_methods,                                 /* tp_methods */
    0,                                              /* tp_members */
    0,                                              /* tp_getset */
    0,                                              /* tp_base */
    0,                                              /* tp_dict */
    0,                                              /* tp_descr_get */
    0,                                              /* tp_descr_set */
    0,                                              /* tp_dictoffset */
    (initproc)Reader_init,                          /* tp_init */
    0,                                              /* tp_alloc */
    Reader_new,                                     /* tp_new */
};
