# -*- coding: utf-8 -*-

import os
import sys
import re
import tarfile

import pip
from setuptools import setup, Extension, find_packages
from distutils.ccompiler import new_compiler


STATIC_BUILD_DIR = "build/static"
STATIC_LIB_NAME = "quickavro"
STATIC_LIB = "{0}/lib{1}.a".format(STATIC_BUILD_DIR, STATIC_LIB_NAME)

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

def pip_install(package):
    pip.main(['install', package])

def download_file(url, path):
    try:
        import requests
    except ImportError:
        pip_install('requests')
        try:
            import requests
        except ImportError:
            sys.stderr.write("Unable to download setup dependencies\n")
    if not os.path.isdir("vendor"):
        os.mkdir("vendor")
    with open(path, 'wb') as f:
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception("{}: {}".format(r.status_code, r.text))
        f.write(r.content)
    return path

def rename_dir(files, name):
    if name is None:
        return files
    for f in files:
        if '/' not in f.path:
            continue
        parts = f.path.split('/', 1)
        f.path = "/".join([name, parts[1]])
    return files

def untar(path, strip=None):
    with tarfile.open(path) as tar:
        tar.extractall("vendor", rename_dir(tar.getmembers(), strip))

def get_version():
    version_regex = re.compile(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', re.MULTILINE)
    with open('quickavro/__init__.py', 'r') as f:
        return version_regex.search(f.read()).group(1)

source_files = [
    {
        "name": "Avro C",
        "version": "1.8.0",
        "url": "https://github.com/apache/avro/archive/release-{0}.tar.gz",
        "dir": "avro",
        "filename": "avro-{0}.tar.gz"
    },
    {
        "name": "Jansson",
        "version": "2.7",
        "url": "https://github.com/akheron/jansson/archive/v{0}.tar.gz",
        "dir": "jansson",
        "filename": "jansson-{0}.tar.gz"
    },
    {
        "name": "Snappy",
        "version": "1.1.3",
        "url": "https://github.com/google/snappy/releases/download/{0}/snappy-{0}.tar.gz",
        "dir": "snappy",
        "filename": "snappy-{0}.tar.gz"
    },
    {
        "name": "zlib",
        "version": "1.2.8",
        "url": "https://github.com/madler/zlib/archive/v{0}.tar.gz",
        "dir": "zlib",
        "filename": "zlib-{0}.tar.gz"
    }
]

def download_source_files():
    for f in source_files:
        url = f["url"].format(f["version"])
        filename = f["filename"].format(f["version"])
        target_path = "vendor/{0}".format(filename)
        untar(download_file(url, target_path), strip=f["dir"])

def compile_vendor_static(static_build_dir, static_lib_name):
    c = new_compiler()
    include_dirs = [ 
        #'vendor/zlib',
        'vendor/snappy',
        'vendor/jansson',
        'vendor/jansson/src',
        'vendor/avro/lang/c/src',
        'vendor/avro/lang/c/src/avro'
    ]   
    sources = [ 
        #'vendor/zlib/adler32.c',
        #'vendor/zlib/compress.c',
        #'vendor/zlib/crc32.c',
        #'vendor/zlib/deflate.c',
        #'vendor/zlib/gzclose.c',
        #'vendor/zlib/gzlib.c',
        #'vendor/zlib/gzread.c',
        #'vendor/zlib/gzwrite.c',
        #'vendor/zlib/infback.c',
        #'vendor/zlib/inffast.c',
        #'vendor/zlib/inflate.c',
        #'vendor/zlib/inftrees.c',
        #'vendor/zlib/trees.c',
        #'vendor/zlib/uncompr.c',
        #'vendor/zlib/zutil.c',
        'vendor/snappy/snappy-c.cc',
        'vendor/snappy/snappy-sinksource.cc',
        'vendor/snappy/snappy-stubs-internal.cc',
        # 'vendor/snappy/snappy-test.cc',
        'vendor/snappy/snappy.cc',
        # 'vendor/snappy/snappy_unittest.cc',
        'vendor/jansson/src/dump.c',
        'vendor/jansson/src/error.c',
        'vendor/jansson/src/hashtable.c',
        'vendor/jansson/src/hashtable_seed.c',
        'vendor/jansson/src/load.c',
        'vendor/jansson/src/memory.c',
        'vendor/jansson/src/pack_unpack.c',
        'vendor/jansson/src/strbuffer.c',
        'vendor/jansson/src/strconv.c',
        'vendor/jansson/src/utf.c',
        'vendor/jansson/src/value.c',
        'vendor/avro/lang/c/src/allocation.c',
        'vendor/avro/lang/c/src/array.c',
        'vendor/avro/lang/c/src/codec.c',
        'vendor/avro/lang/c/src/consume-binary.c',
        'vendor/avro/lang/c/src/consumer.c',
        'vendor/avro/lang/c/src/datafile.c',
        'vendor/avro/lang/c/src/datum.c',
        'vendor/avro/lang/c/src/datum_equal.c',
        'vendor/avro/lang/c/src/datum_read.c',
        'vendor/avro/lang/c/src/datum_size.c',
        'vendor/avro/lang/c/src/datum_skip.c',
        'vendor/avro/lang/c/src/datum_validate.c',
        'vendor/avro/lang/c/src/datum_value.c',
        'vendor/avro/lang/c/src/datum_write.c',
        'vendor/avro/lang/c/src/dump.c',
        'vendor/avro/lang/c/src/encoding_binary.c',
        'vendor/avro/lang/c/src/errors.c',
        'vendor/avro/lang/c/src/generic.c',
        'vendor/avro/lang/c/src/io.c',
        'vendor/avro/lang/c/src/map.c',
        'vendor/avro/lang/c/src/memoize.c',
        'vendor/avro/lang/c/src/resolved-reader.c',
        'vendor/avro/lang/c/src/resolved-writer.c',
        'vendor/avro/lang/c/src/resolver.c',
        'vendor/avro/lang/c/src/schema.c',
        'vendor/avro/lang/c/src/schema_equal.c',
        'vendor/avro/lang/c/src/st.c',
        'vendor/avro/lang/c/src/string.c',
        'vendor/avro/lang/c/src/value-hash.c',
        'vendor/avro/lang/c/src/value-json.c',
        'vendor/avro/lang/c/src/value-read.c',
        'vendor/avro/lang/c/src/value-sizeof.c',
        'vendor/avro/lang/c/src/value-write.c',
        'vendor/avro/lang/c/src/value.c',
        'vendor/avro/lang/c/src/wrapped-buffer.c',
    ]
    depends = [
        #'vendor/zlib/crc32.h',
        #'vendor/zlib/deflate.h',
        #'vendor/zlib/gzguts.h',
        #'vendor/zlib/inffast.h',
        #'vendor/zlib/inffixed.h',
        #'vendor/zlib/inflate.h',
        #'vendor/zlib/inftrees.h',
        #'vendor/zlib/trees.h',
        #'vendor/zlib/zconf.h',
        #'vendor/zlib/zlib.h',
        #'vendor/zlib/zutil.h',
        'vendor/snappy/snappy-c.h',
        'vendor/snappy/snappy-internal.h',
        'vendor/snappy/snappy-sinksource.h',
        'vendor/snappy/snappy-stubs-internal.h',
        'vendor/snappy/snappy-stubs-public.h',
        'vendor/snappy/snappy-test.h',
        'vendor/snappy/snappy.h',
        'vendor/jansson/src/hashtable.h',
        'vendor/jansson/src/jansson.h',
        'vendor/jansson/src/jansson_private.h',
        'vendor/jansson/src/lookup3.h',
        'vendor/jansson/src/strbuffer.h',
        'vendor/jansson/src/utf.h',
        'vendor/jansson/src/hashtable.h',
        'vendor/avro/lang/c/src/avro.h',
        'vendor/avro/lang/c/src/avro_generic_internal.h',
        'vendor/avro/lang/c/src/avro_private.h',
        'vendor/avro/lang/c/src/codec.h',
        'vendor/avro/lang/c/src/datum.h',
        'vendor/avro/lang/c/src/dump.h',
        'vendor/avro/lang/c/src/encoding.h',
        'vendor/avro/lang/c/src/schema.h',
        'vendor/avro/lang/c/src/st.h',
        'vendor/avro/lang/c/src/avro/allocation.h',
        'vendor/avro/lang/c/src/avro/basics.h',
        'vendor/avro/lang/c/src/avro/consumer.h',
        'vendor/avro/lang/c/src/avro/data.h',
        'vendor/avro/lang/c/src/avro/errors.h',
        'vendor/avro/lang/c/src/avro/generic.h',
        'vendor/avro/lang/c/src/avro/io.h',
        'vendor/avro/lang/c/src/avro/legacy.h',
        'vendor/avro/lang/c/src/avro/msinttypes.h',
        'vendor/avro/lang/c/src/avro/msstdint.h',
        'vendor/avro/lang/c/src/avro/platform.h',
        'vendor/avro/lang/c/src/avro/refcount.h',
        'vendor/avro/lang/c/src/avro/resolver.h',
        'vendor/avro/lang/c/src/avro/schema.h',
        'vendor/avro/lang/c/src/avro/value.h',
    ]
    extra_compile_args = ['-O3', '-fPIC', '-g', '-Wall', '-Wfatal-errors', '-DHAVE_STDINT_H', '-DJSON_INLINE=inline']
    touch('vendor/jansson/src/jansson_config.h')
    objs = c.compile(sources,
        include_dirs=include_dirs,
        extra_preargs=extra_compile_args,
        depends=depends
    )

    c.create_static_lib(objs, static_lib_name, output_dir=static_build_dir)

def compile_ext(static_lib):
    include_dirs = [
        os.path.join(os.getcwd(), "src"),
        #'vendor/zlib',
        'vendor/snappy',
        'vendor/jansson',
        'vendor/jansson/src',
        'vendor/avro/lang/c/src',
        'vendor/avro/lang/c/src/avro',
    ]
    libraries = ['stdc++']
    library_dirs = []
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
    extra_compile_args = ['-Wfatal-errors']
    linker_flags = ['-shared', '-Wl,--export-dynamic']

    macros = []
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
        extra_objects=[static_lib]
    )

def exists(path):
    try:
        with open(path):
            return True
    except (OSError, IOError):
        return False

if __name__ == '__main__':
    if not exists("vendor/avro"):
        download_source_files()
    if not exists(STATIC_LIB):
        sys.stderr.write("Compiling vendor static library ...\n")
        compile_vendor_static(STATIC_BUILD_DIR, STATIC_LIB_NAME)
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
            compile_ext(STATIC_LIB)
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
            'Development Status :: 5 - Production/Stable',
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
