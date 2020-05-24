"""
Dynamically create wheels.

The Folder heirarchy of .data directory directs file install location.

https://docs.python.org/3/install/index.html#alternate-installation
https://github.com/pypa/pip/blob/master/src/pip/_internal/models/scheme.py
    def __init__(
        self,
        platlib,  # type: str
        purelib,  # type: str
        headers,  # type: str
        scripts,  # type: str
        data,  # type: str
    ):

Reference:

https://github.com/pypa/wheel/blob/master/src/wheel/wheelfile.py
class WheelFile(ZipFile):

https://github.com/pypa/wheel/blob/master/src/wheel/bdist_wheel.py

https://github.com/pypa/wheel/blob/master/src/wheel/cli/convert.py

"""
import shutil
import typing
from dataclasses import dataclass
from pathlib import Path

from setuptools import dist
from wheel.bdist_wheel import bdist_wheel
from wheel.wheelfile import WheelFile

# the reference implmentation...


@dataclass
class _BdistWheelContextMgr:
    """Context manager class for bdist_wheel."""

    root_is_purelib: bool
    dist_info_dir: Path
    the_wheel: bdist_wheel = None

    def __post_init__(self) -> None:
        """Create the internal wheel instance."""

        class _BdistWheelTag(bdist_wheel):
            """Support for platlib tags."""

            full_tag_supplied = False
            full_tag = None

            def get_tag(self) -> str:
                """Get the tag wheel."""
                return (
                    self.full_tag
                    if self.full_tag_supplied and self.full_tag is not None
                    else bdist_wheel.get_tag(self)
                )

        self.the_wheel = (
            bdist_wheel(dist.Distribution())
            if self.root_is_purelib
            else _BdistWheelTag(dist.Distribution())
        )
        self.the_wheel.root_is_pure = self.root_is_purelib

    def __enter__(self) -> bdist_wheel:
        """Context manager enter."""
        return self.the_wheel

    def __exit__(
        self, atype: typing.Type, value: typing.Any, traceback: typing.Callable
    ) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Context manager close."""
        self.the_wheel.write_wheelfile(self.dist_info_dir)


def get_wheel_name(
    pkgname: str,
    version: str,
    plat_tag: str,
    python_tag: str,
    build_tag: str = None,
    abi_tag: str = "none",
) -> str:
    """
    Compose wheel name using paramters.

    :param pkgname: name of package
    :param version: version number for build, wheel file name
    :param plat_tag: architecture for wheel file name
    :param python_tag: python version for wheel file name
    :param build_tag: python version for wheel file name
    :param abi_tag: application binary interface
    :return: name of wheel
    """
    # https://www.python.org/dev/peps/pep-0491/#file-name-convention
    first = f"{pkgname}-{version}"
    last = f"{python_tag}-{abi_tag}-{plat_tag}.whl"
    return (
        f"{first}-{last}"
        if build_tag is None
        else f"{first}-{build_tag}-{last}"
    )


def dynawheel(
    metadata_content: str,
    src_root_dir: Path,
    pkgname: str,
    whlver: str,
    plat_name: str,
    python_tag: str,
    whl_dest_dir: Path = Path("dist"),
    root_is_purelib: bool = False,
    # abi = 'cp' + python_tag[2:] if plat_name != 'any' else 'none'
    build_tag: str = None,
    abi_tag: str = "none",
    cleanup_dist_info_dir: bool = True,
) -> Path:
    """
    Create wheels without setup.py in manner of zip file.

    :param metadata_content: string to write as METADATA file
    :param src_root_dir: directory containing namespace or package source
    :param pkgname: name of package
    :param whlver: version number for build, wheel file name
    :param plat_name: architecture for wheel file name
    :param python_tag: python version for wheel file name
    :param whl_dest_dir: where to write the wheel file
    :param root_is_purelib: is this a pure library
    :param build_tag:
    :param abi_tag: application binary interface
    :param cleanup_dist_info_dir:
    :return: path to wheel
    """
    # location specified by standard
    dist_info_dir = src_root_dir / f"{pkgname}-{whlver}.dist-info"

    # make the output dirs
    whl_dest_dir.mkdir(parents=True, exist_ok=True)
    dist_info_dir.mkdir(parents=True, exist_ok=True)

    # write METADATA to .dist-info
    metadata_file = dist_info_dir / "METADATA"
    with metadata_file.open("w") as mdfh:
        print(metadata_content, file=mdfh)

    # write WHEEL to .dist-info on close()
    with _BdistWheelContextMgr(root_is_purelib, dist_info_dir) as bdwheel:
        bdwheel.python_tag = python_tag
        bdwheel.plat_name_supplied = True
        bdwheel.plat_name = plat_name
        if not root_is_purelib:
            bdwheel.full_tag_supplied = True
            bdwheel.full_tag = (python_tag, abi_tag, plat_name)

    # tools parse the wheel name for info...
    wheel_name = get_wheel_name(
        pkgname, whlver, plat_name, python_tag, build_tag, abi_tag
    )
    wheel_path = whl_dest_dir / wheel_name

    with WheelFile(wheel_path, "w") as wheel_file:
        # compose RECORD as hash of staged files - NOT written to .dist-info
        wheel_file.write_files(src_root_dir)

    print(f"wrote {wheel_path}")

    # cleanup dist_info_dir we wrote to
    if cleanup_dist_info_dir:
        shutil.rmtree(dist_info_dir)

    return wheel_path
