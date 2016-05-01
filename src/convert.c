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
#include <avro.h>
#include "compat.h"


PyObject* array_to_pylist(avro_value_t* value) {
    size_t record_length;
    int i;
    avro_value_get_size(value, &record_length);
    PyObject* l = PyList_New(record_length);
    for (i=0; i<record_length; i++) {
        avro_value_t field_value;
        avro_value_get_by_index(value, i, &field_value, NULL);
        PyList_SetItem(l, i, avro_to_python(&field_value));
    }
    return l;
}

PyObject* avro_to_python(avro_value_t* value) {
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
            return fixed_to_pystring(value);
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

PyObject* boolean_to_pybool(avro_value_t* value) {
    int t;
    avro_value_get_boolean(value, &t);
    return PyBool_FromLong(t);
}

PyObject* bytes_to_pybytes(avro_value_t* value) {
    unsigned char* buf;
    size_t length;
    avro_value_get_bytes(value, &buf, &length);
    return PyBytes_FromStringAndSize((char*)buf, length);
}

PyObject* double_to_pyfloat(avro_value_t* value) {
    double d;
    avro_value_get_double(value, &d);
    return PyFloat_FromDouble(d);
}

PyObject* enum_to_pystring(avro_value_t* value) {
    int index;
    avro_value_get_enum(value, &index);
    avro_schema_t schema = avro_value_get_schema(value);
    char* name = avro_schema_enum_get(schema, index);
    if (name == NULL) {
        fprintf(stderr, "Enum to pystring failed.\n");
        Py_RETURN_NONE;
    }
    return PyUnicode_FromString(name);
}

PyObject* fixed_to_pystring(avro_value_t* value) {
    unsigned char* buf;
    size_t length;
    avro_value_get_fixed(value, &buf, &length);
    return PyBytes_FromStringAndSize((char*)buf, length);
}

PyObject* float_to_pyfloat(avro_value_t* value) {
    float f;
    avro_value_get_float(value, &f);
    return PyFloat_FromDouble(f);
}

PyObject* int32_to_pylong(avro_value_t* value) {
    int32_t l;
    avro_value_get_int(value, &l);
    return PyLong_FromLong(l);
}

PyObject* int64_to_pylong(avro_value_t* value) {
    int64_t q;
    avro_value_get_long(value, &q);
    return PyLong_FromLong(q);
}

PyObject* map_to_pydict(avro_value_t* value) {
    size_t record_length;
    int i;
    PyObject* d = PyDict_New();
    avro_value_get_size(value, &record_length);
    for (i=0; i<record_length; i++) {
        const char* field_name;
        avro_value_t field_value;
        avro_value_get_by_index(value, i, &field_value, &field_name);
        PyDict_SetItemString(d, field_name, avro_to_python(&field_value));
    }
    return d;
}

PyObject* null_to_pynone(avro_value_t* value) {
    avro_value_get_null(value);
    Py_RETURN_NONE;
}

PyObject* string_to_pystring(avro_value_t* value) {
    char* buf;
    size_t length;
    avro_value_get_string(value, &buf, &length);
    return PyUnicode_FromStringAndSize(buf, length-1);
}

PyObject* union_to_python(avro_value_t *value) {
    avro_value_t v;
    avro_value_get_current_branch(value, &v);
    return avro_to_python(&v);
}
