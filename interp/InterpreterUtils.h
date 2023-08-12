//
// Created by maksim on 8/11/23.
//

#ifndef INTEROP_INTERPRETERUTILS_H
#define INTEROP_INTERPRETERUTILS_H


#include "clang/AST/DeclBase.h"
#include "clang/AST/Mangle.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Interpreter/Interpreter.h"
#include "clang/Sema/Lookup.h"
#include "clang/Sema/TemplateDeduction.h"

#include "llvm/Support/TargetSelect.h"

// Type aliases to make the core clearer.
typedef void *Decl_t;
typedef unsigned long FnAddr_t;
extern "C" {
// Parses C++ input.
void Clang_Parse(const char *Code);

void Clang_ParseExecute(const char *Code);
// Looks up a name in a given context.
Decl_t Clang_LookupName(const char *Name, Decl_t Context = nullptr);
// Creates an object of the given type and returns the allocated memory.
void *Clang_CreateObject(Decl_t RecordDecl, int x = 0);
// Instantiates a template within a given context
Decl_t Clang_InstantiateTemplate(Decl_t Context, const char *Name, const char *Args);
//// Returns the low-level name of the compiled function.
FnAddr_t Clang_GetFunctionAddress(Decl_t D);
}

#endif//INTEROP_INTERPRETERUTILS_H
