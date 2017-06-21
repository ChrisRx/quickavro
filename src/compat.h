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

#ifndef __COMPAT_H
#define __COMPAT_H

#ifndef PyVarObject_HEAD_INIT
    #define PyVarObject_HEAD_INIT(type, size) \
        PyObject_HEAD_INIT(type) size,
#endif

#ifndef Py_TYPE
    #define Py_TYPE(ob) (((PyObject*)(ob))->ob_type)
#endif

#if PY_MAJOR_VERSION >= 3
  #define MOD_ERROR_VAL NULL
  #define MOD_SUCCESS_VAL(val) val
  #define MOD_INIT(name) PyMODINIT_FUNC PyInit_##name(void)
  #define MOD_DEF(ob, name, doc, methods) \
          static struct PyModuleDef moduledef = { \
            PyModuleDef_HEAD_INIT, name, doc, -1, methods, }; \
          ob = PyModule_Create(&moduledef);

  #define Py_TPFLAGS_HAVE_ITER 0
  #define MOD_ERROR_VAL NULL

  #define TEXT_T Py_UNICODE
  #define _PyLong_Check(ob) PyLong_Check(ob)
  #define _PyUnicode_CheckExact(ob) PyUnicode_CheckExact(ob)
#else
  #define PyUnicode_AsUTF8 PyString_AsString
  #define PyNumber_FloorDivide PyNumber_Divide
  #define PyBytes_FromStringAndSize PyString_FromStringAndSize
  #define _PyLong_Check(ob) (PyLong_Check(ob) || PyInt_Check(ob))
  #define _PyUnicode_CheckExact(ob) (PyString_CheckExact(ob) || PyUnicode_CheckExact(ob))

  #define MOD_ERROR_VAL
  #define MOD_SUCCESS_VAL(val)
  #define MOD_INIT(name) void init##name(void)
  #define MOD_DEF(ob, name, doc, methods) \
          ob = Py_InitModule3(name, methods, doc);
#endif    

#endif
