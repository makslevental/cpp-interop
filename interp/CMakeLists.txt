find_package(LLVM REQUIRED CONFIG)
find_package(Clang REQUIRED CONFIG)

message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

set(LLVM_RUNTIME_OUTPUT_INTDIR ${CMAKE_BINARY_DIR}/bin)
set(LLVM_LIBRARY_OUTPUT_INTDIR ${CMAKE_BINARY_DIR}/lib)

list(APPEND CMAKE_MODULE_PATH "${LLVM_CMAKE_DIR}")
list(APPEND CMAKE_MODULE_PATH "${CLANG_CMAKE_DIR}")

include(AddLLVM)
include(AddClang)
include(HandleLLVMOptions)

include_directories(${LLVM_INCLUDE_DIRS})
link_directories(${LLVM_BUILD_LIBRARY_DIR})
add_definitions(${LLVM_DEFINITIONS})

#add_clang_executable(interop main.cpp InterpreterUtils.cpp)
add_clang_library(interop InterpreterUtils.cpp)

llvm_map_components_to_libnames(LLVM_LIBS ${LLVM_TARGETS_TO_BUILD})

clang_target_link_libraries(interop
        PRIVATE
        clangAST
        clangAnalysis
        clangBasic
        clangCodeGen
        clangDriver
        clangFrontend
        clangFrontendTool
        clangLex
        clangParse
        clangSema
        clangSerialization
        clangInterpreter
        )

target_link_libraries(interop PRIVATE
        LLVMCore
        LLVMLineEditor
        LLVMOption
        LLVMOrcJIT
        LLVMSupport
        ${LLVM_LIBS}
        )


install(TARGETS interop DESTINATION lib)
set_target_properties(interop PROPERTIES PUBLIC_HEADER InterpreterUtils.h)
install(TARGETS interop
        PUBLIC_HEADER
        DESTINATION include
        )