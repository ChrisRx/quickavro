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

#include "writerobject.h"
#include "compat.h"
#include "convert.h"
#include "quickavro.h"
#include <avro.h>


static void Writer_dealloc(Writer* self) {
    if (self->schema) {
        avro_schema_decref(self->schema);
    }
    if (self->iface) {
        avro_value_iface_decref(self->iface);
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject* Writer_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    Writer* self;

    self = (Writer*)type->tp_alloc(type, 0);
    return (PyObject*)self;
}

static int Writer_init(Writer* self, PyObject* args, PyObject* kwds) {
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
    self->buffer = (char*)avro_malloc(INITIAL_BUFFER_SIZE);
    self->buffer_length = INITIAL_BUFFER_SIZE;
    self->writer = avro_writer_memory(self->buffer, self->buffer_length);
    return 0;
}

static PyObject* Writer_write(Writer* self, PyObject* args) {
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
        if (self->buffer) {
            PyErr_NoMemory();
            return NULL;
        }
        self->buffer_length = new_size;
        avro_writer_memory_set_dest(self->writer, self->buffer, self->buffer_length);
        rval = avro_value_write(self->writer, &value);
    }

    if (rval) {
        avro_value_decref(&value);
        Py_RETURN_NONE;
    }
    PyObject* s = PyBytes_FromStringAndSize(self->buffer, avro_writer_tell(self->writer));
    avro_writer_reset(self->writer);
    avro_value_decref(&value);
    return s;
}

static PyObject* Writer_write_long(Writer* self, PyObject* args) {
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

static PyMethodDef Writer_methods[] = {
    {"write", (PyCFunction)Writer_write, METH_VARARGS, ""},
    {"write_long", (PyCFunction)Writer_write_long, METH_VARARGS, ""},
    {NULL}  /* Sentinel */
};

PyTypeObject WriterType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_quickavro.Writer",                            /* tp_name */
    sizeof(Writer),                                 /* tp_basicsize */
    0,                                              /* tp_itemsize */
    (destructor)Writer_dealloc,                     /* tp_dealloc */
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
    "Writer objects",                               /* tp_doc */
    0,                                              /* tp_traverse */
    0,                                              /* tp_clear */
    0,                                              /* tp_richcompare */
    0,                                              /* tp_weaklistoffset */
    0,                                              /* tp_iter */
    0,                                              /* tp_iternext */
    Writer_methods,                                 /* tp_methods */
    0,                                              /* tp_members */
    0,                                              /* tp_getset */
    0,                                              /* tp_base */
    0,                                              /* tp_dict */
    0,                                              /* tp_descr_get */
    0,                                              /* tp_descr_set */
    0,                                              /* tp_dictoffset */
    (initproc)Writer_init,                          /* tp_init */
    0,                                              /* tp_alloc */
    Writer_new,                                     /* tp_new */
};
