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


PyObject* avro_to_python(avro_value_t* value) {
    avro_type_t value_type = avro_value_get_type(value);
    switch (value_type) {
        case AVRO_STRING:
            return string_to_pystring(value);
        case AVRO_BYTES:
        case AVRO_INT32:
            return int32_to_pylong(value);
        case AVRO_INT64:
            return int64_to_pylong(value);
        case AVRO_FLOAT:
        case AVRO_DOUBLE:
        case AVRO_BOOLEAN:
        case AVRO_NULL:
            Py_RETURN_NONE;
        case AVRO_RECORD:
            return record_to_python(value);
        case AVRO_ENUM:
        case AVRO_FIXED:
        case AVRO_MAP:
        case AVRO_ARRAY:
        case AVRO_UNION:
            return union_to_python(value);
        case AVRO_LINK:
        default:
            fprintf(stderr, "Unhandled Type: %d\n", value_type);
    }
    Py_RETURN_NONE;
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

PyObject* record_to_python(avro_value_t* value) {
    size_t record_length;
    int i;
    avro_schema_t schema = avro_value_get_schema(value);
    avro_value_get_size(value, &record_length);
    PyObject* l = PyList_New(record_length);
    for (i=0; i<record_length; i++) {
        avro_value_t field_value;
        avro_value_get_by_index(value, i, &field_value, NULL);
        PyList_SetItem(l, i, avro_to_python(&field_value));
    }
    return l;
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
