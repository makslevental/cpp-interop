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

set(LLVM_OPTIONAL_SOURCES p3-ex4.c p3-ex4-lib.cpp)
set(LLVM_LINK_COMPONENTS
  ${LLVM_TARGETS_TO_BUILD}
  Support
)
add_llvm_library(p3-ex4-lib SHARED p3-ex4-lib.cpp
  LINK_LIBS
  clangAST
  clangSema
  clangInterpreter
  )
install(TARGETS p3-ex4-lib DESTINATION p3-ex4)
set_source_files_properties(p3-ex4-lib.cpp
  PROPERTIES COMPILE_DEFINITIONS "LLVM_BINARY_DIR=\"${LLVM_BINARY_DIR}\"")
add_llvm_executable(p3-ex4 p3-ex4.c)
target_link_libraries(p3-ex4
  PRIVATE
  p3-ex4-lib
  )
# Makes the binary symbols visible to the JIT.
export_executable_symbols(p3-ex4)
install(TARGETS p3-ex4 DESTINATION p3-ex4)
