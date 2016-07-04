# -*- coding: utf-8 -*-

import os
import sys
import re
import tarfile
import glob

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

def exists(path):
    try:
        with open(path):
            return True
    except (OSError, IOError):
        return False

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


class StaticCompiler(object):
    name = None
    version = None
    url = None
    target = None
    filename = None

    include_dirs = []
    source_dir = None
    excluded = []
    sources = []
    depends = []

    extra_compile_args = []

    def __init__(self):
        self.c = new_compiler()
        self.default_compile_args = ['-O3', '-fPIC', '-g', '-Wall', '-Wfatal-errors']

    def compile(self, force=False):
        if exists(os.path.join(STATIC_BUILD_DIR, self.static_lib_name)) and not force:
            return
        sys.stderr.write("Compiling {0} to static library ...\n".format(self.name))
        sys.stderr.write("="*32)
        sys.stderr.write("\n")
        self.sources = [
            *glob.glob("{0}/*.c".format(self.source_dir)),
            *glob.glob("{0}/*.cc".format(self.source_dir)),
        ]
        self.depends = [
            *glob.glob("{0}/*.h".format(self.source_dir)),
            *glob.glob("{0}/*/*.h".format(self.source_dir))
        ]
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

        self.c.create_static_lib(objs, self.target, output_dir=STATIC_BUILD_DIR)
        sys.stderr.write("\n")

    def download(self, force=False):
        if exists("vendor/{0}".format(self.filename)) and not force:
            return
        sys.stderr.write("Downloading {0} ...\n".format(self.name))
        sys.stderr.write("="*32)
        sys.stderr.write("\n")
        untar(download_file(self.url, "vendor/{0}".format(self.filename)), strip=self.target)
        sys.stderr.write("Downloaded successfully -> vendor/{0}\n\n".format(self.filename))

    @property
    def static_lib_name(self):
        return "lib{0}.a".format(self.target)

    @property
    def static_library(self):
        return os.path.join(STATIC_BUILD_DIR, self.static_lib_name)


class Jansson(StaticCompiler):
    name = "Jansson"
    version = "2.7"
    url = "https://github.com/akheron/jansson/archive/v{0}.tar.gz".format(version)
    target = "jansson"
    filename = "jansson-{0}.tar.gz".format(version)

    include_dirs = [
        'vendor/jansson',
        'vendor/jansson/src',
    ]
    source_dir = "vendor/jansson/src"

    extra_compile_args = ['-DHAVE_STDINT_H', '-DJSON_INLINE=inline']
    touch(os.path.join(source_dir, "jansson_config.h"))


class Snappy(StaticCompiler):
    name = "Snappy"
    version = "1.1.3"
    url = "https://github.com/google/snappy/releases/download/{0}/snappy-{0}.tar.gz".format(version)
    target = "snappy"
    filename = "snappy-{0}.tar.gz".format(version)

    include_dirs = [
        'vendor/snappy',
    ]
    source_dir = "vendor/snappy"
    excluded = [
        "snappy-test.cc",
        "snappy_unittest.cc",
    ]


class AvroC(StaticCompiler):
    name = "Avro C"
    version = "1.8.0"
    url = "https://github.com/apache/avro/archive/release-{0}.tar.gz".format(version)
    target = "avro"
    filename = "avro-{0}.tar.gz".format(version)

    include_dirs = [
        'vendor/avro/lang/c/src',
        'vendor/avro/lang/c/src/avro'
    ]
    source_dir = "vendor/avro/lang/c/src"

    excluded = [
        "schema_specific.c",
    ]


def compile_ext():
    force = True if '--force' in sys.argv else False
    libs = [Snappy(), Jansson(), AvroC()]
    for lib in libs:
        lib.download()
        lib.compile(force)
    include_dirs = [
        os.path.join(os.getcwd(), "src"),
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
    for lib in libs:
        include_dirs += lib.include_dirs
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
