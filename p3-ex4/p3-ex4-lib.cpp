/* See the LICENSE file in the project root for license terms. */

#include "p3-ex4-lib.h"

#include "clang/Basic/Version.h"
#include "clang/Config/config.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Interpreter/Interpreter.h"
#include "clang/Sema/Lookup.h"
#include "clang/Sema/TemplateDeduction.h"

#include "llvm/Support/TargetSelect.h"

#include <memory>
#include <iostream>
#include <sstream>
#include <vector>

using namespace clang;

llvm::ExitOnError ExitOnErr;

std::string MakeResourcesPath() {
    using namespace llvm;
#ifdef LLVM_BINARY_DIR
    StringRef Dir = LLVM_BINARY_DIR;
#else
    // Dir is bin/ or lib/, depending on where BinaryPath is.
    void *MainAddr = (void *) (intptr_t) MakeResourcesPath;
    std::string BinaryPath = llvm::sys::fs::getMainExecutable(/*Argv0=*/nullptr, MainAddr);

    // build/tools/clang/unittests/Interpreter/Executable -> build/
    StringRef Dir = sys::path::parent_path(BinaryPath);

    Dir = sys::path::parent_path(Dir);
    Dir = sys::path::parent_path(Dir);
    Dir = sys::path::parent_path(Dir);
    Dir = sys::path::parent_path(Dir);
    //Dir = sys::path::parent_path(Dir);
#endif// LLVM_BINARY_DIR
    SmallString<128> P(Dir);
    sys::path::append(P, CLANG_INSTALL_LIBDIR_BASENAME, "clang",
                      CLANG_VERSION_MAJOR_STRING);
    return P.str().str();
}

static std::unique_ptr<clang::Interpreter> CreateInterpreter() {
    clang::IncrementalCompilerBuilder CB;
    std::string ResourceDir = MakeResourcesPath();
    CB.SetCompilerArgs({"-resource-dir", ResourceDir.c_str(), "-std=c++20"});

    // Create the incremental compiler instance.
    std::unique_ptr<clang::CompilerInstance> CI;
    CI = ExitOnErr(CB.CreateCpp());

    // Create the interpreter instance.
    std::unique_ptr<Interpreter> Interp = ExitOnErr(Interpreter::create(std::move(CI)));

    return Interp;
}

class ExampleLibrary {
public:
    static clang::Interpreter *GetInterpreter() {
        if (!Instance) {
            Instance = std::unique_ptr<ExampleLibrary>(new ExampleLibrary());
        }
        return Instance->Interp;
    }

private:
    /// FIXME: Leaks the interpreter object due to D107087.
    ExampleLibrary() : Interp(CreateInterpreter().release()) {
    }
    struct LLVMInitRAII {
        LLVMInitRAII() {
            llvm::InitializeNativeTarget();
            llvm::InitializeNativeTargetAsmPrinter();
        }
        ~LLVMInitRAII() { llvm::llvm_shutdown(); }
    } LLVMInit;
    clang::Interpreter *Interp;
    static std::unique_ptr<ExampleLibrary> Instance;
};
std::unique_ptr<ExampleLibrary> ExampleLibrary::Instance = nullptr;

void Clang_Parse(const char *Code) {
    ExitOnErr(ExampleLibrary::GetInterpreter()->Parse(Code));
}

static LookupResult LookupName(Sema &SemaRef, const char *Name) {
    ASTContext &C = SemaRef.getASTContext();
    DeclarationName DeclName = &C.Idents.get(Name);
    LookupResult R(SemaRef, DeclName, SourceLocation(), Sema::LookupOrdinaryName);
    SemaRef.LookupName(R, SemaRef.TUScope);
    assert(!R.empty());
    return R;
}

Decl_t Clang_LookupName(const char *Name, Decl_t Context /*=0*/) {
    return LookupName(ExampleLibrary::GetInterpreter()->getCompilerInstance()->getSema(), Name).getFoundDecl();
}

FnAddr_t Clang_GetFunctionAddress(Decl_t D) {
    clang::FunctionDecl *FD = static_cast<clang::FunctionDecl *>(D);
    auto Addr = ExampleLibrary::GetInterpreter()->getSymbolAddress(FD);
    if (!Addr) {
        std::string mangledName;
        llvm::raw_string_ostream RawStr(mangledName);
        FD->dump(RawStr);
        std::cerr << "couldn't find addr for func: " << mangledName;
        return 0;
    }
    //return Addr.toPtr<void*>();
    return Addr->getValue();
    //return *Addr;
}

void *Clang_CreateObject(Decl_t RecordDecl) {
    clang::TypeDecl *TD = static_cast<clang::TypeDecl *>(RecordDecl);
    std::string Name = TD->getQualifiedNameAsString();
    const clang::Type *RDTy = TD->getTypeForDecl();
    clang::ASTContext &C = ExampleLibrary::GetInterpreter()->getCompilerInstance()->getASTContext();
    size_t size = C.getTypeSize(RDTy);
    void *loc = malloc(size);

    // Tell the interpreter to call the default ctor with this memory. Synthesize:
    // new (loc) ClassName;
    static unsigned counter = 0;
    std::stringstream ss;
    ss << "auto _v" << counter++ << " = "
       << "new ((void*)" << loc << ")" << Name << "();";

    if (auto Err = ExampleLibrary::GetInterpreter()->ParseAndExecute(ss.str())) {
      std::cerr << "couldn't create object for " << ss.str() << "\n";
      return nullptr;
    }

    return loc;
}

/// auto f = &B::callme<A, int, C*>;
Decl_t Clang_InstantiateTemplate(Decl_t Scope, const char *Name, const char *Args) {
    static unsigned counter = 0;
    std::stringstream ss;
    NamedDecl *ND = static_cast<NamedDecl *>(Scope);
    // Args is empty.
    // FIXME: Here we should call Sema::DeduceTemplateArguments (for fn addr) and
    // extend it such that if the substitution is unsuccessful to get out the list
    // of failed candidates, eg TemplateSpecCandidateSet.
    ss << "auto _t" << counter++ << " = &" << ND->getNameAsString() << "::"
       << Name;
    llvm::StringRef ArgList = Args;
    if (!ArgList.empty())
        ss << '<' << Args << '>';
    ss << ';';
    auto PTU1 = &llvm::cantFail(ExampleLibrary::GetInterpreter()->Parse(ss.str()));
    llvm::cantFail(ExampleLibrary::GetInterpreter()->Execute(*PTU1));

    //PTU1->TUPart->dump();

    VarDecl *VD = static_cast<VarDecl *>(*PTU1->TUPart->decls_begin());
    UnaryOperator *UO = llvm::cast<UnaryOperator>(VD->getInit());
    return llvm::cast<DeclRefExpr>(UO->getSubExpr())->getDecl();
}
