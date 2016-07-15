# -*- coding: utf-8 -*-

import os
import sys
import re
import tarfile
import glob

import pip
from setuptools import setup, Extension, find_packages
from distutils.ccompiler import new_compiler


WIN = sys.platform.startswith('win')
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if not PY3:
    FileNotFoundError = (IOError, OSError)

STATIC_BUILD_DIR = "build/static"
STATIC_LIB_NAME = "quickavro"
if WIN:
    STATIC_LIB = "{0}/{1}.lib".format(STATIC_BUILD_DIR, STATIC_LIB_NAME)
else:
    STATIC_LIB = "{0}/lib{1}.a".format(STATIC_BUILD_DIR, STATIC_LIB_NAME)


def exists(path):
    if os.path.isdir(path):
        return True
    try:
        with open(path):
            return True
    except (OSError, IOError):
        return False

def get_version():
    version_regex = re.compile(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', re.MULTILINE)
    with open('quickavro/__init__.py', 'r') as f:
        return version_regex.search(f.read()).group(1)

def is_64bit():
    if sys.maxsize > 2**32:
        return True
    return False


class StaticCompiler(object):
    name = None
    version = None
    url = None

    include_dirs = []
    source_dir = None
    excluded = []
    sources = []
    depends = []
    libraries = []

    extra_compile_args = []

    def __init__(self):
        self.c = new_compiler()
        self.include_dirs.append(os.path.join(os.getcwd(), "src"))
        if WIN:
            self.default_compile_args = [
                '-D_WIN32',
                '-D_CRT_SECURE_NO_WARNINGS',
                '-DWIN32',
                '-DNDEBUG',
                '-D_WINDOWS',
                '-D__x86_64__',
                '-D__i386__',
            ]
        else:
            self.default_compile_args = ['-O3', '-fPIC', '-g', '-Wall', '-Wfatal-errors']
        if not exists(STATIC_BUILD_DIR):
            os.makedirs(STATIC_BUILD_DIR)
        self.setup()

    def compile(self, force=False):
        if exists(os.path.join(STATIC_BUILD_DIR, self.static_lib_name)) and not force:
            return
        sys.stderr.write("Compiling {0} to static library ...\n".format(self.name))
        sys.stderr.write("="*32)
        sys.stderr.write("\n")
        self.sources = []
        for ext in {'c', 'cc'}:
            self.sources.extend(glob.glob("{0}/*.{1}".format(self.source_dir, ext)))
        self.depends = []
        for ext in {'h', 'hpp'}:
            self.depends.extend(glob.glob("{0}/*.{1}".format(self.source_dir, ext)))
        for exclude in self.excluded:
            matches = [s for s in self.sources if exclude in s]
            if matches:
                for match in matches:
                    self.sources.remove(match)
        objs = self.c.compile(self.sources,
            include_dirs=self.include_dirs,
            extra_preargs=self.default_compile_args + self.extra_compile_args,
            depends=self.depends
        )
        if self.libraries:
            for lib in self.libraries:
                o = glob.glob("{0}/*.o".format(lib.source_dir))
                objs.extend(o)

        self.c.create_static_lib(objs, self.name.lower(), output_dir=STATIC_BUILD_DIR)
        sys.stderr.write("\n")
        return objs

    def setup(self):
        pass

    @property
    def static_lib_name(self):
        if WIN:
            return "{0}.lib".format(self.name.lower())
        else:
            return "lib{0}.a".format(self.name.lower())

    @property
    def static_library(self):
        return os.path.join(STATIC_BUILD_DIR, self.static_lib_name)


class Jansson(StaticCompiler):
    name = "Jansson"
    version = "2.7"
    include_dirs = [
        "vendor",
        "vendor/jansson/src",
    ]
    source_dir = "vendor/jansson/src"
    if WIN and PY2:
        extra_compile_args = ['-DHAVE_STDINT_H', '-DJSON_INLINE=__inline']
    else:
        extra_compile_args = ['-DHAVE_STDINT_H', '-DJSON_INLINE=inline']


class Snappy(StaticCompiler):
    name = "Snappy"
    if WIN:
        version = "1.1.1.8"
        include_dirs = [
            "vendor",
            "vendor/snappy-windows/src",
        ]
        source_dir = "vendor/snappy-windows/src"
    else:
        version = "1.1.3"
        include_dirs = [
            "vendor/snappy/src"
        ]
        source_dir = "vendor/snappy/src"
    excluded = [
        "snappy-test.cc",
        "snappy_unittest.cc",
    ]
    extra_compile_args = ['-DSNAPPY_STATIC']


class AvroC(StaticCompiler):
    name = "Avro"
    version = "1.8.0"
    include_dirs = [
        "vendor/avro/src",
        "vendor/avro/src/avro",
    ]
    if not WIN:
        excluded = ["generic.cc"]
    include_dirs.extend(Jansson.include_dirs)
    libraries = [Jansson]
    source_dir = "vendor/avro/src"
    extra_compile_args = ['-DHAVE_STDINT_H', '-DJSON_INLINE=inline']


def compile_ext():
    force = True if '--force' in sys.argv else False
    libs = [Snappy(), Jansson(), AvroC()]
    for lib in libs:
        lib.compile(force)
    include_dirs = [
        os.path.join(os.getcwd(), "src"),
    ]
    libraries = []
    library_dirs = []
    macros = []
    linker_flags = []
    extra_compile_args = []
    sources = [
        'src/convert.c',
        'src/encoderobject.c',
        'src/snappyobject.c',
        'src/module.c',
    ]
    depends = [
        'src/compat.h',
        'src/convert.h',
        'src/encoderobject.h',
        'src/snappyobject.h',
        "src/quickavro.h",
    ]
    for lib in libs:
        include_dirs += lib.include_dirs
    if WIN:
        macros.append(('_WIN32', 1))
        macros.append(('SNAPPY_STATIC', 1))
    else:
        libraries.append('stdc++')
        extra_compile_args.append('-Wfatal-errors')
        linker_flags.append('-shared')
        linker_flags.append('-Wl,--export-dynamic')
    return Extension(
        "_quickavro",
        language="c",
        extra_compile_args=extra_compile_args,
        library_dirs=library_dirs,
        libraries=libraries,
        include_dirs=include_dirs,
        define_macros=macros,
        sources=sources,
        depends=depends,
        extra_objects=[lib.static_library for lib in libs]
    )


if __name__ == '__main__':
    setup(
        name="quickavro",
        version=get_version(),
        description="Very fast Avro library for Python.",
        long_description=open("docs/README.rst").read(),
        author="Chris Marshall",
        license="Apache 2.0",
        url="https://github.com/ChrisRx/quickavro",
        packages=find_packages(exclude=['tests*']),
        ext_modules=[
            compile_ext()
        ],
        entry_points={
            'console_scripts': [
                'quickavro = quickavro.__main__:main'
            ]
        },
        zip_safe=False,
        package_dir={'quickavro': 'quickavro'},
        install_requires=[
        ],
        extras_require={
        },
        setup_requires=[
            "pytest-runner",
        ],
        tests_require=[
            "pytest>=2.8.7",
        ],
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Apache Software License',
            'Natural Language :: English',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: C',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Topic :: Software Development',
            'Topic :: Software Development :: Libraries',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Utilities'
        ]
    )
