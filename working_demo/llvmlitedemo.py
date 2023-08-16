from ctypes import CFUNCTYPE, c_int

import llvmlite.binding as llvm

llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

llvm_ir = """
; ModuleID = 'test.cpp'
source_filename = "test.cpp"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

%class.MyClass = type { i8 }

@_ZN7MyClassC1Ei = dso_local unnamed_addr alias void (%class.MyClass*, i32), void (%class.MyClass*, i32)* @_ZN7MyClassC2Ei
@_ZN7MyClassC1EiMine = dso_local unnamed_addr alias void (i8*, i32), void (i8*, i32)* @_ZN7MyClassC2EiMine

define dso_local void @_ZN7MyClassC2Ei(%class.MyClass* noundef nonnull align 1 dereferenceable(1) %0, i32 noundef %1) unnamed_addr #0 align 2 {
  %3 = alloca %class.MyClass*, align 8
  %4 = alloca i32, align 4
  store %class.MyClass* %0, %class.MyClass** %3, align 8
  store i32 %1, i32* %4, align 4
  %5 = load %class.MyClass*, %class.MyClass** %3, align 8
  ret void
}

define dso_local void @_ZN7MyClassC2EiMine(i8* noundef nonnull align 1 dereferenceable(1) %0, i32 noundef %1) unnamed_addr #0 align 2 {
  %blah = bitcast i8* %0 to %class.MyClass*
  %3 = alloca %class.MyClass*, align 8
  %4 = alloca i32, align 4
  store %class.MyClass* %blah, %class.MyClass** %3, align 8
  store i32 %1, i32* %4, align 4
  %5 = load %class.MyClass*, %class.MyClass** %3, align 8
  ret void
}



define dso_local noundef i32 @main() #1 {
  %1 = alloca i8*, align 8
  %2 = call noalias i8* @malloc(i64 noundef 1) #3
  store i8* %2, i8** %1, align 8
  %3 = load i8*, i8** %1, align 8
  %4 = bitcast i8* %3 to %class.MyClass*
  call void @_ZN7MyClassC1Ei(%class.MyClass* noundef nonnull align 1 dereferenceable(1) %4, i32 noundef 1)
  call void @_ZN7MyClassC1EiMine(i8* noundef nonnull align 1 dereferenceable(1) %3, i32 noundef 1)
  ; %5 = alloca %class.MyClass*, align 8
  ; store %class.MyClass* %4, %class.MyClass** %5, align 8
  ret i32 0
}

declare noalias i8* @malloc(i64 noundef) #2
"""


def create_execution_engine():
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()
    # And an execution engine with an empty backing module
    backing_mod = llvm.parse_assembly("")
    engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
    return engine


def compile_ir(engine, llvm_ir):
    mod = llvm.parse_assembly(llvm_ir)
    mod.verify()
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()
    return mod


engine = create_execution_engine()
mod = compile_ir(engine, llvm_ir)

func_ptr = engine.get_function_address("_ZN7MyClassC1Ei")
print(func_ptr)

func_ptr = engine.get_function_address("main")

cfunc = CFUNCTYPE(c_int)(func_ptr)
res = cfunc()
print("main() =", res)
