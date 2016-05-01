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


PyObject* array_to_pylist(avro_value_t* value);
PyObject* avro_to_python(avro_value_t* value);
PyObject* boolean_to_pybool(avro_value_t* value);
PyObject* bytes_to_pybytes(avro_value_t* value);
PyObject* double_to_pyfloat(avro_value_t* value);
PyObject* enum_to_pystring(avro_value_t* value);
PyObject* fixed_to_pystring(avro_value_t* value);
PyObject* float_to_pyfloat(avro_value_t* value);
PyObject* int32_to_pylong(avro_value_t* value);
PyObject* int64_to_pylong(avro_value_t* value);
PyObject* map_to_pydict(avro_value_t* value);
PyObject* null_to_pynone(avro_value_t* value);
PyObject* string_to_pystring(avro_value_t* value);
PyObject* union_to_python(avro_value_t *value);

#ifdef __cplusplus
}
#endif

#endif
