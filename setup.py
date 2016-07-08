# -*- coding: utf-8 -*-

import os
import sys
import re
import tarfile
import glob

import pip
from setuptools import setup, Extension, find_packages

from setup_utils import *

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if not PY3:
    FileNotFoundError = (IOError, OSError)

class Jansson(StaticCompiler):
    name = "Jansson"
    version = "2.7"
    url = "https://github.com/akheron/jansson/archive/v{0}.tar.gz".format(version)
    target = "jansson"
    filename = "jansson-{0}.tar.gz".format(version)

    include_dirs = [
        'vendor/jansson-{0}'.format(version),
        'vendor/jansson-{0}/src'.format(version),
    ]
    source_dir = "vendor/jansson-{0}/src".format(version)
    extra_compile_args = ['-DHAVE_STDINT_H', '-DJSON_INLINE=inline']

    def setup(self):
        try:
            touch(os.path.join(self.source_dir, "jansson_config.h"))
        except FileNotFoundError as error:
            pass


class Snappy(StaticCompiler):
    name = "Snappy"
    if WIN:
        version = "1.1.1.8"
        url = "https://github.com/kiddlu/snappy-windows/archive/master.tar.gz"
        filename = "snappy-windows-{0}.tar.gz".format(version)

        include_dirs = [
            'vendor/snappy-windows-master/src',
        ]
        source_dir = "vendor/snappy-windows-master/src"
    else:
        version = "1.1.3"
        url = "https://github.com/google/snappy/releases/download/{0}/snappy-{0}.tar.gz".format(version)
        filename = "snappy-{0}.tar.gz".format(version)

        include_dirs = [
            'vendor/snappy-{0}/src'.format(version),
        ]
        source_dir = "vendor/snappy-{0}/src".format(version)

    excluded = [
        "snappy-test.cc",
        "snappy_unittest.cc",
    ]
    extra_compile_args = ['-DSNAPPY_STATIC']


class AvroC(StaticCompiler):
    name = "Avro"
    version = "1.8.0"
    url = "https://github.com/apache/avro/archive/release-{0}.tar.gz".format(version)
    filename = "avro-{0}.tar.gz".format(version)

    include_dirs = [
        'vendor/avro-release-{0}/lang/c/src'.format(version),
        'vendor/avro-release-{0}/lang/c/src/avro'.format(version)
    ]
    include_dirs.extend(Jansson.include_dirs)

    source_dir = "vendor/avro-release-{0}/lang/c/src".format(version)
    excluded = [
        "schema_specific.c",
        "avroappend.c",
        "avrocat.c",
        "avromod.c",
        "avropipe.c",
    ]
    extra_compile_args = ['-DJSON_INLINE=inline']

    def setup(self):
        filename = "{0}/avro_private.h".format(self.source_dir)
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            try:
                n = lines.index('#define snprintf _snprintf\n')
                if "_WIN32" in lines[n-1]:
                    lines[n-1] = "#if _MSC_VER < 1900\n"
                    with open(filename, 'w') as f:
                        f.write("".join(lines))
                    print("Successfully patched '{0}'.".format(filename))
            except ValueError as error:
                pass
        except FileNotFoundError as error:
            pass

def compile_ext():
    force = True if '--force' in sys.argv else False
    libs = [Snappy(), Jansson(), AvroC()]
    # libs = [Snappy()]
    # libs = [AvroC()]
    for lib in libs:
        lib.download()
        lib.extract()
        lib.compile(force)
    # sys.exit()
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
