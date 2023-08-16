import ctypes
import platform
from ctypes import cdll, sizeof, cast
from ctypes.util import find_library
from pathlib import Path

libc = cdll.LoadLibrary(find_library("c"))
libc.malloc.argtypes = [ctypes.c_size_t]
libc.malloc.restype = ctypes.c_void_p
libc.free.argtypes = [ctypes.c_void_p]

libc.printf.argtypes = [ctypes.c_char_p]

libc.printf("Hello World via Python -> libc\n".encode("ascii"))


def shlib_ext():
    if platform.system() == "Darwin":
        shlib_ext = "dylib"
    elif platform.system() == "Linux":
        shlib_ext = "so"
    elif platform.system() == "Windows":
        shlib_ext = "lib"
    else:
        raise NotImplementedError(f"unknown platform {platform.system()}")

    return shlib_ext


libfoo = ctypes.CDLL(
    str(Path(__file__).parent.absolute() / "lib" / f"libfoo.{shlib_ext()}")
)
MyClassCtor = libfoo._ZN7MyClassC1Ei

# even though void?
MyClassCtor.restype = ctypes.c_int
# the first argument here is the implicit `this`
MyClassCtor.argtypes = [ctypes.c_void_p, ctypes.c_int]

ptr = libc.malloc(1 * sizeof(ctypes.c_int32))
MyClassCtor(ptr, 42)

printMyClass = libfoo._Z12printMyClassP7MyClass
printMyClass.restype = ctypes.c_int
printMyClass.argtypes = [ctypes.c_void_p]

printMyClass(ptr)
