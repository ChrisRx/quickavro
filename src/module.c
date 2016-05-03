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

#include <Python.h>
#include "compat.h"

#include "readerobject.h"
#include "writerobject.h"


#ifdef __cplusplus
extern "C" {
#endif 


static PyMethodDef module_methods[] = {
    {NULL}  /* Sentinel */
};

MOD_INIT(_quickavro)
{
    PyObject* m;

    if (PyType_Ready(&ReaderType) < 0) {
        return MOD_ERROR_VAL;
    }

    if (PyType_Ready(&WriterType) < 0) {
        return MOD_ERROR_VAL;
    }

    MOD_DEF(m, "_quickavro", "", module_methods);

    if (m == NULL) {
        return MOD_ERROR_VAL;
    }

    Py_INCREF(&ReaderType);
    PyModule_AddObject(m, "Reader", (PyObject*)&ReaderType);

    Py_INCREF(&WriterType);
    PyModule_AddObject(m, "Writer", (PyObject*)&WriterType);

    return MOD_SUCCESS_VAL(m);
}


#ifdef __cplusplus
}
#endif
