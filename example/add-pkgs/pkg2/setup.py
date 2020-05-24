"""Setup.py. """
import os
from pathlib import Path

import dynawheel as dw


namespace = "anamespace"
pkgname = "pkg2"
whlver = "1.0.0"

nm_pkg = f"{namespace}.{pkgname}"

is_nt = os.name == "nt"
os_cls = (
    "Operating System :: Microsoft :: Windows"
    if is_nt
    else "Operating System :: POSIX"
)
metadata_content = f"""Metadata-Version: 2.1
Name: {nm_pkg}
Version: {whlver}
Summary: DynaWheel add-pkgs example pkg1
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
    src_root_dir=Path("src"),
    pkgname=nm_pkg,
    whlver=whlver,
    arch="linux_x86_64",
    pyver="py3.8",
    whl_dest_dir=Path("../dist"),
    root_is_purelib=False,
    # abi = 'cp' + pyver[2:] if arch != 'any' else 'none'
    abi="none",
)
