import ctypes
from textwrap import dedent

libInterop = ctypes.CDLL("lib/libinterop.dylib")

_cpp_compile = libInterop.Clang_Parse
_cpp_compile.restype = ctypes.c_int
_cpp_compile.argtypes = [ctypes.c_char_p]

_cpp_compile_execute = libInterop.Clang_ParseExecute
_cpp_compile_execute.restype = ctypes.c_int
_cpp_compile_execute.argtypes = [ctypes.c_char_p]


def cpp_compile(arg):
    return _cpp_compile(arg.encode("ascii"))


def cpp_compile_execute(arg):
    return _cpp_compile_execute(arg.encode("ascii"))


_get_scope = libInterop.Clang_LookupName
_get_scope.restype = ctypes.c_size_t
_get_scope.argtypes = [ctypes.c_char_p]


def get_scope(name):
    return _get_scope(name.encode("ascii"))


_construct = libInterop.Clang_CreateObject
_construct.restype = ctypes.c_void_p
_construct.argtypes = [ctypes.c_size_t]

_get_template_ct = libInterop.Clang_InstantiateTemplate
_get_template_ct.restype = ctypes.c_size_t
_get_template_ct.argtypes = [ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p]

_get_funcptr = libInterop.Clang_GetFunctionAddress
_get_funcptr.restype = ctypes.c_void_p
_get_funcptr.argtypes = [ctypes.c_size_t]


class CallCPPFunc:
    # Responsible for calling low-level function pointers.

    def __init__(self, func):
        # In real life this would normally go through the interop layer to know
        # whether to pass pointer, reference, or value of which type etc.
        proto = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p)
        self._funcptr = proto(_get_funcptr(func))

    def __call__(self, *args, **kwds):
        # See the comment above.
        a0 = ctypes.cast(args[0].cppobj, ctypes.POINTER(ctypes.c_void_p))
        a1 = args[1]
        a2 = args[2].cppobj
        return self._funcptr(a0, a1, a2)


def get_template(scope, name, tmpl_args=None, tpargs=None):
    if tpargs is None:
        tpargs = []
    if tmpl_args is None:
        tmpl_args = []

    if tmpl_args:
        # Instantiation is explicit from full name
        full_name = name + "<" + ", ".join([a for a in tmpl_args]) + ">"
        meth = _get_template_ct(scope, full_name.encode("ascii"), "".encode("ascii"))
    elif tpargs:
        # Instantiation is implicit from argument types
        meth = _get_template_ct(
            scope,
            name.encode("ascii"),
            (", ".join([a.__name__ for a in tpargs])).encode("ascii"),
        )
    else:
        # Instantiation is implicit from argument types
        meth = _get_template_ct(scope, name.encode("ascii"), "".encode("ascii"))
    return CallCPPFunc(meth)


def construct(cpptype):
    return _construct(cpptype)


def construct_with_arg(cpptype, arg):
    return _construct(cpptype, arg)


class TemplateWrapper:
    # Responsible for finding a template which matches the arguments.
    def __init__(self, scope, name):
        self._scope = scope
        self._name = name

    def __getitem__(self, *args, **kwds):
        # Look up the template and return the overload.
        return get_template(self._scope, self._name, tmpl_args=args)

    def __call__(self, *args, **kwds):
        # Keyword arguments are not supported for this demo.
        assert not kwds

        # Construct the template arguments from the types and find the overload.
        ol = get_template(self._scope, self._name, tpargs=[type(a) for a in args])

        # Call actual method.
        ol(*args, **kwds)


def cpp_allocate(proxy):
    pyobj = object.__new__(proxy)
    proxy.__init__(pyobj)
    pyobj.cppobj = construct(proxy.handle)
    return pyobj


def cpp_allocate_with_arg(proxy, arg):
    pyobj = object.__new__(proxy)
    proxy.__init__(pyobj)
    cppobj = construct_with_arg(proxy.handle, arg)
    pyobj.cppobj = cppobj
    return pyobj


if __name__ == "__main__":
    cpp_compile(
        dedent(
            r"""\
    class Main {
    public:
        int x;
        Main(int x) : x(x) {}
    };
    
    
    extern "C" int printf(const char*, ...);
    class A {};
    class C {};
    class B {
    public:
        template<typename T, typename S, typename U>
        static void callme(T, S, U*) { printf(" callme in B! \n"); }
    };
    """
        )
    )
    # create a couple of types to play with
    A = type("A", (), {"handle": get_scope("A"), "__new__": cpp_allocate})
    h = get_scope("B")
    B = type(
        "B",
        (A,),
        {"handle": h, "__new__": cpp_allocate, "callme": TemplateWrapper(h, "callme")},
    )
    C = type("C", (), {"handle": get_scope("C"), "__new__": cpp_allocate})

    # call templates
    a = A()
    b = B()
    c = C()

    # explicit template instantiation
    b.callme["A, int, C*"](a, 42, c)

    # implicit template instantiation
    b.callme(a, 42, c)

    Main = type(
        "Main", (), {"handle": get_scope("Main"), "__new__": cpp_allocate_with_arg}
    )

    m = Main(1)

    cpp_compile_execute(
        dedent(
            r"""\
    void printMain(void* m) {
        Main *m_ = static_cast<Main *>(m);
        printf(" callme in printMain! \n");
        printf("%d", m_->x);
    }
    """
        )
    )

    printMain = libInterop.Clang_LookupName("printMain".encode("ascii"))
    printMain = _get_funcptr(printMain)
    proto = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
    printMain = proto(printMain)

    m_ptr = ctypes.pointer(m)
    m0 = ctypes.cast(m_ptr, ctypes.POINTER(ctypes.c_void_p))
    printMain(m0)
