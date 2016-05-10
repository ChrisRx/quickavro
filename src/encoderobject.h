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

#ifndef __ENCODEROBJECT_H
#define __ENCODEROBJECT_H

#ifdef __cplusplus
extern "C" {
#endif

#include <Python.h>
#include <avro.h>


typedef struct {
    PyObject_HEAD
    avro_schema_t schema;
    avro_value_iface_t* iface;
    avro_reader_t reader;
    avro_writer_t writer;

    char* buffer;
    size_t buffer_length;
} Encoder;

extern PyTypeObject EncoderType;

#ifdef __cplusplus
}
#endif

#endif
