"""Require pyslang to load Slang from the conda environment's library directory."""

import ctypes
import sys
from pathlib import Path

import pyslang

prefix = Path(sys.prefix).resolve()
if sys.platform == "win32":
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
    kernel32.GetModuleHandleW.restype = ctypes.c_void_p
    handle = kernel32.GetModuleHandleW("svlang.dll")
    assert handle, "pyslang did not load svlang.dll"
    kernel32.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint]
    buffer = ctypes.create_unicode_buffer(32768)
    assert kernel32.GetModuleFileNameW(handle, buffer, len(buffer))
    libraries = [Path(buffer.value)]
    library_dir = prefix / "Library" / "bin"
elif sys.platform == "darwin":
    dyld = ctypes.CDLL(None)
    dyld._dyld_image_count.restype = ctypes.c_uint32
    dyld._dyld_get_image_name.argtypes = [ctypes.c_uint32]
    dyld._dyld_get_image_name.restype = ctypes.c_char_p
    libraries = [
        Path(dyld._dyld_get_image_name(i).decode())
        for i in range(dyld._dyld_image_count())
    ]
    library_dir = prefix / "lib"
else:
    libraries = [
        Path(line.split(maxsplit=5)[-1].strip())
        for line in Path("/proc/self/maps").read_text().splitlines()
    ]
    library_dir = prefix / "lib"

slang_libraries = [
    p.resolve() for p in libraries
    if p.name.startswith("libsvlang.") or p.name.lower() == "svlang.dll"
]
assert slang_libraries, "pyslang did not load the Slang shared library"
assert all(p.parent == library_dir.resolve() for p in slang_libraries), slang_libraries
print("Loaded conda Slang:", *slang_libraries)
