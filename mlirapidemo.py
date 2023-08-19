import ctypes
import platform
from ctypes import cdll, sizeof, cast, POINTER, pointer, c_void_p, c_size_t
from ctypes.util import find_library
from pathlib import Path


libc = cdll.LoadLibrary(find_library("c"))
libc.malloc.argtypes = [c_size_t]
libc.malloc.restype = c_void_p
libc.free.argtypes = [c_void_p]

MLIRIR = cdll.LoadLibrary(
    "/Users/mlevental/dev_projects/llvm-project/cmake-build-release/lib/libMLIRIR.dylib"
)

mlirContextSize = MLIRIR._Z15mlirContextSizev
mlirContextSize.argtypes = [c_void_p]
mlirContextSize.restype = c_size_t

# int mlirContextSize() { return sizeof(MLIRContext); }
mlir_ctx_size = mlirContextSize(None)

ptr = libc.malloc(mlir_ctx_size)
# mlir::MLIRContext::MLIRContext(mlir::MLIRContext::Threading)
MLIRContext = MLIRIR._ZN4mlir11MLIRContextC1ENS0_9ThreadingE
MLIRContext.argtypes = [c_void_p]
MLIRContext.restype = c_void_p

mlir_context = MLIRContext(ptr)


# mlir::Float64Type::get(mlir::MLIRContext*)
MLIRIR._ZN4mlir11Float64Type3getEPNS_11MLIRContextE.argtypes = [c_void_p]
MLIRIR._ZN4mlir11Float64Type3getEPNS_11MLIRContextE.restype = c_void_p
f64 = MLIRIR._ZN4mlir11Float64Type3getEPNS_11MLIRContextE(mlir_context)


class Float64Type(ctypes.Structure):
    _fields_ = [("impl", ctypes.POINTER(ctypes.c_double))]


F64 = Float64Type()
F64.impl = ctypes.cast(f64, ctypes.POINTER(ctypes.c_double))

# void myMlirTypeDumpTypePointer(mlir::Float64Type *t) { t->dump(); }
# void myMlirTypeDumpVoid(void *t) {
#   auto *t_ = static_cast<mlir::Float64Type *>(t);
#   ::myMlirTypeDumpTypePointer(t_);
# }
# void myMlirTypeDumpType(mlir::Float64Type t) { ::myMlirTypeDumpTypePointer(&t); }

MLIRIR._Z25myMlirTypeDumpTypePointerPN4mlir11Float64TypeE(ctypes.pointer(F64))
MLIRIR._Z18myMlirTypeDumpVoidPv(ctypes.cast(ctypes.pointer(F64), ctypes.c_void_p))
MLIRIR._Z18myMlirTypeDumpTypeN4mlir11Float64TypeE(F64)

MLIRArith = cdll.LoadLibrary(
    "/Users/mlevental/dev_projects/llvm-project/cmake-build-release/lib/libMLIRArithDialect.dylib"
)

# mlir::arith::ConstantOp::build(mlir::OpBuilder&, mlir::OperationState&, mlir::TypedAttr)
