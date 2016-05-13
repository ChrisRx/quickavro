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

#include "snappyobject.h"
#include "compat.h"
#include <snappy-c.h>


static void Snappy_dealloc(Snappy* self) {
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject* Snappy_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    Snappy* self;

    self = (Snappy*)type->tp_alloc(type, 0);
    return (PyObject*)self;
}

static int Snappy_init(Snappy* self, PyObject* args, PyObject* kwds) {
    return 0;
}

static PyObject* Snappy_compress(Snappy* self, PyObject* args) {
    Py_buffer buffer;
    PyObject* result;

    if (!PyArg_ParseTuple(args, "s*", &buffer)) {
        Py_RETURN_NONE;
    }

    size_t output_length = snappy_max_compressed_length(buffer.len);
    char* output = (char*)malloc(output_length);
    if (snappy_compress(buffer.buf, buffer.len, output, &output_length) == SNAPPY_OK) {
        result = PyBytes_FromStringAndSize(output, output_length);
    } else {
        Py_INCREF(Py_None);
        result = Py_None;
    }
    free(output);
    PyBuffer_Release(&buffer);
    return result;
}

static PyObject* Snappy_uncompress(Snappy* self, PyObject* args) {
    Py_buffer buffer;
    PyObject* result;

    if (!PyArg_ParseTuple(args, "s*", &buffer)) {
        Py_RETURN_NONE;
    }
    size_t output_length;
    if (snappy_uncompressed_length(buffer.buf, buffer.len, &output_length) != SNAPPY_OK) {
        Py_RETURN_NONE;
    }
    char* output = (char*)malloc(output_length);
    if (snappy_uncompress(buffer.buf, buffer.len, output, &output_length) == SNAPPY_OK) {
        result = PyBytes_FromStringAndSize(output, output_length);
    } else {
        Py_INCREF(Py_None);
        result = Py_None;
    }
    free(output);
    PyBuffer_Release(&buffer);
    return result;
}

static PyObject* Snappy_validate(Snappy* self, PyObject* args) {
    Py_buffer buffer;

    if (!PyArg_ParseTuple(args, "s*", &buffer)) {
        Py_RETURN_NONE;
    }
    if (snappy_validate_compressed_buffer(buffer.buf, buffer.len) == SNAPPY_OK) {
        Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

static PyMethodDef Snappy_methods[] = {
    {"compress", (PyCFunction)Snappy_compress, METH_VARARGS|METH_CLASS, ""},
    {"uncompress", (PyCFunction)Snappy_uncompress, METH_VARARGS|METH_CLASS, ""},
    {"validate", (PyCFunction)Snappy_validate, METH_VARARGS|METH_CLASS, ""},
    {NULL}  /* Sentinel */
};

PyTypeObject SnappyType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_quickavro.Snappy",                            /* tp_name */
    sizeof(Snappy),                                 /* tp_basicsize */
    0,                                              /* tp_itemsize */
    (destructor)Snappy_dealloc,                     /* tp_dealloc */
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
    "Snappy objects",                               /* tp_doc */
    0,                                              /* tp_traverse */
    0,                                              /* tp_clear */
    0,                                              /* tp_richcompare */
    0,                                              /* tp_weaklistoffset */
    0,                                              /* tp_iter */
    0,                                              /* tp_iternext */
    Snappy_methods,                                 /* tp_methods */
    0,                                              /* tp_members */
    0,                                              /* tp_getset */
    0,                                              /* tp_base */
    0,                                              /* tp_dict */
    0,                                              /* tp_descr_get */
    0,                                              /* tp_descr_set */
    0,                                              /* tp_dictoffset */
    (initproc)Snappy_init,                          /* tp_init */
    0,                                              /* tp_alloc */
    Snappy_new,                                     /* tp_new */
};
