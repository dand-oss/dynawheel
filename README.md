# DynaWheel: dynamically composed wheel installations

___Relief for the system integrator___

## Benefit
   * Painlessly install into python without limitations

## Advantages
   * Treat wheels like tarballs
   * Create Cumulative, addtive, virtual packages
   * Make submodules which load their dlls into a common namepace
   * Put all your dlls alongside your c-extension pyds
   * Stop arranging your source into packages
   * Solve DLL Hell
   * Source directory heirarchy need not match installation heirarchy
   * Befriend CI
   * Avoid learning the interaction of "data_files" and "package_data" and MANIFEST.in and "py_modules" and "namespace_packages" and "packages" via experimentation

## Features
   * Requires no setup.py
   * Easily make nested namespaces
   * Install into python root or namespace root
   * "setup.py" can work more like a Dockerfile

# Quick PyPI server

Arrange your "wheelhouse" like so

```
somedir/
   namespace-mod/
       namespace.mod-1.0.0-py3.8-non-linux_x86_64.whl
```

Serve your private pypi with a one liner
```
python -m http.server --directory /somedir 8087
```

The SimpleHTTPServer will autoindex the directory witth pypi layout

Use your private pypi server
```
RUN pip install \
  --trusted-host localhost \
  -i http://localhost:8087 \
  namespace.mod
```

Configure pip for private server:

```
# ~/.config/pip/pip.conf

# allow access to pypi server on VPN
pip config set global.trusted-host localhost

# add index to search list
pip config set global.extra-index-url http://localhost:8087
```


You can load any file into docker with this trick...

build.bash
```
trap "exit" INT TERM
trap "kill 0" EXIT

declare -r PYPI_PORT="8087"
declare -r PYPI_SERVER="$(uname -n)"

# start pypi server in background
python -m http.server --directory /release/pypi ${PYPI_PORT} &

docker build
   --build-arg LOCAL_PYPI_SERVER="${PYPI_SERVER}" \
    --build-arg LOCAL_PYPI_PORT="${PYPI_PORT}" \
    --network=host \
    .
```

Dockerfile
```
FROM argbargle

ARG LOCAL_PYPI_SERVER=localhost
ARG LOCAL_PYPI_PORT=8087

RUN pip install \
  --trusted-host "$LOCAL_PYPI_SERVER" \
  -i "http://$LOCAL_PYPI_SERVER:$LOCAL_PYPI_PORT" \
  namespace.mod
```

Upload Wheels:
```
twine upload *.whl -r locahost
```

Configure Wheel uploading
```
# installation
pip install pypirc-chappers

# command
pypirc -s localhost -u uname -p uname -r http://locahost:8087
```


# "Cumulative" Packages Method


# Example Use Case

You want this result in your "python install"

```
python-root/
   a.txt                    # some data file
   bin/
      aexe                  # an exe
   ...
   site-packages/
      plat.py  # file in the root of site packages
      anamespace/           # your own namespace for packages
         mod.py             # a python file
         _mod.so            # a c extension
         suppport_mod.so    # a library required by the c extenssion
         loadme.so          # a plugin, perhaps dynamically loaded dlopen() or LoadLibrary() in _mod.so 
         more.so            # some extensions need quite a few dlls, like QT
         pkg_std/           # an old school package
            __init__.py
            ma.py
         pkg_ns/            # a namespace package
            mb.py
```

using

```
pip install pkg1.whl
pip install pkg2.whl
```

"stage" a directory for each wheel after your build
... just copy files from elsewhere

```
pkg1/
   setup.py                 # write or generate this [1]
   src/                     # just some subdir, not needed
      anamespace/           # avoids package name collision in site-packages root, not required
         apy.py
         _apy.so
         support.so
         pkg_std/
            __init__.py
            ma.py
         pkg_ns/
            mb.py
```
       
```
pkg2/                       # wheel has ZERO python files: still installs by distutils
   setup.py
   src /
      anamespace/           # free to use same namespace as prev
         loadme.so          # we can add more dlls here
         more.so
      pkg2-1.0.0.data.data/ # [2] this is part of the format standard
         scripts/
            aexe
         purelib/
            pure.py # not installed if platlib
         platlib/
            plat.py
         headers/
            a.h ?
         data/
            dat.tx
```
notes:

[1] no setup.py is needed, could be CI system staging an install.  setup.py is familair name.

[2] .data directory conventions
   * distutils supports the following install paths under ".data"
   * [Python 3: Installing Python Modules - Alternate Installations - The User Scheme](https://docs.python.org/3/install/index.html#alternate-installation)
   * [PEP 491 -- The Wheel Binary Package Format 1.9](https://www.python.org/dev/peps/pep-0491/#file-contents)
   * [github.com:pypa/pip/schema.py](https://github.com/pypa/pip/blob/master/src/pip/_internal/models/scheme.py)
```
    def __init__(
        self,
        platlib,  # type: str
        purelib,  # type: str
        headers,  # type: str
        scripts,  # type: str
        data,  # type: str
    ):
```
   * one of purelib or platlib is installed in root of site-packages - or anwhere the installer can be directed?

## setup.py for pkg1

```
import os
from pathlib import Path
import dynawheel as dw


namespace = 'anamespace'
pkgname = 'pkg2'
whlver = '1.0.0'

nm_pkg = f'{namespace}.{pkgname}'

is_nt = os.name == 'nt'
os_cls = 'Operating System :: Microsoft :: Windows' \
    if is_nt else 'Operating System :: POSIX'
metadata_content = f"""Metadata-Version: 2.1
Name: {nm_pkg}
Version: {whlver}
Summary: DynaWheel example pkg1
Home-page: UNKNOWN
Author: DynaWheel
Author-email: UNKNOWN
License: UNKNOWN
Platform: UNKNOWN
Classifier: Development Status :: 4 - Beta
Classifier: Environment :: Console
Classifier: Intended Audience :: Developers
Classifier: {os_cls}

UNKNOWN

"""

dw.dynawheel(
    metadata_content,
    src_root_dir=Path('src'),
    pkgname=nm_pkg,
    whlver=whlver,
    arch='linux_x86_64',
    pyver='py3.8',
    whl_dest_dir=Path('../dist'),
    root_is_purelib=False,
    # abi = 'cp' + pyver[2:] if arch != 'any' else 'none'
    abi='none')
```

## setup.py for pkg2

same boilerplate, just change the package name

diff pkg1/setup.py pkg2/setup.py

```diff
 namespace = 'anamespace'
-pkgname = 'pkg1'
+pkgname = 'pkg2'
 whlver = '1.0.0'
```

# The Story of DynaWheel

# An Installer Format, not an Install builder
   * [wheel.readthedocs.oi: The Story of Wheel](https://wheel.readthedocs.io/en/stable/story.html)
> Wheel is an *installation format*

... Like MSI.

> it’s simple enough that there really could be __alternate implementations__; the simplest (but less than ideal) installer is __nothing more than “unzip archive.whl”__ somewhere on sys.path.

> Of course there is a different way to massively simplify the install process. It’s called built or binary packages. You never have to run setup.py because __there is no setup.py__.

> Installation has two steps: ‘build package’; ‘install package’, and __you can skip the first step [build package__, have someone else do it for you, do it on another machine, or install the build system from a binary package and __let the build system handle the building__. 

**... Challenge accepted!**

If wheels are "just zip files" with "a bit of metadata" then why can't we transplant YOUR desired directory structure into site-packages? 

some people want:

[Python Microlibs](https://medium.com/@jherreras/python-microlibs-5be9461ad979)

"plugins", or "virtual packages" or "namespace packages" where multiple wheels can leave artifacts in the same namespace
[Python Namesapce Packages for TiddlyWeb](https://web.archive.org/web/20150425043954/http://cdent.tumblr.com/post/216241761/python-namespace-packages-for-tiddlyweb)

or to to distribute dlls for use in python
[discuss.python.org:1401 Packaging DLLS on Windows](https://discuss.python.org/t/packaging-dlls-on-windows/1401)
> but __ultimately there’s not enough coherence between build and runtime environments for packages on PyPI for it to actually be reliable.__

> Someone has to do some extra work to make the packages work together,[...] This person is the __system integrator__.


# A Ladder Up From DLL Hell

https://bugs.python.org/issue36085
> __the only totally reliable way is to put HelperLib.dll alongside my_module.pyd.__ Author: Steve Dower

Piling your dll(s)/so(s) alongside your C extensions IN ONE DIRECTORY under python is ONE WAY to "get it all to load" without environment changes to PATH or LD_LIBRARY_PATH

setuptools/distutils doesn't assist you in doing this (subit a PR if you can get them to do these things)

## Shared Library Background
Remeber back when shared libraries became prevelant?

   * stop repeating code via static linking,
   * substitute functionality at runtime,
   * reload libraries...
   * the OS is made of shared libraries!

# Shared Library System Integrator's Reference
___how to get your libraries to load from "directory with the pyd"___

## Linux/Mac/BSD
you can set "rpath" to "$ORIGIN" so that _.so are loaded along with any c-extension "_.so"

via linker option to gcc/clang
[Creating relocateable Linux executables by setting RPATH with $ORIGIN](https://medium.com/@nehckl0/creating-relocatable-linux-executables-by-setting-rpath-with-origin-45de573a2e98)

```
-Wl,-rpath="$ORIGIN"
```

via "configure"
```
configure LDFLAG="-Wl,-rpath=$ORIGIN"
```

in cmake use either

a global include
[The RPATH guide should set CMAKE_BUILD_WITH_INSTALL_RPATH](https://github.com/conan-io/conan/issues/3996)

```
default.cmake
  set(CMAKE_INSTALL_RPATH "$ORIGIN")
  set(CMAKE_BUILD_WITH_INSTALL_RPATH ON)
```

or per target
[stackoverflow - Prepent to RPATH](https://stackoverflow.com/questions/40079424/prepend-to-rpath)

```
set_target_properties(libname PROPERTIES
  BUILD_WITH_INSTALL_RPATH TRUE
  INSTALL_RPATH "$ORIGIN")
```

OR you can set the rpath after build, say during staging

[manpage - patchelf](http://manpages.ubuntu.com/manpages/cosmic/man1/patchelf.1.html)

```
patchelf --set-rpath "$ORIGIN" *.so
```

ala "auditwheel repair"
[github.com:pypa/auditwheel/repair.py](https://github.com/pypa/auditwheel/blob/master/auditwheel/repair.py)

## Windows

Use SetDllPath with the module path to load all your dlls "alongside" the pyd

windtl.cpp

```
// https://github.com/microsoft/Azure-Kinect-Sensor-SDK/blob/develop/src/dynlib/dynlib_windows.c

#incude <windows.h>

#include <fmt/ostream.h>
using namespace fmt::literals ;

// https://github.com/microsoft/Azure-Kinect-Sensor-SDK/blob/develop/src/dynlib/dynlib_windows.c
#include <pathcch.h>

extern bool add_current_module_to_search()
{
    HMODULE hModule = nullptr;

    if (GetModuleHandleEx(
            GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS,
            (LPCTSTR) add_current_module_to_search,
            &hModule) == 0)
    {
        throw std::runtime_error(
                "Failed to get current module ({})."_format(GetLastError()));
        return 0;
    }

    wchar_t dll_fpath[MAX_PATH];
    if (GetModuleFileNameW(hModule, dll_fpath, _countof(dll_fpath)) == 0)
    {
        throw std::runtime_error(
            "Failed to get current module file name ({})."_format(GetLastError()));
        return 0;
    }

    const auto result = PathCchRemoveFileSpec(dll_fpath, _countof(dll_fpath));
    if (result != S_OK)
    {
        throw std::runtime_error(
            "Failed to remove the file name from the path ({})."_format(result));
        return 0;
    }

    // This adds the directory of the current module (_pyoil.dll) to the loader's search path.
    // The loader for C code only loads from the path of the current executable, not the current
    // module. By adding the current module path, this will mimic how C# and Linux loads DLLs.
    const auto dllres = SetDllDirectoryW(dll_fpath);
    if (dllres == 0)
    {
        throw std::runtime_error(
            "Failed to add the directory to the DLL search path ({})."_format(GetLastError()));
    }

    return dllres;
}
```

Inside dllmain.cpp

```
// executed on load
static const auto trip_path = add_current_module_to_search();
```

Then just call LoadLibrary to load your DLLS from python namespace directory in addition to the norma PATH search.

If you use the LoadLibraryEx() call with 0 flags it will work like LoadLibrary().  If you pass any SEARCH_* flags to LoadLibraryEx, PATH will be ignored.

## Windows DLL Breakage History

Python 3.8 LoadLibrary() was modified to ignore OS PATH on Windows.

Dynload_win.c # c-extensions

3.7
https://github.com/python/cpython/blob/3.7/Python/dynload_win.c
```
        /* We use LoadLibraryEx so Windows looks for dependent DLLs
            in directory of pathname first. */
        /* XXX This call doesn't exist in Windows CE */
        hDLL = LoadLibraryExW(wpathname, NULL,
                              LOAD_WITH_ALTERED_SEARCH_PATH);
```

3.8
https://github.com/python/cpython/blob/master/Python/dynload_win.c
```
        hDLL = LoadLibraryExW(wpathname, NULL,
                              LOAD_LIBRARY_SEARCH_DEFAULT_DIRS |
                              LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR);
```

Similar "fix" for ctypes
   * looks like mandated "load_flags" is now "defaulted" "load_flags"
   * altougth "load_flags" parameter is undocumented https://docs.python.org/3/library/ctypes.html

callproc.c # ctypes

3.7
https://github.com/python/cpython/blob/3.7/Modules/_ctypes/callproc.c
```
    if (!PyArg_ParseTuple(args, "U|O:LoadLibrary", &nameobj, &ignored))
    ...
    hMod = LoadLibraryW(name);
```

3.8 
https://github.com/python/cpython/blob/master/Modules/_ctypes/callproc.c
```
    int load_flags = 0;
    ...
    if (!PyArg_ParseTuple(args, "U|i:LoadLibrary", &nameobj, &load_flags))
    ...
    /* bpo-36085: Limit DLL search directories to avoid pre-loading
     * attacks and enable use of the AddDllDirectory function.
     */
    hMod = LoadLibraryExW(name, NULL, (DWORD)load_flags);

```

How this breaking change was debated
   * https://bugs.python.org/issue36085

Python 3.8 woes
   * https://valdyas.org/fading/software/python-3-8-woes/
> even copying the Qt5 dll’s to the PyQt5 folder, using add_dll_directory in various ways, I would always get the same error.

> And now I’m stuck. Downgrading to Python 3.6 makes everything work again, 

A year later Conda still hasn't gotten 3.8 working
   * https://github.com/conda/conda/issues/9343
> commented on Mar 28

> The Anaconda 2020.02 Individiual Edition installers are still based upon Python 3.7 as __there are still a few key packages in the ecosystem which do not support Python 3.8.__

# Summary

this is more of a technique than code.

dynawheel is a short example of using the fundemental wheel module from PYPA to build packages:

rather going through distutils or setuptools, which impose conventions on you via the cruft of decades of evolution.

dynawheel is 50 lines, less than 5 lines *do* anything,

the "wheel" package is also small.

You can step through dynawheel and look at how the wheel is composed.

Use the source instead of googling!

```

from distutils import dist
from pathlib import Path
import shutil

# the reference implmentation...
from wheel.bdist_wheel import bdist_wheel
from wheel.wheelfile import WheelFile

...

    # location specified by standard
    dist_info_dir = src_root_dir / f'{pkgname}-{whlver}.dist-info'

    # make the output dirs
    whl_dest_dir.mkdir(parents=True, exist_ok=True)
    dist_info_dir.mkdir(parents=True, exist_ok=True)

    # write METADATA to .dist-info
    metadata_file = dist_info_dir / 'METADATA'
    with metadata_file.open('w') as mdfh:
        print(metadata_content, file=mdfh)

    # write WHEEL to .dist-info
    with _ctBdistWheel(root_is_purelib, dist_info_dir) as bw:
        bw.python_tag = pyver
        bw.plat_name_supplied = True
        bw.plat_name = arch
        if not root_is_purelib:
            bw.full_tag_supplied = True
            bw.full_tag = (pyver, abi, arch)

    wheel_name = f'{pkgname}-{whlver}-{pyver}-{abi}-{arch}.whl'
    wheel_path = whl_dest_dir / wheel_name
    # write *.whl on WheelFile.close()
    with WheelFile(wheel_path, 'w') as wf:
        # compose RECORD as hash of staged files - NOT written to .dist-info
        wf.write_files(src_root_dir)

    print(f'wrote {wheel_path}')

    # cleanup dist_info_dir we wrote to
    if cleanup_dist_info_dir:
        shutil.rmtree(dist_info_dir)
```
