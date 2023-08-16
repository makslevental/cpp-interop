#!/usr/bin/env bash
set -xe

clang -S -emit-llvm foo.cpp
clang -shared -o libfoo.so foo.cpp