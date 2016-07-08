# -*- coding: utf-8 -*-

import os
import sys
import re
import tarfile
import glob
from distutils.ccompiler import new_compiler
from distutils.errors import *


__all__ = ['WIN', 'STATIC_BUILD_DIR', 'STATIC_LIB', 'STATIC_LIB_NAME', 'StaticCompiler', 'touch', 'get_version']


WIN = sys.platform.startswith('win')

STATIC_BUILD_DIR = "build/static"
STATIC_LIB_NAME = "quickavro"
if WIN:
    STATIC_LIB = "{0}/{1}.lib".format(STATIC_BUILD_DIR, STATIC_LIB_NAME)
else:
    STATIC_LIB = "{0}/lib{1}.a".format(STATIC_BUILD_DIR, STATIC_LIB_NAME)


def fix_compile():
    import distutils.msvccompiler
    def _fix_compile(self, sources, output_dir=None, macros=None, include_dirs=None, debug=0,
                extra_preargs=None, extra_postargs=None, depends=None):

        if not self.initialized:
            self.initialize()
        compile_info = self._setup_compile(output_dir, macros, include_dirs,
                                           sources, depends, extra_postargs)
        macros, objects, extra_postargs, pp_opts, build = compile_info

        compile_opts = extra_preargs or []
        compile_opts.append ('/c')
        if debug:
            compile_opts.extend(self.compile_options_debug)
        else:
            compile_opts.extend(self.compile_options)

        for obj in objects:
            try:
                src, ext = build[obj]
            except KeyError:
                continue
            if debug:
                # pass the full pathname to MSVC in debug mode,
                # this allows the debugger to find the source file
                # without asking the user to browse for it
                src = os.path.abspath(src)

            # if src.endswith("generic.c") or 'avro' in src:
            if src.endswith("generic.c"):
                print("Compiling with C++: {0}".format(src))
                input_opt = "/Tp" + src
            elif ext in self._c_extensions:
                input_opt = "/Tc" + src
            elif ext in self._cpp_extensions:
                input_opt = "/Tp" + src
            elif ext in self._rc_extensions:
                # compile .RC to .RES file
                input_opt = src
                output_opt = "/fo" + obj
                try:
                    self.spawn([self.rc] + pp_opts +
                               [output_opt] + [input_opt])
                except DistutilsExecError as msg:
                    raise CompileError(msg)
                continue
            elif ext in self._mc_extensions:
                # Compile .MC to .RC file to .RES file.
                #   * '-h dir' specifies the directory for the
                #     generated include file
                #   * '-r dir' specifies the target directory of the
                #     generated RC file and the binary message resource
                #     it includes
                #
                # For now (since there are no options to change this),
                # we use the source-directory for the include file and
                # the build directory for the RC file and message
                # resources. This works at least for win32all.
                h_dir = os.path.dirname(src)
                rc_dir = os.path.dirname(obj)
                try:
                    # first compile .MC to .RC and .H file
                    self.spawn([self.mc] +
                               ['-h', h_dir, '-r', rc_dir] + [src])
                    base, _ = os.path.splitext (os.path.basename (src))
                    rc_file = os.path.join (rc_dir, base + '.rc')
                    # then compile .RC to .RES file
                    self.spawn([self.rc] +
                               ["/fo" + obj] + [rc_file])

                except DistutilsExecError as msg:
                    raise CompileError(msg)
                continue
            else:
                # how to handle this file?
                raise CompileError("Don't know how to compile %s to %s"
                                   % (src, obj))

            output_opt = "/Fo" + obj
            try:
                self.spawn([self.cc] + compile_opts + pp_opts +
                           [input_opt, output_opt] +
                           extra_postargs)
            except DistutilsExecError as msg:
                raise CompileError(msg)

        return objects

    distutils.msvccompiler.MSVCCompiler.compile = _fix_compile

fix_compile()


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

def pip_install(package):
    import pip
    pip.main(['install', package])

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

def rename_dir(files, name):
    if name is None:
        return files
    for f in files:
        if '/' not in f.path:
            continue
        parts = f.path.split('/', 1)
        f.path = "/".join([name, parts[1]])
    return files

def untar(path):
    with tarfile.open(path) as tar:
        tar.extractall("vendor", tar.getmembers())


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

        self.c.create_static_lib(objs, self.name.lower(), output_dir=STATIC_BUILD_DIR)
        sys.stderr.write("\n")

    def download(self, force=False):
        if exists("vendor/{0}".format(self.filename)) and not force:
            return
        sys.stderr.write("Downloading {0} ...\n".format(self.name))
        sys.stderr.write("="*32)
        sys.stderr.write("\n")
        download_file(self.url, "vendor/{0}".format(self.filename))
        sys.stderr.write("Downloaded successfully -> vendor/{0}\n\n".format(self.filename))

    def extract(self, force=False):
        if exists(self.source_dir):
            return
        untar("vendor/{0}".format(self.filename))
        self.setup()

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
