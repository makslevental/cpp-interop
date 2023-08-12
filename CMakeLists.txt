cmake_minimum_required(VERSION 3.25)
project(interop)

set(CMAKE_CXX_STANDARD 17)

set(CMAKE_BUILD_WITH_INSTALL_NAME_DIR ON)

set(CMAKE_CXX_STANDARD
        17
        CACHE STRING "C++ standard to conform to")

add_subdirectory(interp)
add_subdirectory(other)
add_subdirectory(p3-ex4)