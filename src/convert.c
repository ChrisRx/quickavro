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

#include "convert.h"
#include "compat.h"
#include <avro.h>


int avro_error(int rval) {
    if (rval != 0) {
        PyErr_Format(PyExc_IOError, "%s", avro_strerror());
    }
    return rval;
}

static const char* lookup(const char* key) {
    size_t i;
    size_t table_length = tabledef_size(p2a);
    for (i=0; i<table_length; i++) {
        if (strcmp(key, p2a[i].python_type) == 0) {
            return p2a[i].avro_type;
        }
    }
    return key;
}

static PyObject* array_to_pylist(avro_value_t* value) {
    size_t record_length;
    size_t i;
    avro_value_get_size(value, &record_length);
    PyObject* l = PyList_New(record_length);
    for (i=0; i<record_length; i++) {
        avro_value_t field_value;
        avro_value_get_by_index(value, i, &field_value, NULL);
        PyList_SetItem(l, i, avro_to_python(&field_value));
    }
    return l;
}

static PyObject* boolean_to_pybool(avro_value_t* value) {
    int t;
    avro_value_get_boolean(value, &t);
    return PyBool_FromLong(t);
}

static PyObject* bytes_to_pybytes(avro_value_t* value) {
    const void* buf;
    size_t length;
    avro_value_get_bytes(value, &buf, &length);
    return PyBytes_FromStringAndSize((char*)buf, length);
}

static PyObject* double_to_pyfloat(avro_value_t* value) {
    double d;
    avro_value_get_double(value, &d);
    return PyFloat_FromDouble(d);
}

static PyObject* enum_to_pystring(avro_value_t* value) {
    // TODO: Return quickavro enum object
    int index;
    avro_value_get_enum(value, &index);
    avro_schema_t schema = avro_value_get_schema(value);
    const char* name = avro_schema_enum_get(schema, index);
    if (name == NULL) {
        fprintf(stderr, "Enum to pystring failed.\n");
        Py_RETURN_NONE;
    }
    return PyUnicode_FromString(name);
}

static PyObject* fixed_to_pybytes(avro_value_t* value) {
    const void* buf;
    size_t length;
    avro_value_get_fixed(value, &buf, &length);
    return PyBytes_FromStringAndSize((char*)buf, length);
}

static PyObject* float_to_pyfloat(avro_value_t* value) {
    float f;
    avro_value_get_float(value, &f);
    return PyFloat_FromDouble(f);
}

static PyObject* int32_to_pylong(avro_value_t* value) {
    int32_t l;
    avro_value_get_int(value, &l);
    return PyLong_FromLong(l);
}

static PyObject* int64_to_pylong(avro_value_t* value) {
    int64_t q;
    avro_value_get_long(value, &q);
    return PyLong_FromLong(q);
}

static PyObject* map_to_pydict(avro_value_t* value) {
    PyObject* item;
    size_t record_length;
    size_t i;
    PyObject* d = PyDict_New();
    avro_value_get_size(value, &record_length);
    for (i=0; i<record_length; i++) {
        const char* field_name;
        avro_value_t field_value;
        avro_value_get_by_index(value, i, &field_value, &field_name);
        item = avro_to_python(&field_value);
        PyDict_SetItemString(d, field_name, item);
        Py_DECREF(item);
    }
    return d;
}

static PyObject* null_to_pynone(avro_value_t* value) {
    avro_value_get_null(value);
    Py_RETURN_NONE;
}

static PyObject* string_to_pystring(avro_value_t* value) {
    const char* buf;
    size_t length;
    avro_value_get_string(value, &buf, &length);
    return PyUnicode_FromStringAndSize(buf, length-1);
}

static PyObject* union_to_python(avro_value_t *value) {
    avro_value_t v;
    avro_value_get_current_branch(value, &v);
    return avro_to_python(&v);
}

static int pybool_to_boolean(PyObject* obj, avro_value_t* value) {
    int t = PyObject_IsTrue(obj);
    return avro_error(avro_value_set_boolean(value, t));
}

static int pybytes_to_bytes(PyObject* obj, avro_value_t* value) {
    char* buf;
    Py_ssize_t length;
    if (PyBytes_Check(obj)) {
        PyBytes_AsStringAndSize(obj, &buf, &length);
    } else {
        PyErr_SetString(PyExc_Exception, "Expected bytes, given str");
        return -1;
    }
    return avro_error(avro_value_set_bytes(value, buf, length));
}

static int pydict_to_map(PyObject* obj, avro_value_t* dest) {
    PyObject *key, *value;
    Py_ssize_t pos = 0;
    int rval = 0;

    while (PyDict_Next(obj, &pos, &key, &value)) {
        avro_value_t v;

        const char* k = PyUnicode_AsUTF8(key);
        rval = avro_value_add(dest, k, &v, NULL, NULL);
        if (rval == 0) {
            rval = python_to_avro(value, &v);
        }
    }
    return rval;
}

static int pyfloat_to_double(PyObject* obj, avro_value_t* value) {
    long l = PyFloat_AsDouble(obj);
    return avro_error(avro_value_set_double(value, l));
}

static int pyfloat_to_float(PyObject* obj, avro_value_t* value) {
    long l = PyFloat_AsDouble(obj);
    return avro_error(avro_value_set_float(value, l));
}

static int pylist_to_array(PyObject* obj, avro_value_t* dest) {
    int rval = 0;
    Py_ssize_t i;
    Py_ssize_t array_length = PySequence_Size(obj);
    for (i=0; i<array_length; i++) {
        PyObject* item = PySequence_GetItem(obj, i);
        avro_value_t v;
        avro_value_append(dest, &v, NULL);
        rval = python_to_avro(item, &v);
        Py_DECREF(item);
        if (rval) {
            return rval;
        }
    }
    return 0;
}

static int pylong_to_int32(PyObject* obj, avro_value_t* value) {
    long l = PyLong_AsLong(obj);
    return avro_error(avro_value_set_int(value, l));
}

static int pylong_to_int64(PyObject* obj, avro_value_t* value) {
    long long q = PyLong_AsLongLong(obj);
    return avro_error(avro_value_set_long(value, q));
}

static int pynone_to_null(PyObject* obj, avro_value_t* value) {
    return avro_error(avro_value_set_null(value));
}

static int pystring_to_enum(PyObject* obj, avro_value_t* value) {
    int index;
    const char* symbol_name;
    avro_schema_t schema = avro_value_get_schema(value);
    if (_PyUnicode_CheckExact(obj)) {
        symbol_name = PyUnicode_AsUTF8(obj);
    } else if (_PyLong_Check(obj)) {
        symbol_name = avro_schema_enum_get(schema, PyLong_AsLong(obj));
    } else {
        PyObject* s = PyObject_GetAttrString(obj, "value");
        symbol_name = PyUnicode_AsUTF8(s);
        Py_DECREF(s);
    }
    index = avro_schema_enum_get_by_name(schema, symbol_name);
    return avro_error(avro_value_set_enum(value, index));
}

static int pybytes_to_fixed(PyObject* obj, avro_value_t* value) {
    int status;
    char* buf;
    Py_ssize_t length;
    if (PyBytes_Check(obj)) {
        PyBytes_AsStringAndSize(obj, &buf, &length);
    } else {
        PyErr_SetString(PyExc_Exception, "Expected bytes, given str");
        return -1;
    }
    int rval = avro_error(avro_value_set_fixed(value, buf, length));
    return rval;
}

static int pystring_to_string(PyObject* obj, avro_value_t* value) {
    // Switch to PyUnicode_AsUTF8AndSize and add macros for compat with
    // Python versions before 3.3
    int status;
    char* buf;
    Py_ssize_t length;
    if (PyUnicode_Check(obj)) {
        PyObject* s = PyUnicode_AsUTF8String(obj);
        status = PyBytes_AsStringAndSize(s, &buf, &length);
        if (!status) {
            //
        }
        Py_DECREF(s);
    } else {
        status = PyBytes_AsStringAndSize(obj, &buf, &length);
        if (!status) {
            //
        }
    }
    int rval = avro_error(avro_value_set_string_len(value, buf, length+1));
    return rval;
}

static int python_to_record(PyObject* obj, avro_value_t* value) {
    size_t record_length;
    size_t i;
    int rval;
    avro_value_get_size(value, &record_length);
    for (i=0; i<record_length; i++) {
        const char* field_name;
        avro_value_t field_value;
        avro_value_get_by_index(value, i, &field_value, &field_name);
        PyObject* v = PyDict_GetItemString(obj, field_name);
        if (v == NULL) {
            PyErr_Clear();
            v = Py_None;
        }
        rval = python_to_avro(v, &field_value);
        if (rval) {
            // const char* record_name = avro_schema_name(avro_value_get_schema(value));
            return rval;
        }
    }
    return 0;
}

static int python_to_union(PyObject* obj, avro_value_t* value) {
    int branch_index;
    avro_value_t branch;
    avro_schema_t schema;
    avro_schema_t branch_schema;
    const char* name;

    schema = avro_value_get_schema(value);

    if (PyDict_Check(obj)) {
        branch_index = validate(obj, schema);
    } else if (_PyUnicode_CheckExact(obj)) {
        branch_index = validate(obj, schema);
    } else if (PyBytes_CheckExact(obj)) {
        branch_index = validate(obj, schema);
    } else if (_PyLong_Check(obj)) {
        branch_index = validate(obj, schema);
    } else {
        if (strcmp(Py_TYPE(obj)->tp_name, "enum") == 0) {
            PyObject* n = PyObject_GetAttrString(obj, "name");
            name = PyUnicode_AsUTF8(n);
        } else if (obj == Py_None) {
            name = "null";
        } else {
            name = lookup(Py_TYPE(obj)->tp_name);
        }

        branch_schema = avro_schema_union_branch_by_name(schema, &branch_index, name);
        if (branch_schema == NULL) {
            return -1;
        }
    }
    avro_value_set_branch(value, branch_index, &branch);
    return python_to_avro(obj, &branch);
}

static int validate_array(PyObject* obj, avro_schema_t schema) {
    avro_schema_t subschema;
    Py_ssize_t i;
    if (!PyList_Check(obj)) {
        return -1;
    }
    subschema = avro_schema_array_items(schema);
    for (i = 0; i < PyList_GET_SIZE(obj); i++) {
        if (validate(PyList_GET_ITEM(obj, i), subschema) < 0) {
            return -1;
        }
    }
    return 0;
}

static int validate_enum(PyObject* obj, avro_schema_t schema) {
    const char* symbol_name;

    if (obj == Py_None) {
        return -1;
    } else if (_PyUnicode_CheckExact(obj)) {
        symbol_name = PyUnicode_AsUTF8(obj);
    } else if (_PyLong_Check(obj)) {
        symbol_name = avro_schema_enum_get(schema, PyLong_AsLong(obj));
    } else {
        PyObject* s = PyObject_GetAttrString(obj, "value");
        symbol_name = PyUnicode_AsUTF8(obj);
        Py_DECREF(s);
    }
    return avro_schema_enum_get_by_name(schema, symbol_name);
}

static int validate_map(PyObject* obj, avro_schema_t schema) {
    PyObject *key, *value;
    Py_ssize_t pos = 0;
    avro_schema_t subschema;

    if (!PyDict_Check(obj)) {
        return -1;
    }

    subschema = avro_schema_map_values(schema);

    while (PyDict_Next(obj, &pos, &key, &value)) {
        if (!_PyUnicode_CheckExact(key) || validate(value, subschema) < 0) {
            return -1;
        }
    }
    return 0;
}

static int validate_record(PyObject* obj, avro_schema_t schema) {
    size_t record_size;
    size_t i;
    PyObject* v;
    avro_schema_t subschema;

    if (!PyDict_Check(obj)) {
        return -1;
    }

    record_size = avro_schema_record_size(schema);
    for (i = 0; i < record_size; i++) {
        v = PyDict_GetItemString(obj, avro_schema_record_field_name(schema, i));
        if (v == NULL) {
            v = Py_None;
        }
        subschema = avro_schema_record_field_get_by_index(schema, i);
        if (validate(v, subschema) < 0) {
            return -1;
        }
    }
    return 0;
}

static int validate_union(PyObject* obj, avro_schema_t schema) {
    size_t union_size;
    size_t i;
    union_size = avro_schema_union_size(schema);
    for (i = 0; i < union_size; i++) {
        if (validate(obj, avro_schema_union_branch(schema, i)) >= 0) {
            return i;
        }
    }
    return -1;
}

PyObject* avro_to_python(avro_value_t* value) {
    // The Avro spec calls for defaults to only be applied on read. If
    // defaults are handled they *could* be done here with a function
    // that wraps the type conversion functions checking for NoneType
    // and returning the default value when NoneType is encountered.
    // This is made difficult since the avro_schema_t does not contain
    // this information currently. The other option would be to make
    // a Python closure that returns a function that applies defaults.
    // This would be light weight and would fit with the general
    // design of quickavro to be more expressive in Python and let C
    // just do the heavy lifting.
    avro_type_t value_type = avro_value_get_type(value);
    switch (value_type) {
        case AVRO_STRING:
            return string_to_pystring(value);
        case AVRO_BYTES:
            return bytes_to_pybytes(value);
        case AVRO_INT32:
            return int32_to_pylong(value);
        case AVRO_INT64:
            return int64_to_pylong(value);
        case AVRO_FLOAT:
            return float_to_pyfloat(value);
        case AVRO_DOUBLE:
            return double_to_pyfloat(value);
        case AVRO_BOOLEAN:
            return boolean_to_pybool(value);
        case AVRO_NULL:
            return null_to_pynone(value);
        case AVRO_RECORD:
            return map_to_pydict(value);
        case AVRO_ENUM:
            return enum_to_pystring(value);
        case AVRO_FIXED:
            return fixed_to_pybytes(value);
        case AVRO_MAP:
            return map_to_pydict(value);
        case AVRO_ARRAY:
            return array_to_pylist(value);
        case AVRO_UNION:
            return union_to_python(value);
        case AVRO_LINK:
        default:
            fprintf(stderr, "Unhandled Type: %d\n", value_type);
    }
    Py_RETURN_NONE;
}

int python_to_avro(PyObject* obj, avro_value_t* value) {
    avro_type_t value_type = avro_value_get_type(value);
    switch (value_type) {
        case AVRO_STRING:
            return pystring_to_string(obj, value);
        case AVRO_BYTES:
            return pybytes_to_bytes(obj, value);
        case AVRO_INT32:
            return pylong_to_int32(obj, value);
        case AVRO_INT64:
            return pylong_to_int64(obj, value);
        case AVRO_FLOAT:
            return pyfloat_to_float(obj, value);
        case AVRO_DOUBLE:
            return pyfloat_to_double(obj, value);
        case AVRO_BOOLEAN:
            return pybool_to_boolean(obj, value);
        case AVRO_NULL:
            return pynone_to_null(obj, value);
        case AVRO_RECORD:
            return python_to_record(obj, value);
        case AVRO_ENUM:
            return pystring_to_enum(obj, value);
        case AVRO_FIXED:
            return pybytes_to_fixed(obj, value);
        case AVRO_MAP:
            return pydict_to_map(obj, value);
        case AVRO_ARRAY:
            return pylist_to_array(obj, value);
        case AVRO_UNION:
            return python_to_union(obj, value);
        case AVRO_LINK:
        default:
            fprintf(stderr, "Unhandled Type: %d\n", value_type);
    }
    return 0;
}

int validate(PyObject* obj, avro_schema_t schema) {
    switch(schema->type) {
        case AVRO_STRING:
            return _PyUnicode_CheckExact(obj) ? 0 : -1;
        case AVRO_BYTES:
            return PyBytes_Check(obj) ? 0 : -1;
        case AVRO_INT32:
        case AVRO_INT64:
            return _PyLong_Check(obj) ? 0 : -1;
        case AVRO_FLOAT:
        case AVRO_DOUBLE:
            return (_PyLong_Check(obj) || PyFloat_Check(obj)) ? 0 : -1;
        case AVRO_BOOLEAN:
            return PyBool_Check(obj) ? 0 : -1;
        case AVRO_NULL:
            return obj == Py_None ? 0 : -1;
        case AVRO_RECORD:
            return validate_record(obj, schema);
        case AVRO_ENUM:
            return validate_enum(obj, schema);
        case AVRO_FIXED:
            return PyBytes_Check(obj) ? 0 : -1;
        case AVRO_MAP:
            return validate_map(obj, schema);
        case AVRO_ARRAY:
            return validate_array(obj, schema);
        case AVRO_UNION:
            return validate_union(obj, schema);
        case AVRO_LINK:
            return validate(obj, avro_schema_link_target(schema));
        default:
            return -1;
    }
}
