# PyInstaller hook for sqlite3
# Windows venvs do NOT copy DLLs into the venv; the C extension (_sqlite3.pyd)
# and the native sqlite3.dll live in the BASE interpreter's DLLs directory.
# PyInstaller's default hook scans sys.prefix/DLLs (the venv) which is absent,
# so it silently collects nothing and the frozen app crashes with
# "ModuleNotFoundError: No module named 'sqlite3'". We locate the files
# explicitly via sys.base_prefix.
import os
import sys

from PyInstaller.utils.hooks import collect_submodules

_hiddenimports = ["sqlite3", "_sqlite3"] + collect_submodules("sqlite3")


def _find_base_dlls():
    candidates = [
        os.path.join(sys.base_prefix, "DLLs"),
        os.path.join(sys.prefix, "DLLs"),
    ]
    for d in candidates:
        if os.path.isdir(d):
            return d
    return None


_dll_dir = _find_base_dlls()
_binaries = []
if _dll_dir:
    for _name in ("_sqlite3.pyd", "sqlite3.dll"):
        _p = os.path.join(_dll_dir, _name)
        if os.path.exists(_p):
            _binaries.append((_p, "."))

hiddenimports = _hiddenimports
binaries = _binaries
