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

#ifndef __CONVERT_H
#define __CONVERT_H

#ifdef __cplusplus
extern "C" {
#endif

#include <Python.h>
#include <avro.h>


#define tabledef_size(x) (sizeof(x)/sizeof((x)[0]))

typedef struct {
    const char* python_type;
    const char* avro_type;
} tabledef;

static const tabledef p2a[] = {
    {"int", "int"},
    {"long", "long"},
    {"str", "string"},
    {"unicode", "string"},
    {"NoneType", "null"},
    {"bool", "boolean"},
    {"list", "array"},
    {NULL}
};

int avro_error(int rval);
int python_to_avro(PyObject* obj, avro_value_t* value);
PyObject* avro_to_python(avro_value_t* value);
int validate(PyObject* obj, avro_schema_t schema);

#ifdef __cplusplus
}
#endif

#endif
